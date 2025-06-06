from dataclasses import dataclass

from .BaseConfig import BaseConfig


@dataclass
class OrchestrationConfig(BaseConfig):
    """
    Configuration that dictates what channels will be used by the orchestration plugin.
    """

    gps_channel: str
    """
    The name of the gps channel whose messages will be used for alignment and the fusion engine.
    """

    velocity_channel: str = 'unused'
    """
    The name of the velocity channel whose messages will be used for measurement updates in the fusion engine.
    """

    group: str
