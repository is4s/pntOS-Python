from dataclasses import dataclass
from typing import Tuple


@dataclass
class ImuConfig:
    accel_bias_sigma: Tuple[float, float, float]
    accel_bias_tau: Tuple[float, float, float]
    gyro_bias_sigma: Tuple[float, float, float]
    gyro_bias_tau: Tuple[float, float, float]

    group: str = "/config/cobra/imu_config"


IMU_CONFIG_COMMERCIAL = ImuConfig(
    accel_bias_sigma=(0.0098, 0.0098, 0.0098),
    accel_bias_tau=(3600.0, 3600.0, 3600.0),
    gyro_bias_sigma=(9.234e-6, 9.234e-6, 9.234e-6),
    gyro_bias_tau=(3600.0, 3600.0, 3600.0),
)

IMU_CONFIG_TACTICAL = ImuConfig(
    accel_bias_sigma=(0.0098, 0.0098, 0.0098),
    accel_bias_tau=(3600.0, 3600.0, 3600.0),
    gyro_bias_sigma=(1.234e-6, 1.234e-6, 1.234e-6),
    gyro_bias_tau=(3600.0, 3600.0, 3600.0),
)
