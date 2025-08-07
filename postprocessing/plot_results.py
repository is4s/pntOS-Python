#!/usr/bin/env python3

import argparse
from os import mkdir, path
from typing import Any

from plots import plot_solution


def harvest_data(logfile: str, channels: list[str]) -> dict[str, Any]:
    # ROS bagfile
    if logfile.endswith('.db3') or logfile.endswith('.mcap'):
        from ros_bag_reader import RosBagReader

        return RosBagReader(logfile).harvest_topics(channels)

    # LCM logfile
    with open(logfile, 'rb') as f:
        if f.read(4) != b'\xed\xa1\xda\x01':  # LCM logfile magic bytes
            raise ValueError(f'Invalid ROS/LCM log file: {logfile}')
    from lcm_stripper import harvest_by_channel

    return harvest_by_channel(logfile, channels)


def plot_results(logfile: str, solution_channel: str, truth_channel: str):
    data = harvest_data(logfile, [solution_channel, truth_channel])

    log_dir = path.dirname(logfile)
    filt = path.basename(logfile).split('.')[0]
    filt_dir = path.join(log_dir, filt)
    if not path.exists(filt_dir):
        mkdir(filt_dir)

    print(f'Plotting results...')
    try:
        plot_solution(
            [f'Cobra Solution ({solution_channel})', data[solution_channel]],
            [f'Truth ({truth_channel})', data[truth_channel]],
            filt_dir,
            True,
        )
    except IndexError as e:
        print(
            '*' * 16,
            'Hint: are the solution and truth channels set correctly?',
            '*' * 16,
        )
        raise e
    print(f'Plots have been saved to {filt_dir}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Generates plots from LCM or ROS log file.'
    )
    parser.add_argument('filename', help='Path to LCM or ROS log file')
    parser.add_argument(
        '-s', '--solution', default='/solution/cobra/pva', help='Solution channel name'
    )
    parser.add_argument(
        '-t', '--truth', default='/sensor/ins-d/pva', help='Truth channel name'
    )
    args = parser.parse_args()
    plot_results(args.filename, args.solution, args.truth)
