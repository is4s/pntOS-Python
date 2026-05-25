from dataclasses import dataclass

from .BaseConfig import BaseConfig


@dataclass
class PvaMessageInitializationConfig(BaseConfig):
    """Config for manual initialization from PVA message.

    Args:
        group: Inherited from BaseConfig. Registry group in which to store this config.
        initial_pva_channel: Channel on which to receive PVA messages for initialization.
        initial_accel_bias_sigma: 3-D accel bias sigma (m/s^2).
        initial_gyro_bias_sigma: 3-D gyro bias sigma (rad/s).
        initial_pva_sigma: Optional PVA 1-sigma. First 3 elements are NED position sigma (m),
            next 3 are NED velocity sigma (m/s), and last 3 are NED tilt sigma (rad).
            If unset, will use covariance on PVA message.
        start_time: Optional absolute time of validity (in seconds) after which to accept PVA
            messages for initialization. If None, will initialize from first PVA message received.
    """

    group: str
    initial_pva_channel: str
    initial_accel_bias_sigma: tuple[float, float, float]
    initial_gyro_bias_sigma: tuple[float, float, float]
    initial_pva_sigma: (
        tuple[float, float, float, float, float, float, float, float, float] | None
    ) = None
    start_time: float | None = None
