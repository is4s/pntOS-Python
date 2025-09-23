#!/usr/bin/env python3

import os
from sys import argv

from plot_results import plot_results
from pntos.cobra.utils.lcm import run_pntos_with_log_transport

OUTPUT_LOG = 'pntos_output.log'


if __name__ == '__main__':
    app_to_run = argv[1] if len(argv) > 1 else 'apps/standard/gps_ins.py'
    run_pntos_with_log_transport(app_to_run, OUTPUT_LOG)
    if os.path.exists(OUTPUT_LOG):
        plot_results(OUTPUT_LOG, '/solution/pntos/pva', '/sensor/ins-d/pva')
    else:
        print(
            f'Cannot plot results. pntOS failed to generate output log "{OUTPUT_LOG}"'
        )
