from typing import Protocol

from .common import CommonPlugin, LoggingLevel, PluginTypes


class LoggingPlugin(CommonPlugin, Protocol):
    """
    A plugin for logging out data to an arbitrary sink (e.g. console, file,
    network, etc.).
    """

    def log(
        self,
        source_plugin_type: PluginTypes,
        source_plugin_identifier: str,
        level: LoggingLevel,
        message: str,
    ) -> None:
        """
        Log a string to the logging plugin's sink. `source_plugin_type` and
        `source_plugin_identifier` are information on the plugin that sent the
        logout, `level` is the event severity, and `message` the string
        contents to be logged.
        """
        pass
