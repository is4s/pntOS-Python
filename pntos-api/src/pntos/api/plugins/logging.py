from typing import Protocol

from .common import CommonPlugin, LoggingLevel


class LoggingPlugin(CommonPlugin, Protocol):
    def log(
        self,
        source_plugin_type: type,
        source_plugin_identifier: str,
        level: LoggingLevel,
        message: str,
    ) -> None:
        pass
