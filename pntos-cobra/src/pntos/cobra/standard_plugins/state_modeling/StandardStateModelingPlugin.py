import numpy as np
from pntos import api
from pntos.api.plugins.common import LoggingLevel, Mediator
from pntos.api.plugins.fusion import StandardFusionEngine
from pntos.api.plugins.state_modeling import (
    StateModelingPlugin,
    StateModelProviderType,
    VirtualStateBlock,
)
from pntos.cobra.config import (
    ClockBiasStateBlockConfig,
    ConstantStateBlockConfig,
    FogmStateBlockConfig,
    PinsonStateBlockConfig,
    SensorMeasurementProcessorConfig,
    StateExtractorConfig,
    config_from_registry,
)

from .AltitudeMeasurementProcessor import AltitudeMeasurementProcessor
from .ClockBiasStateBlock import ClockBiasStateBlock
from .ConstantStateBlock import ConstantStateBlock
from .Direction3DToPointsMeasurementProcessor import (
    Direction3DToPointsMeasurementProcessor,
)
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
from .PositionMeasurementProcessor import PositionMeasurementProcessor
from .virtual_state_blocks.PinsonErrorToStandard import PinsonErrorToStandard
from .virtual_state_blocks.StateExtractor import StateExtractor


class StandardStateModelProvider(api.StandardStateModelProvider):
    """StandardStateModelProvider that offers a 15-state pinson state block, variable-size
    Fogm Block and various position measurement processors.
    """

    _mediator: Mediator

    def __init__(self, mediator: Mediator) -> None:
        """
        Standard Position and INS State Model Provider

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
            'position',
            'direction3D_to_points',
        ]
        self.block_identifiers: list[str] = [
            'pinson15',
            'fogm',
            'clock_bias',
            'constant',
        ]
        self.virtual_block_identifiers: list[str] = [
            'pinson_error_to_standard',
            'state_extractor',
        ]

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
        | PositionMeasurementProcessor
        | Direction3DToPointsMeasurementProcessor
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
                - Index 7 corresponds to a :class:`PositionMeasurementProcessor`.
                - Index 8 corresponds to a :class:`Direction3DToPointsMeasurementProcessor`.
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
            case 7:
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
                return PositionMeasurementProcessor(
                    label,
                    state_block_labels,
                    self._mediator,
                    np.array(sensor_mp_config.sensor_config.lever_arm),
                )

            case 8:
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
                        'Could not get direction3D to points sensor config from registry.',
                    )
                    return None
                return Direction3DToPointsMeasurementProcessor(
                    label,
                    state_block_labels,
                    self._mediator,
                    np.array(sensor_mp_config.sensor_config.lever_arm),
                    np.array(sensor_mp_config.sensor_config.orientation),
                )
        self._mediator.log_message(
            LoggingLevel.ERROR,
            f'Invalid processor index of {processor_index}. StandardStateModelProvider provides {len(self.processor_identifiers)} processors.',
        )
        return None

    def new_block(
        self,
        block_index: int,
        engine: StandardFusionEngine | None,
        label: str,
        config_group: str | None,
    ) -> Pinson15NedBlock | FogmBlock | ClockBiasStateBlock | ConstantStateBlock | None:
        """
        Generate a new StandardStateBlock that describes a set of states and how they propagate over time.

        Args:
            block_index (int): Index into self.block_identifiers used to select the desired type of state block.

                - Index 0 corresponds to a :class:`Pinson15NedBlock`.
                - Index 1 corresponds to a :class:`FogmBlock`.
                - Index 2 corresponds to a :class:`ClockBiasStateBlock`.
                - Index 3 corresponds to a :class:`ConstantStateBlock`.
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
                    label, self._mediator, sb_config.h_0, sb_config.h_neg2, sb_config.q3
                )
            case 3:
                if config_group is None:
                    self._mediator.log_message(
                        LoggingLevel.ERROR,
                        f'A config group is required for state block {self.block_identifiers[block_index]}',
                    )
                    return None
                constant_sb_config = config_from_registry(
                    ConstantStateBlockConfig, self._mediator, config_group
                )
                if constant_sb_config is None:
                    self._mediator.log_message(
                        LoggingLevel.ERROR,
                        f'Could not get config for state block "{label}" from registry.',
                    )
                    return None
                x_and_p = constant_sb_config.estimate_with_covariance
                if x_and_p is None:
                    self._mediator.log_message(
                        LoggingLevel.ERROR,
                        f'Missing initial EstimateWithCovariance for state block "{label}". Cannot initialize block.',
                    )
                    return None

                return ConstantStateBlock(
                    label,
                    self._mediator,
                    num_states=x_and_p.estimate.shape[0],
                    Q=np.array(constant_sb_config.Q),
                )

            case _:
                self._mediator.log_message(
                    LoggingLevel.ERROR,
                    f'Invalid block index of {block_index}. StandardStateModelProvider provides {len(self.block_identifiers)} state blocks.',
                )
                return None

    def new_virtual_block(
        self,
        virtual_block_index: int,
        source_label: str,
        target_label: str,
        config_group: str | None,
    ) -> VirtualStateBlock | None:
        """
        Generate a new VirtualStateBlock that converts a set of states to another representation.

        Args:
            virtual_block_index (int): Index into self.virtual_block_identifiers used to select the desired type of state block.

                - Index 0 corresponds to a :class:`PinsonErrorToStandard` VSB.
                - Index 1 corresponds to a :class:`StateExtractor` VSB.
                - All other indices will result in a return value of None.
            source_label (str): A string which will be used to populate the ``source`` field
                of the newly created virtual state block. This ``source_label`` should correspond
                to either a different 'real' or virtual state block.
            target_label (str): A string which will be used to populate the ``target`` field
                of the newly create virtual state block. This ``target`` should be unique,
                differing from all other targets on the other instances of :class:`pntos.api.VirtualStateBlock`.
            config_group (str | None): Indicates which (if any) parameter group in the
                registry may be used to obtain additional configuration values to
                generate the new virtual state block. If the state block requires no
                outside configuration, ``config_group`` may be ``None``.

        Returns:
            VirtualStateBlock | None: The newly created VirtualStateBlock or ``None`` when no virtual state block can be produced
            with the given ``block_index``, ``engine``, and ``config_group``.
        """
        match virtual_block_index:
            case 0:
                return PinsonErrorToStandard(self._mediator, source_label, target_label)
            case 1:
                if config_group is None:
                    self._mediator.log_message(
                        LoggingLevel.ERROR,
                        f'A config group is required for virtual state block {self.virtual_block_identifiers[virtual_block_index]}',
                    )
                    return None
                se_config = config_from_registry(
                    StateExtractorConfig, self._mediator, config_group
                )
                if se_config is None:
                    self._mediator.log_message(
                        LoggingLevel.ERROR,
                        'Could not get StateExtractorConfig from registry.',
                    )
                    return None
                return StateExtractor(
                    self._mediator,
                    source_label,
                    target_label,
                    se_config.incoming_state_size,
                    list(se_config.indices_to_extract),
                )

        self._mediator.log_message(
            LoggingLevel.ERROR,
            f'Invalid virtual block index of {virtual_block_index}. StandardStateModelProvider provides {len(self.virtual_block_identifiers)} virtual state blocks.',
        )
        return None


class StandardStateModelingPlugin(StateModelingPlugin):
    """StateModelingPlugin that generates a :class:`pntos.cobra.internal.StandardStateModelProvider`."""

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

        return StandardStateModelProvider(self._mediator)

    def is_fusion_type_supported(self, type: StateModelProviderType) -> bool:
        return type is api.StandardStateModelProvider
