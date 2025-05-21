from dataclasses import dataclass

from .BaseConfig import BaseConfig


@dataclass
class SensorConfig(BaseConfig):
    """
    Information about a sensor's relationship to the platform frame.
    """

    group: str

    lever_arm: tuple[float, float, float]
    """
    The positional difference from the sensor frame to the platform frame. (m)
    """

    orientation: tuple[float, float, float, float]
    """
    A quaternion representing the rotational difference from the sensor frame to the platform frame.
    The corresponding DCM would be C_sensor_to_platform.
    """

    use_for_alignment: bool
    """
    If true this config will be used during alignment with the platform frame.
    """

    sensor_name: str
    """
    A designated name for the sensor.
    """
