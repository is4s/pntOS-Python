import numpy as np
from pntos.api import (
    LoggingLevel,
    Mediator,
    StandardFusionEngine,
    StandardStateModelProvider,
    StateModelingPlugin,
    StateModelProviderType,
    VirtualStateBlock,
)
from pntos.cobra.config import FogmConfig, ImuConfig, SensorConfig, config_from_registry

from .TutorialFogmBlock import TutorialFogmBlock
from .TutorialPinson15NedBlock import TutorialPinson15NedBlock
from .TutorialPinsonVelocityMeasurementProcessor import (
    TutorialPinsonVelocityMeasurementProcessor,
)
from .TutorialPinsonWithNedFogmPositionMeasurementProcessor import (
    TutorialPinsonWithNedFogmPositionMeasurementProcessor,
)


class TutorialGpsInsStateModelProvider(StandardStateModelProvider):
    """StandardStateModelProvider that offers a 15-state pinson state block, variable-size
    Fogm Block and various position and velocity measurement processors.
    """

    _mediator: Mediator

    def __init__(self, mediator: Mediator):
        """
        Tutorial GPS and INS State Model Provider

        Args:
            mediator (Mediator): A :class:(Mediator) instance.
        """
        self._mediator = mediator
        self.processor_identifiers: list[str] = [
            'pinson_velocity',
            'pinson_with_ned_fogm_position',
        ]
        self.block_identifiers: list[str] = ['pinson15', 'fogm']
        self.virtual_block_identifiers: list[str] = []
        """List of identifiers for virtual state blocks."""

    def new_processor(
        self,
        processor_index: int,
        engine: StandardFusionEngine | None,
        label: str,
        state_block_labels: list[str],
        config_group: str | None,
    ) -> (
        TutorialPinsonWithNedFogmPositionMeasurementProcessor
        | TutorialPinsonVelocityMeasurementProcessor
        | None
    ):
        """
        Generate a new StandardMeasurementProcessor that describes the relationship between a measurement and a set of states.

        Args:
            processor_index (int): Index into self.processor_identifiers used to select the desired type of measurement processor.
                - Index 1 corresponds to a PinsonVelocityMeasurementProcessor.
                - Index 2 corresponds to a PinsonWithNedFogmPositionMeasurementProcessor.
                - All other indices will result in a return value of None.
            engine (pntos.api.plugins.fusion.StandardFusionEngine | None): An optional parameter that may be provided to the
                new processor, such that the processor may interact with the fusion engine it
                is being used in (for example, to add/remove states). Set it to
                ``None`` when no engine is available for the processor to use.
            label (str): A string which will be used to populate the ``label`` field
                of the newly created processor. This ``label`` will be the unique
                name for the returned instance of a processor, and used to
                track the processor throughout its lifecycle. Note that it differs from
                :attr:`pntos.api.StandardStateModelProvider.processor_identifiers` which is the
                model's mechanism for selecting the *type* of processor to create.
            config_group (str): Indicates which (if any) parameter group in the
                registry may be used to obtain additional configuration values to
                generate the new processor. If the processor requires no
                outside configuration, ``config_group`` may be ``None``.

        Returns:
            StandardMeasurementProcessor | None: The newly created StandardMeasurementProcessor or ``None`` when no processor can be produced
            with the given ``processor_index``, ``engine``, and ``config_group``.
        """
        match processor_index:
            case 0:
                return TutorialPinsonVelocityMeasurementProcessor(
                    label,
                    state_block_labels,
                    self._mediator,
                )
            case 1:
                sensor_config: SensorConfig = config_from_registry(
                    SensorConfig, self._mediator, config_group
                )
                if sensor_config is None:
                    self._mediator.log_message(
                        LoggingLevel.ERROR,
                        f'Could not get position sensor config from registry.',
                    )
                    return None
                return TutorialPinsonWithNedFogmPositionMeasurementProcessor(
                    label,
                    state_block_labels,
                    self._mediator,
                    np.array(sensor_config.lever_arm),
                )

        self._mediator.log_message(
            LoggingLevel.ERROR,
            f'Invalid processor index of {processor_index}. TutorialGpsInsStateModelingProvider provides {len(self.processor_identifiers)} processors.',
        )
        return None

    def new_block(
        self,
        block_index: int,
        engine: StandardFusionEngine | None,
        label: str,
        config_group: str | None,
    ) -> TutorialPinson15NedBlock | TutorialFogmBlock | None:
        """
        Generate a new StandardStateBlock that describes a set of states and how they propagate over time.

        Args:
            block_index (int): Index into self.block_identifiers used to select the desired type of state block.

                - Index 0 corresponds to a Pinson15NedBlock.
                - Index 1 corresponds to a FogmBlock.
                - All other indices will result in a return value of None.
            engine (pntos.api.plugins.fusion.StandardFusionEngine | None): An optional parameter that may be provided to the
                new block, such that the block may interact with the fusion engine it
                is being used in (for example, to add/remove states). Set it to
                ``None`` when no engine is available for the block to use.
            label (str): A string which will be used to populate the ``label`` field
                of the newly created state block. This ``label`` will be the unique
                name for the returned instance of a state block, and used to track the state block
                throughout its lifecycle. Note that it differs from
                :attr:`pntos.api.StandardStateModelProvider.block_identifiers` which is the model's
                mechanism for selecting the *kind* of state block to create.
            config_group (str): Indicates which (if any) parameter group in the
                registry may be used to obtain additional configuration values to
                generate the new state block. If the state block requires no
                outside configuration, ``config_group`` may be ``None``.

        Returns:
            StandardStateBlock | None: The newly created StandardStateBlock or ``None`` when no state block can be produced
            with the given ``block_index``, ``engine``, and ``config_group``.
        """
        if block_index == 0:
            if config_group is None:
                self._mediator.log_message(
                    LoggingLevel.ERROR,
                    f'A config group is required for state block type {self.block_identifiers[block_index]}',
                )
                return None
            imu_config = config_from_registry(ImuConfig, self._mediator, config_group)
            if imu_config is None:
                self._mediator.log_message(
                    LoggingLevel.ERROR,
                    f'Could not get IMU config from registry.',
                )
                return None

            return TutorialPinson15NedBlock(label, self._mediator, imu_config)

        if block_index == 1:
            if config_group is None:
                self._mediator.log_message(
                    LoggingLevel.ERROR,
                    f'A config group is required for state block type {self.block_identifiers[block_index]}',
                )
                return None
            fogm_config = config_from_registry(FogmConfig, self._mediator, config_group)
            if fogm_config is None:
                self._mediator.log_message(
                    LoggingLevel.ERROR,
                    f'Could not get fogm config from registry.',
                )
                return None

            return TutorialFogmBlock(
                label,
                self._mediator,
                np.array(fogm_config.sigma),
                np.array(fogm_config.tau),
            )

        self._mediator.log_message(
            LoggingLevel.ERROR,
            f'Invalid block index of {block_index}. TutorialGpsInsStateModelingProvider provides {len(self.block_identifiers)} state blocks.',
        )
        return None

    def new_virtual_block(
        self,
        virtual_block_index: int,
        source_label: str,
        target_label: str,
        config_group: str | None,
    ) -> VirtualStateBlock | None:
        self._mediator.log_message(
            LoggingLevel.ERROR,
            f'Invalid virtual block index of {virtual_block_index}. TutorialGpsInsStateModelingProvider provides {len(self.virtual_block_identifiers)} virtual state blocks.',
        )
        return None


class TutorialGpsInsStateModelingPlugin(StateModelingPlugin):
    """StateModelingPlugin that generates a :class:`pntos.cobra.internal.TutorialGpsInsStateModelProvider`."""

    _mediator: Mediator

    def __init__(self, identifier: str):
        self.identifier = identifier

    def init_plugin(
        self,
        plugin_resources_location: str | None = None,
        mediator: Mediator | None = None,
    ) -> None:
        if mediator is not None:
            self._mediator = mediator

    def shutdown_plugin(self) -> None:
        pass

    def new_state_model_provider(
        self, fusion_type: type[StateModelProviderType]
    ) -> StateModelProviderType | None:
        if not self.is_fusion_type_supported(fusion_type):
            return None

        return TutorialGpsInsStateModelProvider(self._mediator)

    def is_fusion_type_supported(self, fusion_type: StateModelProviderType) -> bool:
        return fusion_type is StandardStateModelProvider
