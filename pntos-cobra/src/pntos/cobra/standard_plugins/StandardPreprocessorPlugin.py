from aspn23 import (
    AspnBase,
    MeasurementAltitude,
    MeasurementAltitudeErrorModel,
    MeasurementAltitudeReference,
    MeasurementBarometer,
    MeasurementImu,
    TypeTimestamp,
)
from numpy import array, float64
from numpy.typing import NDArray
from pntos.api import (
    LoggingLevel,
    Mediator,
    Message,
    Preprocessor,
    PreprocessorPlugin,
)
from pntos.cobra.config import (
    BarometerToAltitudeConfig,
    DownsamplerConfig,
    ImuRotatorConfig,
    TimeAdjusterConfig,
    config_from_registry,
)


class BarometerToAltitudePreprocessor(Preprocessor):
    """
    A preprocessor that converts barometer measurements to altitude measurements.
    """

    _deg_k: float
    _channel: str
    _mediator: Mediator

    def __init__(self, channel: str, mediator: Mediator):
        """
        Cobra Barometer to Altitude Preprocessor
        """
        self._deg_k = 288.15
        self._channel = channel
        self._mediator = mediator

    def _convert_pressure(self, pressure: float) -> float:
        pwm1: float = pow(pressure / 101325, 8314.32 * 0.0065 / (9.80665 * 28.9644)) - 1
        return -(self._deg_k / 0.0065) * pwm1

    def process_pntos_message(self, message: Message) -> list[Message]:
        if message.source_identifier == self._channel:
            msg = message.wrapped_message
            if isinstance(msg, MeasurementBarometer):
                altitude = self._convert_pressure(msg.pressure)
                sf = altitude / msg.pressure
                altitude_variance = msg.variance * (sf**2)
                return [
                    Message(
                        MeasurementAltitude(
                            msg.header,
                            msg.time_of_validity,
                            MeasurementAltitudeReference.MSL,
                            altitude,
                            altitude_variance,
                            MeasurementAltitudeErrorModel.NONE,
                            msg.error_model_params,
                            msg.integrity,
                        ),
                        message.source_identifier,
                    )
                ]
            else:
                self._mediator.log_message(
                    LoggingLevel.WARN,
                    f'BarometerToAltitudePreprocessor expected barometer message, but got {type(message.wrapped_message)}. Cannot convert.',
                )
        return [message]


class PreprocessorDownsampler(Preprocessor):
    """
    A downsampling preprocessor that periodically discards certain messages.

    It collects a list of channels and factors from the registry and allows 1 out of
    every ``N`` messages to pass through. This is done for every channel ``c`` and factor
    ``N``. Where ``c = channel[i]`` and ``N = factor[i]``.
    """

    _downsampling_factors: dict[str, int]
    _update_counters: dict[str, int]

    def __init__(self, config_group: str, mediator: Mediator):
        """
        Cobra Downsampler Preprocessor

        Args:
            config_group (str): The :class:`pntos.cobra.config.DownsamplerConfig` config group.
            mediator (Mediator): A :class:`pntos.api.Mediator` instance.
        """
        self._downsampling_factors = {}
        self._update_counters = {}
        self.mediator = mediator
        config = config_from_registry(DownsamplerConfig, mediator, config_group)

        if config is None:
            self.mediator.log_message(
                LoggingLevel.ERROR,
                'Unable to retrieve config from registry.',
            )
            return

        channels = config.channels_to_downsample
        factors = array(config.downsampling_factors, dtype=int)
        chan_len = len(channels)
        fac_len = len(factors)

        if not chan_len == fac_len:
            self.mediator.log_message(
                LoggingLevel.WARN,
                f'Channels to downsample has {chan_len} elements, '
                + f'but downsampling factors has {fac_len}. '
                + 'Downsampling will be disabled.',
            )
            return

        for idx in range(chan_len):
            channel = channels[idx]
            if factors[idx] < 0:
                self.mediator.log_message(
                    LoggingLevel.WARN,
                    f'Downsampling factor of {factors[idx]} '
                    + f'for channel "{channel}" cannot be negative. '
                    + 'Channel will not be downsampled.',
                )
            else:
                self._downsampling_factors[channel] = factors[idx]
                # Setting to -1 so the first message is always processed
                self._update_counters[channel] = -1

    def process_pntos_message(self, message: Message) -> list[Message] | None:
        identifier = message.source_identifier
        if identifier not in self._downsampling_factors:
            return [message]

        # Keep 1 out of every N messages on the current channel
        # where N = factor.
        factor = self._downsampling_factors[identifier]
        count = self._update_counters[identifier]
        self._update_counters[identifier] = (count + 1) % factor

        if not self._update_counters[identifier] == 0:
            return None

        return [message]


