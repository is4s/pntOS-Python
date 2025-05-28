# Introduction

## Motivation

Many Position, Navigation, and Timing (PNT) systems are [stovepipe systems](https://en.wikipedia.org/wiki/Stovepipe_system)
that are designed for a specific configuration of sensors to solve a particular PNT need. However,
reliance on PNT in industry is evolving rapidly, and GNSS-challenged environments are becoming more
commonplace. Complementary PNT approaches mitigate these limitations, but changing current PNT
systems is a slow and expensive process.

The Python pntOS Application Programming Interface (API) is designed to address this
situation. It has broken up the concept of a PNT sensor fusion system into its component pieces
(called plugins) and defined an API to standardize their interactions, allowing for
plugins to be individually swappable. In order to aid development of new plugins,
[pntos-python](https://git.aspn.us/pntos/pntos-python) provides not only a [full Python
API](./documentation/api.rst),
but also a set of plugins and {term}`Apps<App>` to serve as a reference implementation
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

While pntOS is analogous to an operating system in terms of its comprehensive scope, it is not a true
operating system in the sense of a kernel. For more information, see {ref}`is-pntos-an-operating-system`.

## High Level Overview of Python pntOS

At the toplevel, the Python pntOS API defines a set of plugins that collectively: accept sensor data from various sensors,
perform sensor fusion on the sensor data, and finally produce a resulting navigation solution. 
This concept is illustrated below, with an example experimental setup where pntOS is receiving and processing
data from three sensors and producing a fused navigation solution:

![](images/pntos_overview.svg)

In this example, the data comes from the three sensors on the left and is processed by a set of Python pntOS plugins;
Python pntOS then produces a solution on the right. Data from all three sensors are accepted by pntOS,
even though some of the data is in proprietary formats and some of it is in ASPN. This is because pntOS
accepts both ASPN and non-ASPN data from sensors, and will operate in a heterogeneous environment where both ASPN and
non-ASPN sensor data is available.

```{note}
All navigation data used internally by Python pntOS plugins must be ASPN-formatted (with exceptions
made for truly exceptional use cases); thus, the cleanest way to send data into pntOS 
is in the ASPN format, as shown by the "ASPN Native Sensor" in the figure. However, most
sensors do not output ASPN data natively, and such  non-ASPN sensor data needs to be converted to ASPN before
it can be used by pntOS internally. This conversion can happen in two places:

1. In-between the sensor and pntOS, by using an ASPN adapter that intercepts the data and converts it
  to ASPN, as shown by the top sensor in the above figure. 
2. Inside Python pntOS, there is a plugin called the [Transport Plugin](./plugins/transport_plugin.md), which is designed to
  accept non-ASPN sensor data off the wire and convert it to ASPN for use by the other pntOS plugins. 
  The middle sensor in the figure above sends proprietary sensor data directly into pntOS, so its data would need
  to be converted into ASPN by a [Transport Plugin](./plugins/transport_plugin.md) inside pntOS. 
  We'll learn more about the transport plugin and how it converts incoming data to ASPN in the 
  [tour of Python pntOS](#a-tour-of-python-pntos).

```

Now that we've covered what pntOS' top-level objectives are, we will shift gears and take
a brief tour of Python pntOS, walking through a Python pntOS system and examining
how Python pntOS decomposes the "sensor data in, sensor fusion solution out" problem into a set of
isolated plugins.

## A Tour of Python pntOS

The Python pntOS black box in the figure from the previous section is really a collection
of plugins that are utilized by an app, as shown here:


![image](images/pntos_overview2.svg)
**TODO**: Edit this with a version of the image that replaces the loader with an App.


In this tour, we will dive into the details of how one would go about implementing
each of the components of pntOS in the above figure, examining each part of Python pntOS piece by piece
and discussing how we would create a Python pntOS solution from start to finish. 
We will start at the bottom of the figure with the {term}`App` (which is the entry point into any 
Python pntOS system) and work our way through the control flow. In particular, in this 
section we will walk through how:

1. The {term}`App` kick starts the system, then transfers control to the
  {py:obj}`Controller Plugin<pntos.api.ControllerPlugin>`, passing it a list of plugins to use.
2. The {py:obj}`Controller Plugin<pntos.api.ControllerPlugin>` takes in the list of plugins and
  wires them up to be able to communicate with each other via the
  {py:obj}`Mediator<pntos.api.Mediator>`.
3. The {py:obj}`Transport Plugin<pntos.api.TransportPlugin>` receives data off the wire from a
  sensor, then delivers that data to the {py:obj}`Mediator<pntos.api.Mediator>`.
4. The {py:obj}`Mediator<pntos.api.Mediator>` routes the sensor data it receives from the
  {py:obj}`Transport Plugin<pntos.api.TransportPlugin>` to the 
  {py:obj}`Orchestration Plugin<pntos.api.OrchestrationPlugin>`.
5. The {py:obj}`Orchestration Plugin<pntos.api.OrchestrationPlugin>` receives the sensor data
  and processes it into a solution, and makes the PNT solution available to anyone who calls 
  {py:obj}`OrchestrationPlugin.request_solutions()<pntos.api.OrchestrationPlugin.request_solutions()>`.


You can find more details about the {term}`Cobra` implementations of
each of these plugins in the [Plugin Reference](./plugins.md) section of these docs.


### The App

All Python pntOS solutions start with an {term}`App`. In Python pntOS terminology, an {term}`App` consists 
of a single Python script that the user may run and produces a working Python pntOS system. 
In general, the {term}`App` is responsible for:

1. Importing the desired Python pntOS plugin definitions (from Cobra or elsewhere)
2. Defining any initial config, either from inline structs or from a config file
3. Creating an instance of a controller plugin
4. Creating a list of instances of other plugins to pass to the controller, as desired
5. Calling {py:obj}`ControllerPlugin.take_control()<pntos.api.ControllerPlugin.take_control>` on the 
  controller plugin we created in `3.` to start the system. The controller plugin is passed in the 
  list of the other plugins we created in `4.`, and it is now responsible for setting up the system using them. 
  Once {py:obj}`ControllerPlugin.take_control()<pntos.api.ControllerPlugin.take_control>` is called,
  the {term}`App`'s job is done, and the {py:obj}`Controller Plugin<pntos.api.ControllerPlugin>` coordinates
  the pntOS system going forward.

```{note}
One way to think of an {term}`App` is that it is a simple Python script that kicks off the system, finds the plugins and
config that we want to use, then hands off control to the {py:obj}`Controller Plugin<pntos.api.ControllerPlugin>`. 
The {py:obj}`Controller Plugin<pntos.api.ControllerPlugin>` is the conceptual "main" function of Python pntOS,
in that {py:obj}`ControllerPlugin.take_control()<pntos.api.ControllerPlugin.take_control>` is where the plugins are
wired up to talk to each other, told to start listening and processing data, and so forth.
```

Most apps will look very similar to each other, with the only changes being which plugins the {term}`App` has 
decided to use and what config stanzas it needs. You can find an example of a full-fledged {term}`App` that performs
GPS/INS sensor fusion from sensor data it receives from an LCM network bus
[here](https://git.aspn.us/pntos/pntos-python/-/blob/main/apps/fusion_gps_ins/fusion_gps_ins.py?ref_type=heads).
For instructions on how to run this example app, see [running an app](first_app.md).

### Implementing Our Own Custom App

For the purposes of this tour, suppose we defined a new app that used five plugins, of the following types:

| Plugin Type          | Description                                                                                     |
|----------------------|-------------------------------------------------------------------------------------------------|
| Orchestration Plugin | A plugin that is given sensor data and produces a solution (i.e. via sensor fusion internally)  |
| Transport Plugin     | A plugin that listens for sensor data from a network and converts it to ASPN format (if needed) | 
| Registry Plugin      | A plugin that stores key/value pairs, and comes pre-populated with values from a config file    | 
| Logging Plugin       | A plugin that takes errors/warnings and prints them to a log (e.g. the console)                 |
| Controller Plugin    | A plugin that receives all the other plugins and takes over control from the App.               | 

Furthermore, suppose we wanted to use off-the-shelf Cobra plugins for the transport, registry, logging, and controller
plugins, but wanted to implement our own sensor fusion solution in a custom 
{py:obj}`Orchestration Plugin<pntos.api.OrchestrationPlugin>`. Then we might write our app like this:

```python
# Use the off-the-shelf Cobra implementations of these plugins
from pntos.cobra import (
    SimpleTransportPlugin,
    SimpleRegistryPlugin,
    SimpleLoggingPlugin,
    SimpleControllerPlugin,
)

# Define our own OrchestrationPlugin (sensor data in, solution out)
from my.example.project import (
    MyOrchestrationPlugin,
)

# Create the orchestration plugin
my_orchestration = MyOrchestrationPlugin("My Orchestration Name")

# Create the other plugins and put them into a list
my_transport = SimpleTransportPlugin("My Transport Name")
my_registry = SimpleRegistryPlugin("My Registry Name")
my_logging = SimpleLoggingPlugin("My Logger Name")
my_controller = SimpleControllerPlugin("My Controller Name")
other_plugin_list = [my_orchestration, my_transport, my_registry, my_logging]

# Give the controller control, and pass it the list of other plugins
my_controller.take_control(other_plugin_list)
```

...and thats it! Once our {term}`App` calls
{py:obj}`my_controller.take_control()<pntos.api.ControllerPlugin.take_control>`, passing in
the `other_plugin_list` as the `plugins` parameter, our app is done. The rest of the work is done
inside the {py:obj}`SimpleControllerPlugin<pntos.api.ControllerPlugin>` implementation, which is the 
next stop on our tour.


### Understanding the Controller Plugin

Once the {term}`App` has called {py:obj}`ControllerPlugin.take_control()<pntos.api.ControllerPlugin.take_control>`, 
the {py:obj}`Controller Plugin<pntos.api.ControllerPlugin>` is
responsible for all activity in the app going forward. The {py:obj}`Controller Plugin<pntos.api.ControllerPlugin>`
has one method on it, namely {py:obj}`take_control()<pntos.api.ControllerPlugin.take_control>`, so implementing
that method is all that is needed to fully implement a {py:obj}`Controller Plugin<pntos.api.ControllerPlugin>`. 
Thus, we will turn out attention towards what is required to implement 
the {py:obj}`take_control()<pntos.api.ControllerPlugin.take_control>` method.


As a parameter, 
{py:obj}`take_control<pntos.api.ControllerPlugin.take_control>` receives a list of plugins that it is
supposed to use to set up the Python pntOS system. For example, our {py:obj}`Controller<pntos.api.ControllerPlugin>`
might receive this list of plugins:

```python
[my_orchestration, my_transport, my_registry, my_logging]
```

as described in the last section.

Our task in implementing the {py:obj}`take_control()<pntos.api.ControllerPlugin.take_control>` method is
to write some code that takes those four plugins that were passed in as parameters and create a PNT fusion
system out of them.

Let's suppose we wanted to start with the simplest possible implementation of 
{py:obj}`take_control()<pntos.api.ControllerPlugin.take_control>`, and so we decided to throw out 
`my_registry` (configuration) and `my_logging` (error logging) plugins for the moment. Then we would be left with two: A 
{py:obj}`Transport Plugin<pntos.api.TransportPlugin>` called `my_transport`, which _produces_ sensor data from the
network, and an {py:obj}`Orchestration Plugin<pntos.api.Orchestration Plugin>` called `my_orchestration`, which
_consumes_ sensor data and produces PNT solutions. Then the implementation of
{py:obj}`take_control()<pntos.api.ControllerPlugin.take_control>` would ideally set up a pipeline that looked like this:

```
        (sensor data)              (ASPN sensor data)                    (ASPN solution)
Network       ->        my_transport      ->             my_orchestration      ->      Output
```
**TODO** Figure here if we have time, instead of text drawing. Similar to the figure above, with other details cut,
such as the external sensors.

To set up that chain of data flow, the {py:obj}`take_control()<pntos.api.ControllerPlugin.take_control>` method
would need to perform the following steps in order:

0. First call {py:obj}`init_plugin()<pntos.api.CommonPlugin.init_plugin>` on both 
  {py:obj}`my_transport<pntos.api.TransportPlugin>` and 
  {py:obj}`my_orchestration<pntos.api.OrchestrationPlugin>` plugins before using them 
  (more on why we need to do this in a minute).
1. Tell {py:obj}`my_transport<pntos.api.TransportPlugin>` to start listening to its network bus,
  by calling {py:obj}`my_transport.start_listening()<pntos.api.TransportPlugin.start_listening>`.
2. Take the sensor data received from {py:obj}`my_transport<pntos.api.TransportPlugin>` and send 
  it to 
  {py:obj}`my_orchestration<pntos.api.OrchestrationPlugin>`'s 
  {py:obj}`process_pntos_message()<pntos.api.OrchestrationPlugin.process_pntos_message>`, which accepts ASPN sensor data
  and processes it into a solution.
3. Call {py:obj}`my_orchestration<pntos.api.OrchestrationPlugin>`'s 
  {py:obj}`request_solutions()<pntos.api.OrchestrationPlugin.request_solutions()>`, which asks the 
  {py:obj}`Orchestration Plugin<pntos.api.OrchestrationPlugin>` to return the PNT solution it has computed 
  by utilizing all previously received data from step 2.

```{note}
A few other necessary chores are omitted here for brevity.
```

Step 1 is relatively straightforward, since we have the {py:obj}`my_transport<pntos.api.TransportPlugin>`
in our hand (it was passed in as a parameter) and we can directly call the
{py:obj}`my_transport.start_listening()<pntos.api.TransportPlugin.start_listening>` method on it. Similarly,
Step 3 is relatively straightforward, as we have the {py:obj}`my_orchestration<pntos.api.OrchestrationPlugin>`
in our hand (it was passed in as a parameter) and we can directly call the
{py:obj}`my_orchestration.request_solutions()<pntos.api.OrchestrationPlugin.request_solutions()>` method on it. However, 
Step 2 requires us to receive data from the {py:obj}`Transport Plugin<pntos.api.TransportPlugin>`, such that
we might pass it into the {py:obj}`Orchestration Plugin<pntos.api.OrchestrationPlugin>`'s 
  {py:obj}`process_message()<pntos.api.OrchestrationPlugin.process_message()>`. How do we do that?

The answer lies in the mediator, and the {py:obj}`init_plugin()<pntos.api.CommonPlugin.init_plugin>` call in Step 0
that we overlooked.

### The Mediator and init_plugin

In Python pntOS, plugins do not ever directly communicate with each other. Instead, when the 
{py:obj}`Controller Plugin<pntos.api.ControllerPlugin>` receives a list of plugins as a parameter to its
{py:obj}`take_control()<pntos.api.ControllerPlugin.take_control>` method, the first thing the
{py:obj}`Controller Plugin<pntos.api.ControllerPlugin>` does is pass each plugin in the list a 
{py:obj}`Mediator<pntos.api.Mediator>`, by calling each plugin's
{py:obj}`init_plugin()<pntos.api.CommonPlugin.init_plugin>` method and passing in the
{py:obj}`Mediator<pntos.api.Mediator>` as a parameter. Each plugin is then required to save off the
{py:obj}`Mediator<pntos.api.Mediator>` it was passed, and use it for all communications with other plugins going
forward. Understanding how the {py:obj}`Mediator<pntos.api.Mediator>` works is vital to understanding the pntOS
architecture, as all data that pass from one plugin to another flows through it.

```{note}
One way to think of the Mediator is that it is a "communications object". Every plugin is handed a communications
object when it first starts, and from then on that plugin should use the communications object for all interactions
with any other Python pntOS plugin.
```
```{note}
Mediators are so named because they implement the computer science [mediator design
pattern](https://en.wikipedia.org/wiki/Mediator_pattern) concept. They represent an abstraction of the
middleware between plugins, and allow plugins to be used in a variety of concurrency models (multi-threaded,
single-threaded, coroutines, distributed computing, etc.) without the plugin knowing or caring how
comms between plugins is actually being implemented. While the inversion-of-control that comes with
using a Mediator pattern adds complexity, it is necessary to support swappable/pluggable concurrency models.
```

Because the design of pntOS is such that all plugins must communicate with other plugins via the
{py:obj}`Mediator<pntos.api.Mediator>`, that means that our previous figure actually should look like


```
        (sensor data)                 (ASPN sensor data)       (ASPN sensor data)                 (ASPN solution)
Network       ->        Transport Plugin      ->        Mediator      ->      Orchestration Plugin      ->      Output
```

That is, the {py:obj}`Transport Plugin<pntos.api.TransportPlugin>` cannot directly send data to the
{py:obj}`Orchestration Plugin<pntos.api.OrchestrationPlugin>`, but instead must send the data into
the {py:obj}`Mediator<pntos.api.Mediator>`, and it is the {py:obj}`Mediator<pntos.api.Mediator>`'s job
to route that data to the {py:obj}`Orchestration Plugin<pntos.api.OrchestrationPlugin>`.

That brings us back to the question: How do we implement Step 2 of the
{py:obj}`take_control()<pntos.api.ControllerPlugin.take_control>` task list? Our goal is to receive the data
that the {py:obj}`Transport Plugin<pntos.api.TransportPlugin>` receives off the wire, so we can send it
into the next stage. In order to understand how to do that, it would be helpful to fully understand 
how the {py:obj}`Transport Plugin<pntos.api.TransportPlugin>`
is implemented and how it delivers data to its {py:obj}`Mediator<pntos.api.Mediator>`. Thus, 
let's take a detour and look at how a simple {py:obj}`Transport Plugin<pntos.api.TransportPlugin>`
is implemented, and then we'll return to the implementation of
{py:obj}`take_control()<pntos.api.ControllerPlugin.take_control>` in a minute,
armed with that knowledge and better prepared to implement Step 2 of the
{py:obj}`take_control()<pntos.api.ControllerPlugin.take_control>` method.

### Understanding the Transport Plugin

A {py:obj}`Transport Plugin<pntos.api.TransportPlugin>` has one primary purpose: receive sensor data from
a sensor and deliver it into its {py:obj}`Mediator<pntos.api.Mediator>`, for consumption/routing to other
plugins. 

How a {py:obj}`Transport Plugin<pntos.api.TransportPlugin>` collects data from the sensor/network is totally arbitrary
and depends on the nature of the sensor data. 
For example, one transport plugin might listen to an ethernet connection for data streaming over DDS or LCM. 
Another transport plugin might listen to a local serial device or UART. 
Yet another transport plugin might simulate data,
or replay it from a log file, and not even connect to a physical network at all.

```{note}
Transport plugins are actually bi-directional bridges, translating sensor data _into_ Python pntOS
as well as sending data back out _onto_ the network bus. We'll skip the outward direction for
brevity in this tutorial. 
```

Whatever the source of the sensor data is, a {py:obj}`Transport Plugin<pntos.api.TransportPlugin>` is required to convert it into ASPN before
sending it on to its {py:obj}`Mediator<pntos.api.Mediator>`. If the source data is already in ASPN format,
great! In this case, the {py:obj}`Transport Plugin<pntos.api.TransportPlugin>` simply acts as a transparent 
network bridge, marshaling data from the source of choice into the mediator without needing to convert 
from a non-ASPN to ASPN format.

The {py:obj}`Transport Plugin<pntos.api.TransportPlugin>` has three methods of interest for the purposes of
this tour:

- {py:obj}`init_plugin()<pntos.api.CommonPlugin.init_plugin>` method, which it inherits from
  {py:obj}`CommonPlugin<pntos.api.CommonPlugin>` method. This is used to receive the 
  {py:obj}`Mediator<pntos.api.Mediator>` from the controller, and is guaranteed to be called before any of
  its other methods.
- {py:obj}`TransportPlugin.start_listening()<pntos.api.TransportPlugin.start_listening>`, which is called
  by the controller when this {py:obj}`Transport Plugin<pntos.api.TransportPlugin>` should start listening to its
  data source
- {py:obj}`TransportPlugin.stop_listening()<pntos.api.TransportPlugin.stop_listening>`, which is called
  by the controller when this {py:obj}`Transport Plugin<pntos.api.TransportPlugin>` should stop listening to its 
  data source

```{note}
Every plugin in Python pntOS is guaranteed to have its 
{py:obj}`init_plugin()<pntos.api.CommonPlugin.init_plugin>` method called by the controller
before any other method. Thus a {py:obj}`Mediator<pntos.api.Mediator>` is passed as a parameter to
{py:obj}`init_plugin()<pntos.api.CommonPlugin.init_plugin>` to each and every plugin used by Python pntOS.
```

Thus, a simple example implementation of a {py:obj}`Transport Plugin<pntos.api.TransportPlugin>`
might do the following:

- Implement {py:obj}`init_plugin()<pntos.api.CommonPlugin.init_plugin>` as a method that simply
  saves off the {py:obj}`Mediator<pntos.api.Mediator>` it is passed.
- Implement {py:obj}`TransportPlugin.start_listening()<pntos.api.TransportPlugin.start_listening>`
  as a `while` loop that collects sensor data from a log file, simulation source, or dummy data set
  and sends it into the {py:obj}`Mediator<pntos.api.Mediator>`.
- Implement {py:obj}`TransportPlugin.stop_listening()<pntos.api.TransportPlugin.stop_listening>`
  as setting a boolean that interrupts the `while` loop in 
  {py:obj}`TransportPlugin.start_listening()<pntos.api.TransportPlugin.start_listening>`.

So, how does the `while` loop in 
{py:obj}`TransportPlugin.start_listening()<pntos.api.TransportPlugin.start_listening>`
send data into the {py:obj}`Mediator<pntos.api.Mediator>`? Let's take a look at the methods available
on the {py:obj}`Mediator<pntos.api.Mediator>` for the {py:obj}`Transport Plugin<pntos.api.TransportPlugin>`
to call. The {py:obj}`Mediator<pntos.api.Mediator>`
has a lot of fields on it for things like logging, config, and so forth. But the one of interest to us
here is {py:obj}`Mediator.process_pntos_message(message)<pntos.api.Mediator.process_pntos_message>`.
The docstring reads:

> Send a new message to the system for arbitrary processing.
> For example, this function is useful for plugins who have just received new sensor 
> data that they wish to relay to the system to be used in a sensor fusion solution.

If we look at the type of the parameter that
{py:obj}`Mediator.process_pntos_message(message)<pntos.api.Mediator.process_pntos_message>`
accepts, we see that it is a {py:obj}`pntos.api.Message<pntos.api.Message>`, which is defined as

> A container for an ASPN message.

Which looks like exactly what we need. In short:

- Every plugin has an instance of {py:obj}`Mediator<pntos.api.Mediator>` available to it, passed to it
  via a call to its {py:obj}`init_plugin()<pntos.api.CommonPlugin.init_plugin>` method.
- Every {py:obj}`Mediator<pntos.api.Mediator>` has a
  {py:obj}`process_pntos_message(message)<pntos.api.Mediator.process_pntos_message>`
  method on it, which accepts delivery of new sensor data to the system from a sensor data source (such as
  a transport plugin)

We now have enough information to implement the `while` loop in
{py:obj}`TransportPlugin.start_listening()<pntos.api.TransportPlugin.start_listening>`:
for each piece of sensor data we receive, convert it to an ASPN-Python message, wrap the ASPN-Python message
in a {py:obj}`pntos.api.Message<pntos.api.Message>` by calling its constructor and passing in the ASPN-Python
message, then pass the {py:obj}`pntos.api.Message<pntos.api.Message>` into
{py:obj}`Mediator.process_pntos_message(message)<pntos.api.Mediator.process_pntos_message>`. The sensor data
will now be delivered to the {py:obj}`Mediator<pntos.api.Mediator>` and the 
{py:obj}`Transport Plugin<pntos.api.TransportPlugin>` can move on to the next sensor data in its loop (or
go back to waiting for data from the wire, for networked {py:obj}`Transport Plugins<pntos.api.TransportPlugin>`)

### A Simple Transport Plugin Example


The {py:obj}`SimpleTransportPlugin<pntos.cobra.SimpleTransportPlugin>` is designed to be the simplest possible
implementation of a {py:obj}`Transport Plugin<pntos.api.TransportPlugin>` possible to demonstrate the concepts
above, which is why it was chosen as the transport for our [custom app](#implementing-our-own-custom-app).
The source code of the {py:obj}`SimpleTransportPlugin<pntos.cobra.SimpleTransportPlugin>` can be
[found here](https://git.aspn.us/pntos/pntos-python/-/blob/main/pntos-cobra/src/pntos/cobra/SimpleTransportPlugin.py).
We can see from the source that it is very similar to the simple approach we've described above, namely it:

- Saves off its {py:obj}`Mediator<pntos.api.Mediator>` in its
  {py:obj}`init_plugin()<pntos.api.CommonPlugin.init_plugin>` method
- Implements the {py:obj}`TransportPlugin.start_listening()<pntos.api.TransportPlugin.start_listening>`
  as a `while` loop that sends a all-zeros dummy data set into the {py:obj}`Mediator<pntos.api.Mediator>`.
- Implements {py:obj}`TransportPlugin.stop_listening()<pntos.api.TransportPlugin.stop_listening>`
  as a boolean that interrupts the `while` loop in 
  {py:obj}`TransportPlugin.start_listening()<pntos.api.TransportPlugin.start_listening>`.

While this transport is not suitable for navigation (it just sends sensor data fills with zeros),
it serves as a concrete example of a transport plugin that delivers data into the mediator.

```{note}
You'll see in the implementation of `start_listening` in `SimpleTransport` that a new thread is created
to send in the zeros. This is because the Python pntOS APIs require that plugins do not block on pntOS system threads.
Since `start_listening` was called by the Python pntOS system, it is not ours to block, and so the `SimpleTransport`
creates its own thread to spin in a busy loop and call the mediator.
```

### Back to the Controller

In the previous section, we explored how the transport plugin delivered sensor data into its
{py:obj}`Mediator<pntos.api.Mediator>`. Recall that in the [](#the-mediator-and-init_plugin) section,
we decided that the data flow we wanted to support was this:

```
        (sensor data)                 (ASPN sensor data)       (ASPN sensor data)                 (ASPN solution)
Network       ->        Transport Plugin      ->        Mediator      ->      Orchestration Plugin      ->      Output
```

Also recall that in the [](#understanding-the-controller-plugin) section, we outlined our implementation
of the {py:obj}`take_control()<pntos.api.ControllerPlugin.take_control>`
method as the following four steps:

0. First call {py:obj}`init_plugin()<pntos.api.CommonPlugin.init_plugin>` on both 
  {py:obj}`my_transport<pntos.api.TransportPlugin>` and 
  {py:obj}`my_orchestration<pntos.api.OrchestrationPlugin>` plugins before using them 
  (more on why we need to do this in a minute).
1. Tell {py:obj}`my_transport<pntos.api.TransportPlugin>` to start listening to its network bus,
  by calling {py:obj}`my_transport.start_listening()<pntos.api.TransportPlugin.start_listening>`.
2. Take the sensor data received from {py:obj}`my_transport<pntos.api.TransportPlugin>` and send 
  it to 
  {py:obj}`my_orchestration<pntos.api.OrchestrationPlugin>`'s 
  {py:obj}`process_pntos_message()<pntos.api.OrchestrationPlugin.process_pntos_message>`, which accepts ASPN sensor data
  and processes it into a solution.
3. Call {py:obj}`my_orchestration<pntos.api.OrchestrationPlugin>`'s 
  {py:obj}`request_solutions()<pntos.api.OrchestrationPlugin.request_solutions()>`, which asks the 
  {py:obj}`Orchestration Plugin<pntos.api.OrchestrationPlugin>` to return the PNT solution it has computed 
  by utilizing all previously received data from step 2.

At the time, we knew how to implement Steps 1 and 3, but didn't understand how to implement Step 2.
Now we come back armed with knowledge of how the Transport Plugin delivers its data into the
{py:obj}`Mediator.process_pntos_message(message)<pntos.api.Mediator.process_pntos_message>` method
of the {py:obj}`Mediator<pntos.api.Mediator>` it received in its
{py:obj}`init_plugin()<pntos.api.CommonPlugin.init_plugin>` method. So, in order for our controller
to receive data from {py:obj}`my_transport<pntos.api.TransportPlugin>` and route it to
{py:obj}`my_orchestration<pntos.api.OrchestrationPlugin>`, we need to:

- Define and implement a {py:obj}`Mediator<pntos.api.Mediator>` object
- In the implementation of the {py:obj}`Mediator<pntos.api.Mediator>`'s
  {py:obj}`process_pntos_message(message)<pntos.api.Mediator.process_pntos_message>`
  method, forwards all messages that are received to {py:obj}`my_orchestration<pntos.api.OrchestrationPlugin>`'s
  {py:obj}`process_pntos_message()<pntos.api.OrchestrationPlugin.process_pntos_message>`
- Pass the newly defined {py:obj}`Mediator<pntos.api.Mediator>` into both
  {py:obj}`my_orchestration<pntos.api.OrchestrationPlugin>`'s and
  {py:obj}`my_transport<pntos.api.TransportPlugin>`'s 
  {py:obj}`init_plugin()<pntos.api.CommonPlugin.init_plugin>` method

and thats it! we've now set up a pipeline that forwards all data received by a
{py:obj}`Transport Plugin<pntos.api.TransportPlugin>` into the
{py:obj}`Orchestration Plugin<pntos.api.OrchestrationPlugin>`.

### A Simple Controller Plugin Example

The {py:obj}`SimpleControllerPlugin<pntos.cobra.SimpleControllerPlugin>` is designed to be a simple implementation 
of a {py:obj}`Controller Plugin<pntos.api.ControllerPlugin>` to demonstrate the concepts
above, which is why it was chosen as the controller for our [custom app](#implementing-our-own-custom-app).
The source code of the {py:obj}`SimpleControllerPlugin<pntos.cobra.SimpleControllerPlugin>` can be
[found here](https://git.aspn.us/pntos/pntos-python/-/blob/main/pntos-cobra/src/pntos/cobra/simple_controller/SimpleControllerPlugin.py),
along with its {py:obj}`SimpleMediator<pntos.cobra.SimpleMediator>`
[here](https://git.aspn.us/pntos/pntos-python/-/blob/main/pntos-cobra/src/pntos/cobra/simple_controller/SimpleMediator.py).

We can see from the source code that the {py:obj}`SimpleMediator<pntos.cobra.SimpleMediator>` 
is similar to the approach we've described above, namely:

- In the [take_control](https://git.aspn.us/pntos/pntos-python/-/blob/main/pntos-cobra/src/pntos/cobra/simple_controller/SimpleControllerPlugin.py?ref_type=heads#L101)
  implementation, the controller first
  [calls init_plugin](https://git.aspn.us/pntos/pntos-python/-/blob/main/pntos-cobra/src/pntos/cobra/simple_controller/SimpleControllerPlugin.py?ref_type=heads#L174)
  on each plugin before using them, which is our Step 0 above.
- In the [take_control](https://git.aspn.us/pntos/pntos-python/-/blob/main/pntos-cobra/src/pntos/cobra/simple_controller/SimpleControllerPlugin.py?ref_type=heads#L101)
  implementation, the controller tells [all the transport plugins to start listening](https://git.aspn.us/pntos/pntos-python/-/blob/main/pntos-cobra/src/pntos/cobra/simple_controller/SimpleControllerPlugin.py?ref_type=heads#L284),
  which is our Step 1 above.
- The [implementation of SimpleMediator.process_pntos_message](https://git.aspn.us/pntos/pntos-python/-/blob/main/pntos-cobra/src/pntos/cobra/simple_controller/SimpleMediator.py#L74)
  does some simple error checking and then 
  [passes messages received from the Transport Plugin into the orchestration plugin's process_pntos_message](https://git.aspn.us/pntos/pntos-python/-/blob/main/pntos-cobra/src/pntos/cobra/simple_controller/SimpleMediator.py#L91),
  which is our Step 2 above.

One notable difference in {py:obj}`SimpleControllerPlugin<pntos.cobra.SimpleControllerPlugin>` compared to the approach
we discussed in this tour is in Step 3. In our tour, in Step 3 we envisioned that the controller might decide to call the
{py:obj}`Orchestration Plugin<pntos.api.OrchestrationPlugin>`'s {py:obj}`request_solutions()<pntos.api.OrchestrationPlugin.request_solutions()>`,
however the {py:obj}`SimpleControllerPlugin<pntos.cobra.SimpleControllerPlugin>` does not do so. The 
{py:obj}`SimpleControllerPlugin<pntos.cobra.SimpleControllerPlugin>` forwards sensor data to the
{py:obj}`Orchestration Plugin<pntos.api.OrchestrationPlugin>` but does not force the
{py:obj}`Orchestration Plugin<pntos.api.OrchestrationPlugin>` to produce a solution. Instead, it allows other plugins to
request a solution from the {py:obj}`Orchestration Plugin<pntos.api.OrchestrationPlugin>`. For an example of where
another plugin requests a solution and sends it out onto the network bus as Python pntOS' solution, see 
[the Aspn23LcmTransportPlugin](https://git.aspn.us/pntos/pntos-python/-/blob/main/pntos-cobra/src/pntos/cobra/Aspn23LcmTransportPlugin.py?ref_type=heads#L115).


```{note}

Because all data passing between plugins are sent through one or more 
{py:obj}`Mediator<pntos.api.Mediator>` objects, 
the {py:obj}`Mediator<pntos.api.Mediator>` is where all concurrency and
synchronization are decided. In the single threaded case, the Mediator implementation
can be relatively simple, but in the more advanced cases such as multi-processed
or distributed, they can become quite complicated. For example, in a multithreaded implementation
where each plugin is in a separate thread but share a single 
{py:obj}`Mediator<pntos.api.Mediator>`, the {py:obj}`Controller
Plugin<pntos.api.ControllerPlugin>` might implement the single
{py:obj}`Mediator<pntos.api.Mediator>` by creating and storing internally a set of mutex
locks, one per thread, and then locking each call to a
{py:obj}`Mediator<pntos.api.Mediator>` function using a mutex. The
{py:obj}`Mediator<pntos.api.Mediator>` function calls would then consist of locking
logic followed by routing calls from one plugin to another. In order to prevent global
locks (and therefore performance bottlenecks), a fine-grained locking strategy per-resource
and per-{py:obj}`Mediator<pntos.api.Mediator>` is likely desired, which will require
additional complexity.

In another example, 
suppose instead we were writing a multiprocessed controller. In this
case, the controller might ``fork()`` to put plugins into their own processes, and then
write a {py:obj}`Mediator<pntos.api.Mediator>` that opens IPC communication primitives
(such as ``/dev/shm`` or sockets) in order to route the data from the {py:obj}`Transport
Plugin<pntos.api.TransportPlugin>` to the {py:obj}`Orchestration
Plugin<pntos.api.OrchestrationPlugin>`, which are now in different processes. Thus the
{py:obj}`Mediator<pntos.api.Mediator>` that is constructed by the {py:obj}`Controller
Plugin<pntos.api.ControllerPlugin>` is tied closely to the concurrency model chosen by
the {py:obj}`Controller Plugin<pntos.api.ControllerPlugin>`.

Thus, the {py:obj}`Controller Plugin<pntos.api.ControllerPlugin>` is fundamentally the
plugin that defines the concurrency model that is used by Python pntOS, because it's
implementation of the {py:obj}`Mediator<pntos.api.Mediator>` defines how plugins interact
with each other and whether concurrency is used in those interactions. Conceptually,
the {py:obj}`Controller Plugin<pntos.api.ControllerPlugin>` is the unit of modularity
that defines concurrency, because it implements the {py:obj}`Mediator<pntos.api.Mediator>`.
```

### Orchestration

TODO: the tour goes into here, rework the below.

The {py:obj}`Orchestration Plugin<pntos.api.OrchestrationPlugin>` contains the core
navigation data fusion and filtering functionality. It is responsible for calculating a
navigation solution from the incoming sensor data. It performs this task by calling out
to various plugins which define the actual sensor fusion algorithm, state space, and
sensor error models. Thus its primary duties are to orchestrate the flow of data
into/out of filters, and picking the set of navigation-related plugins which are used to
model errors and generate estimates.

For more information about {term}`Cobra` implementation of the {py:obj}`Orchestration
Plugin<pntos.api.OrchestrationPlugin>`, see [](./plugins/orchestration_plugin.md).

### End of the Tour

TODO: Redirect people to the sample app, or to the advanced topics below (level 2 integration)

## Next Steps

| Link                    | Description                                                                                                     |
| ----------------------- | --------------------------------------------------------------------------------------------------------------- |
| [](./plugins.md)        | Explore the {term}`Python pntOS API` plugins in greater detail, as well as their {term}`Cobra` implementations. |
| [](./installation.md)   | Installation instructions for getting started with {term}`Cobra`.                                               |
| [](./first_app.md)      | Instructions for running your first {term}`Cobra` tutorial {term}`App`.                                         |
| {ref}`tutorial-apps`    | Explore the {term}`Cobra` tutorial apps.                                                                        |
| {ref}`pntos_python_api` | Explore the {term}`Python pntOS API` documentation.                                                             |
| [](./cobra.md)          | Explore the {term}`Cobra` documentation.                                                                        |