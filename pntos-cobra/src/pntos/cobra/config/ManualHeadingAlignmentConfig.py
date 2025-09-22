from dataclasses import dataclass

from .ImuConfig import ImuConfig
from .StaticAlignmentConfig import AlignmentStrategy, StaticAlignmentConfig


@dataclass
class ManualHeadingAlignmentConfig(StaticAlignmentConfig):
    """
    Configuration specifically for a manual heading alignment which is used in the 'StaticAlignInitializationPlugin.py' plugin.
    """

    # INHERITED FIELDS
    group: str

    strategy: AlignmentStrategy

    static_time: float

    imu_model: ImuConfig

    # UNIQUE FIELDS

    heading: float
    """
    Heading of the platform. (rad, right handed rotation from north,
    about the down axis)
    """

    heading_sigma: float
    """
    The one-sigma, standard deviation of the tilt error about the down axis associated with the initial heading.
    """
