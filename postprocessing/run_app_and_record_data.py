#!/usr/bin/env python3

import os
import signal
from subprocess import PIPE, Popen
from sys import argv

from plot_results import plot_results

OUTPUT_LOG_FILENAME = 'pntos_output.log'


def run_pntos(app_to_run: str = 'tutorial/gps_ins'):
    """Spin up pntOS, process log, then shut down."""
    # Remove output log if it exists
    if os.path.exists(OUTPUT_LOG_FILENAME):
        os.remove(OUTPUT_LOG_FILENAME)
    # Start the app
    # Set unbuffered flag so the subprocess standard output can be read in real time
    cobra_process = Popen(
        ['python3', '-u', f'apps/{app_to_run}.py', OUTPUT_LOG_FILENAME],
        stdout=PIPE,
        text=True,
        bufsize=1,
    )

    # Wait until pntOS is done processing the LCM log
    done_msg = 'Done processing LCM log. Press Ctrl + C to shut down pntOS.'
    for line in cobra_process.stdout:
        if done_msg in line:
            # Send interrupt signal to shut down pntOS cleanly
            cobra_process.send_signal(signal.SIGINT)

    print('pntOS Finished')


if __name__ == '__main__':
    if len(argv) < 2:
        run_pntos()
    elif len(argv) == 2:
        run_pntos(argv[1])
    if os.path.exists(OUTPUT_LOG_FILENAME):
        plot_results(OUTPUT_LOG_FILENAME, '/solution/pntos/pva', '/sensor/ins-d/pva')
    else:
        print(f'pntOS failed to generate output log "{OUTPUT_LOG_FILENAME}"')