class ImuRotationPreprocessor(Preprocessor):
    _mediator: Mediator
    _imu_channel: str
    _C_imu_to_platform: NDArray[float64]

    def __init__(
        self,
        mediator: Mediator,
        imu_channel: str,
        C_imu_to_platform: NDArray[float64],
    ):
        self._mediator = mediator
        self._imu_channel = imu_channel
        self._C_imu_to_platform = C_imu_to_platform

    def process_pntos_message(self, message: Message) -> list[Message]:
        if message.source_identifier == self._imu_channel:
            if isinstance(message.wrapped_message, MeasurementImu):
                imu = message.wrapped_message
                imu.meas_accel = self._C_imu_to_platform @ imu.meas_accel
                imu.meas_gyro = self._C_imu_to_platform @ imu.meas_gyro
            else:
                self._mediator.log_message(
                    LoggingLevel.WARN,
                    f'ImuRotationPreprocessor expected IMU message, but got {type(message.wrapped_message)}. Cannot rotate.',
                )

        return [message]


class TimeAdjusterPreprocessor(Preprocessor):
    _mediator: Mediator
    _channel_to_correct: str
    _last_nsec: int | None
    _expected_dt_nsec: int
    _tolerance_nsec: int

    def __init__(
        self,
        config_group: str,
        mediator: Mediator,
    ):
        self._mediator = mediator
        config = config_from_registry(TimeAdjusterConfig, self._mediator, config_group)
        if config is None:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'Failed to populate TimeAdjusterConfig in TimeAdjusterPreprocessor.',
            )
            return None
        self._channel_to_correct = config.channel_to_correct
        self._last_nsec = None
        self._expected_dt_nsec = config.expected_dt_nsec
        self._tolerance_nsec = int(0.0001 * 1e9)

    def process_pntos_message(self, message: Message) -> list[Message] | None:
        if message.source_identifier != self._channel_to_correct:
            return [message]

        msg: AspnBase = message.wrapped_message
        if not hasattr(msg, 'time_of_validity'):
            self._mediator.log_message(
                LoggingLevel.WARN,
                f'TimeAdjusterPreprocessor received a message from channel {message.source_identifier} with no time of validity. Ignoring message.',
            )
            return [message]

        curr_nsec: int = msg.time_of_validity.elapsed_nsec
        if self._last_nsec is None:
            self._last_nsec = curr_nsec
            return [message]

        is_valid_time: bool = (
            abs((curr_nsec - self._last_nsec) - self._expected_dt_nsec)
            < self._tolerance_nsec
        )
        if not is_valid_time:
            synthetic_time: int = self._last_nsec + self._expected_dt_nsec
            msg.time_of_validity = TypeTimestamp(synthetic_time)
            self._last_nsec = synthetic_time
        else:
            self._last_nsec = curr_nsec

        return [message]


