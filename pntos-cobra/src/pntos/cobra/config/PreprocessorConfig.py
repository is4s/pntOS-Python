from dataclasses import dataclass

from .BaseConfig import BaseConfig


@dataclass
class PreprocessorConfig(BaseConfig):
    """The base preprocessor config all preprocessor configs should inherit from."""

    group: str

    identifier: str
    """
    A string that specifies which preprocessor this config should be used in.

    This field will be matched against the `preprocessor_identifiers` field on the preprocessor plugin.
    """


@dataclass
class BarometerToAltitudeConfig(PreprocessorConfig):
    """
    Configuration for the barometer to altitude preprocessor.

    Attributes:
        group (str): Inherited from PreprocessorConfig. Registry group in which to store this config.
        identifier (str): Inherited from PreprocessorConfig. Identifier associated with the desired type of preprocessor.
        channel (str): Name of the barometric pressure channel to convert to altitude. Assumed to end in `baro_pressure`. Altitude measurements will be output on this channel, with `baro_pressure` replaced with `altitude`.
        alt_sigma (float | None): Optional value used to override altitude measurement variance. If not specified baro pressure variance will be converted to altitude variance using the scale factor necessary to convert the pressure measurement to altitude.
    """

    # INHERITED FIELDS
    group: str

    identifier: str

    # UNIQUE FIELDS
    channel: str

    alt_sigma: float | None = None


@dataclass
class DownsamplerConfig(PreprocessorConfig):
    """
    Configuration for the downsampler preprocessor.
    """

    # INHERITED FIELDS
    group: str

    identifier: str

    # UNIQUE FIELDS
    channels_to_downsample: tuple[str, ...]
    """
    A series of channels to downsample
    """

    downsampling_factors: tuple[int, ...]
    """
    A series of downsampling factors to apply to the channels
    """


@dataclass
class ImuRotatorConfig(PreprocessorConfig):
    """
    Configuration for the IMU rotator preprocessor
    """

    # INHERITED FIELDS
    group: str

    identifier: str

    # UNIQUE FIELDS
    channel: str
    """
    The name of the channel to rotate.
    """

    C_imu_to_platform: tuple[
        tuple[float, float, float],
        tuple[float, float, float],
        tuple[float, float, float],
    ]
    """DCM used to rotate measurements from IMU sensor frame to platform frame."""


@dataclass
class TimeAdjusterConfig(PreprocessorConfig):
    """
    Configuration for the time adjuster preprocessor.
    """

    # INHERITED FIELDS
    group: str

    identifier: str

    # UNIQUE FIELDS
    channel_to_correct: str
    """
    The name of the channel to correct.
    """

    expected_dt_nsec: int
    """
    The expected time between messages in nanoseconds.

    For example, a 100 Hz sensor sends 100 messages per second which is 0.01 seconds per message (interval in seconds).
    Convert that to nanoseconds like so `int(0.01 * 1e9)`.
    """


@dataclass
class TimeBiasConfig(PreprocessorConfig):
    """
    Configuration for the time bias preprocessor.
    """

    # INHERITED FIELDS
    group: str

    identifier: str

    # UNIQUE FIELDS
    channels_to_correct: tuple[str, ...]
    """
    The names of the channels to correct.
    """

    time_bias: int
    """
    The amount the timestamps are biased by in nanoseconds.

    For example, if a given channel has timestamps which are 0.1s in the future then this should be
    set to 100'000'000 and the preprocessor will return messages with a timestamp of
    `original - 100'000'000`.
    """
