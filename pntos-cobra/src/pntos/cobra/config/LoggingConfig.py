from dataclasses import dataclass

from pntos.api import LoggingLevel


@dataclass
class LoggingConfig:
    log_level: LoggingLevel = LoggingLevel.WARN

    group: str = "/config/cobra/logging_config/default"
