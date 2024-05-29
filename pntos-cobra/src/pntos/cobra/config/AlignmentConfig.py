from dataclasses import dataclass
from typing import Tuple


@dataclass
class AlignmentConfig:
    initialPosCov: Tuple[float, float, float]
    initialVelCov: Tuple[float, float, float]
    initialTiltCov: Tuple[float, float, float]
    initialAccelBiasCov: Tuple[float, float, float]
    initialGyroBiasCov: Tuple[float, float, float]

    group: str = "/config/cobra/alignment_config"


ALIGNMENT_CONFIG_GYROCOMPASS = AlignmentConfig(
    initialPosCov=(9.0, 9.0, 9.0),
    initialVelCov=(0.1, 0.1, 0.1),
    initialTiltCov=(0.01, 0.01, 0.01),
    initialAccelBiasCov=(9.604e-5, 9.604e-5, 9.604e-5),
    initialGyroBiasCov=(2.3504074e-11, 2.3504074e-11, 2.3504074e-11),
)
