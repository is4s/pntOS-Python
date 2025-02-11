from dataclasses import dataclass


@dataclass
class AlignmentConfig:
    initial_pos: tuple[float, float, float]
    initial_vel: tuple[float, float, float]
    initial_rpy: tuple[float, float, float]
    initial_accel_bias: tuple[float, float, float]
    initial_gyro_bias: tuple[float, float, float]
    initial_accel_scale_factor: tuple[float, float, float]
    initial_gyro_scale_factor: tuple[float, float, float]

    initial_time: float

    initial_pos_var: tuple[float, float, float]
    initial_vel_var: tuple[float, float, float]
    initial_tilt_var: tuple[float, float, float]
    initial_accel_bias_var: tuple[float, float, float]
    initial_gyro_bias_var: tuple[float, float, float]
    initial_accel_scale_factor_var: tuple[float, float, float]
    initial_gyro_scale_factor_var: tuple[float, float, float]

    group: str
