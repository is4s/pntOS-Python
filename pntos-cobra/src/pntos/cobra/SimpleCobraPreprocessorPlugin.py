from aspn23 import MeasurementImu
from numpy import array, float64
from numpy.typing import NDArray

from pntos.api import (
    LoggingLevel,
    Mediator,
    Message,
    Preprocessor,
    PreprocessorPlugin,
)
from pntos.cobra.config import DownsamplerConfig, InertialConfig, config_from_registry


class SimplePreprocessorDownsampler(Preprocessor):
    """
    A simple downsampling preprocessor that periodically discards certain messages.

    It collects a list of channels and factors from the registry and allows 1 out of
    every ``N`` messages to pass through. This is done for every channel ``c`` and factor
    ``N``. Where ``c = channel[i]`` and ``N = factor[i]``.
    """

    _downsampling_factors: dict[str, int]
    _update_counters: dict[str, int]

    def __init__(self, config_group: str, mediator: Mediator):
        """
        Cobra Simple Downsampler Preprocessor

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


class SimpleImuRotationPreprocessor(Preprocessor):
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
                    f'SimpleImuRotationPreprocessor expected IMU message, but got {type(message.wrapped_message)}. Cannot rotate.',
                )

        return [message]


class SimpleCobraPreprocessorPlugin(PreprocessorPlugin):
    """A preprocessor plugin that provides a simple set of preprocessors.

    The preprocessors this plugin provides are:

    1. SimplePreprocessorDownsampler - Downsamples messages on a given list of channels.
    2. SimpleImuRotationPreprocessor - Rotated IMU measurements from IMU to platform frame.
    """

    mediator: Mediator | None

    def __init__(self, identifier: str):
        """Constructor.

        Args:
            identifier (str): The plugin identifier used to set
                this plugin's :attr:`pntos.api.CommonPlugin.identifier` field.
        """
        self.identifier = identifier
        self.preprocessor_identifiers = ['downsampler', 'imu_rotator']

    def init_plugin(
        self,
        plugin_resources_location: str | None = None,
        mediator: Mediator | None = None,
    ) -> None:
        if mediator is None:
            print('Error: mediator cannot be None')
        self.mediator = mediator

    def shutdown_plugin(self):
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

                return SimplePreprocessorDownsampler(config_group, self.mediator)

            case 1:
                if config_group is None:
                    preproc_id = self.preprocessor_identifiers[preprocessor_index]
                    self.mediator.log_message(
                        LoggingLevel.ERROR,
                        f'config_group is a required parameter for preprocessor "{preproc_id}" and cannot be None.',
                    )
                    return None

                config = config_from_registry(
                    InertialConfig, self.mediator, config_group
                )
                if config is None:
                    self.mediator.log_message(
                        LoggingLevel.ERROR,
                        f'Failed to populate InertialConfig for preprocessor {self.preprocessor_identifiers[preprocessor_index]}.',
                    )
                    return None

                return SimpleImuRotationPreprocessor(
                    self.mediator, config.channel, array(config.C_imu_to_platform)
                )

            case _:
                self.mediator.log_message(
                    LoggingLevel.ERROR,
                    f'Invalid preprocessor index of {preprocessor_index}. '
                    'SimpleCobraPreprocessorPlugin provides '
                    f'{len(self.preprocessor_identifiers)} preprocessors.',
                )
                return None
