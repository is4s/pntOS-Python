#!/usr/bin/env python3

from pathlib import Path
from sys import argv

from plot_results import plot_results
from pntos.cobra.utils.lcm import run_pntos_with_log_transport

OUTPUT_LOG = Path('pntos_output.log')


if __name__ == '__main__':
    app_to_run = argv[1] if len(argv) > 1 else 'apps/standard/gps_ins.py'
    run_pntos_with_log_transport(Path(app_to_run), [OUTPUT_LOG.as_posix()])

    # Tutorial apps include UI plugin which automatically plots upon shutdown, so no need to plot again
    if 'tutorial' not in app_to_run:
        if OUTPUT_LOG.exists():
            plot_results(OUTPUT_LOG, '/solution/pntos/pva', '/sensor/ins-d/pva')
        else:
            print(
                f'Cannot plot results. pntOS failed to generate output log "{OUTPUT_LOG}"'
            )
