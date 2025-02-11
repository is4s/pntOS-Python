from dataclasses import dataclass

from pntos.api import LoggingLevel

from .BaseConfig import BaseConfig


@dataclass
class LoggingConfig(BaseConfig):
    group: str

    log_level: LoggingLevel = LoggingLevel.WARN
    config_group: str = 'config/logging/all'
    colorize_key: str = 'force_colorize'
    global_log_level_key: str = 'default_log_level'
    global_log_level: LoggingLevel = LoggingLevel.INFO
    dt_fmt: str = '%d/%m/%Y %H:%M:%S'  # date-time format
