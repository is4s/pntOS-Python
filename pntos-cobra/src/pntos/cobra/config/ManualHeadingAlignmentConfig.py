from dataclasses import dataclass

from .BaseConfig import BaseConfig
from .ImuConfig import ImuConfig


@dataclass
class ManualHeadingAlignmentConfig(BaseConfig):
    """
    Configuration specifically for a manual heading alignment which is used in the 'ManualHeadingAlignInitializationPlugin.py' plugin.
    """

    static_time: float
    """
    The amount of IMU data that must be collected before calculating an alignment. (s)
    """

    imu_model: ImuConfig
    """
    A nested config that contains IMU model info.

    For more information, see ImuConfig.py.
    """

    heading: float
    """
    Heading of the platform. (rad, right handed rotation from north, about the down axis)
    """

    heading_sigma: float
    """
    The one-sigma, standard deviation of the tilt error about the down axis associated with the
    initial heading.
    """

    group: str
