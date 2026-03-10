# ControllerPlugin

## Summary
The {py:obj}`ControllerPlugin<pntos.api.ControllerPlugin>` is responsible for invoking plugin startup
logic, choosing the concurrency model, and coordinating any platform-independent plugin activity.
It is the conceptual *main* function of a {term}`pntOS-Python` {term}`App`.

## General Plugin Description

We'll introduce the {py:obj}`ControllerPlugin<pntos.api.ControllerPlugin>` by first considering the
general construction of a {term}`pntOS-Python` {term}`App`, which is the means by which a user
creates and starts a {term}`pntOS-Python` system. Every implementation of a {term}`pntOS-Python` {term}`App`
follows the same general flow: 

1. Set up plugin configuration.
2. Instantiate a {py:obj}`ControllerPlugin<pntos.api.ControllerPlugin>`.
3. Instantiate any additional plugins.
4. Start up the controller plugin by calling the {py:meth}`controller.init_plugin<pntos.api.CommonPlugin.init_plugin>` function.
5. Start up the rest of the plugins by passing them to the controller via {py:meth}`controller.take_control<pntos.api.ControllerPlugin.take_control>`.
6. Eventually shut the system down using {py:meth}`controller.shutdown_plugin<pntos.api.CommonPlugin.shutdown_plugin>`.

Aside from selecting the initial batch of plugins to use and setting up any required
configuration, all direct interaction is with the {py:obj}`ControllerPlugin<pntos.api.ControllerPlugin>`.
Thus, the {py:obj}`ControllerPlugin<pntos.api.ControllerPlugin>`, and more specifically its
{py:meth}`take_control<pntos.api.ControllerPlugin.take_control>` function, could be considered the *on button*
of the {term}`pntOS-Python` API. Once given control, it is the {py:obj}`ControllerPlugin's<pntos.api.ControllerPlugin>`
responsibility to organize and initialize all the other plugins with the basics they need to run.
This typically includes:

1. Ensuring a registry is available through a {py:obj}`RegistryPlugin<pntos.api.RegistryPlugin>`,
which allows all plugins have access to their initial configuration.
2. Providing {py:obj}`Mediators<pntos.api.Mediator>` to all other plugins via their
{py:meth}`init_plugin<pntos.api.CommonPlugin.init_plugin>` function, through which plugins can access the registry
and broadcast messages out through the transport plugin(s).
3. Calling any specialized plugin startup functions, such as
{py:meth}`OrchestrationPlugin.init_orchestration_plugin<pntos.api.OrchestrationPlugin.init_orchestration_plugin>` and
{py:meth}`TransportPlugin.start_listening<pntos.api.TransportPlugin.start_listening>`.
4. Implementing the concurrency model (single threaded, multithreaded etc.).
5. Buffering and sorting of incoming data.
6. Defining default system outputs, through controller-initiated calls to {py:meth}`Mediator.request_solutions <pntos.api.Mediator.request_solutions>` or {py:meth}`Mediator.broadcast_aspn_message <pntos.api.Mediator.broadcast_aspn_message>`.

More information on plugin requirements may be found in the plugin's {py:obj}`API documentation<pntos.api.ControllerPlugin>`.

## Related Classes
This section describes a few classes that {py:obj}`ControllerPlugins<pntos.api.ControllerPlugin>`
may interact with directly.

