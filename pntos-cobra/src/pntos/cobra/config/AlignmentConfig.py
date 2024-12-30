from dataclasses import dataclass


@dataclass
class AlignmentConfig:
    initial_pos_var: tuple[float, float, float]
    initial_vel_var: tuple[float, float, float]
    initial_tilt_var: tuple[float, float, float]
    initial_accel_bias_var: tuple[float, float, float]
    initial_gyro_bias_var: tuple[float, float, float]

    group: str
