#!/usr/bin/env python3

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
from analysis.lcm.data import LogData, PvaData
from analysis.lcm.log_readers import read_pva
from pntos.cobra.utils import plot_pva


def harvest_data(logfile: Path, channels: list[str]) -> LogData[PvaData]:
    # ROS bagfile
    if logfile.suffix in {'.db3', '.mcap'}:
        from analysis.ros import RosBagReader  # noqa: PLC0415

        return RosBagReader(logfile).harvest_topics(channels)

    # LCM logfile
    return read_pva(logfile=logfile, read_all=True)


def plot_results(logfile: Path, solution_channel: str, truth_channel: str) -> None:
    log_data = harvest_data(logfile, [solution_channel, truth_channel])

    solution = log_data.data[solution_channel]
    solution.label = 'Cobra Solution'
    truth = log_data.data[truth_channel]
    truth.label = 'Truth'

    print('Plotting results...')
    plt.rcParams['figure.figsize'] = (10, 6)
    logfile = Path(logfile)
    save_dir = logfile.parent / logfile.stem
    plot_pva(solution, truth, log_data.t0, save_dir=save_dir)
    print(f'Plots saved to {save_dir}.')
    plt.show()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Generates plots from LCM or ROS log file.'
    )
    parser.add_argument('filename', help='Path to LCM or ROS log file', type=Path)
    parser.add_argument(
        '-s', '--solution', default='/solution/pntos/pva', help='Solution channel name'
    )
    parser.add_argument(
        '-t', '--truth', default='/sensor/ins-d/pva', help='Truth channel name'
    )
    args = parser.parse_args()
    plot_results(args.filename, args.solution, args.truth)
