from dataclasses import dataclass

from .BaseConfig import BaseConfig


@dataclass
class ImuConfig(BaseConfig):
    """
    The error model of an inertial unit, including white noise (random walk)
    and a bias modeled as a First-Order Gauss-Markov (FOGM) process for each sensor.
    """

    group: str

    accel_bias_sigma: tuple[float, float, float]
    """
    The steady-state sigma of the bias state in m/s^2.
    """

    accel_bias_tau: tuple[float, float, float]
    """
    The time constant for the accelerometer's FOGM process in seconds.
    """

    accel_random_walk_sigma: tuple[float, float, float]
    """
    The sigma for the accelerometer random walk process in m/s^(3/2)
    """

    gyro_bias_sigma: tuple[float, float, float]
    """
    The steady-state sigma of the bias state in rad/s
    """

    gyro_bias_tau: tuple[float, float, float]
    """
    The time constant for the gyro's FOGM process in seconds
    """

    gyro_random_walk_sigma: tuple[float, float, float]
    """The sigma for the gyro random walk process in rad/s^(1/2)"""
