#!/usr/bin/env python3

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from analysis.lcm.data import LogData, PvaData
from analysis.lcm.log_readers import read_pva
from pntos.api import LoggingLevel
from pntos.cobra.utils import load_from_hdf5_file, plot_pva, plot_x_and_p, print_message


def harvest_data(
    logfile: Path, channels: list[str], truth_channel: str
) -> LogData[PvaData]:
    # ROS bagfile
    if logfile.suffix in {'.db3', '.mcap'}:
        from analysis.ros import RosBagReader  # noqa: PLC0415

        return RosBagReader(logfile).harvest_topics(channels)

    # LCM logfile
    return read_pva(logfile=logfile, read_all=True, truth_channel=truth_channel)


def plot_results(
    logfile: Path,
    solution_channel: str,
    truth_channel: str,
    hdf5_file: Path | None = None,
) -> None:
    log_data = harvest_data(
        logfile, [solution_channel, truth_channel], truth_channel=truth_channel
    )

    solution = log_data.data[solution_channel]
    solution.label = 'Cobra Solution'
    truth = log_data.data[truth_channel]
    truth.label = 'Truth'

    print('Plotting results...')
    plt.rcParams['figure.figsize'] = (10, 6)
    plt.rcParams['figure.max_open_warning'] = 0

    logfile = Path(logfile)
    save_dir = logfile.parent / logfile.stem
    plot_pva(solution, truth, log_data.t0, save_dir=save_dir)
    print(f'Plots saved to {save_dir}.')

    if hdf5_file:

        def log(level: LoggingLevel, message: str) -> None:
            print_message(level, 'Postprocessing', message)

        h5_data = load_from_hdf5_file(hdf5_file, log)

        for key in ['state_labels', 'time', 'estimate', 'sigma']:
            if key not in h5_data:
                log(
                    LoggingLevel.WARN,
                    f'Missing key {key} in {hdf5_file.as_posix()}. Cannot create state estimate plots.',
                )
                plt.show()
                return
        state_labels = h5_data['state_labels'][0]
        time_ns = np.array(h5_data['time'])
        t0_ns = time_ns[0]
        time_s = (time_ns - t0_ns) / 1e9
        t0_s = t0_ns / 1e9
        plot_x_and_p(
            time_s,
            t0_s,
            state_labels,
            np.array(h5_data['estimate']),
            np.array(h5_data['sigma']),
            save_dir,
        )

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
    parser.add_argument(
        '--hdf5-file',
        type=Path,
        help='Optional path to HDF5 file containing state estimate and covariance.',
    )
    args = parser.parse_args()
    plot_results(args.filename, args.solution, args.truth, args.hdf5_file)