### Mediator
The {py:obj}`Mediator<pntos.api.Mediator>` is a class that provides a set of functions that allow some
limited communication between plugins. Named after the computer science [mediator design pattern](https://en.wikipedia.org/wiki/Mediator_pattern),
it encapsulates communication and shared state between the plugins.
The {py:obj}`ControllerPlugin<pntos.api.ControllerPlugin>` must select a {py:obj}`Mediator<pntos.api.Mediator>`
implementation to provide to the other plugins through their {py:obj}`init_plugin()<pntos.api.CommonPlugin.init_plugin()>` function.
Then all other plugins may communicate back to the {py:obj}`ControllerPlugin<pntos.api.ControllerPlugin>` or indirectly with each other by
invoking the functions on their {py:obj}`Mediator<pntos.api.Mediator>`. As all plugins have access to the {py:obj}`Mediator<pntos.api.Mediator>`,
its implementation is tightly related to the concurrency model that the {py:obj}`ControllerPlugin<pntos.api.ControllerPlugin>` must provide.

The {py:obj}`Mediator<pntos.api.Mediator>` is therefore where concurrency and
synchronization are decided. In the case of a multithreaded implementation
where each plugin is in a separate thread, the {py:obj}`ControllerPlugin<pntos.api.ControllerPlugin>`
might implement a simple {py:obj}`Mediator<pntos.api.Mediator>` by creating and storing internally
a set of mutex locks, one per thread, and then locking each call to a
{py:obj}`Mediator<pntos.api.Mediator>` function using a mutex. The
{py:obj}`Mediator<pntos.api.Mediator>` function calls would then consist of locking
logic followed by routing calls from one plugin to another.

As another example, suppose instead we were writing a multiprocessed controller. In this
case, the controller might ``fork()`` to put plugins into their own processes, and then
write a {py:obj}`Mediator<pntos.api.Mediator>` that opens IPC communication primitives
(such as ``/dev/shm`` or sockets) in order to route the data from the 
{py:obj}`TransportPlugin<pntos.api.TransportPlugin>` to the 
{py:obj}`OrchestrationPlugin<pntos.api.OrchestrationPlugin>`, which are now in different processes.
Thus the {py:obj}`Mediator<pntos.api.Mediator>` that is constructed by the
{py:obj}`ControllerPlugin<pntos.api.ControllerPlugin>` is tied closely to the concurrency model
chosen by the {py:obj}`ControllerPlugin<pntos.api.ControllerPlugin>`.

### MessageStreamConfig
Data ingested by the system will pass through the {py:obj}`Mediator's<pntos.api.Mediator>`
{py:meth}`process_pntos_message<pntos.api.Mediator.process_pntos_message>` function. From here data
is usually passed to an {py:obj}`OrchestrationPlugin's<pntos.api.OrchestrationPlugin>`
{py:meth}`process_pntos_message<pntos.api.OrchestrationPlugin.process_pntos_message>` function. However,
the {py:obj}`OrchestrationPlugin's<pntos.api.OrchestrationPlugin>` may have requirements with regards
to data ordering. The {py:obj}`MessageStreamConfig <pntos.api.MessageStreamConfig>` is the mechanism
by which the {py:obj}`OrchestrationPlugin's<pntos.api.OrchestrationPlugin>` may request that the 
{py:obj}`ControllerPlugin<pntos.api.ControllerPlugin>` provide buffering/sorting of certain data streams
before passing them along for further processing. 

### PlatformIntegrationPlugin
The {py:obj}`ControllerPlugin<pntos.api.ControllerPlugin>` and {py:obj}`PlatformIntegrationPlugin<pntos.api.PlatformIntegrationPlugin>`
are exactly the same from a code standpoint- they have the same members and methods. Their differences
are defined by docstring. The {py:obj}`ControllerPlugin<pntos.api.ControllerPlugin>` performs all activities
that may be completed regardless of platform, including initialiazing the other plugins and
providing {py:obj}`Mediators<pntos.api.Mediator>`. The
{py:obj}`PlatformIntegrationPlugin<pntos.api.PlatformIntegrationPlugin>`, if present, will then take
over control to handle platform-specific activities.


## ControllerPlugin API
As with all the other plugins, the {py:obj}`ControllerPlugin<pntos.api.ControllerPlugin>` inherits
functions from the {py:obj}`CommonPlugin<pntos.api.CommonPlugin>` parent class. However,
{py:obj}`ControllerPlugin<pntos.api.ControllerPlugin>` implementations of these functions have
special requirements:

1. {py:meth}`init_plugin()<pntos.api.CommonPlugin.init_plugin>`: Since the {py:obj}`ControllerPlugin<pntos.api.ControllerPlugin>`
is the one responsible for creation of the {py:obj}`Mediator<pntos.api.Mediator>`, it should not receive a 
{py:obj}`Mediator<pntos.api.Mediator>` instance via {py:meth}`init_plugin()<pntos.api.CommonPlugin.init_plugin>`.

2. {py:meth}`shutdown_plugin()<pntos.api.CommonPlugin.shutdown_plugin>`: Most plugins need only to
worry about performing their own shutdown requirements, but as the {py:obj}`ControllerPlugin<pntos.api.ControllerPlugin>`
manages all other plugins, calling its {py:meth}`shutdown_plugin()<pntos.api.CommonPlugin.shutdown_plugin>` method
should trigger an orderly shutdown of all other plugins.

Those aside, the controller API has only one additional function:
```{literalinclude} ../../pntos-api/src/pntos/api/plugins/controller.py
:pyobject: ControllerPlugin.take_control
:end-at: "-> None"
:lineno-match:
```

This function is used to run a specific instantiation of the {term}`pntOS-Python` {term}`API`.
In fact, the entirety of a {term}`App` is simply setting up the arguments for this function.

## ControllerPlugin Implementations
As of this writing {term}`Cobra` has two {py:obj}`ControllerPlugin<pntos.api.ControllerPlugin>` implementations,
the {py:obj}`StandardControllerPlugin<pntos.cobra.StandardControllerPlugin>` and the 
{py:obj}`BuscatControllerPlugin<pntos.cobra.BuscatControllerPlugin>`.

### StandardControllerPlugin
As the base-level example, it uses a single-threaded concurrency model and leans very hard on the
{py:obj}`StandardMediator<pntos.cobra.internal.StandardMediator>` implementation to support communication-
essentially attaching a core set of plugins to the {py:obj}`StandardMediator<pntos.cobra.internal.StandardMediator>`
to implement its callback functionality. The {py:obj}`StandardMediator<pntos.cobra.internal.StandardMediator>`
routes incoming data to, and extracts solutions from a single The {py:obj}`OrchestrationPlugin<pntos.api.OrchestrationPlugin>`,
supporting sensor fusion.


Note that this plugin does not currently support {py:obj}`PlatformIntegrationPlugins<pntos.api.PlatformIntegrationPlugin>`
and it assumes that each {py:obj}`TransportPlugin<pntos.api.TransportPlugin>` it receives has a non-blocking 
{py:meth}`start_listening<pntos.api.TransportPlugin.start_listening>` function (i.e. they manage their own thread).

### BuscatControllerPlugin
The {py:obj}`BuscatControllerPlugin<pntos.cobra.BuscatControllerPlugin>` is a specialized controller
that does not support full sensor fusion as the {py:obj}`StandardControllerPlugin<pntos.cobra.StandardControllerPlugin>` does.
Rather, it works with a subset of plugins to enable the combination of data streams and/or conversion
of any transport-supported data format to any other.

### Comparison
Below is a table illustrating the plugins supported by each of the above {py:obj}`ControllerPlugins<pntos.api.ControllerPlugin>`:

| Plugin     | {py:obj}`Standard<pntos.cobra.StandardControllerPlugin>` supports | {py:obj}`Buscat<pntos.cobra.BuscatControllerPlugin>` supports |
| ---------- | ----------------------------------------------------------------- | ------------------------------------------------------------- |
| {py:obj}`pntos.api.ControllerPlugin`          | 0  |0  |
| {py:obj}`pntos.api.FusionPlugin`              | 1+ |0  |
| {py:obj}`pntos.api.FusionStrategyPlugin`      | 1+ |0  |
| {py:obj}`pntos.api.InertialPlugin`            | 1+ |0  |
| {py:obj}`pntos.api.InitializationPlugin`      | 1+ |0  |
| {py:obj}`pntos.api.LoggingPlugin`             | 1  |1  |
| {py:obj}`pntos.api.OrchestrationPlugin`       | 1  |0  |
| {py:obj}`pntos.api.PlatformIntegrationPlugin` | 0  |0  |
| {py:obj}`pntos.api.PreprocessorPlugin`        | 0+ |0  |
| {py:obj}`pntos.api.RegistryPlugin`            | 1  |1  |
| {py:obj}`pntos.api.StateModelingPlugin`       | 0+ |0  |
| {py:obj}`pntos.api.TransportPlugin`           | 1+ |1+ |
| {py:obj}`pntos.api.UiPlugin`                  | 0+*|0+*|
| {py:obj}`pntos.api.UtilityPlugin`             | 0+ |0  |

```{note}
In the above table
1. A numerical entry indicates the controller requires at least the specified number of that plugin type.
2. A ``+`` indicates more than the listed number is supported but not required.
3. ``*`` for UI plugins only, this means an arbitrary number is supported, but only 1 instance may have a
{py:meth}`UiPlugin.requires_main_thread <pntos.api.UiPlugin.requires_main_thread>` return of ``True``.
```