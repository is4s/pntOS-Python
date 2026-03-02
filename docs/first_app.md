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
[](#select-an-app).

If you have not yet created a Python virtual environment for the [`pntos-python`
repository](https://git.aspn.us/pntos/pntos-python), follow the instructions in [](./installation.md) then go
to [](#select-an-app).

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

### Select an App

The available apps can be found in each subfolder of the `{workspace-root}/apps`
directory. If this is your first time with {term}`pntOS-Python`, it is recommended you
start with the `gps_ins` app. If you are running your own custom app, just switch out
the paths to the off-the-shelf apps with the path to your app in the following
instructions.

The available off-the-shelf apps are in the
{ref}`tutorial-apps` section of these docs.

`````{tab-set}

````{tab-item} GPS INS App
:sync: gps-ins-tutorial
For documentation specifically explaining the `gps_ins` app, see
[](./apps/gps_ins.md).

### Run the GPS INS Tutorial App

To run this app, run this command from the root workspace directory (with the Python virtual
environment activated):

```shell
apps/tutorial/gps_ins.py
```
````

````{tab-item} GPS INS Velocity App
:sync: vel-app
For documentation specifically explaining the this app, see
[](./apps/gps_vel_ins.md).

### Position and Velocity Update App

To run this app, run this command from the root workspace directory (with the Python virtual
environment activated):

```shell
apps/tutorial/gps_vel_ins.py
```
````

````{tab-item} GPS INS Standard App
:sync: gps-ins-standard

### Run the GPS INS Standard App

To run this app, run this command from the root workspace directory (with the Python virtual
environment activated):

```shell
apps/standard/gps_ins.py
```
````
`````

Once the app is started, you should see something like the following:

```shell
WARNING:  [Controller] Expected one UiPlugin but received 0. Running without a UI plugin.
[31/03/2025 11:55:06] [LoggingPlugin] [INFO] using hard-coded global logging level INFO
[31/03/2025 11:55:06] [OrchestrationPlugin] [INFO] Aligned filter at TypeTimestamp(elapsed_nsec=1743621678330456320).
LCM tcpq: connecting...
[31/03/2025 11:55:06] [TransportPlugin] [INFO] LCM message handler is running.
[31/03/2025 11:55:06] [ControllerPlugin] [INFO] Press Ctrl + C at any time to shut down pntOS...
```

The app will immediately start processing messages from the input log, with a progress bar tracking the percentage of messages that have been processed.

### View Results

The app records the filter PVA solution to `pntos_output.log`. To plot the recorded results, run:

```shell
postprocessing/plot_results.py pntos_output.log
```

These plots should look fairly similar to the first app's plots, since the position update will be
the dominating update. To be able to see a bigger difference, try inducing a position measurement
outage to see the velocity update constrain the solution's drift.
