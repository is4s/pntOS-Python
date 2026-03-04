# Utility Plugin

The {py:obj}`Utility Plugin<pntos.api.UtilityPlugin>` is intended for any functionality
that does not fall into the domain of other plugins but still needs access to pntOS
resources.

This plugin can be used for a wide variety of purposes. A few examples could include:

- Watching a registry group and recording values to a file for later analysis.
- Monitoring system resources.
- Publishing diagnostic information to the registry or out through the transport.
- Calculating filter performance metrics upon shutdown.

## Utility Plugin API

Like all plugin types, the {py:obj}`Utility Plugin<pntos.api.UtilityPlugin>` inherits from
{py:obj}`CommonPlugin<pntos.api.CommonPlugin>`, and thus is required to implement the
{py:obj}`init_plugin()<pntos.api.CommonPlugin.init_plugin>` and
{py:obj}`shutdown_plugin()<pntos.api.CommonPlugin.shutdown_plugin>` methods.

Unlike most other plugin types, the utility plugin API does not include any additional methods. This
is because the functionality of a utility plugin will be specific to a particular implementation.
While the API does not require additional methods, a utility plugin implementation can of course
include internal methods supporting the operation of the plugin.

```{important}
As a reminder, plugins should only directly interact with each other through the API.
Implementation-specific methods are not part of the API and must not be invoked by other plugins.
Since the utility plugin API does not include unique methods, internal communication between a
utility plugin and other plugins should occur via the registry.
```

## Utility Plugin Implementations

Cobra currently includes a single utility plugin, the
{py:obj}`DiagnosticLogPlugin<pntos.cobra.DiagnosticLogPlugin>`. Upon initialization, this plugin
registers a callback to a particular registry group, as seen below:

```{literalinclude} ../../pntos-cobra/src/pntos/cobra/standard_plugins/DiagnosticLogPlugin.py
:language: python
:pyobject: DiagnosticLogPlugin.init_plugin
:dedent: 4
```

Whenever a key in this registry group is added or modified, the `_callback` method saves it off.
Upon shutdown, the series of values associated with each key are recorded to a file in
[HDF5](https://www.h5py.org/) format via {py:obj}`save_to_hdf5_file()<pntos.cobra.utils.save_to_hdf5_file>`.

```{note}
In most cases, a utility plugin must spin up a thread inside `init_plugin` so that the plugin can
continually operate until it is eventually terminated by a call to `shutdown_plugin`. However, this
plugin does not have to actively monitor the registry group in a separate thread. Instead, the
callback will be executed by whichever thread updates the values in
the group.
```
