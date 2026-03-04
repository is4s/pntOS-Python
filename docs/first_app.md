# Running Your First App

In the `{workspace-root}/apps` directory, there are several off-the-shelf {term}`apps
<App>` of increasing complexity assembled from off-the-shelf {term}`Cobra` plugins that
serve to demonstrate {term}`pntOS-Python` and the development process for you to
build your own {term}`apps <App>`. This page serves as an introduction to running an
arbitrary {term}`Cobra` {term}`app <App>`. For more details on any particular app, refer
to the corresponding page in the {ref}`tutorial-apps` section of the docs.

## Running an App

A Python app consists of a Python script containing all plugin imports, config, and code
needed to start a particular instance of Python pntOS. The {term}`Cobra` plugin set
contains a [Transport plugin](./plugins/transport_plugin.md) that retrieves
{term}`ASPN` messages from an
[LCM](https://github.com/lcm-proj/lcm)
relay. This allows pntOS to ingest data either from sensors sending ASPN measurements
live, or (in the case of the tutorial apps) from an LCM log file replaying data over
the relay.

These instructions will walk you through starting a generic app, spinning up the LCM
relay, and playing back a log file to feed data into pntOS.

### Activate Virtual Environment

These instructions assume an active virtual environment as outlined in the
[](./installation.md). If you currently have that virtual environment activated, skip to
[](#select-and-run-an-app).

If you have not yet created a Python virtual environment for the [`pntos-python`
repository](https://git.aspn.us/pntos/pntos-python), follow the instructions in [](./installation.md) then go
to [](#select-and-run-an-app).

If you have created the virtual environment but it is not currently activated, run the below command
from the root directory to enter the virtual environment. The command varies depending on your shell:

`````{tab-set}
````{tab-item} **bash/zsh**
```
source .venv/bin/activate
```
````
````{tab-item} **fish**
```
source .venv/bin/activate.fish
```
````
`````

### Select and Run an App

The available apps can be found in each subfolder of the `{workspace-root}/apps`
directory. If this is your first time with {term}`pntOS-Python`, it is recommended you
start with the `gps_ins` app. If you are running your own custom app, just switch out
the paths to the off-the-shelf apps with the path to your app in the following
instructions.

The available off-the-shelf apps are in the
{ref}`tutorial-apps` section of these docs.

`````{tab-set}

````{tab-item} GPS INS Tutorial App
:sync: gps-ins-tutorial
For documentation specifically explaining this app, see
[](./apps/gps_ins.md).

### Run the GPS INS Tutorial App

To run this app, run this command from the root workspace directory (with the Python virtual
environment activated):

```shell
apps/tutorial/gps_ins.py
```

Once the app is started, it will immediately start processing messages from the input log, 
with a progress bar tracking the percentage of messages that have been processed.
Once the entire input log has been processed, you should see something like the following:

```text
[17/02/2026 14:47:19] [LoggingPlugin] [INFO] using hard-coded global logging level INFO
[17/02/2026 14:47:19] [OrchestrationPlugin] [INFO] Aligned filter at 1747680879.539799929s
[17/02/2026 14:47:19] [TransportPlugin] [INFO] LCM log reader is running.
[17/02/2026 14:47:19] [ControllerPlugin] [INFO] Press Ctrl + C at any time to shut down pntOS...
[18/02/2026 15:10:01] [TransportPlugin] [INFO] Found new channel /sensor/vn-100/imu      with a timestamp of 1747680879.539799690s
[18/02/2026 15:10:01] [TransportPlugin] [INFO] Found new channel /sensor/ins-d/pva       with a timestamp of 1747680879.543048859s
[18/02/2026 15:10:01] [TransportPlugin] [INFO] Found new channel /sensor/simulated/velocity      with a timestamp of 1747680879.543048859s
[18/02/2026 15:10:01] [TransportPlugin] [INFO] Found new channel /sensor/ublox-ZED-F9T/position  with a timestamp of 1747680880.300589800s
[18/02/2026 15:10:01] [TransportPlugin] [INFO] Found new channel /sensor/ublox-ZED-F9T/velocity  with a timestamp of 1747680880.300589800s
[18/02/2026 15:10:01] [TransportPlugin] [INFO] Found new channel /sensor/ublox-ZED-F9T/pva       with a timestamp of 1747680880.300589800s
[18/02/2026 15:10:01] [TransportPlugin] [INFO] Found new channel /sensor/bmp388/baro_pressure    with a timestamp of 1747680880.328312635s
100%|██████████████████████████████████████████████████████████████████████████████████████████████| 472M/472M [00:37<00:00, 12.7MB/s]
[18/02/2026 15:10:38] [TransportPlugin] [INFO] Done processing LCM log. Press Ctrl + C to shut down pntOS.
```


For tutorial apps, a UI plugin for LCM log plotting is initiated on shutdown. Pressing `Ctrl + C` after running the tutorial app will start the shutdown process and display something like the following:

```text
[17/02/2026 14:51:41] [ControllerPlugin] [INFO] Keyboard Interrupt Detected.
[17/02/2026 14:51:41] [ControllerPlugin] [INFO] Shutting down all plugins...
[17/02/2026 14:51:41] [TransportPlugin] [INFO] Shutdown plugin for Cobra LCM Log Transport Plugin.
Reading measurements from log...
100%|█████████████████████████████████████████████████████████████████████████████████████████████████| 475M/475M [00:13<00:00, 34.0MB/s]
[17/02/2026 14:51:57] [UiPlugin] [INFO] Plotting results. Close all windows to continue shutdown.
[17/02/2026 14:52:10] [UiPlugin] [INFO] Plots saved to pntos_output.
```

The results from the tutorial app will be displayed in separate windows. To continue with the shutdown, simply close all the plotting windows.

```{note}
The UI plotting plugin is only used in tutorial apps. 

However, most apps record the pntOS solution to `pntos_output.log` by default for plotting or further processing.
For information on how to plot the pntOS solution from a log file, see [](#view-results-from-a-log-file).
```
````

````{tab-item} GPS INS Velocity Tutorial App
:sync: vel-app
For documentation specifically explaining this app, see
[](./apps/gps_vel_ins.md).

### Run the Position and Velocity Update App

To run this app, run this command from the root workspace directory (with the Python virtual
environment activated):

```shell
apps/tutorial/gps_vel_ins.py
```

Once the app is started, it will immediately start processing messages from the input log, 
with a progress bar tracking the percentage of messages that have been processed.
Once the entire input log has been processed, you should see something like the following:

```text
[17/02/2026 14:47:19] [LoggingPlugin] [INFO] using hard-coded global logging level INFO
[17/02/2026 14:47:19] [OrchestrationPlugin] [INFO] Aligned filter at 1747680879.539799929s
[17/02/2026 14:47:19] [TransportPlugin] [INFO] LCM log reader is running.
[17/02/2026 14:47:19] [ControllerPlugin] [INFO] Press Ctrl + C at any time to shut down pntOS...
[18/02/2026 15:10:01] [TransportPlugin] [INFO] Found new channel /sensor/vn-100/imu      with a timestamp of 1747680879.539799690s
[18/02/2026 15:10:01] [TransportPlugin] [INFO] Found new channel /sensor/ins-d/pva       with a timestamp of 1747680879.543048859s
[18/02/2026 15:10:01] [TransportPlugin] [INFO] Found new channel /sensor/simulated/velocity      with a timestamp of 1747680879.543048859s
[18/02/2026 15:10:01] [TransportPlugin] [INFO] Found new channel /sensor/ublox-ZED-F9T/position  with a timestamp of 1747680880.300589800s
[18/02/2026 15:10:01] [TransportPlugin] [INFO] Found new channel /sensor/ublox-ZED-F9T/velocity  with a timestamp of 1747680880.300589800s
[18/02/2026 15:10:01] [TransportPlugin] [INFO] Found new channel /sensor/ublox-ZED-F9T/pva       with a timestamp of 1747680880.300589800s
[18/02/2026 15:10:01] [TransportPlugin] [INFO] Found new channel /sensor/bmp388/baro_pressure    with a timestamp of 1747680880.328312635s
100%|██████████████████████████████████████████████████████████████████████████████████████████████| 472M/472M [00:37<00:00, 12.7MB/s]
[18/02/2026 15:10:38] [TransportPlugin] [INFO] Done processing LCM log. Press Ctrl + C to shut down pntOS.
```

For tutorial apps, a UI plugin for LCM log plotting is initiated on shutdown. Pressing `Ctrl + C` after running the tutorial app will start the shutdown process and display something like the following:

```text
[17/02/2026 14:51:41] [ControllerPlugin] [INFO] Keyboard Interrupt Detected.
[17/02/2026 14:51:41] [ControllerPlugin] [INFO] Shutting down all plugins...
[17/02/2026 14:51:41] [TransportPlugin] [INFO] Shutdown plugin for Cobra LCM Log Transport Plugin.
Reading measurements from log...
100%|█████████████████████████████████████████████████████████████████████████████████████████████████| 475M/475M [00:13<00:00, 34.0MB/s]
[17/02/2026 14:51:57] [UiPlugin] [INFO] Plotting results. Close all windows to continue shutdown.
[17/02/2026 14:52:10] [UiPlugin] [INFO] Plots saved to pntos_output.
```

The results from the tutorial app will be displayed in separate windows. To continue with the shutdown, simply close all the plotting windows.

```{note}
The UI plotting plugin is only used in tutorial apps. 

However, most apps record the pntOS solution to `pntos_output.log` by default for plotting or further processing.
For information on how to plot the pntOS solution from a log file, see [](#view-results-from-a-log-file).
```
````

````{tab-item} GPS INS Standard App
:sync: gps-ins-standard
For documentation specifically explaining this app, see
[](./apps/gps_ins_standard.md).

### Run the GPS INS Standard App

To run this app, run this command from the root workspace directory (with the Python virtual
environment activated):

```shell
apps/standard/gps_ins.py
```

Once the app is started, it will immediately start processing messages from the input log, 
with a progress bar tracking the percentage of messages that have been processed.
Once the entire input log has been processed, you should see something like the following:

```text
[18/02/2026 15:47:50] [LoggingPlugin] [INFO] using hard-coded global logging level INFO
[18/02/2026 15:47:50] [TransportPlugin] [INFO] LCM log reader is running.
[18/02/2026 15:47:50] [ControllerPlugin] [INFO] Press Ctrl + C at any time to shut down pntOS...
[18/02/2026 15:47:50] [TransportPlugin] [INFO] Found new channel /sensor/vn-100/imu with a timestamp of 1747680879.539799690s
[18/02/2026 15:47:50] [TransportPlugin] [INFO] Found new channel /sensor/ublox-ZED-F9T/position  with a timestamp of 1747680880.300589800s
[18/02/2026 15:47:50] [OrchestrationPlugin] [INFO] Aligned filter at 1747680889.549539804s
100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████▉| 472M/472M [00:26<00:00, 18.0MB/s]
[18/02/2026 15:48:16] [TransportPlugin] [INFO] Done processing LCM log. Press Ctrl + C to shut down pntOS.
```

The pntOS solution will be recorded to `pntos_output.log` and you can press `Ctrl + C` to shut down pntOS.
For information on how to plot the pntOS solution from a log file, see [](#view-results-from-a-log-file).
````

````{tab-item} LCM Relay App
:sync: lcm-relay

The LCM Relay App is similar to the GPS INS Standard App, but uses a different transport plugin that requires
the user to separately spin up an LCM relay, and manually record the output log file. The purpose of this
app is to support real-time use cases where pntOS may ingest sensor data over the network, and broadcast a live solution.

To run this app, follow the steps below:

```{warning}
The following commands each require separate terminals. Be sure to activate the virtual environment for each
terminal as described in [](#activate-virtual-environment) before running these commands.
```

### Start a Local TCP Server

In order to feed messages into the transport plugin from an LCM log file, we need to first start
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

- /sensor/bmp388/baro_pressure
- /sensor/ins-d/pva
- /sensor/simulated/velocity
- /sensor/ublox-ZED-F9T/position
- /sensor/ublox-ZED-F9T/pva
- /sensor/ublox-ZED-F9T/velocity
- /sensor/vn-100/imu

### Record Output

If you wish to record the pntOS solutions that are published by the LCM transport plugin, start the lcm-logger:

```{warning}
You must delete or rename any existing `pntos_output.log` files before running this command.
```

```shell
lcm-logger --lcm-url=tcpq:// pntos_output.log
```

This process will listen to any messages transmitted over LCM and record them to `pntos_output.log`.

Alternatively, to just see the solution printed to the terminal, set the logging level
to `DEBUG` when initializing the {py:obj}`pntos.cobra.StandardLoggingPlugin`.

### Run the LCM Relay App
Finally, to start the LCM Relay App run the following command in a new terminal:

```shell
apps/standard/lcm_relay.py
```

This will spin up pntOS and it is ready to start processing messages. To produce solutions, simply
push the `play` button in the LogPlayer to start the datastream. You should see something similar to the following:

```text
[20/02/2026 12:14:00] [LoggingPlugin] [INFO] using hard-coded global logging level INFO
LCM tcpq: connecting...
[20/02/2026 12:14:00] [TransportPlugin] [INFO] LCM message handler is running.
[20/02/2026 12:14:00] [ControllerPlugin] [INFO] Press Ctrl + C at any time to shut down pntOS...
[20/02/2026 12:14:03] [TransportPlugin] [INFO] Found new channel /sensor/ins-d/pva	 with a timestamp of 1747680882.938483715s
[20/02/2026 12:14:03] [TransportPlugin] [INFO] Found new channel /sensor/vn-100/imu	 with a timestamp of 1747680882.940131664s
[20/02/2026 12:14:03] [TransportPlugin] [INFO] Found new channel /sensor/ublox-ZED-F9T/position	 with a timestamp of 1747680883.294163942s
[20/02/2026 12:14:03] [TransportPlugin] [INFO] Found new channel /sensor/ublox-ZED-F9T/velocity	 with a timestamp of 1747680883.294163942s
[20/02/2026 12:14:03] [TransportPlugin] [INFO] Found new channel /sensor/ublox-ZED-F9T/pva	 with a timestamp of 1747680883.294163942s
[20/02/2026 12:14:04] [TransportPlugin] [INFO] Found new channel /sensor/simulated/velocity	 with a timestamp of 1747680883.543442726s
[20/02/2026 12:14:06] [TransportPlugin] [INFO] Found new channel /sensor/bmp388/baro_pressure	 with a timestamp of 1747680885.336656809s
[20/02/2026 12:14:13] [OrchestrationPlugin] [INFO] Aligned filter at 1747680892.949498653s
```

Unlike the other apps, there will be no progess bar displayed in the console. The LogPlayer will have a progress bar where you can track the progress
of the log file. Once it is done processing, you may press `Ctrl + C` to shutdown pntOS.

```{note}
You may click the `>>` button in the LogPlayer GUI to speed up the playback. However, if the data is played
too fast, pntOS may not be able to provide solutions at the requested rate. In this case, you will want
to wait for pntOS to process all messages before shutting down. To know when pntOS is done processing
data, you can observe the terminal output where the `lcm-logger` command was run (see [](#record-output)),
which will print summary statements at 1 second intervals until no more traffic is observed on the network
bus.
```
````

````{tab-item} All Other Apps
:sync: all-other-apps

pntOS includes several other off-the-shelf apps that are not mentioned on this page.
Each app is categorized as a `dummy`, `tutorial`, `standard`, or `advanced` app where each
type showcases certain capabilities and features of pntOS from low to high complexity.

Any other apps not mentioned here may be run with the following command:

```shell
apps/{app-type}/{app-name}.py
```

Where you would replace `{app-type}` with the app's designated type, and replace `{app-name}` with the name
of the Python script of the actual app. This is essentially just a path to the executable Python file.
````
`````

### View Results from a Log File

To view the plots of the results from a log file run:

```shell
postprocessing/plot_results.py pntos_output.log
```

This should display the pntOS results in individual windows and save the plots
to the `{workspace-root}/pntos_output` directory.

