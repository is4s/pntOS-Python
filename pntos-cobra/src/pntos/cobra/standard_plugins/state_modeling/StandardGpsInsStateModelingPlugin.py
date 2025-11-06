import numpy as np
from pntos.api.plugins.common import LoggingLevel, Mediator
from pntos.api.plugins.fusion import StandardFusionEngine
from pntos.api.plugins.state_modeling import (
    StandardStateModelProvider,
    StateModelingPlugin,
    StateModelProviderType,
    VirtualStateBlock,
)
from pntos.cobra.config import (
    ClockBiasStateBlockConfig,
    FogmStateBlockConfig,
    PinsonStateBlockConfig,
    SensorMeasurementProcessorConfig,
    config_from_registry,
)

from .AltitudeMeasurementProcessor import AltitudeMeasurementProcessor
from .ClockBiasStateBlock import ClockBiasStateBlock
from .FogmBlock import FogmBlock
from .Pinson15NedBlock import Pinson15NedBlock
from .PinsonBodyVelocityMeasurementProcessor import (
    PinsonBodyVelocityMeasurementProcessor,
)
from .PinsonPositionMeasurementProcessor import PinsonPositionMeasurementProcessor
from .PinsonPosVelMeasurementProcessor import PinsonPosVelMeasurementProcessor
from .PinsonVelocityMeasurementProcessor import PinsonVelocityMeasurementProcessor
from .PinsonWithLeverArmPositionMeasurementProcessor import (
    PinsonWithLeverArmPositionMeasurementProcessor,
)
from .PinsonWithNedFogmPositionMeasurementProcessor import (
    PinsonWithNedFogmPositionMeasurementProcessor,
)


