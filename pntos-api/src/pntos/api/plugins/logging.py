"""Python API of pntOS."""

from abc import ABC, abstractmethod

from pntos.api import CommonPlugin, LoggingLevel


class LoggingPlugin(CommonPlugin, ABC):
    """
    Logging plugin.

    A plugin for logging out data to an arbitrary sink (e.g. console, file,
    network, etc.).
    """

    @abstractmethod
    def log(
        self,
        source_plugin_type: type[CommonPlugin],
        source_plugin_identifier: str,
        level: LoggingLevel,
        message: str,
    ) -> None:
        """
        Log a string to the logging plugin's sink.

        Args:
            source_plugin_type (type[CommonPlugin]): Information on the plugin that sent the logout.
            source_plugin_identifier (str): Information on the plugin that sent the logout.
            level (LoggingLevel): The event severity.
            message (str): The string contents to be logged.
        """
        pass
