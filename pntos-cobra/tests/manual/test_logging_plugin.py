import re
import time
from typing import Any

from pntos.api import (
    CommonPlugin,
    LoggingLevel as ll,
    LoggingPlugin,
    Mediator,
)
from pntos.cobra import StandardLoggingPlugin
from pntos.cobra.internal import SimpleMediator, StandardRegistry

expected_results: dict[ll, str] = {
    ll.DEBUG: '',
    ll.ERROR: '',
    ll.INFO: '',
    ll.WARN: '',
}


def remove_color_codes(input_string: str) -> str:
    ansi_escape = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', input_string)


def call(logging_plugin: StandardLoggingPlugin) -> None:
    logging_plugin.log(
        logging_plugin.__class__,
        logging_plugin.identifier,
        ll.INFO,
        'This is an INFO message',
    )
    logging_plugin.log(
        logging_plugin.__class__,
        logging_plugin.identifier,
        ll.DEBUG,
        'This is a DEBUG message',
    )
    logging_plugin.log(
        logging_plugin.__class__,
        logging_plugin.identifier,
        ll.WARN,
        'This is an WARNING message',
    )
    logging_plugin.log(
        logging_plugin.__class__,
        logging_plugin.identifier,
        ll.ERROR,
        'This is an ERROR message',
    )


def call_color_and_not(logging_plugin: StandardLoggingPlugin) -> None:
    logging_plugin.colorize = False
    print('Without color:')
    call(logging_plugin)
    print('With color:')
    logging_plugin.colorize = True
    call(logging_plugin)


def dummy_log(level: ll, message: str) -> None:
    pass


class DummyPlugin(CommonPlugin):
    def __init__(self, identifier: str) -> None:
        self.identifier = identifier

    def init_plugin(
        self,
        plugin_resources_location: str | None = None,
        mediator: Mediator | None = None,
    ) -> None:
        pass

    def shutdown_plugin(self) -> None:
        pass


def test_manual() -> None:
    """This is for user tests of the logger plugin, not for the pytest suite."""
    # Initialize registry through mediator to have config values for logger
    dummy_plugin = DummyPlugin('dummy plugin')
    registry = StandardRegistry(dummy_log)
    mediator = SimpleMediator(dummy_plugin.identifier, LoggingPlugin)
    SimpleMediator.registry = registry
    config_group = 'config/logging/all'
    colorize_key = 'force_colorize'
    global_log_level_key = 'default_log_level'

    kv_store = mediator.registry.batch_start(config_group)
    kv_store.set_value(colorize_key, True)
    kv_store.set_value(global_log_level_key, 'warn')
    kv_store.batch_end()

    # Initialize StandardLoggingPlugin and hand it the ready-made registry
    logging_plugin = StandardLoggingPlugin(identifier='my_logger')
    logging_plugin.init_plugin('', mediator)

    # Prove that it read the config file - expecting only WARN and ERROR with color
    print('\nPer config, expecting color and only WARN and ERROR message:\n')
    call(logging_plugin)

    # Now demonstrate all colorized and non-colorized logging levels
    print('\nTesting all log levels both colorized and not')
    logging_plugin.global_log_level = ll.DEBUG
    print('\nGLOBAL_LOG_LEVEL = DEBUG')
    call_color_and_not(logging_plugin)
    logging_plugin.global_log_level = ll.INFO
    print('\nGLOBAL_LOG_LEVEL = INFO')
    call_color_and_not(logging_plugin)
    logging_plugin.global_log_level = ll.WARN
    print('\nGLOBAL_LOG_LEVEL = WARN')
    call_color_and_not(logging_plugin)
    logging_plugin.global_log_level = ll.ERROR
    print('\nGLOBAL_LOG_LEVEL = ERROR')
    call_color_and_not(logging_plugin)


def remove_decimal_numbers(input_string: str) -> str:
    # Regular expression to match decimal numbers before or after / or :
    pattern = r'(?<=[:/])\d*\.?\d+|\d*\.?\d+(?=[:/])'
    # Substitute the matched decimal numbers with an empty string
    return re.sub(pattern, '', input_string)


