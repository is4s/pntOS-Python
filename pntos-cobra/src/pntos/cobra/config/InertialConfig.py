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

    group: str
