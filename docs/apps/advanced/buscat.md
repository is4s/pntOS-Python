# Buscat App

This app is very different from other apps. While pntOS is designed for sensor fusion, Buscat takes advantage of its modularity to convert and retransmit sensor data.

## Overview

This app reads in an LCM log containing ASPN2 measurements and outputs them as ASPN23 measurements.

To do this, we harness the {py:obj}`BuscatControllerPlugin<pntos.cobra.BuscatControllerPlugin>`,
which implements a {py:obj}`Mediator <pntos.api.Mediator>` that takes messages in various formats or
traveling via various transport protocols and funnels them out in a unified format through a common
[transport plugin](../../plugins/transport_plugin.md). This is useful for combining multiple streams
of data into one, or, in the case of this app, for converting between data models (e.g. ASPN
versions).

## App Walkthrough

Let's walk through the app piece by piece. You can find the app file at
[`pntos-python/apps/advanced/buscat.py`](https://git.aspn.us/pntos/pntos-python/-/blob/main/apps/advanced/buscat.py?ref_type=heads)
to follow along.

### Imports

The Buscat app uses much fewer imports compared to a sensor fusion app. Let's look at what it does use.

#### API Imports

Like the sensor fusion apps, this app only uses a single import from the API to initialize the global log level of the {py:obj}`StandardLoggingPlugin<pntos.cobra.StandardLoggingPlugin>`, the {py:obj}`LoggingLevel <pntos.api.LoggingLevel>` enum:

```{literalinclude} ../../../apps/advanced/buscat.py
:start-at: "from pntos.api import"
:end-at: "from pntos.api import"
:lineno-match:
```

Let's move to the plugin imports.

#### Cobra Plugin Imports

The Buscat app only imports the following {term}`Cobra` plugins:

```{literalinclude} ../../../apps/advanced/buscat.py
:start-at: "from pntos.cobra import ("
:end-at: ")"
:lineno-match:
```

Like before, we'll walk through what each of these plugins are doing
further along in [](#plugins-overview). Next up we have the config imports.

#### Cobra Config Imports

This example includes two config objects. The first is for the
{py:obj}`BuscatControllerPlugin<pntos.cobra.BuscatControllerPlugin>` itself, specifying which
transport plugin to designate as the output transport. In this case, we are only using a single
transport plugin (the {py:obj}`LcmLogTransportPlugin <pntos.cobra.LcmLogTransportPlugin>`), so we
designate that as the desired output transport. The second config object is for the
{py:obj}`LcmLogTransportPlugin <pntos.cobra.LcmLogTransportPlugin>`, specifying the input file to
read from, the output file to write to, and the ASPN version to use for the output messages (ASPN23).

```{literalinclude} ../../../apps/advanced/buscat.py
:start-at: "from pntos.cobra.config import ("
:end-at: "# End Config"
:lineno-match:
```

Now that we have our config set up in `my_config`, let's look at instantiating our plugins.

### Instantiate Plugins

The steps for instantiating plugins is the same as described in the [GPS INS
App](../gps_ins.md#instantiate-plugins); however, this time, we are instantiating the
{py:obj}`BuscatControllerPlugin<pntos.cobra.BuscatControllerPlugin>` and a shorter list of plugins.

#### 1. Instantiate Controller Plugin

We can instantiate our buscat controller plugin much like the standard controller plugin in the tutorial apps:

```{literalinclude} ../../../apps/advanced/buscat.py
:start-at: "controller = "
:end-before: "plugins = "
:lineno-match:
```

#### 2. Generate List of Plugins

```{literalinclude} ../../../apps/advanced/buscat.py
:start-at: "plugins = "
:end-at: "]"
:lineno-match:
```

It is important to ensure the {py:obj}`identifier<pntos.api.CommonPlugin>` for the output transport
plugin exists in the `output_transports` tuple input in the
{py:obj}`BuscatConfig<pntos.cobra.config.BuscatConfig>`.

That's all the configuration for the Buscat app. Now, let's look at a top-level overview of what each of the plugins in this app are contributing to the app.

## Plugins Overview

For each plugin in this app, let's explore briefly what it is and how it contributes to
this app:

| Cobra Plugin                                                                            | Contribution to App                                                                                                                                                                                                                                                                                                                                                                                                                                      | More Info                                |
| --------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------- |
| {py:obj}`BuscatControllerPlugin <pntos.cobra.BuscatControllerPlugin>`                   | Sets up communication between plugins by calling {py:obj}`init_plugin() <pntos.api.CommonPlugin.init_plugin>` with a {py:obj}`Mediator <pntos.api.Mediator>` for each plugin, then calls {py:obj}`start_listening()<pntos.api.TransportPlugin.start_listening>` on the [transport plugin](../../plugins/transport_plugin.md) to start moving {py:obj}`Messages <pntos.api.Message>` across the system from the input transport plugins to the output transport plugin.                                                                      | [](../../plugins/controller_plugin.md)      |
| {py:obj}`StandardLoggingPlugin <pntos.cobra.StandardLoggingPlugin>`                         | Prints {py:obj}`mediator.log_message() <pntos.api.Mediator.log_message>` calls from any other plugin to the terminal via the mediator.                                                                                                                                                                                                                                                                                                                                | [](../../plugins/logging_plugin.md)         |
| {py:obj}`StandardRegistryPlugin <pntos.cobra.StandardRegistryPlugin>`                       | A group-key-value store for data storage and communication between plugins within the app.                                                                                                                                                                                                                                                                                                                                                                               | [](../../plugins/registry_plugin.md)        |
| {py:obj}`LcmLogTransportPlugin <pntos.cobra.LcmLogTransportPlugin>`               | Reads {term}`ASPN` messages from an {term}`LCM` log file and feeds these {term}`ASPN` messages into the app as pntOS {py:obj}`Message <pntos.api.Message>`s. In this case, it also records the outputs of the app as {term}`ASPN` messages to an output log.                                                                                                                                                                                                                                                                                                              | [](../../plugins/transport_plugin.md)       |

## Expected Outputs

For all supported messages, the converted output will be recorded to the output log via the output transport plugin in a new channel with the same name as the input channel prefixed with `/buscat/pntos`. The table below includes a few examples of input and output channel names.

| Input Channel Name | Input ASPN2 Message Type | Output Channel Name | Output ASPN23 Message Type |
|--------------------|-------------------------|---------------------|--------------------------|
| /sensor/ins-d/pva | positionvelocityattitude | /buscat/pntos/sensor/ins-d/pva | measurement_position_velocity_attitude |
| /sensor/vn-100/imu | imu | /buscat/pntos/sensor/vn-100/imu | measurement_IMU |
| /sensor/ublox-ZED-F9T/position | geodeticposition3d | /buscat/pntos/sensor/ublox-ZED-F9T/position | measurement_position |

The {py:obj}`LcmLogTransportPlugin <pntos.cobra.LcmLogTransportPlugin>` automatically records all
input messages to the output file. Since the
{py:obj}`BuscatControllerPlugin<pntos.cobra.BuscatControllerPlugin>` routes all messages back
through this transport, then for every input channel in the log, there will also be a channel with
the prefix `/buscat/pntos`. To confirm this, run the following command:

```shell
print_channels pntos_output.log
```

You should see something like the output below, listing each channel from the original input log, as
well as a corresponding duplicate with the `/buscat/pntos` prefix. Note that the channels with this
prefix contain the converted ASPN23 measurements, while the original channels contain ASPN2
measurements.

```text
Channels in pntos_output.log:
	/buscat/pntos/sensor/ins-d/pva
	/buscat/pntos/sensor/ublox-ZED-F9T/position
	/buscat/pntos/sensor/vn-100/imu
	/sensor/ins-d/pva
	/sensor/ublox-ZED-F9T/position
	/sensor/vn-100/imu
```

You have now seen how we can use the
{py:obj}`BuscatControllerPlugin<pntos.cobra.BuscatControllerPlugin>` to convert a dataset from one
ASPN version to another!
