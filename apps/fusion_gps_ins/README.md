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

You should see periodic printouts of an info message (shown below) followed by a
printout of the current PVA solution message.

```shell
[20/03/2025 17:04:27] [TransportPlugin] [INFO] Got a solution! <printout of PVA message>
```

NOTE: This should change once we have a UI plugin.
