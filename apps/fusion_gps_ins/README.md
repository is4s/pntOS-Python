# Fusion GPS INS App Tutorial
## Overview

This app is meant to be a simple demonstration of a sensor fusion between two
sensors. In this case, it is the fusion between GPS position measurements and IMU readings.

## Running the App

### Open Local TCP Server

In order to feed messages into the transport from an LCM log file, we need to first open
a local TCP server in a new terminal:

```shell
java -classpath $VIRTUAL_ENV/lib/python3.*/site-packages/share/java/lcm.jar lcm.lcm.TCPService
```

### Play LCM Log File

Then we can play the log file in another terminal via:

```shell
play-dataset
```

This should open the LCM LogPlayer GUI with a play button. You should see the following channels:

- `/sensor/ins-d/pva`
- `/sensor/ublox/position`
- `/sensor/vn-100/imu`

## Record Output

In order to save off the solutions produced by pntOS and sent over the wire, start lcm-logger:

```shell
lcm-logger --lcm-url=tcpq:// pntos_output.log
```

This process will listen to any messages transmitted over LCM and record them to `pntos_output.log`.

Alternatively, to just see the solution printed to the terminal, set the logging level to `DEBUG`.

### Run the App

To run the app, run this command from the root workspace directory (with the python virtual
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

### Validate Results

To plot the saved results run:

```shell
postprocessing/plot_results.py pntos_output.log
```
