"""Python API of pntOS."""

from typing import Protocol

from pntos.api import CommonPlugin, LoggingLevel


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

        Args:
            source_plugin_type (type): Information on the plugin that sent the logout.
            source_plugin_identifier (str): Information on the plugin that sent the logout.
            level (LoggingLevel): The event severity.
            message (str): The string contents to be logged.
        """
        pass
