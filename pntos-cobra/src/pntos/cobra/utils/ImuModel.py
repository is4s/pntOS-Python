from dataclasses import dataclass

from numpy import float64
from numpy.typing import NDArray


@dataclass
class ImuModel:
    accel_bias_sigma: NDArray[float64]
    accel_bias_tau: NDArray[float64]
    accel_random_walk_sigma: NDArray[float64]
    gyro_bias_sigma: NDArray[float64]
    gyro_bias_tau: NDArray[float64]
    gyro_random_walk_sigma: NDArray[float64]
