import time

from pntos.api import CommonPlugin, LoggingLevel, LoggingPlugin, Mediator


class fmts:
    """Formats for printing to terminal"""

    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    DRKGRAY = '\033[90m'
    LTGRAY = '\033[37m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    TAN = '\033[2m'
    WHITE = '\033[97m'


class StandardLoggingPlugin(LoggingPlugin):
    """
    A logging plugin that dictates the formatting and handles logging to the console.
    """

    def __init__(
        self,
        identifier: str,
        colorize: bool = True,
        global_log_level: LoggingLevel = LoggingLevel.INFO,
        date_time_format: str = '%d/%m/%Y %H:%M:%S',
    ) -> None:
        """
        Cobra Logging Plugin

        Args:
            identifier (str): Populates the ``CommonPlugin.identifier`` field.
            colorize (bool): Prints colored log messages if true, uncolored if false.
            global_log_level (LoggingLevel): Selects which log levels get printed. See
                :meth:`log` for more info.
            date_time_format (str): Specifies the date-time format according to the
                available format specifiers. See ``time.strftime()`` for more info on
                supported formats.
        """
        self.identifier = identifier
        self.colorize: bool = colorize
        self.global_log_level: LoggingLevel = global_log_level
        self.date_time_format: str = date_time_format

    def init_plugin(
        self,
        plugin_resources_location: str | None = None,
        mediator: Mediator | None = None,
    ) -> None:
        self.log(
            LoggingPlugin,  # type: ignore[type-abstract]
            self.identifier,
            LoggingLevel.INFO,
            'using hard-coded global logging level ' + self.global_log_level.name,
        )

    def shutdown_plugin(self) -> None:
        self.log(
            LoggingPlugin,  # type: ignore[type-abstract]
            self.identifier,
            LoggingLevel.INFO,
            ' Logging plugin shut down correctly.',
        )

    def log(
        self,
        source_plugin_type: type[CommonPlugin],
        source_plugin_identifier: str,
        level: LoggingLevel,
        message: str,
    ) -> None:
        """
        Log a message.

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
        INFO = LoggingLevel.INFO
        DEBUG = LoggingLevel.DEBUG
        WARN = LoggingLevel.WARN

        match level:
            case LoggingLevel.INFO:
                if self.global_log_level is INFO or self.global_log_level is DEBUG:
                    self._output_time()
                    self._output_plugin_id(plugin_id)
                    if self.colorize:
                        print(fmts.OKGREEN + ' [INFO] ' + fmts.ENDC, end='')
                    else:
                        print(' [INFO] ', end='')
                    print(message)
            case LoggingLevel.WARN:
                if (
                    self.global_log_level is INFO
                    or self.global_log_level is DEBUG
                    or self.global_log_level is WARN
                ):
                    self._output_time()
                    self._output_plugin_id(plugin_id)
                    if self.colorize:
                        print(fmts.WARNING + ' [WARN] ' + fmts.ENDC, end='')
                    else:
                        print(' [WARN] ', end='')
                    print(message)
            case LoggingLevel.DEBUG:
                if self.global_log_level is DEBUG:
                    self._output_time()
                    self._output_plugin_id(plugin_id)
                    if self.colorize:
                        print(fmts.OKBLUE + ' [DEBUG] ' + fmts.ENDC, end='')
                    else:
                        print(' [DEBUG] ', end='')
                    print(message)
            case LoggingLevel.ERROR:
                self._output_time()
                self._output_plugin_id(plugin_id)
                if self.colorize:
                    print(fmts.FAIL + ' [ERROR] ' + fmts.ENDC, end='')
                else:
                    print(' [ERROR] ', end='')
                print(message)

    def _output_time(self) -> None:
        """Prints out the current system time using the date-time format provided at construction."""
        if self.colorize:
            print(
                fmts.LTGRAY
                + '['
                + time.strftime(self.date_time_format)
                + ']'
                + fmts.ENDC,
                end='',
            )
        else:
            print('[' + time.strftime(self.date_time_format) + ']', end='')

    def _output_plugin_id(self, plugin_id: str) -> None:
        """Prints out the name of the plugin from which the message originated (e.g. ORCHESTRATION)."""
        if self.colorize:
            print(fmts.DRKGRAY + ' [' + plugin_id + ']' + fmts.ENDC, end='')
        else:
            print(' [' + plugin_id + ']', end='')
