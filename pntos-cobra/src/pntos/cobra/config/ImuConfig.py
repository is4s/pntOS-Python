from dataclasses import dataclass
from typing import Tuple


@dataclass
class ImuConfig:
    accel_bias_sigma: Tuple[float, float, float]
    accel_bias_tau: Tuple[float, float, float]
    accel_rw_sigma: Tuple[float, float, float]
    gyro_bias_sigma: Tuple[float, float, float]
    gyro_bias_tau: Tuple[float, float, float]
    gyro_rw_sigma: Tuple[float, float, float]

    group: str = "/config/cobra/imu_config/default"
