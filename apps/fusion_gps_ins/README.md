# Fusion GPS INS App Tutorial
## Overview
This app is meant to be a simple demonstration of a sensor fusion between two
sensors. In this case, it is the fusion between GPS and INS readings.

## Running the App

### Open Local TCP Server
In order to feed messages into the transport from an lcm log file, we need to first open
a local TCP server in a new terminal:
```sh
java -classpath $VIRTUAL_ENV/lib/python3.*/site-packages/share/java/lcm.jar lcm.lcm.TCPService
```

### Load LCM Log File
Then we can open the log file with `lcm-logplayer-gui` in another terminal:
```sh
lcm-logplayer-gui --paused --lcm-url=tcpq:// .venv/lib/python3.11/site-packages/pntos_python_datasets/2025_03_05_12_04_log_1.log
```
This should open a gui with a play button. Select only the following channels:
- `/sensor/ins-d/pva`
- `/sensor/ublox/position`
- `/sensor/vn-100/imu`

### Run the App
To run the app, run this command inside the python virtual environment from the root
workspace directory:
```sh
python apps/fusion_gps_ins/fusion_gps_ins.py 
```
You should see something like the following:
```sh
WARNING:  [Controller] Expected one UiPlugin but received 0. Running without a UI plugin.
[20/03/2025 17:04:19] [LoggingPlugin] [INFO] using hard-coded global logging level INFO
LCM tcpq: connecting...
[20/03/2025 17:04:19] [TransportPlugin] [INFO] LCM tcpq connected.
[20/03/2025 17:04:19] [TransportPlugin] [INFO] Subscribed to all available channels.
[20/03/2025 17:04:19] [TransportPlugin] [INFO] LCM message handler is running.
[20/03/2025 17:04:19] [ControllerPlugin] [INFO] Press Ctrl + C at any time to shut down pntOS...
```
Then push the `play` button on the lcm log-player gui.

### Validate Results
You should see periodic printouts of an info message (shown below) followed by a
printout of the current PVA solution message.
```sh
[20/03/2025 17:04:27] [TransportPlugin] [INFO] Got a solution! <printout of pva message>
```
NOTE: This should change once we have a UI plugin.
