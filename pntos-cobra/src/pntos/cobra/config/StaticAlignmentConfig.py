from dataclasses import dataclass
from enum import Enum

from .BaseConfig import BaseConfig
from .ImuConfig import ImuConfig


class AlignmentStrategy(Enum):
    """
    Various inertial alignment strategies.
    """

    STATIC = 0
    """
    Calculate alignment from stationary data.

    Performs gyrocompassing on IMU data to calculate initial orientation. Populates position from a
    position measurement.

    For more information, see the NavToolkit docs on the StaticAlignment class.
    """

    MANUAL_HEADING = 1
    """
    A variant of the static alignment which requires a user-provided heading.

    Uses IMU data to calculate roll and pitch.

    For more information, see the NavToolkit docs on the ManualHeadingAlignment class.
    """


@dataclass
class StaticAlignmentConfig(BaseConfig):
    strategy: AlignmentStrategy
    static_time: float
    imu_model: ImuConfig

    group: str
