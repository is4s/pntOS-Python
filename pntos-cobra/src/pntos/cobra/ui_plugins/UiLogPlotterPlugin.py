import os

import matplotlib.pyplot as plt
import numpy as np
from analysis.lcm.data import LogData, PvaData
from analysis.lcm.log_readers import read_pva
from pntos.api import LoggingLevel, Mediator, Message, UiPlugin
from pntos.cobra.config import UiLogPlottingConfig, config_from_registry
from pntos.cobra.utils import plot_pva


class UiLogPlottingPlugin(UiPlugin):
    """
    A simple UI plugin that plots results from an LCM or ROS log file on shut down.
    This plugin ingests UiLogPlottingConfig from config group config/ui_logfile_plotting.
    """

    identifier: str
    mediator: Mediator

    def __init__(self, identifier: str) -> None:
        """
        A UI plotting plugin for LCM or ROS log files.

        Args:
            identifier (str): The plugin identifier passed to the
                :meth:`pntos.api.CommonPlugin.identifier` field.
        """
        self.identifier = identifier

    def init_plugin(
        self,
        plugin_resources_location: str | None = None,
        mediator: Mediator | None = None,
    ) -> None:
        """
        PntOS plugin initialization function.

        This is called by the pntOS system before calling any other function.
        """
        if mediator is not None:
            self.mediator = mediator

        config_group = 'config/ui_logfile_plotting'
        config = config_from_registry(UiLogPlottingConfig, self.mediator, config_group)
        if config is None:
            self.mediator.log_message(
                LoggingLevel.ERROR,
                'Unable to retrieve config from registry. No config given or incorrect config group given. Expects config group "config/ui_logfile_plotting".',
            )
            return
        self.logfile = config.logfile
        self.solution_channel = config.solution_channel
        self.truth_channel = config.truth_channel

    def shutdown_plugin(self) -> None:
        # Check if log file exist and is valid before plotting or skip and log a warning otherwise.
        # This check allows for a clean pntOS shutdown even if a log file doesn't exist or it is invalid.
        if not os.path.exists(self.logfile):
            self.mediator.log_message(
                LoggingLevel.WARN,
                f'[{self.logfile}] file does not exist. No results will be plotted.',
            )
            return
        with open(self.logfile, 'rb') as f:
            if f.read(4) != b'\xed\xa1\xda\x01':  # LCM log file magic bytes
                self.mediator.log_message(
                    LoggingLevel.WARN,
                    'Invalid LCM log file. No results will be plotted.',
                )
                return

        self._plot_results()

    def _harvest_data(self, channels: list[str]) -> LogData[PvaData]:
        # ROS bagfile
        if self.logfile.endswith('.db3') or self.logfile.endswith('.mcap'):
            from analysis.ros import RosBagReader

            return RosBagReader(self.logfile).harvest_topics(channels)

        # LCM logfile
        return read_pva(logfile=self.logfile, read_all=True)

    def _plot_results(
        self,
    ) -> None:
        log_data = self._harvest_data([self.solution_channel, self.truth_channel])

        solution = log_data.data[self.solution_channel]
        solution.label = 'Cobra Solution'
        truth = log_data.data[self.truth_channel]
        truth.label = 'Truth'

        # Flip truth RPY, as there is a bug in the smartcable (TODO: #236)
        truth_rpy = log_data.data[self.truth_channel].rpy
        log_data.data[self.truth_channel].rpy = np.transpose(
            np.stack((truth_rpy[:, 1], truth_rpy[:, 0], -truth_rpy[:, 2]))
        )
        plt.rcParams['figure.figsize'] = (10, 6)
        save_dir = os.path.join(
            os.path.dirname(self.logfile),
            os.path.splitext(os.path.basename(self.logfile))[0],
        )
        self.mediator.log_message(
            LoggingLevel.INFO,
            'Plotting results. Close all windows to continue shutdown.',
        )
        try:
            plot_pva(solution, truth, log_data.t0, save_dir=save_dir)
            self.mediator.log_message(LoggingLevel.INFO, f'Plots saved to {save_dir}.')
            plt.show()
        except KeyboardInterrupt:
            plt.close('all')

    def requires_main_thread(self) -> bool:
        return False

    def run_main_thread(self) -> None:
        pass
