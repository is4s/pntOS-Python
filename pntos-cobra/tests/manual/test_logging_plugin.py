import re

from pntos.api.plugins.common import LoggingLevel
from pntos.cobra.SimpleControllerPlugin import SimpleMediator
from pntos.cobra.SimpleLoggingPlugin import SimpleLoggingPlugin
from pntos.cobra.SimpleRegistryPlugin import SimpleRegistry

expected_results: dict[LoggingLevel, str] = {
    LoggingLevel.DEBUG: "Without color:\n[22/11/2024 14:33:24] [SimpleLoggingPlugin] [INFO] This is an INFO message\n[22/11/2024 14:33:24] [SimpleLoggingPlugin] [DEBUG] This is a DEBUG message\n[22/11/2024 14:33:24] [SimpleLoggingPlugin] [WARN] This is an WARNING message\n[22/11/2024 14:33:24] [SimpleLoggingPlugin] [ERROR] This is an ERROR message\nWith color:\n\x1b[37m[22/11/2024 14:33:24]\x1b[0m\x1b[90m [SimpleLoggingPlugin]\x1b[0m\x1b[92m [INFO] \x1b[0mThis is an INFO message\n\x1b[37m[22/11/2024 14:33:24]\x1b[0m\x1b[90m [SimpleLoggingPlugin]\x1b[0m\x1b[94m [DEBUG] \x1b[0mThis is a DEBUG message\n\x1b[37m[22/11/2024 14:33:24]\x1b[0m\x1b[90m [SimpleLoggingPlugin]\x1b[0m\x1b[93m [WARN] \x1b[0mThis is an WARNING message\n\x1b[37m[22/11/2024 14:33:24]\x1b[0m\x1b[90m [SimpleLoggingPlugin]\x1b[0m\x1b[91m [ERROR] \x1b[0mThis is an ERROR message\n",
    LoggingLevel.ERROR: "Without color:\n[// ::] [SimpleLoggingPlugin] [ERROR] This is an ERROR message\nWith color:\n\x1b[m[// ::]\x1b[m\x1b[m [SimpleLoggingPlugin]\x1b[m\x1b[m [ERROR] \x1b[mThis is an ERROR message\n",
    LoggingLevel.INFO: "Without color:\n[// ::] [SimpleLoggingPlugin] [INFO] This is an INFO message\n[// ::] [SimpleLoggingPlugin] [WARN] This is an WARNING message\n[// ::] [SimpleLoggingPlugin] [ERROR] This is an ERROR message\nWith color:\n\x1b[m[// ::]\x1b[m\x1b[m [SimpleLoggingPlugin]\x1b[m\x1b[m [INFO] \x1b[mThis is an INFO message\n\x1b[m[// ::]\x1b[m\x1b[m [SimpleLoggingPlugin]\x1b[m\x1b[m [WARN] \x1b[mThis is an WARNING message\n\x1b[m[// ::]\x1b[m\x1b[m [SimpleLoggingPlugin]\x1b[m\x1b[m [ERROR] \x1b[mThis is an ERROR message\n",
    LoggingLevel.WARN: "Without color:\n[// ::] [SimpleLoggingPlugin] [WARN] This is an WARNING message\n[// ::] [SimpleLoggingPlugin] [ERROR] This is an ERROR message\nWith color:\n\x1b[m[// ::]\x1b[m\x1b[m [SimpleLoggingPlugin]\x1b[m\x1b[m [WARN] \x1b[mThis is an WARNING message\n\x1b[m[// ::]\x1b[m\x1b[m [SimpleLoggingPlugin]\x1b[m\x1b[m [ERROR] \x1b[mThis is an ERROR message\n",
}


def call(a: SimpleLoggingPlugin):
    a.log(
        a.__class__, a.identifier, LoggingLevel.INFO, "This is an INFO message"
    )
    a.log(
        a.__class__, a.identifier, LoggingLevel.DEBUG, "This is a DEBUG message"
    )
    a.log(
        a.__class__,
        a.identifier,
        LoggingLevel.WARN,
        "This is an WARNING message",
    )
    a.log(
        a.__class__,
        a.identifier,
        LoggingLevel.ERROR,
        "This is an ERROR message",
    )


def call_color_and_not(a: SimpleLoggingPlugin):
    a.colorize = False
    print("Without color:")
    call(a)
    print("With color:")
    a.colorize = True
    call(a)


