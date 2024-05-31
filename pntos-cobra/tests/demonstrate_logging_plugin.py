from pntos.cobra.SimpleLoggingPluggin import SimpleLoggingPlugin
from pntos.api.plugins.common import LoggingLevel


def call(a: SimpleLoggingPlugin):
    a.colorize = False
    print("Without color:")
    a.log(a.__class__, a.identifier, LoggingLevel.INFO, "This is an INFO message")
    a.log(a.__class__, a.identifier, LoggingLevel.DEBUG, "This is a DEBUG message")
    a.log(a.__class__, a.identifier, LoggingLevel.WARN, "This is an WARNING message")
    a.log(a.__class__, a.identifier, LoggingLevel.ERROR, "This is an ERROR message")
    print("With color:")
    a.colorize = True
    a.log(a.__class__, a.identifier, LoggingLevel.INFO, "This is an INFO message")
    a.log(a.__class__, a.identifier, LoggingLevel.DEBUG, "This is a DEBUG message")
    a.log(a.__class__, a.identifier, LoggingLevel.WARN, "This is an WARNING message")
    a.log(a.__class__, a.identifier, LoggingLevel.ERROR, "This is an ERROR message")


a = SimpleLoggingPlugin(identifier="my_logger")
a.global_log_level = LoggingLevel.DEBUG
print("\nGLOBAL_LOG_LEVEL = DEBUG\n")
call(a)
a.global_log_level = LoggingLevel.INFO
print("\nGLOBAL_LOG_LEVEL = INFO\n")
call(a)
a.global_log_level = LoggingLevel.WARN
print("\nGLOBAL_LOG_LEVEL = WARN\n")
call(a)
a.global_log_level = LoggingLevel.ERROR
print("\nGLOBAL_LOG_LEVEL = ERROR\n")
call(a)
