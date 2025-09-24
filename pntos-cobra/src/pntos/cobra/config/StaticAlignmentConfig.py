from dataclasses import dataclass

from .BaseConfig import BaseConfig
from .ImuConfig import ImuConfig


@dataclass
class StaticAlignmentConfig(BaseConfig):
    """
    Configuration specifically for a manual heading alignment which is used in the 'StaticAlignInitializationPlugin.py' plugin.
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

    group: str
