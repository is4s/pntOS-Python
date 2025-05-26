# Introduction

## Motivation

Many Position, Navigation, and Timing (PNT) systems are [stovepipe systems](https://en.wikipedia.org/wiki/Stovepipe_system)
that are designed for a specific configuration of sensors to solve a particular PNT need. However,
reliance on PNT in industry is evolving rapidly, and GNSS-challenged environments are becoming more
commonplace. Complementary PNT approaches mitigate these threats, but changing current PNT
systems is a slow and expensive process.

The Python pntOS Application Programming Interface (API) is designed to address this
situation. It has broken up the concept of a PNT sensor fusion system into its component pieces
(called plugins) and defined an API to standardize their interactions, allowing for
plugins to be individually swappable. In order to aid development of new plugins,
[`pntos-python`](https://git.aspn.us/pntos/pntos-python) provides not only a full Python
API, but also a set of plugins and {term}`Apps<App>` to serve as a reference implementation
(called {term}`Cobra`).

## Source Code Breakdown

This project consists of the following main parts:

```{table} Python pntOS Project Breakdown
| Component name                                                                               | Location within the project       | Description                                                                               |
|:-------------------------------------------------------------------------------------------- |:--------------------------------- |:----------------------------------------------------------------------------------------- |
| [Python pntOS Architecture Application Programming Interface (API)](./documentation/api.rst) | `pntos-api/src/pntos/api/plugins` | Defines a set of plugins and how they are to interact.                                    |
| [Cobra Plugins](./plugins.md)                                                                | `pntos-cobra/src/pntos/cobra`     | Implementation of API - functional Python plugins and helper objects.                     |
| [Cobra Apps](./first_app.md)                                                                 | `apps/`                           | Each app loads a set of Cobra plugins, defines any config values, and starts the plugins. |
```

While pntOS is analogous to an operating system in its functionality, it is not a true
operating system. For more information, see {ref}`is-pntos-an-operating-system`.

## High Level Overview

First let's look at the Python pntOS API as a black box. It accepts measurements from
various sensors, performs data fusion or filtering, and produces a navigation solution.
All navigation data used internally in the Python pntOS API is ASPN-formatted data. Most
sensors do not output ASPN data so the data needs to be converted before it can be used.
This can happen in a few places:

* In between the sensor and pntOS
* In the pntOS [](./plugins/transport_plugin.md)
* In the sensor itself

The following image illustrates these operating modes in order from top to
bottom respectively:

TODO: Edit this graphic
![](images/pntos_overview.svg)

Next we'll open up the the Python pntOS API box and discuss some of the core components and
plugins that make up the Python pntOS API.

## Python pntOS API Components

We will start at the bottom of the diagram with the {term}`App` and work our way through
the control flow. You can find more details about the {term}`Cobra` implementations of
these plugins in the [](./plugins.md) section of these docs.

TODO: Edit this graphic
![image](images/pntos_overview2.svg)

### App

An {term}`App` consists of a single Python script that is responsible for the following:
* Import plugin objects
* Define any config values
* Create a controller plugin
* Create a list of other plugins to pass to the controller
* Lastly, pass the list of plugins off to the controller with
{py:obj}`ControllerPlugin.take_control()<pntos.api.ControllerPlugin.take_control>` to
pass control to the {py:obj}`Controller Plugin<pntos.api.ControllerPlugin>` and start
the system.

### Controller

From this point forward, the {py:obj}`Controller Plugin<pntos.api.ControllerPlugin>` is
responsible for all activity in the app. It may use any of the plugins it was passed
as desired. The {py:obj}`Controller Plugin<pntos.api.ControllerPlugin>` defines any and
all input and output it supports, which plugins are loaded or used, and the type
of fusion being done. The {py:obj}`Controller Plugin<pntos.api.ControllerPlugin>` should
be written generically to support arbitrary run-time environment sensing. Outside of
some initialization in the {term}`app<App>`, the {py:obj}`Controller
Plugin<pntos.api.ControllerPlugin>` is the conceptual "main" function of the Python
pntOS app.

The controller's main responsibility is to choose and initialize the
concurrency model being used by pntOS. For example, a controller might decide
on a multithreaded implementation, or a multiprocessed implementation for
better isolation and security. A simple controller might create a single thread
for each plugin it was given and then set up thread-safe communication pipes
between those plugins.

For more information on {term}`Cobra` implementation of a {py:obj}`Controller
Plugin<pntos.api.ControllerPlugin>`, see [](./plugins/controller_plugin.md).

### Mediator

Named after the computer science [mediator design
pattern](https://en.wikipedia.org/wiki/Mediator_pattern) concept, the
{py:obj}`Mediator<pntos.api.Mediator>` is an object created by the {py:obj}`Controller
Plugin<pntos.api.ControllerPlugin>` and handed to each plugin. It encapsulates
communication and shared state between the plugins.

Before the controller may use any of the plugins it was passed, it must first call the
{py:obj}`init_plugin()<pntos.api.CommonPlugin.init_plugin()>` function on that plugin
and pass into it a {py:obj}`Mediator<pntos.api.Mediator>`. The
{py:obj}`Mediator<pntos.api.Mediator>` object is the only way that plugins may
communicate back to the {py:obj}`Controller Plugin<pntos.api.ControllerPlugin>`, by
invoking the function pointers on their {py:obj}`Mediator<pntos.api.Mediator>`.

The {py:obj}`Mediator<pntos.api.Mediator>` therefore is where concurrency and
synchronization are decided. Continuing the example of a multithreaded implementation
where each plugin is in a separate thread, the {py:obj}`Controller
Plugin<pntos.api.ControllerPlugin>` might implement a simple
{py:obj}`Mediator<pntos.api.Mediator>` by creating and storing internally a set of mutex
locks, one per thread, and then locking each call to a
{py:obj}`Mediator<pntos.api.Mediator>` function using a mutex. The
{py:obj}`Mediator<pntos.api.Mediator>` function calls would then consist of locking
logic followed by routing calls from one plugin to another. In our current example
illustrated in the above diagram, we are routing data the {py:obj}`Transport
Plugin<pntos.api.TransportPlugin>` received from a sensor through the
{py:obj}`Mediator<pntos.api.Mediator>`, which in turn (after synchronization according
to its concurrency model) sends the data on to the {py:obj}`Orchestration
Plugin<pntos.api.OrchestrationPlugin>`.

As another example, suppose instead we were writing a multiprocessed controller. In this
case, the controller might ``fork()`` to put plugins into their own processes, and then
write a {py:obj}`Mediator<pntos.api.Mediator>` that opens IPC communication primitives
(such as ``/dev/shm`` or sockets) in order to route the data from the {py:obj}`Transport
Plugin<pntos.api.TransportPlugin>` to the {py:obj}`Orchestration
Plugin<pntos.api.OrchestrationPlugin>`, which are now in different processes. Thus the
{py:obj}`Mediator<pntos.api.Mediator>` that is constructed by the {py:obj}`Controller
Plugin<pntos.api.ControllerPlugin>` is tied closely to the concurrency model chosen by
the {py:obj}`Controller Plugin<pntos.api.ControllerPlugin>`.

Since the {py:obj}`Mediator<pntos.api.Mediator>` is part of the {py:obj}`Controller
Plugin<pntos.api.ControllerPlugin>`, see [](./plugins/controller_plugin.md) for more
information on {term}`Cobra` {py:obj}`Mediator<pntos.api.Mediator>` implementation.

### Transport

The {py:obj}`Transport Plugin<pntos.api.TransportPlugin>` receives messages from various
sensors, sends responses back to sensors as needed, and broadcasts the pntOS solution
from the {py:obj}`Orchestration Plugin<pntos.api.OrchestrationPlugin>`. Its primary
responsibility is receiving sensor data from the network, converting it to ASPN format,
and then forwarding it onward to the mediator.

For more information about {term}`Cobra` implementation of the {py:obj}`Transport
Plugin<pntos.api.TransportPlugin>`, see [](./plugins/transport_plugin.md).

### Orchestration

The {py:obj}`Orchestration Plugin<pntos.api.OrchestrationPlugin>` contains the core
navigation data fusion and filtering functionality. It is responsible for calculating a
navigation solution from the incoming sensor data. It performs this task by calling out
to various plugins which define the actual sensor fusion algorithm, state space, and
sensor error models. Thus its primary duties are to orchestrate the flow of data
into/out of filters, and picking the set of navigation-related plugins which are used to
model errors and generate estimates.

For more information about {term}`Cobra` implementation of the {py:obj}`Orchestration
Plugin<pntos.api.OrchestrationPlugin>`, see [](./plugins/orchestration_plugin.md).


### Platform Integration

The {py:obj}`Platform Integration Plugin<pntos.api.PlatformIntegrationPlugin>` is an
optional plugin. It converts the outgoing navigation solution from an ASPN format to any
other format required by the user in addition to handling any signals originating from
the platform (e.g. A platform signal to tell sensors to switch to a low-power mode).


## Orchestration Plugin Components

Next, let's dive into the components and plugins that make up the
{py:obj}`Orchestration Plugin<pntos.api.OrchestrationPlugin>`.

TODO: Update graphic to be "Python pntOS"
![image](images/pntos_overview3.svg)

The {py:obj}`Orchestration Plugin<pntos.api.OrchestrationPlugin>` could be a single
black box solution or broken up into more modular components. In the latter case, a bank
of one or more filters has access to a bank of filtering plugins. Filtering plugins
might include the:

* [Fusion Plugin](#fusion)
* [Fusion Strategy Plugin](#fusion-strategy)
* [Inertial Plugin](#inertial)
* [Initialization Plugin](#initialization)
* [State Modeling Plugin](#state-modeling)
* [Preprocessor Plugin](#preprocessor)

### Fusion

The {py:obj}`Fusion Plugin<pntos.api.FusionPlugin>` accepts sensor measurements (and
possibly a reference Position-Velocity-Attitude (PVA) solution from the
{py:obj}`Inertial Plugin<pntos.api.InertialPlugin>`) via the {py:obj}`Orchestration
Plugin<pntos.api.OrchestrationPlugin>` and passes them to the {py:obj}`Fusion Strategy
Plugin<pntos.api.FusionStrategyPlugin>`. It does all the book-keeping to keep track of
which state blocks and measurement processors correspond to which states in the
{py:obj}`Fusion Strategy Plugin<pntos.api.FusionStrategyPlugin>`.

### Fusion Strategy

The {py:obj}`Fusion Strategy Plugin<pntos.api.FusionStrategyPlugin>` does the core
estimation work. It determines what type of estimator is used, such as an Extended
Kalman Filter (EKF), Rao-Blackwellized Particle Filter (RBPF), or something else. It
receives models from the state blocks and measurement processors in the {py:obj}`State
Modelling Plugin<pntos.api.StateModelingPlugin>`'s via the {py:obj}`Fusion
Plugin<pntos.api.FusionPlugin>` and propagates and updates its states accordingly.

For more details about {term}`Cobra` implementation of this plugin, see
[](./plugins/fusion_strategy_plugin.md).

### Inertial

{py:obj}`Inertial Plugin<pntos.api.InertialPlugin>` receives an initial PVA alignment
and IMU (Inertial Measurement Unit) measurements which it mechanizes to produce an INS
(Inertial Navigation System) solution. This plugin may also handle resets and feedback
from the {py:obj}`Orchestration Plugin<pntos.api.OrchestrationPlugin>`.

For more details about {term}`Cobra` implementation of this plugin, see
[](./plugins/inertial_plugin.md).

### Initialization

This plugin uses sensor data and user inputs received from the {py:obj}`Orchestration
Plugin<pntos.api.OrchestrationPlugin>` to calculate an initial solution. This could be a
PVA used as the starting point for the INS solution generated by the {py:obj}`Inertial
Plugin<pntos.api.InertialPlugin>` or an estimate and covariance used to initialize a
state block.

For more details about {term}`Cobra` implementation of this plugin, see
[](./plugins/initialization_plugin.md).

### State Modeling

The {py:obj}`State Modeling Plugin<pntos.api.StateModelingPlugin>` contains lists of
{py:obj}`Measurement Processor<pntos.api.StandardMeasurementProcessor>`s,
{py:obj}`State Block<pntos.api.StandardStateBlock>`s, and {py:obj}`Virtual State
Block<pntos.api.VirtualStateBlock>`s and a factory to construct them (the
{py:obj}`State Model Provider<pntos.api.StandardStateModelProvider>`). At the
{py:obj}`Orchestration Plugin<pntos.api.OrchestrationPlugin>`'s request it constructs these objects
and adds them to the fusion engine (e.g. {py:obj}`StandardFusionEngine<pntos.api.StandardFusionEngine>`).

![image](images/state_modeling_plugin.svg)

Below is some very brief information about {py:obj}`Measurement
Processor<pntos.api.StandardMeasurementProcessor>`s, {py:obj}`State
Block<pntos.api.StandardStateBlock>`s, and {py:obj}`Virtual State
Block<pntos.api.VirtualStateBlock>`s.

For more details about {term}`Cobra` implementation of this plugin, see
[](./plugins/state_modeling_plugin.md).

#### Measurement Processor

{py:obj}`Measurement Processor<pntos.api.StandardMeasurementProcessor>`s are
responsible for providing the model that the Filter Strategy uses to update its states
given a sensor measurement.

#### State Block

{py:obj}`State Block<pntos.api.StandardStateBlock>`s provide the Filter Strategy with
states and a model to propagate those states.

![image](images/state_block.svg)

#### Virtual State Block

Consider the case where a given {py:obj}`State Block<pntos.api.StandardStateBlock>`
provides three Latitude-Longitude-Altitude (LLH) states and a given {py:obj}`Measurement
Processor<pntos.api.StandardMeasurementProcessor>` provides a model to update three
Earth Centered, Earth Fixed (ECEF) position states. Normally this {py:obj}`Measurement
Processor<pntos.api.StandardMeasurementProcessor>` and {py:obj}`State
Block<pntos.api.StandardStateBlock>` would be incompatible with each other, but a
{py:obj}`Virtual State Block<pntos.api.VirtualStateBlock>` that converts between ECEF
position and LLH position could bridge the gap.

In short, {py:obj}`Virtual State Block<pntos.api.VirtualStateBlock>`s convert the
states provided by {py:obj}`State Block<pntos.api.StandardStateBlock>`s.

## Preprocessor

The Preprocessor plugin can be used by either the Controller plugin or the Orchestration plugin. It
generates at least one type of {py:obj}`Preprocessor<pntos.api.Preprocessor>`.

The job of the Preprocessor is simple: consume a {py:obj}`Message<pntos.api.Message>` and, when
applicable, modify it somehow. There are several ways a Preprocessor plugin could go about this. A
couple example cases:

- A Preprocessor plugin could detect faulty data and reject it, returning nothing.
- A Preprocessor plugin could mitigate issues in a sensor by editing the data before it is sent to
  the filter.

## Another View of the Python pntOS API

At this point, now that we've gotten some understanding of the core components
and plugins in pntOS, let's take a look at everything all together and define
some of the smaller plugins.

TODO: Edit this graphic
![image](images/pntos_yet_another_view.svg)

This graphic shows how the {py:obj}`Orchestration Plugin<pntos.api.OrchestrationPlugin>`
relates to pntOS as a whole, but also the relationship of the plugins that plug into the
{py:obj}`Orchestration Plugin<pntos.api.OrchestrationPlugin>` by the `Plugin
Dependencies` arrows.

The figure also shows an optional use between the {py:obj}`Transport
Plugin<pntos.api.TransportPlugin>` and the {py:obj}`Platform Integration
Plugin<pntos.api.PlatformIntegrationPlugin>`. This indicates that the {py:obj}`Platform
Integration Plugin<pntos.api.PlatformIntegrationPlugin>` is allowed to use the
{py:obj}`Transport Plugin<pntos.api.TransportPlugin>` for input and output or handle
input and output on its own.

So far we've discussed the {term}`App`, {py:obj}`Controller Integration
Plugin<pntos.api.ControllerPlugin>`, {py:obj}`Mediator<pntos.api.Mediator>`,
{py:obj}`Transport Plugin<pntos.api.TransportPlugin>`, {py:obj}`Platform Integration
Plugin<pntos.api.PlatformIntegrationPlugin>`, {py:obj}`Orchestration
Plugin<pntos.api.OrchestrationPlugin>`, {py:obj}`Fusion Plugin<pntos.api.FusionPlugin>`,
{py:obj}`Fusion Strategy Plugin<pntos.api.FusionStrategyPlugin>`, {py:obj}`State
Modeling Plugin<pntos.api.StateModelingPlugin>`, {py:obj}`Inertial
Plugin<pntos.api.InertialPlugin>`, and {py:obj}`Initialization
Plugin<pntos.api.InitializationPlugin>`. Next we'll move on to the remaining plugins: the
{py:obj}`Logging Plugin<pntos.api.LoggingPlugin>`, {py:obj}`Registry
Plugin<pntos.api.RegistryPlugin>`, and {py:obj}`User Interface (UI)
Plugin<pntos.api.UiPlugin>`.

## Logging

The {py:obj}`Logging Plugin<pntos.api.LoggingPlugin>` records messages to an arbitrary
sink (e.g. console, file, network, etc.). For more details about {term}`Cobra`
implementation of this plugin, see [](./plugins/logging_plugin.md).

## Registry

The {py:obj}`Registry Plugin<pntos.api.RegistryPlugin>` implements a global
group-key-value registry. For more details about {term}`Cobra` implementation of this
plugin, see [](./plugins/registry_plugin.md). This is useful for configuring plugins and provides a way for plugins to share data.

# UI

The {py:obj}`UI Plugin<pntos.api.UiPlugin>` implements a UI that is integrated directly
into the Python pntOS API implementation. While it is always possible to write a
Graphical User Interface (GUI) that listens to outputs and interacts with it externally,
this plugin allows users to write a GUI that has direct access to the
mediator. This allows for low latency and high performance
GUI/UIs to be generated. Note that this plugin is designed for developer or research
style UIs and not production environments. A user display in a production environment is
better modeled as a {py:obj}`Platform Integration
Plugin<pntos.api.PlatformIntegrationPlugin>`, as that is designed to represent requests
from the system and not simply status updates.

## Next Steps

| Link                    | Description                                                                                                     |
| ----------------------- | --------------------------------------------------------------------------------------------------------------- |
| [](./plugins.md)        | Explore the {term}`Python pntOS API` plugins in greater detail, as well as their {term}`Cobra` implementations. |
| [](./installation.md)   | Installation instructions for getting started with {term}`Cobra`.                                               |
| [](./first_app.md)      | Instructions for running your first {term}`Cobra` tutorial {term}`App`.                                         |
| {ref}`tutorial-apps`    | Explore the {term}`Cobra` tutorial apps.                                                                        |
| {ref}`pntos_python_api` | Explore the {term}`Python pntOS API` documentation.                                                             |
| [](./cobra.md)          | Explore the {term}`Cobra` documentation.                                                                        |