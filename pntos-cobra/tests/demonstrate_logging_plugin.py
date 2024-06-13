from pntos.api.plugins.common import LoggingLevel
from pntos.cobra.SimpleControllerPlugin import SimpleMediator
from pntos.cobra.SimpleLoggingPluggin import SimpleLoggingPlugin
from pntos.cobra.SimpleRegistryPlugin import SimpleRegistry


def call(a: SimpleLoggingPlugin):
    a.log(a.__class__, a.identifier, LoggingLevel.INFO, "This is an INFO message")
    a.log(a.__class__, a.identifier, LoggingLevel.DEBUG, "This is a DEBUG message")
    a.log(a.__class__, a.identifier, LoggingLevel.WARN, "This is an WARNING message")
    a.log(a.__class__, a.identifier, LoggingLevel.ERROR, "This is an ERROR message")


def call_color_and_not(a: SimpleLoggingPlugin):
    a.colorize = False
    print("Without color:")
    call(a)
    print("With color:")
    a.colorize = True
    call(a)


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
