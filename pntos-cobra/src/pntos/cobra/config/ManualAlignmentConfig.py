from dataclasses import dataclass

from .BaseConfig import BaseConfig


@dataclass
class ManualAlignmentConfig(BaseConfig):
    """
    Configuration to manually align an inertial unit to the platform frame.
    """

    group: str

    initial_pos: tuple[float, float, float]
    """
    Initial latitude, longitude, and altitude of the sensor. (rad, rad, m HAE)
    """

    initial_vel: tuple[float, float, float]
    """
    Initial velocity in the navigation frame (NED) in m/s.
    """

    initial_rpy: tuple[float, float, float]
    """
    Initial attitude expressed as Euler angles (roll, pitch, yaw, in radians).
    The corresponding quaternion is in the same frame as an ASPN PVA's quaternion.
    The corresponding DCM would be `C_platform_to_navigation`.
    """

    initial_accel_bias: tuple[float, float, float]
    """
    Initial bias of the accelerometers, in the sensor frame (m/s^2).
    """

    initial_gyro_bias: tuple[float, float, float]
    """
    Initial bias of the gyroscopes, in the sensor frame (rad/s).
    """

    initial_accel_scale_factor: tuple[float, float, float]
    """
    Initial scale factor error of the accelerometers, in the sensor frame in Parts-Per-Million (PPM).
    """

    initial_gyro_scale_factor: tuple[float, float, float]
    """
    Initial scale factor error of the gyroscopes, in the sensor frame in Parts-Per-Million (PPM).
    """

    initial_time: float
    """
    The time at which this alignment is valid for, in nanoseconds.
    """

    initial_pos_var: tuple[float, float, float]
    """
    The variance of the error in the initial position in the NED frame (m^2, m^2, m^2).
    """

    initial_vel_var: tuple[float, float, float]
    """
    The variance of the error in the initial velocity (m^2/s^2).
    """

    initial_tilt_var: tuple[float, float, float]
    """
    The variance of the tilt errors associated with the initial attitude (rad^2).
    """

    initial_accel_bias_var: tuple[float, float, float]
    """
    The variance of the intial accelerometer bias (m^2/s^4).
    """

    initial_gyro_bias_var: tuple[float, float, float]
    """
    The variance of the initial gyroscope biases (rad^2/s^2).
    """

    initial_accel_scale_factor_var: tuple[float, float, float]
    """
    The variance of the initial accelerometer scale factors (PPM^2).
    """

    initial_gyro_scale_factor_var: tuple[float, float, float]
    """
    The variance of the initial gyroscope scale factors (PPM^2).
    """
