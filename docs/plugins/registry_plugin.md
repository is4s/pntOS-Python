# Registry Plugin

The {py:obj}`Registry Plugin<pntos.api.RegistryPlugin>` serves as a factory for
{py:obj}`Registry<pntos.api.Registry>` objects which implement a global group-key-value
registry. This is useful for configuring plugins and provides a way for plugins to share
data.

The registry can be accessed through the {py:obj}`Mediator<pntos.api.Mediator>`. It is
the responsibility of the {py:obj}`Controller Plugin<pntos.api.ControllerPlugin>` to
find a {py:obj}`Registry Plugin<pntos.api.RegistryPlugin>` in its list of plugins, and
give a {py:obj}`Registry<pntos.api.Registry>` to the
{py:obj}`Mediator<pntos.api.Mediator>`s.

Each call to the registry starts with a
{py:obj}`batch_start()<pntos.api.Registry.batch_start>` call for a given group. Each
group in the registry returns a {py:obj}`KeyValueStore<pntos.api.KeyValueStore>` object
which can be accessed much like a dictionary. When a plugin is done accessing a group in
the registry, it should call {py:obj}`batch_end()<pntos.api.KeyValueStore.batch_end()>`
as quickly as possible for the sake of concurrency. Each group should only be accessed
by one thread at a time, so calling
{py:obj}`batch_start()<pntos.api.Registry.batch_start>` and
{py:obj}`batch_end()<pntos.api.KeyValueStore.batch_end()>` enforces this behavior.

Here is an example of how one might use the registry:
```python
class MyPlugin(UtilityPlugin):
    ...
    def init_plugin(self, plugin_resources_location, mediator) -> None:
        self.mediator = mediator
        ...
        key_value_store = self.mediator.registry.batch_start("my_config_group")
        if "initial_value" in key_value_store:
            self.initial_value = key_value_store["initial_value"]
        key_value_store.batch_end()

    def my_func(self) -> None:
      ...
      key_value_store = self.mediator.registry.batch_start("my_plugin_data")
      key_value_store["newest_data"] = new_data
      key_value_store.batch_end()
      ...
```

For more information about the capabilities of the registry, see the
{py:obj}`pntos.api.RegistryPlugin` documentation.


<!-- TODO (#181) https://git.aspn.us/pntos/pntos-python/-/issues/181 -->