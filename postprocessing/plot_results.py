#!/usr/bin/env python3

from os import mkdir, path
from sys import argv

from lcm_stripper import harvest_by_channel
from plots import plot_solution


def plot_results(lcmlog):
    pntos_solution_channel = '/solution/cobra/pva'
    truth_channel = '/sensor/ins-d/pva'
    channels_to_harvest = [truth_channel, pntos_solution_channel]

    # Generate plots from LCM output
    data = harvest_by_channel(lcmlog, channels_to_harvest)

    log_dir = path.dirname(lcmlog)
    filt = path.basename(lcmlog).split('.')[0]
    filt_dir = path.join(log_dir, filt)
    if not path.exists(filt_dir):
        mkdir(filt_dir)

    print(f'Plotting results...')
    plot_solution(
        [pntos_solution_channel, data[pntos_solution_channel]],  # solution
        [truth_channel, data[truth_channel]],  # truth
        filt_dir,
        True,
    )
    print(f'Plots have been saved to {filt_dir}')


if __name__ == '__main__':
    if len(argv) > 1:
        plot_results(argv[1])
    else:
        raise Exception('Must provide path to LCM log file as first argument')
