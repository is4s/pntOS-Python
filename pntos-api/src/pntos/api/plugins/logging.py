from typing import Protocol

from .common import CommonPlugin, LoggingLevel


class LoggingPlugin(CommonPlugin, Protocol):
    """
    Logging plugin.

    A plugin for logging out data to an arbitrary sink (e.g. console, file,
    network, etc.).
    """

    def log(
        self,
        source_plugin_type: type,
        source_plugin_identifier: str,
        level: LoggingLevel,
        message: str,
    ) -> None:
        """
        Log a string to the logging plugin's sink.

        `source_plugin_type` and `source_plugin_identifier` are information on the
        plugin that sent the logout, `level` is the event severity, and `message` the
        string contents to be logged.
        """
        pass