class StandardGpsInsStateModelProvider(StandardStateModelProvider):
    """StandardStateModelProvider that offers a 15-state pinson state block, variable-size
    Fogm Block and various position measurement processors.
    """

    _mediator: Mediator

    def __init__(self, mediator: Mediator) -> None:
        """
        Standard GPS and INS State Model Provider

        Args:
            mediator (Mediator): A :class:(Mediator) instance.
        """
        self._mediator = mediator
        self.processor_identifiers: list[str] = [
            'pinson_position',
            'pinson_velocity',
            'pinson_with_ned_fogm_position',
            'pinson_altitude',
            'pinson_with_lever_arm_position',
            'pinson_body_velocity',
            'pinson_posvel',
        ]
        self.block_identifiers: list[str] = ['pinson15', 'fogm', 'clock_bias']
        self.virtual_block_identifiers = None

    def new_processor(
        self,
        processor_index: int,
        engine: StandardFusionEngine | None,
        label: str,
        state_block_labels: list[str],
        config_group: str | None,
    ) -> (
        PinsonPositionMeasurementProcessor
        | PinsonWithNedFogmPositionMeasurementProcessor
        | PinsonVelocityMeasurementProcessor
        | AltitudeMeasurementProcessor
        | PinsonWithLeverArmPositionMeasurementProcessor
        | PinsonBodyVelocityMeasurementProcessor
        | PinsonPosVelMeasurementProcessor
        | None
    ):
        """
        Generate a new StandardMeasurementProcessor that describes the relationship between a measurement and a set of states.

        Args:
            processor_index (int): Index into self.processor_identifiers used to select the desired type of measurement processor.

                - Index 0 corresponds to a :class:`PinsonPositionMeasurementProcessor`.
                - Index 1 corresponds to a :class:`PinsonVelocityMeasurementProcessor`.
                - Index 2 corresponds to a :class:`PinsonWithNedFogmPositionMeasurementProcessor`.
                - Index 3 corresponds to a :class:`AltitudeMeasurementProcessor`.
                - Index 4 corresponds to a :class:`PinsonWithLeverArmPositionMeasurementProcessor`.
                - Index 5 corresponds to a :class:`PinsonBodyVelocityMeasurementProcessor`.
                - Index 6 corresponds to a :class:`PinsonPosVelMeasurementProcessor`.
                - All other indices will result in a return value of None.
            engine (StandardFusionEngine | None): An optional parameter that may be provided to the
                new processor, such that the processor may interact with the fusion engine it
                is being used in (for example, to add/remove states). Set it to
                ``None`` when no engine is available for the processor to use.
            label (str): A string which will be used to populate the ``label`` field
                of the newly created processor. This ``label`` will be the unique
                name for the returned instance of a processor, and used to
                track the processor throughout its lifecycle. Note that it differs from
                :attr:`pntos.api.StandardStateModelProvider.processor_identifiers` which is the
                model's mechanism for selecting the *type* of processor to create.
            state_block_labels (list[str]): A list of strings which will be used to
                populate the ``state_block_labels`` field of the newly created
                processor.
            config_group (str | None): Indicates which (if any) parameter group in the
                registry may be used to obtain additional configuration values to
                generate the new processor. If the processor requires no
                outside configuration, ``config_group`` may be ``None``.

        Returns:
            StandardMeasurementProcessor | None: The newly created StandardMeasurementProcessor or ``None`` when no processor can be produced
            with the given ``processor_index``, ``engine``, and ``config_group``.
        """
        match processor_index:
            case 0:
                if config_group is None:
                    self._mediator.log_message(
                        LoggingLevel.ERROR,
                        f'A config group is required for processor {self.processor_identifiers[processor_index]}',
                    )
                    return None
                sensor_mp_config = config_from_registry(
                    SensorMeasurementProcessorConfig, self._mediator, config_group
                )
                if sensor_mp_config is None:
                    self._mediator.log_message(
                        LoggingLevel.ERROR,
                        'Could not get position sensor config from registry.',
                    )
                    return None
                return PinsonPositionMeasurementProcessor(
                    label,
                    state_block_labels,
                    self._mediator,
                    np.array(sensor_mp_config.sensor_config.lever_arm),
                )
            case 1:
                return PinsonVelocityMeasurementProcessor(
                    label,
                    state_block_labels,
                    self._mediator,
                )
            case 2:
                if config_group is None:
                    self._mediator.log_message(
                        LoggingLevel.ERROR,
                        f'A config group is required for processor {self.processor_identifiers[processor_index]}',
                    )
                    return None
                sensor_mp_config = config_from_registry(
                    SensorMeasurementProcessorConfig, self._mediator, config_group
                )
                if sensor_mp_config is None:
                    self._mediator.log_message(
                        LoggingLevel.ERROR,
                        'Could not get position sensor config from registry.',
                    )
                    return None
                return PinsonWithNedFogmPositionMeasurementProcessor(
                    label,
                    state_block_labels,
                    self._mediator,
                    np.array(sensor_mp_config.sensor_config.lever_arm),
                )
            case 3:
                return AltitudeMeasurementProcessor(
                    label,
                    state_block_labels,
                    self._mediator,
                )
            case 4:
                if config_group is None:
                    self._mediator.log_message(
                        LoggingLevel.ERROR,
                        f'A config group is required for processor type {self.processor_identifiers[processor_index]}',
                    )
                    return None
                sensor_config = config_from_registry(
                    SensorMeasurementProcessorConfig, self._mediator, config_group
                )
                if sensor_config is None:
                    self._mediator.log_message(
                        LoggingLevel.ERROR,
                        'Could not get position sensor config from registry.',
                    )
                    return None
                return PinsonWithLeverArmPositionMeasurementProcessor(
                    label,
                    state_block_labels,
                    self._mediator,
                    np.array(sensor_config.sensor_config.lever_arm),
                )
            case 5:
                if config_group is None:
                    self._mediator.log_message(
                        LoggingLevel.ERROR,
                        f'A config group is required for processor {self.processor_identifiers[processor_index]}',
                    )
                    return None
                sensor_mp_config = config_from_registry(
                    SensorMeasurementProcessorConfig, self._mediator, config_group
                )
                if sensor_mp_config is None:
                    self._mediator.log_message(
                        LoggingLevel.ERROR,
                        'Could not get body velocity sensor config from registry.',
                    )
                    return None
                return PinsonBodyVelocityMeasurementProcessor(
                    label,
                    state_block_labels,
                    self._mediator,
                    np.array(sensor_mp_config.sensor_config.lever_arm),
                    np.array(sensor_mp_config.sensor_config.orientation),
                )
            case 6:
                if config_group is None:
                    self._mediator.log_message(
                        LoggingLevel.ERROR,
                        f'A config group is required for processor {self.processor_identifiers[processor_index]}',
                    )
                    return None
                sensor_mp_config = config_from_registry(
                    SensorMeasurementProcessorConfig, self._mediator, config_group
                )
                if sensor_mp_config is None:
                    self._mediator.log_message(
                        LoggingLevel.ERROR,
                        'Could not get position sensor config from registry.',
                    )
                    return None
                return PinsonPosVelMeasurementProcessor(
                    label,
                    state_block_labels,
                    self._mediator,
                    np.array(sensor_mp_config.sensor_config.lever_arm),
                )
        self._mediator.log_message(
            LoggingLevel.ERROR,
            f'Invalid processor index of {processor_index}. StandardGpsInsStateModelProvider provides {len(self.processor_identifiers)} processors.',
        )
        return None

    def new_block(
        self,
        block_index: int,
        engine: StandardFusionEngine | None,
        label: str,
        config_group: str | None,
    ) -> Pinson15NedBlock | FogmBlock | ClockBiasStateBlock | None:
        """
        Generate a new StandardStateBlock that describes a set of states and how they propagate over time.

        Args:
            block_index (int): Index into self.block_identifiers used to select the desired type of state block.

                - Index 0 corresponds to a Pinson15NedBlock.
                - Index 1 corresponds to a FogmBlock.
                - Index 2 corresponds to a ClockBiasStateBlock.
                - All other indices will result in a return value of None.
            engine (StandardFusionEngine | None): An optional parameter that may be provided to the
                new block, such that the block may interact with the fusion engine it
                is being used in (for example, to add/remove states). Set it to
                ``None`` when no engine is available for the block to use.
            label (str): A string which will be used to populate the ``label`` field
                of the newly created state block. This ``label`` will be the unique
                name for the returned instance of a state block, and used to track the state block
                throughout its lifecycle. Note that it differs from
                :attr:`pntos.api.StandardStateModelProvider.block_identifiers` which is the model's
                mechanism for selecting the *kind* of state block to create.
            config_group (str | None): Indicates which (if any) parameter group in the
                registry may be used to obtain additional configuration values to
                generate the new state block. If the state block requires no
                outside configuration, ``config_group`` may be ``None``.

        Returns:
            StandardStateBlock | None: The newly created StandardStateBlock or ``None`` when no state block can be produced
            with the given ``block_index``, ``engine``, and ``config_group``.
        """
        match block_index:
            case 0:
                if config_group is None:
                    self._mediator.log_message(
                        LoggingLevel.ERROR,
                        f'A config group is required for state block {self.block_identifiers[block_index]}',
                    )
                    return None
                pinson_sb_config = config_from_registry(
                    PinsonStateBlockConfig, self._mediator, config_group
                )
                if pinson_sb_config is None:
                    self._mediator.log_message(
                        LoggingLevel.ERROR,
                        'Could not get IMU config from registry.',
                    )
                    return None

                return Pinson15NedBlock(
                    label, self._mediator, pinson_sb_config.imu_model
                )

            case 1:
                if config_group is None:
                    self._mediator.log_message(
                        LoggingLevel.ERROR,
                        f'A config group is required for state block {self.block_identifiers[block_index]}',
                    )
                    return None
                fogm_sb_config = config_from_registry(
                    FogmStateBlockConfig, self._mediator, config_group
                )
                if fogm_sb_config is None:
                    self._mediator.log_message(
                        LoggingLevel.ERROR,
                        'Could not get fogm config from registry.',
                    )
                    return None

                return FogmBlock(
                    label,
                    self._mediator,
                    np.array(fogm_sb_config.fogm_model.sigma),
                    np.array(fogm_sb_config.fogm_model.tau),
                )

            case 2:
                if config_group is None:
                    self._mediator.log_message(
                        LoggingLevel.ERROR,
                        f'A config group is required for state block {self.block_identifiers[block_index]}',
                    )
                    return None
                sb_config = config_from_registry(
                    ClockBiasStateBlockConfig, self._mediator, config_group
                )
                if sb_config is None:
                    self._mediator.log_message(
                        LoggingLevel.ERROR,
                        f'Could not get config for state block "{label}" from registry.',
                    )
                    return None

                return ClockBiasStateBlock(
                    self._mediator, sb_config.h_0, sb_config.h_neg2, sb_config.q3
                )

            case _:
                self._mediator.log_message(
                    LoggingLevel.ERROR,
                    f'Invalid block index of {block_index}. StandardGpsInsStateModelProvider provides {len(self.block_identifiers)} state blocks.',
                )
                return None

    def new_virtual_block(
        self,
        virtual_block_index: int,
        source_label: str,
        target_label: str,
        config_group: str | None,
    ) -> VirtualStateBlock | None:
        if self.virtual_block_identifiers is None:
            virtual_block_count = 0
        else:
            virtual_block_count = len(self.virtual_block_identifiers)

        self._mediator.log_message(
            LoggingLevel.ERROR,
            f'Invalid virtual block index of {virtual_block_index}. StandardGpsInsStateModelProvider provides {virtual_block_count} virtual state blocks.',
        )
        return None


class StandardGpsInsStateModelingPlugin(StateModelingPlugin):
    """StateModelingPlugin that generates a :class:`pntos.cobra.internal.StandardGpsInsStateModelProvider`."""

    _mediator: Mediator

    def __init__(self, identifier: str) -> None:
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
        self, type: type[StateModelProviderType]
    ) -> StateModelProviderType | None:
        if not self.is_fusion_type_supported(type):
            return None

        return StandardGpsInsStateModelProvider(self._mediator)

    def is_fusion_type_supported(self, type: StateModelProviderType) -> bool:
        return type is StandardStateModelProvider
