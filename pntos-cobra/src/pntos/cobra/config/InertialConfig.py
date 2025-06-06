from dataclasses import dataclass

from .BaseConfig import BaseConfig


@dataclass
class InertialConfig(BaseConfig):
    """
    Configuration for the inertial mechanization and buffering.
    """

    expected_dt: float
    """
    The expected delta-time between inertial messages, in seconds.
    """

    inertial_buffer_length: float
    """
    The length of the inertial buffer in seconds.
    """

    channel: str
    """Channel containing IMU measurements."""

    C_imu_to_platform: tuple[
        tuple[float, float, float],
        tuple[float, float, float],
        tuple[float, float, float],
    ]
    """DCM used to rotate measurements from IMU sensor frame to platform frame."""

    group: str
