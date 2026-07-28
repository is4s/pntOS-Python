from dataclasses import dataclass, field

from .BaseConfig import BaseConfig


@dataclass(kw_only=True)
class PreprocessorConfig(BaseConfig):
    """The base preprocessor config all preprocessor configs should inherit from."""

    # INHERITED FIELDS
    group: str

    # UNIQUE FIELDS
    identifier: str
    """
    A string that specifies which preprocessor this config should be used in.

    This field will be matched against the `preprocessor_identifiers` field on the preprocessor plugin.
    """

    channels: tuple[str, ...] | None
    """
    Specifier for which channels/chains should include this preprocessor.

    If `regex` field is True, the strings in the channels will be interpreted as regex patterns.
    """

    regex: bool = False
    """
    Indication whether `channels` field is/are (a) regex pattern(s) or exact string(s)
    """


@dataclass(kw_only=True)
class BarometerToAltitudeConfig(PreprocessorConfig):
    """
    Configuration for the barometer to altitude preprocessor.

    Attributes:
        group (str): Inherited from PreprocessorConfig. Registry group in which to store this config.
        identifier (str): Inherited from PreprocessorConfig. Identifier associated with the desired type of preprocessor.
        channels (tuple[str, ...] | None): Name of the barometric pressure channel to convert to altitude. Assumed to end in `baro_pressure`. Altitude measurements will be output on this channel, with `baro_pressure` replaced with `altitude`.
        regex (bool): Indication whether `channels` contains regex pattern(s)
        alt_sigma (float | None): Optional value used to override altitude measurement variance. If not specified baro pressure variance will be converted to altitude variance using the scale factor necessary to convert the pressure measurement to altitude.
    """

    # INHERITED FIELDS
    group: str

    identifier: str = field(default='baro_converter', init=False)

    channels: tuple[str, ...] | None

    regex: bool = False

    # UNIQUE FIELDS
    alt_sigma: float | None = None


@dataclass(kw_only=True)
class DownsamplerConfig(PreprocessorConfig):
    """
    Configuration for the downsampler preprocessor.
    """

    # INHERITED FIELDS
    group: str

    identifier: str = field(default='downsampler', init=False)

    channels: tuple[str, ...] | None
    """
    A series of channels to downsample.
    """

    regex: bool = field(default=False, init=False)

    # UNIQUE FIELDS
    downsampling_factors: tuple[int, ...]
    """
    A series of downsampling factors to apply to the channels
    """


@dataclass(kw_only=True)
class ImuRotatorConfig(PreprocessorConfig):
    """
    Configuration for the IMU rotator preprocessor
    """

    # INHERITED FIELDS
    group: str

    identifier: str = field(default='imu_rotator', init=False)

    channels: tuple[str, ...] | None
    """
    The name of the channel to rotate.
    """

    regex: bool = False

    # UNIQUE FIELDS
    C_imu_to_platform: tuple[
        tuple[float, float, float],
        tuple[float, float, float],
        tuple[float, float, float],
    ]
    """DCM used to rotate measurements from IMU sensor frame to platform frame."""


@dataclass(kw_only=True)
class TimeAdjusterConfig(PreprocessorConfig):
    """
    Configuration for the time adjuster preprocessor.
    """

    # INHERITED FIELDS
    group: str

    identifier: str = field(default='time_adjuster', init=False)

    channels: tuple[str, ...] | None
    """
    The name of the channel to correct.
    """

    regex: bool = False

    # UNIQUE FIELDS
    expected_dt_nsec: int
    """
    The expected time between messages in nanoseconds.

    For example, a 100 Hz sensor sends 100 messages per second which is 0.01 seconds per message (interval in seconds).
    Convert that to nanoseconds like so `int(0.01 * 1e9)`.
    """


@dataclass(kw_only=True)
class TimeBiasConfig(PreprocessorConfig):
    """
    Configuration for the time bias preprocessor.
    """

    # INHERITED FIELDS
    group: str

    identifier: str = field(default='time_bias', init=False)

    channels: tuple[str, ...] | None
    """
    The names of the channels to correct.
    """

    regex: bool = False

    # UNIQUE FIELDS
    time_bias: int
    """
    The amount the timestamps are biased by in nanoseconds.

    For example, if a given channel has timestamps which are 0.1s in the future then this should be
    set to 100'000'000 and the preprocessor will return messages with a timestamp of
    `original - 100'000'000`.
    """


@dataclass(kw_only=True)
class OutageConfig(PreprocessorConfig):
    """Configuration for OutagePreprocessor.

    Specifies a time period in which to discard messages on a given channel to simulate
    a measurement outage. All measurements in the range [start_time, end_time) will be
    discarded.

    Attributes:

        group (str): Inherited from PreprocessorConfig. Registry group in which to store this config.
        identifier (str): Inherited from PreprocessorConfig. A string that specifies which preprocessor this config should be used in.
        channels (tuple[str, ...] | None): Channel on which to induce an outage.
        regex (bool): Indication whether `channels` contains regex pattern(s)
        start_time (float): Time in seconds at which to begin the outage. This time is
            relative to the timestamp of the first message received on the given channel.
        end_time (float): Time in seconds at which to end the outage. This time is
            relative to the timestamp of the first message received on the given channel.
    """

    # INHERITED FIELDS
    group: str
    identifier: str = field(default='outage', init=False)
    channels: tuple[str, ...] | None
    regex: bool = False

    # UNIQUE FIELDS
    start_time: float
    end_time: float
