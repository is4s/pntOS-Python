import time
from typing import Optional
from enum import Enum

from pntos.api.plugins.common import LoggingLevel, Mediator, PluginTypes
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


def plugin_type_to_string(plugin_type: Enum):
    match plugin_type:
        case PluginTypes.UNDEFINED_PLUGIN:
            return "undefined"
        case PluginTypes.CONTROLLER_PLUGIN:
            return "controller"
        case PluginTypes.FUSION_PLUGIN:
            return "fusion"
        case PluginTypes.FUSION_STRATEGY_PLUGIN:
            return "fusion_strategy"
        case PluginTypes.PLATFORM_INTEGRATION_PLUGIN:
            return "platform_integration"
        case PluginTypes.PREPROCESSOR_PLUGIN:
            return "preprocessor"
        case PluginTypes.INITIALIZATION_PLUGIN:
            return "initialization"
        case PluginTypes.DATABASE_PLUGIN:
            return "database"
        case PluginTypes.TRANSPORT_PLUGIN:
            return "transport"
        case PluginTypes.UI_PLUGIN:
            return "ui"
        case PluginTypes.ORCHESTRATION_PLUGIN:
            return "orchestration"
        case PluginTypes.ORCHESTRATION_STRATEGY_PLUGIN:
            return "orchestration_strategy"
        case PluginTypes.REGISTRY_PLUGIN:
            return "registry"
        case PluginTypes.INERTIAL_PLUGIN:
            return "inertial"
        case PluginTypes.STATE_MODELING_PLUGIN:
            return "state_modeling"
        case PluginTypes.LOGGING_PLUGIN:
            return "logging"
        case PluginTypes.UTILITY_PLUGIN:
            return "utility"
        case _:
            return "unknown"


class SimpleLoggingPlugin(LoggingPlugin):
    config_group = "config/logging/all"
    colorize_key = "force_colorize"
    global_log_level_key = "default_log_level"
    global_log_level = LoggingLevel.INFO
    colorize = False  # Wether to print fancy outputs
    dt_fmt = "%d/%m/%Y %H:%M:%S"  # date-time format

    def init_plugin(
        self, plugin_resources_location: Optional[str], mediator: Optional[Mediator]
    ):
        if mediator:
            config = mediator.registry.batch_start(self.config_group)
            if config.has_key(self.colorize_key):
                self.colorize = config.get_value(self.colorize_key, bool)
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
                            self.WARNF(
                                "logging level "
                                + global_log_level_temp
                                + " is unknown, remaining at "
                                + self.level_to_str(self.global_log_level)
                            )

                else:
                    self.INFOF(
                        "using hard-coded global logging level "
                        + self.level_to_str(self.global_log_level)
                    )
            else:
                self.INFOF(
                    "using hard-coded global logging level "
                    + self.level_to_str(self.global_log_level)
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
        pass

    def level_to_str(self, level: Enum):
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

    def INFOF(self, message: str):
        if (
            self.global_log_level is LoggingLevel.INFO
            or self.global_log_level is LoggingLevel.DEBUG
        ):
            if self.colorize:
                info_color = fmts.OKGREEN
                self.output_time()
                print(info_color + message + fmts.ENDC)
            else:
                self.output_time()
                print(message)

    def DEBUGF(self, message: str):
        if self.global_log_level is LoggingLevel.DEBUG:
            if self.colorize:
                dbg_color = fmts.OKCYAN
                self.output_time()
                print(dbg_color + message + fmts.ENDC)
            else:
                self.output_time()
                print(message)

    def WARNF(self, message: str):
        if self.global_log_level is not LoggingLevel.ERROR:
            if self.colorize:
                warn_color = fmts.WARNING
                self.output_time()
                print(warn_color + message + fmts.ENDC)
            else:
                self.output_time()
                print("Warning: " + message)

    def ERRORF(self, message: str):
        if self.colorize:
            err_color = fmts.FAIL
            self.output_time()
            print(err_color + message + fmts.ENDC)
        else:
            self.output_time()
            print("Error: " + message)
