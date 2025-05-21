from dataclasses import dataclass

from .BaseConfig import BaseConfig


@dataclass
class OrchestrationConfig(BaseConfig):
    """
    Configuration that dictates what channels will be used by the orchestration plugin.
    """

    imu_channel: str
    """
    The name of the inertial channel whose messages will be used for alignment and inertial mechanization.
    """

    gps_channel: str
    """
    The name of the gps channel whose messages will be used for alignment and the fusion engine.
    """

    group: str
