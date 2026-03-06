# Dummy App

[`This app`](https://git.aspn.us/pntos/pntos-python/-/blob/main/apps/dummy/minimal.py?ref_type=heads)
is a supplementary example stripped of most functionality that gives a simplified look at plugin interaction.
If you have not done so, it is recommended that you start with the [gps_ins app](gps_ins.md), which covers
some fundamentals (imports, configuration, and other plugins) not addressed here.

## Overview

[`This app`](https://git.aspn.us/pntos/pntos-python/-/blob/main/apps/dummy/minimal.py?ref_type=heads)
demonstrates the minimal set of plugins that 'does something'- a {py:obj}`TransportPlugin <pntos.api.TransportPlugin>`,
{py:obj}`OrchestrationPlugin <pntos.api.OrchestrationPlugin>`, and {py:obj}`ControllerPlugin <pntos.api.ControllerPlugin>`.
There is no estimation, networking, or sensor data processing and thus many plugins are not represented
here. These three plugins pass fake data from the {py:obj}`DummyTransportPlugin <pntos.cobra.DummyTransportPlugin>`
to the {py:obj}`DummyOrchestrationPlugin <pntos.cobra.DummyOrchestrationPlugin>` and back again, using the
{py:obj}`DuumyMediator <pntos.cobra.internal.DummyMediator>` to communicate.
At each stage a message is printed to the console indicating where the {py:obj}`Message <pntos.api.Message>` is in the pipeline.

## App Walkthrough
Here we'll go through the app line-by-line. To follow along, you can find the app file at
[`pntos-python/apps/dummy/minimal.py`](https://git.aspn.us/pntos/pntos-python/-/blob/main/apps/dummy/minimal.py?ref_type=heads).

### App Workflow

Not accounting for any configuration, the general flow of an app is to:
1. Import plugins.
2. Instantiate the plugins.
3. Call {py:obj}`init_plugin() <pntos.api.CommonPlugin.init_plugin>` on the controller plugin.
4. Hand the list of plugins off to the controller with {py:obj}`take_control() <pntos.api.ControllerPlugin.take_control>`.

Taking each step in 
#### 1. Imports

First we must import the plugins we wish to use, which assumes you've [installed](../installation.md) the `pntos` Python module.
As a minimal example requiring no configuration or special commands, there are only a few plugin
imports from the top-level of [`pntos.cobra`](../autodocs/cobra_plugins.rst), as follows:
```{literalinclude} ../../apps/dummy/minimal.py
:start-at: "from pntos.cobra import ("
:end-at: ")"
:lineno-match:
```

#### 2. Instantiate Plugins
None of the dummy plugins require any initialization arguments aside from their
{py:attr}`CommonPlugin.identifier <pntos.api.CommonPlugin.identifier>`.
```{literalinclude} ../../apps/dummy/minimal.py
:start-at: "controller = "
:end-at: "]"
:lineno-match:
```
As the {py:obj}`Controller <pntos.api.ControllerPlugin>` gets to 'take control' of all the other
plugins it stands alone. The rest are collected into a list to be ingested by the {py:obj}`Controller <pntos.api.ControllerPlugin>` .

#### 3. Call `init_plugin` on Controller
```{literalinclude} ../../apps/dummy/minimal.py
:start-at: "controller.init_plugin()"
:end-at: ")"
:lineno-match:
```
{py:obj}`init_plugin() <pntos.api.CommonPlugin.init_plugin>` is required to be the first function called
on any plugin after it is created. In an app, generally you will only do this for the {py:obj}`Controller <pntos.api.ControllerPlugin>`;
the {py:obj}`Controller <pntos.api.ControllerPlugin>` does this for all the other plugins as part of the
{py:meth}`take_control <pntos.api.ControllerPlugin.take_control>` call.

#### 4. Hand Off Plugins and Control to Controller Plugin

Once the {py:obj}`Controller <pntos.api.ControllerPlugin>` is initialized we just need to hand it
control over the current thread and all the other plugins, done via 
{py:obj}`controller.take_control(plugins) <pntos.api.ControllerPlugin.take_control>`.

However, there is a fair bit of additional code in the app wrapped around that {py:meth}`take_control <pntos.api.ControllerPlugin.take_control>` call:

```{literalinclude} ../../apps/dummy/minimal.py
:start-at: "# Set up"
:lineno-match:
```

Just as the {py:obj}`Controller <pntos.api.ControllerPlugin>` is responsible for spinning up set of
plugins into operation, it is also responsible for managing a
{py:meth}`clean shutdown <pntos.api.CommonPlugin.shutdown_plugin>`. This app is using the `asyncio`
library to manage the termination conditions of the app and ensuring the
{py:obj}`Controller <pntos.api.ControllerPlugin>` is shut down properly, which in turn shuts down
all plugins it has control over. This approach is only one of many alternatives.  

That brings us to the end of the app itself. In the next section we'll briefly address what each of
the plugins in this app are contributing.

## Plugins Overview

Each plugin in this app is a 'dummy' version. They are only implemented to a level that allows
them to work together, but not necessarily do anything useful. 
The following table summarizes the behavior of each of these plugins:

| Cobra Plugin                                                                            | Contribution to App                                                                                                                                                                                                                                                                                                                                                                                                                                      | More Info                                |
| --------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------- |
| {py:obj}`DummyControllerPlugin <pntos.cobra.DummyControllerPlugin>` | Initializes all other plugins, calls {py:meth}`start_listening() <pntos.api.TransportPlugin.start_listening>` for all {py:obj}`TransportPlugins <pntos.api.TransportPlugin>` and {py:meth}`takes control <pntos.api.ControllerPlugin.take_control>`. <br> Provides Mediators to all other plugins to allow for callbacks betwen them.| [](../plugins/controller_plugin.md)      |
| {py:obj}`DummyTransportPlugin <pntos.cobra.DummyTransportPlugin>` | Starts a thread that generates {py:obj}`Messages <pntos.api.Message>` to hand off to the rest of the system, simulating external input. | [](../plugins/transport_plugin.md)   |
| {py:obj}`DummyOrchestrationPlugin <pntos.cobra.DummyOrchestrationPlugin>` | Recieves {py:obj}`Messages <pntos.api.Message>` from the {py:obj}`DummyTransportPlugin <pntos.cobra.DummyTransportPlugin>` via the {py:obj}`Mediator <pntos.api.Mediator>`  and echoes them back as simulated solutions.| [](../plugins/orchestration_plugin.md)   |


## Expected Results

For instructions of how to run this app, see one of the examples in [](../first_app.md), adapting
the executable to be `apps/dummy/minimal.py`. After running the app you should see the following results
showing fake data being passed 'in' on `channel_foo` and 'out' on `channel_foo_echo`:

```shell
[06/03/2026 11:22:24] [unknown_dummy] [INFO] Initialized DummyTransport
[06/03/2026 11:22:24] [unknown_dummy] [INFO] DummyTransport listening
[06/03/2026 11:22:24] [unknown_dummy] [INFO] DummyTransport publishing to channel_foo
[06/03/2026 11:22:24] [unknown_dummy] [INFO] Orchestration processing message from channel_foo
[06/03/2026 11:22:24] [unknown_dummy] [INFO] DummyTransport broadcasting on channel_foo_echo
[06/03/2026 11:22:24] [unknown_dummy] [INFO] DummyTransport publishing to channel_foo
[06/03/2026 11:22:24] [unknown_dummy] [INFO] Orchestration processing message from channel_foo
[06/03/2026 11:22:24] [unknown_dummy] [INFO] DummyTransport broadcasting on channel_foo_echo
```