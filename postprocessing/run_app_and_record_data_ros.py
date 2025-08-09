#!/usr/bin/env python3

import os
import pty
import shutil
import signal
import subprocess
import sys
import time
from subprocess import PIPE, Popen

from plot_results import plot_results

BAG_PATH = 'pntos_output'


def run_pntos(app_to_run: str = 'fusion_gps_ins_ros'):
    """Spin up pntOS and any supporting processes, wait, then spin them down."""

    # Remove any pre-existing output
    if os.path.exists(BAG_PATH):
        shutil.rmtree(BAG_PATH)
    processes = []
    try:
        # Note: start_new_session=True makes processes interruptable.
        print('Starting recording...')
        processes.append(
            Popen(
                ['ros2', 'bag', 'record', '-a', '-o', BAG_PATH], start_new_session=True
            )
        )
        print('Starting Cobra...')
        # Set unbuffered flag so the subprocess standard output can be read in real time
        cobra_process = Popen(
            ['python3', '-u', f'apps/{app_to_run}.py'],
            stdout=PIPE,
            text=True,
            bufsize=1,
            start_new_session=True,
        )
        processes.append(cobra_process)
        # Read standard output until 'Ctrl + C' is found which is only printed out when
        # `init_plugin` has been called on all plugins (e.g. Cobra is fully intialized)
        for line in cobra_process.stdout:
            if 'Ctrl + C' in line:
                print('Cobra Started Successfully')
                break

        # Note: using ros2 bag play --delay N does not work because the ROS
        # clock still starts immediately, which breaks Cobra.
        print('Starting playback...')
        master_fd, slave_fd = pty.openpty()
        processes.append(
            Popen(
                # Rate must be slow enough for fastest topics to be published
                # at full speed in the CI. See "Using ROS" docs.
                ['play-dataset', '-t', 'ros', '-r', '20'],
                stdin=slave_fd,
                start_new_session=True,
            )
        )

        # After a delay for subscription, send a space to start the data
        # Note: pty is used because processes[2].communicate(input=' ') isn't
        # working (even when text=True is used in the Popen constructor)
        time.sleep(3)
        os.write(master_fd, b' ')

        # Wait for any process to exit (an error has occurred, or playback has
        # finished successfully)
        while all(process.poll() is None for process in processes):
            time.sleep(0.5)
    finally:
        print('Stopping all processes...')
        for process in processes:
            # Note: os.killpg is used because process.terminate() or
            # process.kill() don't work for the processes that use Popen again
            # under the hood (i.e. play-dataset)
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGINT)
            except ProcessLookupError:
                pass  # Process already stopped
            process.wait()
        # Ensure all returncodes indicate success (otherwise, fail the test)
        assert all(process.returncode == 0 for process in processes)

    print('pntOS Finished')


def plot():
    bagfile = f'{BAG_PATH}/{BAG_PATH}_0.db3'
    if not os.path.exists(bagfile):
        bagfile = f'{BAG_PATH}/{BAG_PATH}_0.mcap'
        assert os.path.exists(bagfile)
    plot_results(bagfile, '/solution/cobra/pva', '/sensor/ins_d/pva')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        run_pntos()
    elif len(sys.argv) == 2:
        run_pntos(sys.argv[1])
    # Assuming everything ran correctly, generate the plots
    plot()
