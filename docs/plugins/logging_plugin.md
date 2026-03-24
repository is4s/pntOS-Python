# Logging Plugin

A {py:obj}`Logging Plugin<pntos.api.LoggingPlugin>` records messages to an arbitrary
sink (console, file, network, etc.) with four severity levels:
{py:obj}`ERROR<pntos.api.LoggingLevel.ERROR>`,
{py:obj}`WARN<pntos.api.LoggingLevel.WARN>`,
{py:obj}`INFO<pntos.api.LoggingLevel.INFO>`, and
{py:obj}`DEBUG<pntos.api.LoggingLevel.DEBUG>`.

## API Overview

The {py:obj}`LoggingPlugin<pntos.api.LoggingPlugin>` API
([pntos-api/src/pntos/api/plugins/logging.py](../../pntos-api/src/pntos/api/plugins/logging.py))
only defines one method beyond {py:obj}`CommonPlugin<pntos.api.CommonPlugin>`:

```{literalinclude} ../../pntos-api/src/pntos/api/plugins/logging.py
:lines: 52-68
:language: python
```

The {py:obj}`LoggingPlugin.log()<pntos.api.LoggingPlugin.log>` method accepts a message along with context: `source_plugin_type`,
`source_plugin_identifier`, and log `level`.

### Logging Levels

| Level                                         | Value | Description                                                     |
| --------------------------------------------- | ----- | --------------------------------------------------------------- |
| {py:obj}`ERROR<pntos.api.LoggingLevel.ERROR>` | 0     | Program error state requiring inspection.                       |
| {py:obj}`WARN<pntos.api.LoggingLevel.WARN>`   | 1     | Possible unintended state that may indicate a bug.              |
| {py:obj}`INFO<pntos.api.LoggingLevel.INFO>`   | 2     | Informational output indicating correct operation.              |
| {py:obj}`DEBUG<pntos.api.LoggingLevel.DEBUG>` | 3     | Detailed debugging information about plugin state and behavior. |

### Logging From Another Plugin

Plugins log messages through {py:obj}`Mediator.log_message()<pntos.api.Mediator.log_message>`:

```{literalinclude} ../../pntos-api/src/pntos/api/plugins/common.py
:pyobject: Mediator.log_message
:language: python
```

This is almost identical to {py:obj}`LoggingPlugin.log()<pntos.api.LoggingPlugin.log>`
except that {py:obj}`Mediator.log_message<pntos.api.Mediator.log_message>` omits the
first two parameters since it already knows the plugin's type and identifier. For
example, when any plugin (e.g., a UiPlugin) calls:

```python
mediator.log_message(LoggingLevel.INFO, "Ui initialized.")
```

The {py:obj}`Mediator<pntos.api.Mediator>` could internally call:

```python
logging_plugin.log(UiPlugin, "Cobra Ui Plugin", LoggingLevel.INFO, "Ui initialized.")
```

```{note}

There may be cases where a {py:obj}`Mediator<pntos.api.Mediator>` implementation does
_not_ use the logging plugin. For instance, the
{py:obj}`StandardMediator<pntos.cobra.internal.StandardMediator>` will simply print log
messages to the terminal until a
{py:obj}`LoggingPlugin.log()<pntos.api.LoggingPlugin.log>` is initialized.

```

## Cobra Implementation: StandardLoggingPlugin

The {py:obj}`StandardLoggingPlugin<pntos.cobra.StandardLoggingPlugin>`
([pntos-cobra/src/pntos/cobra/standard_plugins/StandardLoggingPlugin.py](../../pntos-cobra/src/pntos/cobra/standard_plugins/StandardLoggingPlugin.py))
logs to the console. Given:

```python
logging_plugin.log(UiPlugin, "Cobra Ui Plugin", LoggingLevel.INFO, "Ui initialized.")
```

The terminal output is:

```{raw} html
<pre style="background-color: #1e1e1e; color: #d4d4d4; padding: 10px; border-radius: 4px; font-family: monospace;"><span style="color: #bbbbbb;">[01/02/2025 12:30:45]</span><span style="color: #808080;"> [UiPlugin]</span><span style="color: #4ec9b0;"> [INFO] </span>Ui initialized.</pre>
```

### Configuration parameters:

The following configuration parameters are passed into the constructor of the
{py:obj}`StandardLoggingPlugin<pntos.cobra.StandardLoggingPlugin>`:

| Parameter          | Type                                           | Default                                     | Description                                                                                                                                                                                                                          |
| ------------------ | ---------------------------------------------- | ------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `colorize`         | `bool`                                         | `True`                                      | Prints colored log messages if true, uncolored if false.                                                                                                                                                                             |
| `global_log_level` | {py:obj}`LoggingLevel<pntos.api.LoggingLevel>` | {py:obj}`INFO<pntos.api.LoggingLevel.INFO>` | Selects which log levels get printed. Any messages with a level greater than `global_log_level` will not be logged.                                                                                                                  |
| `date_time_format` | `str`                                          | `'%d/%m/%Y %H:%M:%S'`                       | Specifies the date-time format according to the available format specifiers. See [time.strftime()](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior) documentation for more info on supported formats. |

### Understanding `global_log_level`

The `global_log_level` filters messages by severity. A message prints only if its level
is less than or equal to `global_log_level`:

| `global_log_level` | ERROR | WARN | INFO | DEBUG |
| ------------------ | ----- | ---- | ---- | ----- |
| `ERROR` (0)        | ✓     | ✗    | ✗    | ✗     |
| `WARN` (1)         | ✓     | ✓    | ✗    | ✗     |
| `INFO` (2)         | ✓     | ✓    | ✓    | ✗     |
| `DEBUG` (3)        | ✓     | ✓    | ✓    | ✓     |

For example, `global_log_level=INFO` (default) prints ERROR, WARN, and INFO but
suppresses DEBUG messages. Set to `DEBUG` for verbose output during development, or
`WARN` for minimal production output.

```{admonition} Note

All off-the-shelf {term}`Cobra` apps using their default configurations should not have `WARN` messages.
Recommended settings: `WARN` (minimal output) or `INFO` (basic feedback).

```
