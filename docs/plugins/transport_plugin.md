# Transport Plugin

The {py:obj}`Transport Plugin<pntos.api.TransportPlugin>` is responsible for transport of messages
to and from an implementation of pntOS. This plugin receives messages from various sources outside
of pntOS and sends messages back out as needed. Most incoming messages will come from sensors
or [Smartcables](https://git.aspn.us/aspn/smartcables/), the primary output message will be a fused
solution obtained by processing the input messages.

In addition to handling the transport of messages themselves, this plugin is responsible for
converting messages to/from ASPN as needed. Internally, pntOS processes ASPN messages, so all
incoming messages need to be converted to ASPN before they can be processed. If incoming messages
are already in an ASPN format, then the data only needs to be marshalled into the proper ASPN Python
class.

For more information about ASPN, see [](../faq.md#aspn-faq).

## Transport Plugin API

In addition to the methods required of all plugins, a transport plugin must implement the following methods:

1. {py:obj}`start_listening()<pntos.api.TransportPlugin.start_listening>` - This will be called by
the {py:obj}`ControllerPlugin<pntos.api.ControllerPlugin>` when it is ready to start processing
messages.
1. {py:obj}`stop_listening()<pntos.api.TransportPlugin.stop_listening>` - Similarly, this can be
called when the controller plugin is done processing messages, or wants to temporarily stop
ingesting data.
1. {py:obj}`broadcast_message()<pntos.api.TransportPlugin.broadcast_message>` - This will be called
by the {py:obj}`Mediator<pntos.api.Mediator>` to output a message. Note that any plugin can publish
a message by calling
{py:obj}`mediator.broadcast_aspn_message<pntos.api.Mediator.broadcast_aspn_message>`, and it is the
mediator's job to route this message out through the desired transport(s).

When a transport plugin receives an incoming message, after converting it into the desired ASPN
message type, it should pass that message to the mediator to be processed by calling
{py:obj}`mediator.process_pntos_message<pntos.api.Mediator.process_pntos_message>`.

```{note}
There is no `process_message` method in the transport plugin API, as the way each plugin handles incoming messages is up to the implementer. In most cases, this involves spinning up a thread that listens for incoming messages, forwarding them on to the mediator as they arrive.
```

## Transport Plugin Implementations

Cobra offers a few off-the-shelf transport plugin implementations, each specific to a particular
transport method.

```{note}
If your desired transport protocol is not supported by these plugins, they may
still be helpful as a reference for implementing your own.
```

`````{tab-set}

````{tab-item} LCM Log Transport Plugin

The {py:obj}`LcmLogTransportPlugin<pntos.cobra.LcmLogTransportPlugin>` utilizes the [Lightweight
Communications and Marshalling (LCM)](https://lcm-proj.github.io/lcm/) protocol, reading ASPN messages from one LCM log and writing messages to another.

This plugin is primarily useful for obtaining fast, postprocessed solutions, as it will run through
all the messages in the input log as quick as possible. It is capable of ingesting
ASPN23 messages from an LCM log.

To use this plugin in your app, you just have to ensure that this plugin is included in your list of
plugins to run, and that it's been configured by setting the
{py:obj}`LcmLogTransportConfig<pntos.cobra.config.LcmLogTransportConfig>`.

See [](../apps/pos_ins.md) for a walkthrough of an app that uses this plugin.
````


````{tab-item} LCM Network Transport Plugin

Like the LCM log-based transport plugin, the
{py:obj}`LcmTransportPlugin<pntos.cobra.LcmTransportPlugin>` uses LCM to decode ASPN2 and ASPN23
input messages and to output messages in either version. However, instead of reading from and
writing to a log, this plugin listens and publishes messages over the network, via either TCP or
UDP.

This plugin is primarily useful for real-time scenarios, where pntOS is listening to and processing
data from various sensors to produce a live solution.

To use this plugin in your app, you need to do the following:

1. Ensure that this plugin is included in your list of plugins to run
2. Ensure that the plugin configuration is set by filling out the
{py:obj}`LcmTransportConfig<pntos.cobra.config.LcmTransportConfig>`.
3. Before starting the app, spin up a network relay.
4. If desired, before starting the app, spin up an LCM logger so that input and output messages can
be recorded.
5. After starting the app, start streaming data over the network by playing messages from a log file
or broadcasting from one or more sensor drivers or smartcables.

See [Running Your First App](../first_app.md#select-and-run-an-app) for specific instructions on
how to run an example app that uses this plugin.
````


````{tab-item} ROS Transport Plugin

```{note}
Currently, this transport only works with ROS2 Humble or Jazzy.
```

The `Aspn23RosTransportPlugin` sends and receives ASPN23 messages over the network using the Robot
Operating System (ROS) protocol.

See [](../apps/advanced/pos_ins_ros.md) for a walkthrough of an app that uses this plugin.
````

`````
