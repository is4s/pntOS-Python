from typing import Protocol, Optional
import time

from pntos.api.plugins.common import LoggingLevel, Mediator
from pntos.api.plugins.logging import LoggingPlugin

global_log_level = LoggingLevel.INFO

class fmts:
    """
    Formats for printing to terminal
    """

    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


class SimpleLoggingPlugin(LoggingPlugin):
    config_group = "config/logging/all"
    colorize_key = "force_colorize"
    log_level_key = "default_log_level"
    log_level: str
    colorize = False  # Wether to print fancy outputs
    dt_fmt = "%d/%m/%Y %H:%M:%S"  # date-time format

    def init_plugin(
        self, plugin_resources_location: Optional[str], mediator: Optional[Mediator]
    ):
        if mediator:
            config = mediator.registry.batch_start(self.config_group)
            if config.has_key(self.colorize_key):
                self.colorize = config.get_value(self.colorize_key, bool)
            if config.has_key(self.log_level_key):
                self.log_level = config.get_value(self.log_level_key, str)
            else:
                self.log_level = 
            config.batch_end()

    def shutdown_plugin(self):
        return

    def log(
        self,
        source_plugin_type: type,
        source_plugin_identifier: str,
        level: LoggingLevel,
        message: str,
    ) -> None:
        """
        This implementation defines the following behavior:
            1. A config defines a global LoggingLevel for the plugin
            2. A logging request has a LoggingLevel and interacts with the global log level to determine if it will be output.

        The rules for the interaction between requested and global level are:
        -requested at INFO should print at global level(s):  INFO, DEBUG
        -requested at WARN should print at global level(s):  INFO, WARN, DEBUG
        -requested at DEBUG should print at global level(s): DEBUG
        -requested at ERROR should print at global level(s): INFO, WARN, DEBUG, ERROR

        or in other words
        -global level: ERROR - only shows ERROR
        -global level: WARN  - shows ERROR or WARN
        -global level: INFO  - shows ERROR, WARN, or INFO
        -global level: DEBUG - shows ERROR, WARN, INFO, or DEBUG
        """
        pass

    def level_to_str(level):
        match level:
            case LoggingLevel.DEBUG:
                return "debug"
            case LoggingLevel.INFO:
                return "info"
            case LoggingLevel.WARN:
                return "warning"
            case LoggingLevel.ERROR:
                return "error"
            case _:
                return "unknown"

    def output_time(self):
        if self.colorize:
            print(
                fmts.BOLD
                + fmts.HEADER
                + "["
                + time.strftime(self.dt_fmt)
                + "]"
                + fmts.ENDC,
                None,
            )
        else:
            print(
                fmts.BOLD + "[" + time.strftime(self.dt_fmt) + "] " + fmts.ENDC, end=""
            )
        pass

    def output_plugin_id(self):
        pass

    def terminal_print(self):
        pass


a = SimpleLoggingPlugin()
a.output_time()
