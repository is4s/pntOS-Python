from dataclasses import dataclass, field

from pntos.cobra.config import PreprocessorConfig


@dataclass(kw_only=True)
class ZeroVelocity2dGeneratorConfig(PreprocessorConfig):
    """Config for ZeroVelocity2dGenerator preprocessor.

    Args:
        channels: Trigger channels for generating zero-velocity measurement.
            Zero-velocity measurements will be generated when a message is received on
            the given channel, provided `trigger_dt_sec` has also been surpassed. If
            None, will generate zero-velocity measurements for all incoming channels.
        trigger_dt_sec: Trigger time for generating zero-velocity measurement.
            Zero-velocity measurements will be generated whenever this delta-time has
            surpassed since last measurement was generated. If 0.0, will generate
            zero-velocity measurement whenever a message is received on a channel
            specified in `channels`.
        lateral_vel_sigma: 1-sigma [m/s] to use for lateral zero-velocity measurement.
        vertical_vel_sigma: 1-sigma [m/s] to use for vertical zero-velocity measurement.
        output_channel: Channel on which to output the zero-velocity measurements.
    """

    identifier: str = field(default='zero_velocity2d_generator', init=False)
    channels: tuple[str, ...] | None = None
    trigger_dt_sec: float = 0.0
    lateral_vel_sigma: float
    vertical_vel_sigma: float
    output_channel: str
