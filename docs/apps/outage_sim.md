# Outage Simulation App

The `standard/outage_sim.py` app demonstrates the capabilities of both Cobra and sensor fusion as a whole. It is a
derivation of `standard/pos_ins.py` that adds three key features:
- a simulated GPS position outage
- a barometer update
- a velocity update

This tutorial will iteratively walk through these features and the effects they have on the performance of Cobra.

## The Outage

Thanks to the handy {py:obj}`OutagePreprocessor<pntos.cobra.internal.OutagePreprocessor>` we are able to simulate an outage of 
any channel we choose. In this app we have chosen to deprive the filter of GPS position measurements for 600 seconds 
(seconds 1000 to 1600). Inducing this outage on the Standard POS INS App creates an IMU-only environment where the 
filter's error grows without any constraints. 

![](../images/outage_ne_traj.png)

Here is the Northing vs. Easting plot which visualizes the drift as it corresponds to a trajectory. On the right hand
side we represent time as a heat map and right around 1000 seconds we begin to see the drift between the Truth and
Cobra Solution.

![](../images/outage_NED_Pos_Error.png)

While the trajectory plot is great for visualization, it does not provide much information on what is going on behind
the scenes. The NED Position Error plot, however, gives us numerical insight into how the filter handled the GPS
position outage. One thing we quickly notice is that the down error grew significantly, something the trajectory did not reveal. 
IMUs are typically very sensitive to vertical position errors because even the smallest gyro misalignment can open the door for
gravity to cause quadratic error growth. 

In both plots, we can clearly see the outage has a significant, adverse effect on the accuracy of the Cobra solution.
So how can we improve our filter's response to an outage? Data - the answer to most problems. If we can provide our
filter with new sources of information about our current state, there is a good chance that we can limit the drift
subsequently improving our solution.

## The Barometer Update

The first sensor update we are bringing in is a barometer update via the BMP388. The data the sensor provides is a
pressure measurement, so we make use of the {py:obj}`BarometerToAltitudePreprocessor<pntos.cobra.internal.BarometerToAltitudePreprocessor>`
and convert these measurements to altitude before the {py:obj}`AltitudeMeasurementProcessor<pntos.cobra.internal.AltitudeMeasurementProcessor>`
receives them. If you would like to run the filter with the baro measurement yourself, enable the measurement in
the config by uncommenting the barometer channel.

```Diff
LcmLogTransportConfig(
    input_file=EXAMPLE_LCM_LOG,
    output_file=OUTPUT_LOG,
    output_version=AspnVersion.V23,
    group='config/lcm_log_transport',
    channels_to_process=(
        '/sensor/vn-100/imu',
        '/sensor/ublox-ZED-F9T/position',
-       # '/sensor/bmp388/baro_pressure',   # uncomment me to use a baro update
+       '/sensor/bmp388/baro_pressure',   # uncomment me to use a baro update
        # '/sensor/ublox-ZED-F9T/velocity', # uncomment me to use a velocity update
    ),
),
```

## Barometer Results

Rather than looking at the trajectory plot again, we will look at the velocity and position error plots for more context.
Let's take a look at the effects ingesting this new measurement has on the filter!

![](../images/outage_NED_Vel_Error_baro.png)

First up, velocity error. Here we can see our downward velocity error is well-bounded and its drift is constrained, but that
is not the case for our `North` and `East` error. The magnitude of our horizontal velocities suggest we are still experiencing
drift that our filter can't account for with an altitude update alone. While there are a couple routes that could improve
performance, let's take a look at the position error plot first.

![](../images/outage_NED_Pos_Error_baro.png)

The first thing that stands out is the massive improvement in downward error. Considering our `AltitudeMeasurementProcessor`
updates our vertical position directly, this is a clear indication that the filter is appropriately ingesting the barometer
update! But you may have noticed some changes in our `North` and `East` error. If we only updated our vertical position error,
why did we experience horizontal effects? This is largely because the filter's estimation of most states can change with both
direct and indirect updates due to the states' coupled relationships. But there is good news! A complicated problem doesn't
always mean a complicated solution! Let's move onto our next measurement update, velocity.

## The Velocity Update

In this section, we will explore the utility that a velocity update can provide in a GPS outage. In this example, we use
the {py:obj}`PinsonVelocityMeasurementProcessor<pntos.cobra.internal.PinsonVelocityMeasurementProcessor>` which directly
updates the Pinson15 NED velocity error states. We expect this update to directly bound the velocity error and due to
the relationship between position and velocity, we also expect to significantly slow the position error drift. Once again,
if you'd like to see the results for yourself, uncomment the velocity channel, run the filter, and plot the results!

```Diff
LcmLogTransportConfig(
    input_file=EXAMPLE_LCM_LOG,
    output_file=OUTPUT_LOG,
    output_version=AspnVersion.V23,
    group='config/lcm_log_transport',
    channels_to_process=(
        '/sensor/vn-100/imu',
        '/sensor/ublox-ZED-F9T/position',
        '/sensor/bmp388/baro_pressure',   # uncomment me to use a baro update
-       # '/sensor/ublox-ZED-F9T/velocity', # uncomment me to use a velocity update
+       '/sensor/ublox-ZED-F9T/velocity', # uncomment me to use a velocity update
    ),
),
```

```{image} ../images/outage_NED_Vel_Error_baro_vel.png
:width: 1000px
```

And voila! As we hoped, the velocity error has now been bound for the other two axes as well.

![](../images/outage_NED_Pos_Error_baro_vel.png)

Not only that, but the massive drift in horizontal position is now gone. Thanks to our barometer and velocity updates,
we have successfully constructed a filter that can handle a 600 second GPS outage!

```{note}
In this example and app, we incorporate a velocity measurement that originates from the Ublox GPS receiver. In a more
realistic scenario, these measurements would likely be lost as well; nonetheless, the underlying mechanics and
utility of adding a velocity update still apply. The update could easily come from a different sensor and provide
similar results, assuming the sensor is reliable and well-modeled. With that being said, these results are for example
purposes only and could vary if different sensors or data were used.
```