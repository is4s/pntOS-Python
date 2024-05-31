import time
from typing import Optional

from pntos.api.plugins.common import LoggingLevel, Mediator
from pntos.api.plugins.logging import LoggingPlugin

global_global_log_level = LoggingLevel.INFO


class fmts:
    """
    Formats for printing to terminal
    """

    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    DRKGRAY = "\033[90m"
    LTGRAY = "\033[37m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    TAN = "\033[100m"


class SimpleLoggingPlugin(LoggingPlugin):
    config_group: str = "config/logging/all"
    colorize_key: str = "force_colorize"
    global_log_level_key: str = "default_log_level"
    global_log_level: LoggingLevel = LoggingLevel.INFO
    colorize: bool = False
    dt_fmt: str = "%d/%m/%Y %H:%M:%S"  # date-time format

    def __init__(self, identifier: str):
        self.identifier = identifier

    def init_plugin(
        self, plugin_resources_location: Optional[str], mediator: Optional[Mediator]
    ):
        if mediator:
            config = mediator.registry.batch_start(self.config_group)
            if config.has_key(self.colorize_key):
                self.colorize
                config_colorize = config.get_value(self.colorize_key, bool)
                if config_colorize is not None:
                    self.colorize = config_colorize
            if config.has_key(self.global_log_level_key):
                global_log_level_temp = config.get_value(self.global_log_level_key, str)
                if global_log_level_temp is not None:
                    match global_log_level_temp:
                        case "error":
                            self.global_log_level = LoggingLevel.ERROR
                        case "debug":
                            self.global_log_level = LoggingLevel.DEBUG
                        case "warn":
                            self.global_log_level = LoggingLevel.WARN
                        case "info":
                            self.global_log_level = LoggingLevel.INFO
                        case _:
                            self.log(
                                self.__class__,
                                "",
                                LoggingLevel.INFO,
                                "logging level "
                                + global_log_level_temp
                                + " is unknown, remaining at "
                                + self.level_to_str(self.global_log_level),
                            )

                else:
                    self.log(
                        self.__class__,
                        "",
                        LoggingLevel.INFO,
                        "using hard-coded global logging level "
                        + self.level_to_str(self.global_log_level),
                    )
            else:
                self.log(
                    self.__class__,
                    "",
                    LoggingLevel.INFO,
                    "using hard-coded global logging level "
                    + self.level_to_str(self.global_log_level),
                )
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
        plugin_id = source_plugin_type.__name__
        GLL = self.global_log_level
        INFO = LoggingLevel.INFO
        DEBUG = LoggingLevel.DEBUG
        WARN = LoggingLevel.WARN

        match level:
            case LoggingLevel.INFO:
                if GLL is INFO or GLL is DEBUG:
                    self.output_time()
                    self.output_plugin_id(plugin_id)
                    if self.colorize:
                        print(fmts.OKGREEN + " [INFO] " + fmts.ENDC, end="")
                    else:
                        print(" [INFO] ", end="")
                    print(message)
            case LoggingLevel.WARN:
                if GLL is INFO or GLL is DEBUG or GLL is WARN:
                    self.output_time()
                    self.output_plugin_id(plugin_id)
                    if self.colorize:
                        print(fmts.WARNING + " [WARN] " + fmts.ENDC, end="")
                    else:
                        print(" [WARN] ", end="")
                    print(message)
            case LoggingLevel.DEBUG:
                if GLL is DEBUG:
                    self.output_time()
                    self.output_plugin_id(plugin_id)
                    if self.colorize:
                        print(fmts.OKBLUE + " [DEBUG] " + fmts.ENDC, end="")
                    else:
                        print(" [DEBUG] ", end="")
                    print(message)
            case LoggingLevel.ERROR:
                self.output_time()
                self.output_plugin_id(plugin_id)
                if self.colorize:
                    print(fmts.FAIL + " [ERROR] " + fmts.ENDC, end="")
                else:
                    print(" [ERROR] ", end="")
                print(message)
            case _:
                self.output_time()
                self.output_plugin_id(plugin_id)
                if self.colorize:
                    print(fmts.TAN + " [UNKOWN LOG LEVEL] " + fmts.ENDC, end="")
                else:
                    print(" [UNKNOWN LOG LEVEL] ", end="")
                print(message)

    def level_to_str(self, level: LoggingLevel):
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
                + fmts.LTGRAY
                + "["
                + time.strftime(self.dt_fmt)
                + "]"
                + fmts.ENDC,
                None,
            )
        else:
            print("[" + time.strftime(self.dt_fmt) + "]", end="")
        pass

    def output_plugin_id(self, plugin_id: str):
        if self.colorize:
            print(
                fmts.DRKGRAY + " [" + plugin_id + "]" + fmts.ENDC,
                None,
            )
        else:
            print(" [" + plugin_id + "]", end="")
