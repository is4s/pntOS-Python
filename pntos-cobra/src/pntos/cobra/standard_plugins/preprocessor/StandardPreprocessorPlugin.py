from numpy import array
from pntos.api import (
    LoggingLevel,
    Mediator,
    Preprocessor,
    PreprocessorPlugin,
)
from pntos.cobra.config import (
    BarometerToAltitudeConfig,
    DownsamplerConfig,
    ImuRotatorConfig,
    OutageConfig,
    TimeAdjusterConfig,
    TimeBiasConfig,
    config_from_registry,
)

from .BarometerToAltitudePreprocessor import BarometerToAltitudePreprocessor
from .DownsamplerPreprocessor import DownsamplerPreprocessor
from .ImuRotationPreprocessor import ImuRotationPreprocessor
from .OutagePreprocessor import OutagePreprocessor
from .TimeAdjusterPreprocessor import TimeAdjusterPreprocessor
from .TimeBiasPreprocessor import TimeBiasPreprocessor


class StandardPreprocessorPlugin(PreprocessorPlugin):
    """A preprocessor plugin that provides the standard-level set of preprocessors.

    The preprocessors this plugin provides are:

    1. DownsamplerPreprocessor - Downsamples messages on a given list of channels.
    2. ImuRotationPreprocessor - Rotated IMU measurements from IMU to platform frame.
    3. TimeAdjusterPreprocessor - Synthesizes timestamps to compensate for erroneous hardware.
    4. BarometerToAltitudePreprocessor - Converts pressure measurements to altitude measurements.
    5. TimeBiasPreprocessor - Applies an offset to timestamps to correct for a constant time bias.
    6. OutagePreprocessor - Induces an outage on a specified channel.
    """

    mediator: Mediator | None

    def __init__(self, identifier: str) -> None:
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
            'time_bias',
            'outage',
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
                preproc_id = self.preprocessor_identifiers[preprocessor_index]
                if config_group is None:
                    self.mediator.log_message(
                        LoggingLevel.ERROR,
                        f'config_group is a required parameter for preprocessor "{preproc_id}" and cannot be None.',
                    )
                    return None

                downsampler_config = config_from_registry(
                    DownsamplerConfig, self.mediator, config_group
                )

                if downsampler_config is None:
                    self.mediator.log_message(
                        LoggingLevel.ERROR,
                        f'Failed to populate DownsamplerConfig for preprocessor {preproc_id}.',
                    )
                    return None
                return DownsamplerPreprocessor(downsampler_config, self.mediator)

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
                        f'Failed to populate ImuRotatorConfig for preprocessor {self.preprocessor_identifiers[preprocessor_index]}.',
                    )
                    return None

                return ImuRotationPreprocessor(
                    self.mediator,
                    inert_config.channel,
                    array(inert_config.C_imu_to_platform),
                )

            case 2:
                preproc_id = self.preprocessor_identifiers[preprocessor_index]
                if config_group is None:
                    self.mediator.log_message(
                        LoggingLevel.ERROR,
                        f'config_group is a required parameter for preprocessor "{preproc_id}" and cannot be None.',
                    )
                    return None

                time_adjuster_cfg = config_from_registry(
                    TimeAdjusterConfig, self.mediator, config_group
                )
                if time_adjuster_cfg is None:
                    self.mediator.log_message(
                        LoggingLevel.ERROR,
                        f'Failed to populate TimeAdjusterConfig for preprocessor {preproc_id}.',
                    )
                    return None

                return TimeAdjusterPreprocessor(time_adjuster_cfg, self.mediator)

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
                    bta_config.channel, self.mediator, bta_config.alt_sigma
                )

            case 4:
                preproc_id = self.preprocessor_identifiers[preprocessor_index]
                if config_group is None:
                    self.mediator.log_message(
                        LoggingLevel.ERROR,
                        f'config_group is a required parameter for preprocessor "{preproc_id}" and cannot be None.',
                    )
                    return None

                time_bias_cfg = config_from_registry(
                    TimeBiasConfig, self.mediator, config_group
                )
                if time_bias_cfg is None:
                    self.mediator.log_message(
                        LoggingLevel.ERROR,
                        f'Failed to populate TimeBiasConfig for preprocessor {preproc_id}.',
                    )
                    return None

                return TimeBiasPreprocessor(time_bias_cfg, self.mediator)

            case 5:
                preproc_id = self.preprocessor_identifiers[preprocessor_index]
                if config_group is None:
                    self.mediator.log_message(
                        LoggingLevel.ERROR,
                        f'config_group is a required parameter for preprocessor "{preproc_id}" and cannot be None.',
                    )
                    return None
                outage = config_from_registry(OutageConfig, self.mediator, config_group)
                if outage is None:
                    self.mediator.log_message(
                        LoggingLevel.ERROR,
                        f'Failed to populate OutageConfig for preprocessor {preproc_id}.',
                    )
                    return None
                return OutagePreprocessor(self.mediator, outage)

            case _:
                self.mediator.log_message(
                    LoggingLevel.ERROR,
                    f'Invalid preprocessor index of {preprocessor_index}. '
                    'StandardPreprocessorPlugin provides '
                    f'{len(self.preprocessor_identifiers)} preprocessors.',
                )
                return None