class StandardPreprocessorPlugin(PreprocessorPlugin):
    """A preprocessor plugin that provides the standard-level set of preprocessors.

    The preprocessors this plugin provides are:

    1. PreprocessorDownsampler - Downsamples messages on a given list of channels.
    2. ImuRotationPreprocessor - Rotated IMU measurements from IMU to platform frame.
    3. TimeAdjusterPreprocessor - Synthesizes timestamps to compensate for erroneous hardware.
    4. BarometerToAltitudePreprocessor - Converts pressure measurements to altitude measurements.
    """

    mediator: Mediator | None

    def __init__(self, identifier: str):
        """Constructor.

        Args:
            identifier (str): The plugin identifier used to set
                this plugin's :attr:`pntos.api.CommonPlugin.identifier` field.
        """
        self.identifier = identifier
        self.preprocessor_identifiers = [
            'downsampler',
            'imu_rotator',
            'time_adjuster',
            'baro_converter',
        ]

    def init_plugin(
        self,
        plugin_resources_location: str | None = None,
        mediator: Mediator | None = None,
    ) -> None:
        if mediator is None:
            print('Error: mediator cannot be None')
        self.mediator = mediator

    def shutdown_plugin(self) -> None:
        pass

    def new_preprocessor(
        self,
        preprocessor_index: int,
        config_group: str | None = None,
    ) -> Preprocessor | None:
        if self.mediator is None:
            print(
                'Error: mediator is None. PreprocessorPlugin.init_plugin must be called'
                + ' and passed a valid mediator before new_preprocessor.'
            )
            return None

        match preprocessor_index:
            case 0:
                if config_group is None:
                    preproc_id = self.preprocessor_identifiers[preprocessor_index]
                    self.mediator.log_message(
                        LoggingLevel.ERROR,
                        f'config_group is a required parameter for preprocessor "{preproc_id}" and cannot be None.',
                    )
                    return None

                return PreprocessorDownsampler(config_group, self.mediator)

            case 1:
                if config_group is None:
                    preproc_id = self.preprocessor_identifiers[preprocessor_index]
                    self.mediator.log_message(
                        LoggingLevel.ERROR,
                        f'config_group is a required parameter for preprocessor "{preproc_id}" and cannot be None.',
                    )
                    return None

                inert_config = config_from_registry(
                    ImuRotatorConfig, self.mediator, config_group
                )
                if inert_config is None:
                    self.mediator.log_message(
                        LoggingLevel.ERROR,
                        f'Failed to populate InertialConfig for preprocessor {self.preprocessor_identifiers[preprocessor_index]}.',
                    )
                    return None

                return ImuRotationPreprocessor(
                    self.mediator,
                    inert_config.channel,
                    array(inert_config.C_imu_to_platform),
                )

            case 2:
                if config_group is None:
                    preproc_id = self.preprocessor_identifiers[preprocessor_index]
                    self.mediator.log_message(
                        LoggingLevel.ERROR,
                        f'config_group is a required parameter for preprocessor "{preproc_id}" and cannot be None.',
                    )
                    return None

                return TimeAdjusterPreprocessor(config_group, self.mediator)

            case 3:
                if config_group is None:
                    preproc_id = self.preprocessor_identifiers[preprocessor_index]
                    self.mediator.log_message(
                        LoggingLevel.ERROR,
                        f'config_group is a required parameter for preprocessor "{preproc_id}" and cannot be None.',
                    )
                    return None
                bta_config = config_from_registry(
                    BarometerToAltitudeConfig, self.mediator, config_group
                )
                if bta_config is None:
                    self.mediator.log_message(
                        LoggingLevel.ERROR,
                        f'Failed to populate BarometerToAltitudeConfig for preprocessor {self.preprocessor_identifiers[preprocessor_index]}.',
                    )
                    return None
                return BarometerToAltitudePreprocessor(
                    bta_config.channel, self.mediator
                )

            case _:
                self.mediator.log_message(
                    LoggingLevel.ERROR,
                    f'Invalid preprocessor index of {preprocessor_index}. '
                    'StandardPreprocessorPlugin provides '
                    f'{len(self.preprocessor_identifiers)} preprocessors.',
                )
                return None
