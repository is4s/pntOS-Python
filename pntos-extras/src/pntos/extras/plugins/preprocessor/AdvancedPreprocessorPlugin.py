from pntos.api import (
    LoggingLevel,
    Mediator,
    Preprocessor,
    PreprocessorPlugin,
)
from pntos.cobra.config import config_from_registry
from pntos.extras.config import ZeroVelocity2dGeneratorConfig
from typing_extensions import override

from .ZeroVelocity2dGenerator import ZeroVelocity2dGenerator


class AdvancedPreprocessorPlugin(PreprocessorPlugin):
    """A preprocessor plugin that provides an advanced set of preprocessors.

    The preprocessors this plugin provides are:

    1. ZeroVelocity2dGenerator - Generates 2-D zero-velocity measurements based on the assumption that a ground vehicle does not slide laterally or lift off of the ground.
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
            ZeroVelocity2dGeneratorConfig.identifier,
        ]

    @override
    def init_plugin(
        self,
        plugin_resources_location: str | None = None,
        mediator: Mediator | None = None,
    ) -> None:
        if mediator is None:
            print('Error: mediator cannot be None')
        self.mediator = mediator

    @override
    def shutdown_plugin(self) -> None:
        pass

    @override
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
                velocity_generator_cfg = config_from_registry(
                    ZeroVelocity2dGeneratorConfig, self.mediator, config_group
                )
                if velocity_generator_cfg is None:
                    self.mediator.log_message(
                        LoggingLevel.ERROR,
                        f'Failed to populate ZeroVelocity2dGeneratorConfig for preprocessor {preproc_id}.',
                    )
                    return None

                channels = velocity_generator_cfg.channels
                dt = velocity_generator_cfg.trigger_dt_sec

                return ZeroVelocity2dGenerator(
                    self.mediator,
                    channels,
                    dt,
                    velocity_generator_cfg.lateral_vel_sigma,
                    velocity_generator_cfg.vertical_vel_sigma,
                    velocity_generator_cfg.output_channel,
                )

            case _:
                self.mediator.log_message(
                    LoggingLevel.ERROR,
                    f'Invalid preprocessor index of {preprocessor_index}. '
                    'PreprocessorPlugin provides '
                    f'{len(self.preprocessor_identifiers)} preprocessors.',
                )
                return None