def test(capsys: Any) -> None:
    # Initialize registry through mediator to have config values for logger
    dummy_plugin = DummyPlugin('dummy plugin')
    registry = StandardRegistry(dummy_log)
    mediator = SimpleMediator(dummy_plugin.identifier, LoggingPlugin)
    SimpleMediator.registry = registry

    # Initialize StandardLoggingPlugin and hand it the ready-made registry
    logging_plugin = StandardLoggingPlugin(identifier='my_logger')
    logging_plugin.init_plugin('', mediator)

    ### Set up expected results

    date_time_str = re.sub(r'\d', '', time.strftime(logging_plugin.date_time_format))

    info_str = (
        f'\033[37m[{date_time_str}]\033[0m\033[90m [StandardLoggingPlugin]'
        + '\033[0m\033[92m [INFO] \033[0mThis is an INFO message\n'
    )
    warn_str = (
        f'\033[37m[{date_time_str}]\033[0m\033[90m '
        + '[StandardLoggingPlugin]\033[0m\033[93m [WARN] \033[0mThis is an '
        + 'WARNING message\n'
    )
    error_str = (
        f'\033[37m[{date_time_str}]\033[0m\033[90m '
        + '[StandardLoggingPlugin]\033[0m\033[91m [ERROR] \033[0mThis is an '
        + 'ERROR message\n'
    )
    debug_str = (
        f'\033[37m[{date_time_str}]\033[0m\033[90m '
        + '[StandardLoggingPlugin]\033[0m\033[94m [DEBUG] \033[0mThis is a '
        + 'DEBUG message\n'
    )

    expected_results: dict[ll, str] = {
        ll.DEBUG: '',
        ll.ERROR: '',
        ll.INFO: '',
        ll.WARN: '',
    }
    without_color_str = 'Without color:\n'
    with_color_str = 'With color:\n'

    def set_expected_str(level: ll, levels_str: str) -> None:
        levels_str_wo_color = remove_color_codes(levels_str)
        color_and_not = (
            without_color_str + levels_str_wo_color + with_color_str + levels_str
        )
        expected_results[level] = color_and_not

    set_expected_str(ll.INFO, info_str + warn_str + error_str)
    set_expected_str(ll.WARN, warn_str + error_str)
    set_expected_str(ll.ERROR, error_str)
    set_expected_str(ll.DEBUG, info_str + debug_str + warn_str + error_str)

    capsys.readouterr()  # clear any previous output

    ### Test all colorized and non-colorized logging levels

    # DEBUG
    logging_plugin.global_log_level = ll.DEBUG
    call_color_and_not(logging_plugin)
    # Remove date and time integers for these tests
    captured = remove_decimal_numbers(capsys.readouterr().out)
    expected = expected_results[logging_plugin.global_log_level]
    assert captured == expected, (
        'Logger failed to log global_logging_level=DEBUG correctly. '
        + f'Expected:\n{expected}\nReceived:\n{captured}'
    )

    # INFO
    logging_plugin.global_log_level = ll.INFO
    call_color_and_not(logging_plugin)
    # Remove date and time integers for these tests
    captured = remove_decimal_numbers(capsys.readouterr().out)
    expected = expected_results[logging_plugin.global_log_level]
    assert captured == expected, (
        'Logger failed to log global_logging_level=INFO correctly. '
        + f'Expected:\n{expected}\nReceived:\n{captured}'
    )

    # WARN
    logging_plugin.global_log_level = ll.WARN
    call_color_and_not(logging_plugin)
    # Remove date and time integers for these tests
    captured = remove_decimal_numbers(capsys.readouterr().out)
    expected = expected_results[logging_plugin.global_log_level]
    assert captured == expected, (
        'Logger failed to log global_logging_level=WARN correctly. '
        + f'Expected:\n{expected}\nReceived:\n{captured}'
    )

    # ERROR
    logging_plugin.global_log_level = ll.ERROR
    call_color_and_not(logging_plugin)
    # Remove date and time integers for these tests
    captured = remove_decimal_numbers(capsys.readouterr().out)
    expected = expected_results[logging_plugin.global_log_level]
    assert captured == expected, (
        'Logger failed to log global_logging_level=ERROR correctly. '
        + f'Expected:\n{expected}\nReceived:\n{captured}'
    )

    ### Test date/time output of logger

    # Turn color off just to simplify things
    logging_plugin.colorize = False

    # Get a log message
    logging_plugin.log(
        logging_plugin.__class__,
        logging_plugin.identifier,
        ll.ERROR,
        'This is an ERROR message',
    )
    captured = capsys.readouterr().out

    # Get the expected datetime and the captured one from output
    captured_datetime = captured.split('] [')[0]
    expected_datetime = '[' + time.strftime(logging_plugin.date_time_format)

    # There is an edge case where the second rolls over between the log capture
    # and the line above, in which case we'll run it again. If it's wrong both
    # times, we've probably got a problem.
    if captured_datetime != expected_datetime:
        # Get a log message
        logging_plugin.log(
            logging_plugin.__class__,
            logging_plugin.identifier,
            ll.ERROR,
            'This is an ERROR message',
        )
        captured = capsys.readouterr().out

        # Get the date
        captured_datetime = captured.split('] [')[0]

    assert captured_datetime == expected_datetime, (
        f'Logger datetime log failed.\nExpected: {expected_datetime}, Received: {captured_datetime}.'
    )


if __name__ == '__main__':
    test_manual()
