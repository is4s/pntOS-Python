# Running Your First App

In the `{workspace-root}/apps` directory, there are several off-the-shelf {term}`apps
<App>` of increasing complexity assembled from off-the-shelf {term}`Cobra` plugins that
serve to demonstrate the {term}`Python pntOS API` and the development process for you to
build your own {term}`apps <App>`. This page serves as an introduction to running an
arbitrary {term}`Cobra` {term}`app <App>`. For more details on any particular app, refer
to the corresponding page in the {ref}`tutorial-apps` section of the docs.

## Running an App

A python app consists of a python script containing all plugin imports, config, and code
needed to start a particular instance of Python pntOS. The {term}`Cobra` plugin set
currently contains a [Transport plugin](./plugins/transport_plugin.md) that retrieves
{term}`ASPN` messages from an
[LCM](https://github.com/lcm-proj/lcm)
relay. This allows pntOS to ingest data either from sensors sending ASPN measurements
live, or - in the case of the tutorial apps - from an LCM log file replaying data over
the relay.

These instructions will walk you through starting a generic app, spinning up the LCM
relay, and playing back a log file to feed data into pntOS.

### Activate Virtual Environment

These instructions assume an active virtual environment as outlined in the
[](./installation.md). If you currently have that virtual environment activated, skip to
[](#start-a-local-tcp-server).

If you have not yet created a python virtual environment for the [`pntos-python`
repository](https://git.aspn.us/pntos/pntos-python), follow the instructions in [](./installation.md) then go
to [](#start-a-local-tcp-server).

If you have created the virtual environment but it is not currently activated, run this
command from the root directory to enter into the virtual environment:

```shell
source .venv/bin/activate
```

### Start a Local TCP Server

In order to feed messages into the transport from an LCM log file, we need to first start
a local TCP server (located in the virtual environment) in a new terminal:

```shell
java -classpath $VIRTUAL_ENV/lib/python3.*/site-packages/share/java/lcm.jar lcm.lcm.TCPService
```

### Play LCM Log File

The `pntos-python-datasets` package installs a script to find the installed data and start playing
it back:

```shell
play-dataset
```

```{note}
If you would like to see what the above command is doing or would like to know where the dataset
exists on the disk, you can run the command with a `-v` verbose flag:

    play-dataset -v

Running the above will print out the exact command the script executes before executing it.
```

This should open the LCM LogPlayer GUI with a play button. You should see the following channels:

- `/sensor/ins-d/pva`
- `/sensor/ublox-ZED-F9T/position`
- `/sensor/ublox-ZED-F9T/velocity`
- `/sensor/vn-100/imu`

## Record Output

In order to save off the solutions produced by pntOS and sent over the wire, start lcm-logger:

```shell
lcm-logger --lcm-url=tcpq:// pntos_output.log
```

This process will listen to any messages transmitted over LCM and record them to `pntos_output.log`.

Alternatively, to just see the solution printed to the terminal, set the logging level
to `DEBUG` when initializing the {py:obj}`pntos.cobra.SimpleLoggingPlugin`.

### Select an App

The available apps can be found in each subfolder of the `{workspace-root}/apps`
directory. If this is your first time with the {term}`Python pntOS API`, it is recommending you
start with the `fusion_gps_ins` app. If you are running your own custom app, just switch
out the paths to the off-the-shelf apps with the path to your app in the following instructions.

The available off-the-shelf apps are in the
{ref}`tutorial-apps` section of these docs.

`````{tab-set}

````{tab-item} GPS INS Fusion App
:sync: gps-ins-fusion
For documentation specifically explaining the `fusion_gps_ins` app, see
[](./apps/fusion_gps_ins.md).

### Run the GPS INS Fusion App

To run this app, run this command from the root workspace directory (with the python virtual
environment activated):

```shell
apps/fusion_gps_ins/fusion_gps_ins.py
```

You should see something like the following:

```shell
WARNING:  [Controller] Expected one UiPlugin but received 0. Running without a UI plugin.
[31/03/2025 11:55:06] [LoggingPlugin] [INFO] using hard-coded global logging level INFO
[31/03/2025 11:55:06] [OrchestrationPlugin] [INFO] Aligned filter at TypeTimestamp(elapsed_nsec=1743621678330456320).
LCM tcpq: connecting...
[31/03/2025 11:55:06] [TransportPlugin] [INFO] LCM message handler is running.
[31/03/2025 11:55:06] [ControllerPlugin] [INFO] Press Ctrl + C at any time to shut down pntOS...
```

Then push the `play` button in the LogPlayer.

```{note}
This app uses real data. There is some jitter present in the IMU sensor timestamps which will
produce a few warnings in the output. They are of the form:

    [warning] Suspicious dt of 0.015978679000000003 compared against nominal of 0.010000062688925596 detected at time 1747683329.241135205s

A more complex app might, for example, use a Preprocessor plugin to correct the incoming data.
```

### Validate Results

To plot the saved results run:

```shell
postprocessing/plot_results.py pntos_output.log
```

For more information on the expected results for this app, see [](./apps/fusion_gps_ins.md#expected-results).
````

````{tab-item} FOGM Bias App
:sync: fogm-bias-app
For documentation specifically explaining the `fogm_bias` app, see
[](./apps/fogm_bias.md).

### Run the FOGM Bias App

To run this app, run this command from the root workspace directory (with the python virtual
environment activated):

```shell
apps/fogm_bias/fogm_bias.py
```

You should see something like the following:

```shell
WARNING:  [Controller] Expected one UiPlugin but received 0. Running without a UI plugin.
[31/03/2025 11:55:06] [LoggingPlugin] [INFO] using hard-coded global logging level INFO
[31/03/2025 11:55:06] [OrchestrationPlugin] [INFO] Aligned filter at TypeTimestamp(elapsed_nsec=1743621678330456320).
LCM tcpq: connecting...
[31/03/2025 11:55:06] [TransportPlugin] [INFO] LCM message handler is running.
[31/03/2025 11:55:06] [ControllerPlugin] [INFO] Press Ctrl + C at any time to shut down pntOS...
```

Then push the `play` button in the LogPlayer.

```{note}
This app uses real data. There is some jitter present in the IMU sensor timestamps which will
produce a few warnings in the output. They are of the form:

    [warning] Suspicious dt of 0.015978679000000003 compared against nominal of 0.010000062688925596 detected at time 1747683329.241135205s

A more complex app might, for example, use a Preprocessor plugin to correct the incoming data.
```

### Validate Results

To plot the saved results run:

```shell
postprocessing/plot_results.py pntos_output.log
```

For more information on the expected results for this app, see [](./apps/fogm_bias.md#expected-results).
````

`````
