from dataclasses import dataclass

from .BaseConfig import BaseConfig


@dataclass
class ManualHeadingAlignmentConfig(BaseConfig):
    """
    Configuration specifically for a manual heading alignment which is used in the 'StaticAlignInitializationPlugin.py' plugin.

    This is designed to be used in conjunction with a StaticAlignmentConfig.

    See StaticAlignmentConfig.py for more information.
    """

    heading: float
    """
    Heading of the platform. (rad, right handed rotation from north,
    about the down axis)
    """

    heading_sigma: float
    """
    The one-sigma, standard deviation of the tilt error about the down axis associated with the initial heading.
    """

    group: str
