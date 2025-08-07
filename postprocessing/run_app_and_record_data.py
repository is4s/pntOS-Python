#!/usr/bin/env python3

import sys
import io

from os import environ, path, remove
from site import getsitepackages
from subprocess import PIPE, Popen
from sys import argv, version_info
from time import sleep

from plot_results import plot_results

OUTPUT_LOG_FILENAME = 'pntos_output.log'


def run_pntos(app_to_run: str = 'fusion_gps_ins'):
    """Spin up pntOS and any supporting processes, wait, then spin them down."""
    # Remove any pre-existing output
    if path.exists(OUTPUT_LOG_FILENAME):
        remove(OUTPUT_LOG_FILENAME)

    # Start the relay
    venv = environ['VIRTUAL_ENV']
    minor = version_info.minor
    relay_process = Popen(
        [
            'java',
            '-classpath',
            f'{venv}/lib/python3.{minor}/site-packages/share/java/lcm.jar',
            'lcm.lcm.TCPService',
        ],
        stdout=PIPE,
        stderr=PIPE,
    )

    # Block until we get the first output, meaning it has finished spinning up.
    relay_process.stdout.readline()

    # Start the logger
    logger_process = Popen(
        ['lcm-logger', '--lcm-url=tcpq://', OUTPUT_LOG_FILENAME],
        stdout=PIPE,
        stderr=PIPE,
    )

    # Start the app
    cobra_process = Popen(['python3', '-u', f'apps/{app_to_run}.py'], stdout=PIPE, text=True, bufsize=1)
    for line in cobra_process.stdout:
        if 'Ctrl + C' in line:
            print('Cobra Started Successfully')
            break

    log_filename = None
    for site in getsitepackages():
        candidate = f'{site}/pntos_python_datasets/cobra_gps_ins_example_data.log'
        if path.exists(candidate):
            log_filename = candidate
            break
    if log_filename is None:
        raise Exception('Could not find log file.')

    # Start the log player
    logplayer_process = Popen(
        [
            'lcm-logplayer',
            '--lcm-url=tcpq://',
            '--speed=1000',
            log_filename,
        ],
        stdout=PIPE,
        stderr=PIPE,
    )

    # Wait until there is some network traffic reported.
    while True:
        line = relay_process.stdout.readline().decode()
        if not line or not ' 0.0 kB/s' in line:
            break

    # Wait until no more network traffic is reported.
    while True:
        line = relay_process.stdout.readline().decode()
        if not line or ' 0.0 kB/s' in line:
            break

    # Shut it all down
    logplayer_process.terminate()
    Popen(['pkill', 'lcm-logplayer'])  # lcm-logplayer command spawns a child process
    cobra_process.terminate()
    logger_process.terminate()
    relay_process.terminate()

    # I don't like it when output comes through after the program finishes.
    sleep(0.5)
    print('pntOS Finished')


if __name__ == '__main__':
    if len(argv) < 2:
        run_pntos()
    elif len(argv) == 2:
        run_pntos(argv[1])
    plot_results(OUTPUT_LOG_FILENAME, '/solution/cobra/pva', '/sensor/ins-d/pva')
