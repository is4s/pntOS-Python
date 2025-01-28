from dataclasses import dataclass


@dataclass
class ImuConfig:
    accel_bias_sigma: tuple[float, float, float]
    accel_bias_tau: tuple[float, float, float]
    accel_rw_sigma: tuple[float, float, float]
    gyro_bias_sigma: tuple[float, float, float]
    gyro_bias_tau: tuple[float, float, float]
    gyro_rw_sigma: tuple[float, float, float]

    group: str = '/config/cobra/imu_config/default'
