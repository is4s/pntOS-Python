from dataclasses import dataclass

from .BaseConfig import BaseConfig


@dataclass
class MountingConfig(BaseConfig):
    """
    Rotation and lever arm from frame A to frame B.
    """

    group: str

    lever_arm: tuple[float, float, float]
    """
    The lever arm from frame A to B, measured in frame A (m).
    """

    orientation: tuple[float, float, float, float]
    """
    A quaternion representing the rotation from frame A to B. The corresponding DCM
    would be C_A_to_B.
    """
