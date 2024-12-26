from dataclasses import dataclass
from typing import Tuple


@dataclass
class AlignmentConfig:
    initialPosCov: Tuple[float, float, float]
    initialVelCov: Tuple[float, float, float]
    initialTiltCov: Tuple[float, float, float]
    initialAccelBiasCov: Tuple[float, float, float]
    initialGyroBiasCov: Tuple[float, float, float]

    group: str = '/config/cobra/alignment_config/default'
