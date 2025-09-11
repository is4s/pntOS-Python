# Using ROS as a Transport

ROS2 Humble or Jazzy can be used as a transport mechanism instead of LCM.
Here's how to do that.

## Environment setup

### Getting ROS

Of course, you'll need ROS. If you don't already have it installed, see [Humble
Installation Guide](https://docs.ros.org/en/humble/Installation.html) or [Jazzy
Installation Guide](https://docs.ros.org/en/jazzy/Installation.html). Note
that, as of now, we only support ROS Humble (Ubuntu 22.04) and ROS Jazzy
(Ubuntu 24.04), the current LTS versions of ROS2.

### Getting ASPN-ROS

To use ROS, Cobra needs access to built ASPN-ROS packages generated in
Firehose. If running on Ubuntu 22.04 or Ubuntu 24.04 (which is likely if you
want to use ROS, since running ROS on other platforms is difficult!) with x86,
it may be easiest to use the ROS Ubuntu x86 development packages automatically
built in the Firehose CI. To do this, simply clone `firehose-outputs` and
source `firehose-outputs/ros_devel/<distro>/setup.<shell>`.

Otherwise, you'll need to build ASPN-ROS for your platform. If you're running
ROS in a Docker container, you may want to copy the result into it so you can
source it from within the container.

For more information on using the dev packages or manually building ASPN-ROS,
see [Firehose](https://git.aspn.us/pntos/firehose/-/tree/main).

### Specifying Python version

Note that your ROS version determines which Python version Cobra needs to use.
Cobra can support any version `>=3.10`. Before proceeding, please ensure that
your virtual environment's Python version is compatible with your ROS version.

:::{note}
For example, here's how to do it with `uv`.

For ROS Humble (Ubuntu 22.04):

```sh
uv sync --python 3.10
```

For ROS Jazzy (Ubuntu 24.04):

```sh
uv sync --python 3.12
```

Or create a `.python-version` file, and `uv` will use it.
:::

## Usage

### ROS App

See `apps/advanced/gps_ins_ros.py` for an example of using Cobra with ROS. This
app is very similar to `apps/tutorial/gps_ins.py`, but the
`AspnLcmTransportPlugin` has been swapped for an `Aspn23RosTransportPlugin`.
Also, the channel names have been changed to use underscores instead of dashes
since ROS topics cannot have dashes. Make sure the channels in your app reflect
the ROS topic names being published by your node or bagfile!

Now your node will subscribe to ROS2 topics.

### Where to get ROS data from

#### Smartcables with ROS

ROS data can be acquired live by running Smartcables with `-t ros` (see
[Smartcables](https://git.aspn.us/aspn/smartcables/) docs for instructions).

This can be recorded into a ROS bagfile with `ros2 bag record`.

#### Playing back bagfiles

:::{warning}
When replaying data from logfiles, it is often desirable to replay faster than
realtime. With ROS, this can be accomplished with the `-r` parameter (see
below). Obviously, there is a physical limit to how fast the data can be
replayed.

When the fastest-published channels reach this limit, `lcm-logplayer` is smart
enough to proportionally slow down the playback of all channels so that the
proportion of the rates is preserved. Unfortunately, `ros2 bag play` does not
do this, so as the rate is increased, slower topics will continue to speed up
even though faster ones cannot. Practically, this means that the data will be
received increasingly out-of-order (or even dropped), which tends to break
Cobra.

Thus, it is important to ensure that your chosen rate is slow
enough for the fastest topics to be published at full speed. This can be
confirmed with `ros2 topic hz`.
:::

Running `play-dataset -t ros` will play a ROS2 sqlite3 bagfile with the same
data as the LCM logfile used by `play-dataset`. Use `-r` to specify the
playback rate.

Existing LCM logfiles can be converted to ROS bagfiles using the
`convert_log_to_ros.py` script in the [`analysis-scripts`
repo](https://git.aspn.us/pntos/analysis-scripts/-/tree/main). This is how the
example bagfile used above was generated.

Whether converted from a LCM logfile or recorded from live ROS data, ROS
bagfiles can be replayed with `ros2 bag play`. Using `-p` will start in the
paused state; `-r` can specify a playback rate.

### Postprocessing

The `postprocessing/plot_results.py` script can generate plots from a LCM
logfile or a ROS bagfile. Use `-h` for more information.
