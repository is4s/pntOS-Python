# Logging Plugin

The {py:obj}`Logging Plugin<pntos.api.LoggingPlugin>` records messages to an arbitrary
sink (e.g. console, file, network, etc.). It supports four logging levels:
{py:obj}`DEBUG<pntos.api.LoggingLevel.DEBUG>`,
{py:obj}`INFO<pntos.api.LoggingLevel.INFO>`,
{py:obj}`WARN<pntos.api.LoggingLevel.WARN>`,
and {py:obj}`ERROR<pntos.api.LoggingLevel.ERROR>` 

A {py:obj}`Logging Plugin<pntos.api.LoggingPlugin>` implementation can choose which of
these log levels to display. For instance, an implementation may contain a `debug`
flag/config value to turn on/off any {py:obj}`DEBUG<pntos.api.LoggingLevel.DEBUG>` log
messages.

Any Python pntOS plugin can access the logging plugin through the mediator:
```python
class MyPlugin(UtilityPlugin):
    ...
    def init_plugin(self, plugin_resources_location, mediator) -> None:
        self.mediator = mediator
        ...
        self.mediator.log_message(LoggingLevel.INFO, "MyPlugin is set up.")

    def my_func(self) -> None:
      ...
      if failed:
          self.mediator.log_message(LoggingLevel.ERROR, "my_func failed.")
          return
      ...
```

<!-- TODO (#175) https://git.aspn.us/pntos/pntos-python/-/issues/175 -->
