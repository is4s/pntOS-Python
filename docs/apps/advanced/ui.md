# Experimental UI App

This app demonstrates the in-progress
{py:obj}`ExperimentalCobraUiPlugin<pntos.cobra.ExperimentalCobraUiPlugin>` which
provides an experimental web GUI for the Cobra ecosystem.

## Installation-Specific Build Instructions

If installing Cobra via a wheel, skip to [](#run-the-app). Otherwise, this app requires building 
the front-end components locally. Running this app requires `nodejs` version `>=v24.16.0` to be 
installed. For installation instructions, see [Node's installation 
docs](https://nodejs.org/en/download). Once nodejs is installed, complete all [pntOS-Python 
installation](../../installation.md) instructions to set up the python environment. If
installing via git url, the build system should automatically build the front-end
components so skip to [](#run-the-app). Otherwise, if working from the
pntOS-Python repo, build the UI components via:

```sh
util/build_ui.sh
```

## Run the App

Run this command to set up the LCM relay:
```sh
java -classpath $VIRTUAL_ENV/lib/python3.*/site-packages/share/java/lcm.jar lcm.lcm.TCPService
```

Then, in a separate terminal (with the with the Python virtual environment activated), run the experimental UI app script with:

```sh
cobra_advanced_ui_app
```

The terminal output should look something like this:

```
$ cobra_advanced_ui_app
[29/05/2026 13:53:25] [LoggingPlugin] [INFO] using hard-coded global logging level INFO
[29/05/2026 13:53:25] [UiPlugin] [INFO] Web server starting on http://localhost:5001
LCM tcpq: connecting...
 * Serving Flask app 'pntos.cobra.advanced_plugins.ui.ExperimentalCobraUiPlugin'
 * Debug mode: off
LCM tcpq: connecting...
[29/05/2026 13:53:25] [TransportPlugin] [INFO] LCM message handler is running.
[29/05/2026 13:53:25] [ControllerPlugin] [INFO] Press Ctrl + C at any time to shut down pntOS...
```

Open the URL from the `UiPlugin` info message (<http://localhost:5001> above) in a
browser, which should display the purple and white Cobra web UI.

Hover over the circular icon on the top-left of the screen to open the widget side-panel
and view the available widgets. To play data in this app, select the Log Player widget,
upload a log file, then click the play button on the left hand side of the widget. The 
location of the example dataset can be found via the following command:

```sh
python -c "from pntos_python_datasets_lcm import EXAMPLE_LCM_LOG as e; print(e)"
```

The terminal output when the log is playing should look something like this:

```
[24/06/2026 11:38:41] [UtilityPlugin] [INFO] Loading file...
[24/06/2026 11:38:41] [UtilityPlugin] [INFO] Started logplayer thread
[24/06/2026 11:38:45] [UtilityPlugin] [INFO] Playing: True
[24/06/2026 11:38:45] [TransportPlugin] [INFO] Found new channel /sensor/vn-100/imu      with a timestamp of 1747680879.539799690s
[24/06/2026 11:38:45] [TransportPlugin] [INFO] Found new channel /sensor/ins-d/pva       with a timestamp of 1747680879.543048859s
[24/06/2026 11:38:45] [TransportPlugin] [INFO] Found new channel /sensor/simulated/velocity      with a timestamp of 1747680879.543048859s
[24/06/2026 11:38:45] [TransportPlugin] [INFO] Found new channel /sensor/simulated/directiontoknownfeature       with a timestamp of 1747680879.543048859s
[24/06/2026 11:38:46] [TransportPlugin] [INFO] Found new channel /sensor/ublox-ZED-F9T/position  with a timestamp of 1747680880.300589800s
[24/06/2026 11:38:46] [TransportPlugin] [INFO] Found new channel /sensor/ublox-ZED-F9T/velocity  with a timestamp of 1747680880.300589800s
[24/06/2026 11:38:46] [TransportPlugin] [INFO] Found new channel /sensor/ublox-ZED-F9T/pva       with a timestamp of 1747680880.300589800s
[24/06/2026 11:38:46] [TransportPlugin] [INFO] Found new channel /sensor/bmp388/baro_pressure    with a timestamp of 1747680880.328312635s
[24/06/2026 11:38:52] [OrchestrationPlugin] [INFO] Aligned filter at 1747680889.549539804s
```

To see a trace of various channels and solutions on a map, click the "Map View" tab. 

## Current Limitations

The {py:obj}`ExperimentalCobraUiPlugin<pntos.cobra.ExperimentalCobraUiPlugin>` is still
under development. This has the following implications:
1. The current widget set and features are quite minimal. More widgets and features will
   come soon in a future release.
2. The current implementation is very new. Any feedback or bug reports are welcome.
3. The UI architecture and websocket API is unstable and liable to change at any time.
   Build against it at your own risk.
4. As outlined in [](#installation-specific-build-instructions), there is a hard
   dependency on nodejs if trying to use the Cobra UI plugin not from a pre-built wheel.
   This dependency should be removed in a future release.
