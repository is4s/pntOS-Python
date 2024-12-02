from dataclasses import dataclass
from enum import Enum

from navtk.filtering import ImuModel

from .BaseConfig import BaseConfig


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
    imu_model: ImuModel
    static_time: float
    group: str


@dataclass
class ManualHeadingAlignmentConfig(BaseConfig):
    heading: float
    heading_sigma: float
    group: str
