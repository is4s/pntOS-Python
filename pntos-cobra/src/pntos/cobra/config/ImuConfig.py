from dataclasses import dataclass

from .BaseConfig import BaseConfig


@dataclass
class ImuConfig(BaseConfig):
    group: str

    accel_bias_sigma: tuple[float, float, float]
    accel_bias_tau: tuple[float, float, float]
    accel_random_walk_sigma: tuple[float, float, float]
    gyro_bias_sigma: tuple[float, float, float]
    gyro_bias_tau: tuple[float, float, float]
    gyro_random_walk_sigma: tuple[float, float, float]
