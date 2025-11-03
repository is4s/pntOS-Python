from pntos.api import CommonPlugin, LoggingLevel, LoggingPlugin, Mediator
from pntos.cobra.utils import print_message


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

        if self.global_log_level >= level:
            print_message(
                level, plugin_id, message, self.colorize, self.date_time_format
            )
