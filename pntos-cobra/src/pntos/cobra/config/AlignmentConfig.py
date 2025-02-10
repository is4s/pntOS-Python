from dataclasses import dataclass


@dataclass
class AlignmentConfig:
    initialPosCov: tuple[float, float, float]
    initialVelCov: tuple[float, float, float]
    initialTiltCov: tuple[float, float, float]
    initialAccelBiasCov: tuple[float, float, float]
    initialGyroBiasCov: tuple[float, float, float]

    group: str
