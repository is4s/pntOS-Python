# GPS INS App

Welcome to the first of the {term}`Cobra` tutorial {term}`apps <App>`!

## Overview

A {term}`Cobra` {term}`app <App>` consists of a single Python script which imports
plugins, instantiates plugins, sets config, and calls
{py:obj}`take_control() <pntos.api.ControllerPlugin.take_control>` on the controller
plugin to run the plugins.

This app is meant to be a simple demonstration of an app that accomplishes sensor
fusion between two sensors. In this case it is the fusion between GPS position
measurements and IMU readings using a simple set of {term}`Cobra` plugins. Each subsequent app
will build on the previous app(s) with a small tweak or expanded capability to
walk you through the process of building increasingly complex sensor-fusion and
navigation systems with the {term}`Python pntOS API` and {term}`Cobra`.

## App Walkthrough

Let's walk through this first app piece by piece. You can find the first app file at
[`pntos-python/apps/tutorial/gps_ins.py`](https://git.aspn.us/pntos/pntos-python/-/blob/main/apps/tutorial/gps_ins.py?ref_type=heads)
to follow along. Let's get started by examining how you import elements from the `pntos` module.

### Imports

Assuming we've [installed](../installation.md) the `pntos` Python module, we can import
{term}`Python pntOS API` or {term}`Cobra` objects from a few different submodules within
the `pntos` module:

| Submodule Location     | Available Imports                                                                                      |
| ---------------------- | ------------------------------------------------------------------------------------------------------ |
| `pntos.api`            | All {term}`Python pntOS API` objects                                                                   |
| `pntos.cobra`          | All {term}`Cobra` Plugins                                                                              |
| `pntos.cobra.internal` | Non-plugin {term}`Cobra` objects (e.g. {py:obj}`StandardMediator <pntos.cobra.internal.StandardMediator>`) |
| `pntos.cobra.utils`    | {term}`Cobra` utility and helper functions                                                             |
| `pntos.cobra.config`   | {term}`Cobra` config objects and config utility functions                                              |

Let's look at how our app uses these locations:

#### API Imports

This app only uses a single import from the API. Most apps will require minimal API
imports since the API is mostly relevant when *implementing* a plugin, not when *using*
a plugin in an app.

In this case, we need to import the {py:obj}`LoggingLevel <pntos.api.LoggingLevel>` enum
from the API:
```{literalinclude} ../../apps/tutorial/gps_ins.py
:start-at: "from pntos.api import"
:end-at: "from pntos.api import"
:lineno-match:
```

This is used for initializing the global log level of the {py:obj}`StandardLoggingPlugin
<pntos.cobra.StandardLoggingPlugin>` later in the app:
```{literalinclude} ../../apps/tutorial/gps_ins.py
:start-at: "StandardLoggingPlugin("
:end-at: ")"
:lineno-match:
```

... and that's it for API imports - now let's move to the plugin imports.

#### Cobra Plugin Imports

You should only see plugin imports from the top-level of [`pntos.cobra`](../documentation/cobra_plugins.rst). For instance,
check out where the app imports the following {term}`Cobra` plugins:
```{literalinclude} ../../apps/tutorial/gps_ins.py
:start-at: "from pntos.cobra import ("
:end-at: ")"
:lineno-match:
```
Notice that each of the imports from `pntos.cobra` is a plugin as indicated by the
suffix of each object name. We'll walk through what each of these plugins are doing
further along in [](#plugins-overview). For now, on to the config imports.

#### Cobra Config Imports

The
[`pntos.cobra.config`](../documentation/cobra_config.rst)
submodule contains {term}`Cobra` config objects and a few utility functions relevant
specifically to these config objects. We'll explore these more in the next section, but
for now we need the following config objects for this GPS INS fusion app:
```{literalinclude} ../../apps/tutorial/gps_ins.py
:start-at: "from pntos.cobra.config import ("
:end-at: ")"
:lineno-match:
```

#### Example Dataset

The `pntos_python_datasets` package provides the example LCM log used in this app, along with a
variable, `EXAMPLE_LCM_LOG`, which specifies the path to this log file. This input log contains the
ASPN measurements to be processed by the filter.

In contrast, `OUTPUT_LOG` specifies the filename of the LCM log to which the filter solution will be
recorded, along with all input measurements. This log can then be used to analyze the accuracy of
the solution. If this filename is not provided as a command-line argument, it defaults to
`pntos_output.log`.

```{literalinclude} ../../apps/tutorial/gps_ins.py
:start-at: "from pntos_python_datasets"
:end-at: "OUTPUT_LOG"
:lineno-match:
```

Lets dive a little more into these config objects as we initialize them next.

### Config Setup

In the {term}`Cobra` config paradigm, the user initializes config objects with the
desired config values in the app, and then the app passes these config objects into the
[Registry Plugin](../plugins/registry_plugin.md) upon instantiation of the [Registry
Plugin](../plugins/registry_plugin.md). The [Registry
Plugin](../plugins/registry_plugin.md) takes these config objects and unpacks them into
any new registry at the specified group. Then, if a plugin wants to access config
values, they simply pull these config objects out of the registry and access their
fields.

To accomplish this, {term}`Cobra` config objects all inherit from {py:obj}`BaseConfig
<pntos.cobra.config.BaseConfig>` and are
[dataclasses](https://docs.python.org/3/library/dataclasses.html), which allows the
{term}`Cobra` objects to use two important helper functions: {py:obj}`config_to_registry
<pntos.cobra.config.config_to_registry>` and {py:obj}`config_from_registry
<pntos.cobra.config.config_from_registry>`. These helper functions are what the registry
uses to unpack these objects into the registry at the specified group, and allows
plugins to retrieve config objects back from the registry.

```{note}
While these helper functions can make it appear that we are storing unsupported types
in the registry (see {py:obj}`RegistryValueTypeUnion<pntos.api.RegistryValueTypeUnion>`
for the supported registry types), the reality is that these utility functions unpack the
dataclass fields into types the registry does support. Thus, the config dataclasses only
support the types specified at the bottom of the [config conventions](../config.md).
The conventions also provide information on creating your own config dataclasses.
```

So, with that background, we can now understand what is happening next in the app:
```{literalinclude} ../../apps/tutorial/gps_ins.py
:start-at: "my_config"
:end-at: "# End Config"
:lineno-match:
```
Here we populate a list of config objects with initial values and assign them a group.
Normally some of these values (such as the `ManualAlignmentConfig` parameters) would be
estimated by an {py:obj}`InitializationPlugin <pntos.api.InitializationPlugin>` or
through some other mechanism, but for the sake of simplicity in this first app, these
values are hard-coded here and easy for us to see.

```{note}
Prepending the group name with `config/*` is good practice for these objects so that
other objects are less likely to interfere with these fields in the registry.
```

Here's a brief description of what each config object is used for in this app:

| Cobra Config Object                                                                   | Description                                                                                                                                               |
| --------------------------------------------------------------------------------------| --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| {py:obj}`LcmLogTransportConfig <pntos.cobra.config.LcmLogTransportConfig>`            | Configuration for the LCM transport plugin, which reads messages from the configured input file and writes messages to the configured output file.        |
| {py:obj}`ImuConfig <pntos.cobra.config.ImuConfig>`                                    | The error model of the inertial unit, including white noise (random walk) and a bias modeled as a First-Order Gauss-Markov (FOGM) process for each sensor.|
| {py:obj}`ManualAlignmentConfig <pntos.cobra.config.ManualAlignmentConfig>`            | Configuration to manually align the inertial unit to the platform frame.                                                                                  |
| {py:obj}`SensorConfig <pntos.cobra.config.SensorConfig>`                              | Information about the GPS antenna's relationship to the platform frame.                                                                                   |
| {py:obj}`InertialConfig <pntos.cobra.config.InertialConfig>`                          | Configuration for the inertial mechanization and buffering.                                                                                               |
| {py:obj}`FogmConfig <pntos.cobra.config.FogmConfig>`                                  | Parameters used to model the FOGM error of the GPS position measurements.                                                                                 |
| {py:obj}`TutorialOrchestrationConfig <pntos.cobra.config.TutorialOrchestrationConfig>`| Configuration that defines the channels to use for alignment, mechanization, and fusion.                                                                  |
| {py:obj}`TimeAdjusterConfig <pntos.cobra.config.TimeAdjusterConfig>`                  | Configuration for a preprocessor that corrects the timestamps of the example IMU measurements, ensuring a consistent delta-time between measurements.     |
| {py:obj}`ImuRotatorConfig <pntos.cobra.config.ImuRotatorConfig>`                      | Configuration for a preprocessor that corrects the rotation of the example IMU measurements, ensuring the measurements are in the correct frame.     |

Now that we have our config set up in `my_config`, let's look at instantiating our plugins.

### Instantiate Plugins

Now we have everything we need to get our plugins running. All that's left is:
1. Instantiate the [controller plugin](../plugins/controller_plugin.md).
2. Generate a list of plugin objects we want this app to run.
3. Call {py:obj}`init_plugin() <pntos.api.CommonPlugin.init_plugin>` on the controller plugin.
4. Hand the list of plugins off to the controller with {py:obj}`take_control() <pntos.api.ControllerPlugin.take_control>`.

#### 1. Instantiate Controller Plugin
We can instantiate our controller plugin like so:
```{literalinclude} ../../apps/tutorial/gps_ins.py
:start-at: "controller = "
:end-before: "plugins = "
:lineno-match:
```

#### 2. Generate List of Plugins
Next we can instantiate all the other plugins we want in this app and put them in a list:
```{literalinclude} ../../apps/tutorial/gps_ins.py
:start-at: "plugins = "
:end-at: "]"
:lineno-match:
```
You'll notice that all the plugins take in an {py:obj}`identifier
<pntos.api.CommonPlugin>` on init by {term}`Cobra` convention in order to populate the
{py:obj}`CommonPlugin.identifier <pntos.api.CommonPlugin>` field which all plugins
inherit. However, there are two plugins which take an extra input here at instantiation in this app:

```{table}
:width: 80%
| Plugin                                                                  | Extra Arg    | Extra Arg Description                                                                                                                                                                                                                                                                                                                                                                                                                             |
| ----------------------------------------------------------------------- | --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| {py:obj}`StandardLoggingPlugin<pntos.cobra.StandardLoggingPlugin.__init__>` |  `global_log_level`   | Takes a global log level parameter to select which log levels to display. For more info, see [](../plugins/logging_plugin.md).|
| {py:obj}`StandardRegistryPlugin<pntos.cobra.StandardRegistryPlugin>`        |   `config`  | Takes in a list of config objects on instantiation to populate new registries. For more information on registry plugins, see [](../plugins/registry_plugin.md).               |
```

We'll explore the roles of all these plugins in the app later in [](#plugins-overview), but for now
since we've got a controller plugin and a list of instantiated plugins, let's see how we
start up the controller:

#### 3. Call `init_plugin` on Controller
```{literalinclude} ../../apps/tutorial/gps_ins.py
:start-at: "controller.init_plugin()"
:end-at: ")"
:lineno-match:
```
According to the API, {py:obj}`init_plugin() <pntos.api.CommonPlugin.init_plugin>` is:
> *"A function that will be called by pntOS once and only once when it first initializes
> the plugin before any other functions on the plugin are called."*

Thus, before we can pass control off to the {py:obj}`ControllerPlugin
<pntos.api.ControllerPlugin>` with {py:obj}`take_control()
<pntos.api.ControllerPlugin.take_control>`, we need to call {py:obj}`init_plugin()
<pntos.api.CommonPlugin.init_plugin>`. For all non-controller plugins, we need to pass
in a {py:obj}`Mediator <pntos.api.Mediator>` object in {py:obj}`init_plugin()
<pntos.api.CommonPlugin.init_plugin>`, but since this is the controller we don't need to
pass in any arguments.

#### 4. Hand Off Plugins and Control to Controller Plugin

After {py:obj}`controller.init_plugin() <pntos.api.CommonPlugin.init_plugin>`, we need only call
{py:obj}`controller.take_control(plugins) <pntos.api.ControllerPlugin.take_control>` to
pass our list of plugins over to the controller. From there, the
{py:obj}`StandardControllerPlugin <pntos.cobra.StandardControllerPlugin>` has control and
our GPS INS fusion app is up and running!

Congratulations, you've just walked through your first {term}`Cobra` app! In the next section
we'll look at a top-level overview of what each of the plugins in this app are
contributing to the app.

## Plugins Overview

For each plugin in this app, let's explore briefly what it is and how it contributes to
this app:

| Cobra Plugin                                                                            | Contribution to App                                                                                                                                                                                                                                                                                                                                                                                                                                      | More Info                                |
| --------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------- |
| {py:obj}`StandardControllerPlugin <pntos.cobra.StandardControllerPlugin>`                   | Sets up communication between plugins by calling {py:obj}`init_plugin() <pntos.api.CommonPlugin.init_plugin>` with a {py:obj}`Mediator <pntos.api.Mediator>` for each plugin, then calls {py:obj}`start_listening()<pntos.api.TransportPlugin.start_listening>` on the [transport plugin](../plugins/transport_plugin.md) to start feeding {py:obj}`Messages <pntos.api.Message>` into the system.                                                                      | [](../plugins/controller_plugin.md)      |
| {py:obj}`StandardLoggingPlugin <pntos.cobra.StandardLoggingPlugin>`                         | Prints {py:obj}`mediator.log_message() <pntos.api.Mediator.log_message>` calls from any other plugin to the terminal via the mediator.                                                                                                                                                                                                                                                                                                                                | [](../plugins/logging_plugin.md)         |
| {py:obj}`StandardRegistryPlugin <pntos.cobra.StandardRegistryPlugin>`                       | A group-key-value store for data storage and communication between plugins within the app.                                                                                                                                                                                                                                                                                                                                                                               | [](../plugins/registry_plugin.md)        |
| {py:obj}`TutorialGpsOrchestrationPlugin <pntos.cobra.TutorialGpsOrchestrationPlugin>`       | Assembles the {py:obj}`TutorialInitializationPlugin <pntos.cobra.TutorialInitializationPlugin>`, {py:obj}`StandardInertialPlugin <pntos.cobra.StandardInertialPlugin>`, {py:obj}`StandardFusionPlugin <pntos.cobra.StandardFusionPlugin>`, {py:obj}`EkfFusionStrategyPlugin <pntos.cobra.EkfFusionStrategyPlugin>`, and {py:obj}`TutorialGpsInsStateModelingPlugin <pntos.cobra.TutorialGpsInsStateModelingPlugin>` into a working GPS INS fusion algorithm. | [](../plugins/orchestration_plugin.md)   |
| {py:obj}`TutorialInitializationPlugin <pntos.cobra.TutorialInitializationPlugin>`       | Provides the {py:obj}`StandardInertialPlugin <pntos.cobra.StandardInertialPlugin>` with an initial {term}`PVA` solution according to the {py:obj}`ManualAlignmentConfig <pntos.cobra.config.ManualAlignmentConfig>` in the registry (see [](#config-setup) for more info on config in the registry).                                                                                                                                                         | [](../plugins/initialization_plugin.md)  |
| {py:obj}`StandardInertialPlugin <pntos.cobra.StandardInertialPlugin>`                   | Performs the inertial mechanization on IMU measurements to provide the fusion engine with {term}`PVA` solutions from the IMU.                                                                                                                                                                                                                                                                                                                            | [](../plugins/inertial_plugin.md)        |
| {py:obj}`StandardFusionPlugin <pntos.cobra.StandardFusionPlugin>`                           | Provides the fusion engine to the {py:obj}`TutorialGpsOrchestrationPlugin <pntos.cobra.TutorialGpsOrchestrationPlugin>`.                                                                                                                                                                                                                                                                                                                                           | [](../plugins/fusion_plugin.md)          |
| {py:obj}`EkfFusionStrategyPlugin <pntos.cobra.EkfFusionStrategyPlugin>`                 | Provides the fusion engine (from the {py:obj}`StandardFusionPlugin <pntos.cobra.StandardFusionPlugin>`) with a fusion strategy - in this case an [Extended Kalman Filter](https://en.wikipedia.org/wiki/Extended_Kalman_filter) (EKF).                                                                                                                                                                                                                       | [](../plugins/fusion_strategy_plugin.md) |
| {py:obj}`TutorialGpsInsStateModelingPlugin <pntos.cobra.TutorialGpsInsStateModelingPlugin>` | Models the state of the filter with Pinson15 states by providing a {py:obj}`TutorialPinsonWithNedFogmPositionMeasurementProcessor <pntos.cobra.internal.TutorialPinsonWithNedFogmPositionMeasurementProcessor>`, a {py:obj}`TutorialPinson15NedBlock <pntos.cobra.internal.TutorialPinson15NedBlock>`, and a {py:obj}`TutorialFogmBlock<pntos.cobra.internal.TutorialFogmBlock>` to the fusion engine.                                                                                                                                                                                 | [](../plugins/state_modeling_plugin.md)  |
| {py:obj}`LcmLogTransportPlugin <pntos.cobra.LcmLogTransportPlugin>`                           | Reads {term}`ASPN` messages from an {term}`LCM` log file and feeds these {term}`ASPN` messages into the app as pntOS {py:obj}`Message <pntos.api.Message>`s.                                                                                                                                                                                                                                                                                                              | [](../plugins/transport_plugin.md)       |

## Expected Results

For instructions of how to run this app, see [](../first_app.md). After running the app you should see the following results:

![](../images/gps_ins_expected_traj.png)

The Northing vs. Easting Trajectory plot which displays the INS-D PVA output and the Cobra PVA solution. It may be hard to tell, but they lie on top of one another, which is exactly what we want to see!

![](../images/gps_ins_expected_vel_err.png)

The NED Velocity Error plot which displays the velocity error between the INS-D PVA output and the Cobra PVA solution at each time epoch.
