import time

from pntos.api import LoggingLevel


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


level_to_color_map = {
    LoggingLevel.INFO: fmts.OKGREEN,
    LoggingLevel.WARN: fmts.WARNING,
    LoggingLevel.DEBUG: fmts.OKBLUE,
    LoggingLevel.ERROR: fmts.FAIL,
}


def get_time_str(colorize: bool, date_time_format: str) -> str:
    """Get the current system time as a string using the date-time format provided at construction."""
    if colorize:
        return f'{fmts.LTGRAY}[{time.strftime(date_time_format)}]{fmts.ENDC}'

    return f'[{time.strftime(date_time_format)}]'


def get_plugin_id_str(plugin_id: str, colorize: bool) -> str:
    """Get out the name of the plugin from which the message originated (e.g. ORCHESTRATION)."""
    if colorize:
        return f'{fmts.DRKGRAY} [{plugin_id}]{fmts.ENDC}'
    return f' [{plugin_id}]'


def get_log_level_str(level: LoggingLevel, colorize: bool) -> str:
    if colorize:
        color = level_to_color_map[level]
        return f'{color} [{level.name}] {fmts.ENDC}'
    return f' [{level.name}] '


def print_message(
    level: LoggingLevel,
    plugin_id: str,
    message: str,
    colorize: bool = True,
    date_time_format: str = '%d/%m/%Y %H:%M:%S',
) -> None:
    """Print a formatted message to the console.

    The printed message will be in the form:

        '<Time> <Plugin ID> <Log Level> <Message>'

    Args:
        level (LoggingLevel): Log-level associated with the message.
        plugin_id (str): ID identifying the type of plugin from which the message comes.
        message (str): The message to log.
        colorize (bool): Whether to add colorization to the logged message. Defaults to True.
        date_time_format (str): Format string for the logged timestamp.
    """
    time_str = get_time_str(colorize, date_time_format)
    plugin_id_str = get_plugin_id_str(plugin_id, colorize)
    log_level_str = get_log_level_str(level, colorize)

    print(f'{time_str}{plugin_id_str}{log_level_str}{message}')