def manual_test():
    """This is for user tests of the logger plugin, not for the pytest suite."""
    # Initialize registry through mediator to have config values for logger
    registry = SimpleRegistry()
    mediator = SimpleMediator(registry, [])
    config_group = "config/logging/all"
    colorize_key = "force_colorize"
    global_log_level_key = "default_log_level"

    kv_store = mediator.registry.batch_start(config_group)
    kv_store.set_value(colorize_key, True)
    kv_store.set_value(global_log_level_key, "warn")
    kv_store.batch_end()

    # Initialize SimpleLoggingPlugin and hand it the ready-made registry
    a = SimpleLoggingPlugin(identifier="my_logger")
    a.init_plugin("", mediator)

    # Prove that it read the config file - expecting only WARN and ERROR with color
    print("\nPer config, expecting color and only WARN and ERROR message:\n")
    call(a)

    # Now demonstrate all colorized and non-colorized logging levels
    print("\nTesting all log levels both colorized and not")
    a.global_log_level = LoggingLevel.DEBUG
    print("\nGLOBAL_LOG_LEVEL = DEBUG")
    call_color_and_not(a)
    a.global_log_level = LoggingLevel.INFO
    print("\nGLOBAL_LOG_LEVEL = INFO")
    call_color_and_not(a)
    a.global_log_level = LoggingLevel.WARN
    print("\nGLOBAL_LOG_LEVEL = WARN")
    call_color_and_not(a)
    a.global_log_level = LoggingLevel.ERROR
    print("\nGLOBAL_LOG_LEVEL = ERROR")
    call_color_and_not(a)


def test(capsys):
    # Initialize registry through mediator to have config values for logger
    registry = SimpleRegistry()
    mediator = SimpleMediator(registry, [])
    config_group = "config/logging/all"
    colorize_key = "force_colorize"
    global_log_level_key = "default_log_level"

    test_str_1 = (
        "\033[37m[22/11/2024 11:33:23]\033[0m\033[90m "
        + "[SimpleLoggingPlugin]\033[0m\033[93m [WARN] \033[0mThis is an "
        + "WARNING message\n\033[37m[22/11/2024 11:33:23]\033[0m\033[90m "
        + "[SimpleLoggingPlugin]\033[0m\033[91m [ERROR] \033[0mThis is an "
        + "ERROR message\n"
    )

    kv_store = mediator.registry.batch_start(config_group)
    kv_store.set_value(colorize_key, True)
    kv_store.set_value(global_log_level_key, "warn")
    kv_store.batch_end()

    # Initialize SimpleLoggingPlugin and hand it the ready-made registry
    a = SimpleLoggingPlugin(identifier="my_logger")
    a.init_plugin("", mediator)

    # Prove that it read the config file - expecting only WARN and ERROR with color
    call(a)
    captured = capsys.readouterr()

    # Removes all integer values from strings so that mismatched timestamps aren't an issue.
    str_1 = re.sub(r"\d", "", captured.out)
    str_2 = re.sub(r"\d", "", test_str_1)
    assert (
        str_1 == str_2
    ), f"Config read failed. \nExpected:\n{str_2}Received:\n{str_1}"

    # Now test all colorized and non-colorized logging levels

    # DEBUG
    a.global_log_level = LoggingLevel.DEBUG
    call_color_and_not(a)
    # Remove date and time integers - TODO: test date and time
    captured = re.sub(r"\d", "", capsys.readouterr().out)
    expected = re.sub(r"\d", "", expected_results[a.global_log_level])
    assert captured == expected, (
        "Logger failed to log global_logging_level=DEBUG correctly. "
        + f"Expected:\n{expected}\nReceived:\n{captured}"
    )

    # INFO
    a.global_log_level = LoggingLevel.INFO
    call_color_and_not(a)
    # Remove date and time integers - TODO: test date and time
    captured = re.sub(r"\d", "", capsys.readouterr().out)
    expected = re.sub(r"\d", "", expected_results[a.global_log_level])
    assert captured == expected, (
        "Logger failed to log global_logging_level=INFO correctly. "
        + f"Expected:\n{expected}\nReceived:\n{captured}"
    )

    # WARN
    a.global_log_level = LoggingLevel.WARN
    call_color_and_not(a)
    # Remove date and time integers - TODO: test date and time
    captured = re.sub(r"\d", "", capsys.readouterr().out)
    expected = re.sub(r"\d", "", expected_results[a.global_log_level])
    assert captured == expected, (
        "Logger failed to log global_logging_level=WARN correctly. "
        + f"Expected:\n{expected}\nReceived:\n{captured}"
    )

    # ERROR
    a.global_log_level = LoggingLevel.ERROR
    call_color_and_not(a)
    # Remove date and time integers - TODO: test date and time
    captured = re.sub(r"\d", "", capsys.readouterr().out)
    expected = re.sub(r"\d", "", expected_results[a.global_log_level])
    assert captured == expected, (
        "Logger failed to log global_logging_level=ERROR correctly. "
        + f"Expected:\n{expected}\nReceived:\n{captured}"
    )


if __name__ == "__main__":
    manual_test()
