#!/usr/bin/env python3

import os
from sys import argv

from plot_results import plot_results
from pntos.cobra.utils import get_ros_bag_file, run_pntos_with_ros_transport
from pntos_python_datasets import EXAMPLE_ROS_LOG

OUTPUT_BAG = 'pntos_output'


if __name__ == '__main__':
    app_to_run = argv[1] if len(argv) > 1 else 'apps/advanced/gps_ins_ros.py'
    run_pntos_with_ros_transport(app_to_run, EXAMPLE_ROS_LOG, OUTPUT_BAG)

    bagfile = get_ros_bag_file(OUTPUT_BAG)
    plot_results(bagfile, '/solution/pntos/pva', '/sensor/ins_d/pva')
