# Example Data

One of the dependencies installed as part of the [Installation Guide](installation.md) is
`pntos-python-datasets`. This Python module contains:

- ASPN23-LCM data: `cobra_gps_ins_example_data.log`
- ASPN2-LCM data: `cobra_aspn2_example_data.log`
- ASPN23-ROS data: `cobra_gps_ins_example_data_0.db3`
- A script (`play_dataset`) which can be used to play back the above data, or return the path to the
  installed file

:::{tip}
The above datasets are provided for convenience, but pntOS-Python is in no way limited to the above
types! An app could use any version of ASPN and any type of transport, so long as there is a
compatible transport plugin to handle the conversion.
:::

## ASPN23-LCM

For simplicity, most example apps use the ASPN23-LCM example data. See below for some more detailed
info about each channel in this log, the data rate, the corresponding ASPN-LCM type, and the error
model:

```{list-table} ASPN23-LCM Example Dataset Info
:header-rows: 1

* - Channel
  - Rate (Hz)
  - ASPN Message
  - About
  - Error Model*

* - `/sensor/bmp388/baro_pressure`
  - 0.2
  - `measurement_barometer`
  - Can be used to bound altitude error
  - FOGM with $\sigma=100m$ and $\tau=3600s$

* - `/sensor/ins-d/pva`
  - 200
  - `measurement_position_velocity_attitude`
  - Reference system (truth)
  - N/A

* - `/sensor/simulated/velocity`
  - 1
  - `measurement_velocity`
  - Simulated 3D platform-frame velocity
  - N/A

* - `/sensor/ublox-ZED-F9T/position`
  - 1
  - `measurement_position`
  - Latitude, longitude, and altitude from a GPS receiver
  - Horizontal FOGM: $\sigma=1.5m$ and $\tau=300s$, Vertical FOGM: $\sigma=2m$ and $\tau=200s$.
    Timestamps are biased about 0.15 seconds into the future.

* - `/sensor/ublox-ZED-F9T/pva`
  - 1
  - `measurement_position_velocity_attitude`
  - PVA from a GPS receiver, used for PosVel update
  - See `/sensor/ublox-ZED-F9T/position`

* - `/sensor/ublox-ZED-F9T/velocity`
  - 1
  - `measurement_velocity`
  - Velocity from a GPS receiver
  - Timestamps are biased about 0.15 seconds into the future.

* - `/sensor/vn-100/imu`
  - 100
  - `measurement_IMU`
  - A tactical-grade IMU
  - See [Appendix](#appendix-imu-error-model)
```

\**In addition to any variances or covariances included in the ASPN message.*

### Appendix: IMU Error Model

This appendix documents the IMU error model which, while more simple than many inertial error
models, is significantly more complex than the error models for the other sensors.

Both the accelerometers and the gyroscopes model two sources of error:

- A FOGM bias
- White noise (which manifests as a random walk in the integrated states)

Unless otherwise noted, all three orthogonal sensors have the same error model. Occasionally, we'll
increase the vertical error as part of the filter tuning process, but this is more of a judgement
call.

#### Accelerometer Error Model

The FOGM bias has the following parameters:

- $\sigma=2.4\text{e-}3, \frac{m}{\text{s}^2}$
- $\sigma_{t=0}=0.072, \frac{m}{\text{s}^2}$
- $\tau=300, \text{s}$

And the white noise is:

- $\sigma=3.887\text{e-}6, \frac{m}{\text{s}^\frac{3}{2}}$

#### Gyroscope Error Model

The FOGM bias has the following parameters:

- $\sigma=2\text{e-}4, \frac{\text{rad}}{\text{s}}$
- $\sigma_{t=0}=0.003, \frac{\text{rad}}{\text{s}}$
- $\tau=500, \text{s}$

And the white noise is:

- $\sigma=9.9\text{e-}4, \frac{\text{rad}}{\text{s}^\frac{1}{2}}$, for the first two axes
- $\sigma=6.7\text{e-}5, \frac{\text{rad}}{\text{s}^\frac{1}{2}}$, for the third axis

#### Orientation

The rotation from the sensor frame to the platform frame is a constant:

$$
C_\text{IMU}^\text{platform} =
\begin{bmatrix}
0.99802515, 0.01772605, 0.06026269\\
-0.01742059, 0.99983262, -0.00559042\\
-0.0603517, 0.00452957, 0.9981669
\end{bmatrix}
$$
