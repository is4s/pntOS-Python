from dataclasses import dataclass, field

from pntos.api import EstimateWithCovariance

from .BaseConfig import BaseConfig
from .FogmConfig import FogmConfig
from .ImuConfig import ImuConfig
from .InertialConfig import InertialConfig
from .PreprocessorConfig import PreprocessorConfig
from .VirtualStateBlockConfig import VirtualStateBlockConfig


@dataclass(kw_only=True)
class StateBlockConfig(BaseConfig):
    """
    Configuration used to generate a new state block.
    """

    group: str

    identifier: str
    """
    An identifier that determines the type of state block to use.

    This field will be matched against the `block_identifiers` field on the state model provider.
    """

    label: str
    """
    The name used to identify and track this state block through its lifecycle.

    This value should be unique from all other `pntos.cobra.config.StateBlockConfig.label`
    and `pntos.cobra.config.VirtualStateBlockConfig.target` values.
    """

    estimate_with_covariance: EstimateWithCovariance | None = None
    """
    An optional field that allows an initial estimate and covariance to be associated with the state block.
    """

    aux_channels: tuple[str, ...] | None = None
    """
    Optional channels to map to this state block's `receive_aux_data` method.
    """


@dataclass(kw_only=True)
class PinsonStateBlockConfig(StateBlockConfig):
    """
    Configuration used to generate a new pinson state block.
    """

    # INHERITED FIELDS
    group: str

    identifier: str = field(default='pinson15', init=False)

    label: str

    estimate_with_covariance: EstimateWithCovariance | None = None

    aux_channels: tuple[str, ...] | None = field(default=None, init=False)

    # UNIQUE FIELDS
    imu_model: ImuConfig
    """
    A nested config that contains information about the IMU model.

    See ImuConfig.py for more information.
    """


@dataclass(kw_only=True)
class FogmStateBlockConfig(StateBlockConfig):
    """
    Configuration used to generate a new FOGM state block.
    """

    # INHERITED FIELDS
    group: str

    identifier: str = field(default='fogm', init=False)

    label: str

    estimate_with_covariance: EstimateWithCovariance  # not optional on this block

    aux_channels: tuple[str, ...] | None = field(default=None, init=False)

    # UNIQUE FIELDS
    fogm_model: FogmConfig
    """
    A nested config that contains information about the FOGM model.

    See FogmConfig.py for more information.
    """


@dataclass
class MeasurementProcessorConfig(BaseConfig):
    """
    Configuration used to generate a new measurement processor.
    """

    group: str

    identifier: str
    """
    An identifier that determines the type of measurement processor to use.

    This field will be matched against the `processor_identifiers` field on the state model provider.
    """

    label: str
    """
    The name used to identify and track this processor through its lifecycle.
    """

    state_block_labels: tuple[str, ...]
    """
    The labels of the state blocks this measurement processor will use.
    """

    channel: str
    """
    The name of the channel from which the measurements originate.

    This corresponds to the `source_identifier` field on the ``pntos.api.Message`` class.
    """

    aux_channels: tuple[str, ...] | None = None
    """
    Optional channels to map to this measurement processor's `receive_aux_data` method.

    The following channel strings are reserved:
        - INERTIAL_PVA: Should be added to `aux_channels` if this measurement processor needs the inertial PVA as aux data.
        - INERTIAL_FORCES_AND_RATES: Should be added to `aux_channels` if this measurement processor needs the inertial forces and/or rates as aux data.
    """


@dataclass(kw_only=True)
class PinsonPositionMPConfig(MeasurementProcessorConfig):
    """
    Configuration for a PinsonPositionMeasurementProcessor.

    This MP relates 3-D position measurements to a PinsonStateBlock modeling inertial
    error-states.

    Attributes:
        group:
            Inherited from MeasurementProcessorConfig. The registry group in which to
            store this config.
        identifier (str):
            Inherited from MeasurementProcessorConfig. The identifier associated with
            the type of measurement processor to use. This field is set to a constant
            value of `pinson_position`, the identifier used to select the
            PinsonPositionMeasurementProcessor in the StandardStateModelingPlugin.
        label:
            Inherited from MeasurementProcessorConfig. The unique label to associate
            with the instance of PinsonPositionMeasurementProcessor added to the fusion
            engine.
        channel:
            Inherited from MeasurementProcessorConfig. The name of the channel from
            which the position measurements originate. This corresponds to the
            `source_identifier` field on the ``pntos.api.Message`` class.
        state_block_labels:
            Inherited from MeasurementProcessorConfig. The labels of the state blocks
            this measurement processor will use. This should be a single
            PinsonStateBlock.
        aux_channels:
            Inherited from MeasurementProcessorConfig. Optional channels to map to this
            measurement processor's `receive_aux_data` method. This field is set to a
            constant value of `('INERTIAL_PVA',)`, since this MP requires inertial PVA
            aux data.
        lever_arm:
            The 3-D vector from the platform frame to the sensor frame, in the platform
            frame (m).
    """

    # INHERITED FIELDS
    group: str

    identifier: str = field(default='pinson_position', init=False)

    label: str

    channel: str

    state_block_labels: tuple[str, ...]

    aux_channels: tuple[str, ...] | None = field(default=('INERTIAL_PVA',), init=False)

    # UNIQUE FIELDS
    lever_arm: tuple[float, float, float]


@dataclass(kw_only=True)
class PinsonWithNedFogmPositionMPConfig(MeasurementProcessorConfig):
    """
    Configuration for a PinsonWithNedFogmPositionMeasurementProcessor.

    This MP relates 3-D position measurements to a PinsonStateBlock modeling inertial
    error-states and a 3-state FogmStateBlock modeling time-correlated NED position
    measurement errors.

    Attributes:
        group:
            Inherited from MeasurementProcessorConfig. The registry group in which to
            store this config.
        identifier (str):
            Inherited from MeasurementProcessorConfig. The identifier associated with
            the type of measurement processor to use. This field is set to a constant
            value of `pinson_with_ned_fogm_position`, the identifier used to select the
            PinsonWithNedFogmPositionMeasurementProcessor in the StandardStateModelingPlugin.
        label:
            Inherited from MeasurementProcessorConfig. The unique label to associate
            with the instance of PinsonWithNedFogmPositionMeasurementProcessor added to
            the fusion engine.
        channel:
            Inherited from MeasurementProcessorConfig. The name of the channel from
            which the position measurements originate. This corresponds to the
            `source_identifier` field on the ``pntos.api.Message`` class.
        state_block_labels:
            Inherited from MeasurementProcessorConfig. The labels of the state blocks
            this measurement processor will use. The first should refer to a
            PinsonStateBlock and the second should refer to a 3-state FogmStateBlock
            estimating NED position measurement errors.
        aux_channels:
            Inherited from MeasurementProcessorConfig. Optional channels to map to this
            measurement processor's `receive_aux_data` method. This field is set to a
            constant value of `('INERTIAL_PVA',)`, since this MP requires inertial PVA
            aux data.
        lever_arm:
            The 3-D vector from the platform frame to the sensor frame, in the platform
            frame (m).
    """

    # INHERITED FIELDS
    group: str

    identifier: str = field(default='pinson_with_ned_fogm_position', init=False)

    label: str

    channel: str

    state_block_labels: tuple[str, ...]

    aux_channels: tuple[str, ...] | None = field(default=('INERTIAL_PVA',), init=False)

    # UNIQUE FIELDS
    lever_arm: tuple[float, float, float]


@dataclass(kw_only=True)
class PinsonWithLeverArmPositionMPConfig(MeasurementProcessorConfig):
    """
    Configuration for a PinsonWithLeverArmPositionMeasurementProcessor.

    This MP relates 3-D position measurements to a PinsonStateBlock modeling inertial
    error-states, a 3-state FogmStateBlock modeling time-correlated NED position
    measurement errors, and an additional 3-state FogmStateBlock modeling error in the
    nominal lever arm.

    Attributes:
        group:
            Inherited from MeasurementProcessorConfig. The registry group in which to
            store this config.
        identifier (str):
            Inherited from MeasurementProcessorConfig. The identifier associated with
            the type of measurement processor to use. This field is set to a constant
            value of `pinson_with_lever_arm_position`, the identifier used to select the
            PinsonWithLeverArmPositionMeasurementProcessor in the StandardStateModelingPlugin.
        label:
            Inherited from MeasurementProcessorConfig. The unique label to associate
            with the instance of PinsonPositionMeasurementProcessor added to the fusion
            engine.
        channel:
            Inherited from MeasurementProcessorConfig. The name of the channel from
            which the position measurements originate. This corresponds to the
            `source_identifier` field on the ``pntos.api.Message`` class.
        state_block_labels:
            Inherited from MeasurementProcessorConfig. The labels of the state blocks
            this measurement processor will use. The first should refer to a
            PinsonStateBlock, the second to a 3-state FogmStateBlock estimating NED
            position measurement errors, and the third to an additional 3-state
            FogmStateBlock estimating error in the nominal lever arm.
        aux_channels:
            Inherited from MeasurementProcessorConfig. Optional channels to map to this
            measurement processor's `receive_aux_data` method. This field is set to a
            constant value of `('INERTIAL_PVA',)`, since this MP requires inertial PVA
            aux data.
        lever_arm:
            The 3-D vector from the platform frame to the sensor frame, in the platform
            frame (m).
    """

    # INHERITED FIELDS
    group: str

    identifier: str = field(default='pinson_with_lever_arm_position', init=False)

    label: str

    channel: str

    state_block_labels: tuple[str, ...]

    aux_channels: tuple[str, ...] | None = field(default=('INERTIAL_PVA',), init=False)

    # UNIQUE FIELDS
    lever_arm: tuple[float, float, float]


@dataclass(kw_only=True)
class PosVelMPConfig(MeasurementProcessorConfig):
    """
    Configuration for a PosVelMeasurementProcessor.

    This MP relates PVA measurements containing 3-D LLH position and 3-D NED velocity to
    a PinsonStateBlock modeling inertial error-states.

    Attributes:
        group:
            Inherited from MeasurementProcessorConfig. The registry group in which to
            store this config.
        identifier (str):
            Inherited from MeasurementProcessorConfig. The identifier associated with
            the type of measurement processor to use. This field is set to a constant
            value of `pinson_posvel`, the identifier used to select the
            PosVelMeasurementProcessor in the StandardStateModelingPlugin.
        label:
            Inherited from MeasurementProcessorConfig. The unique label to associate
            with the instance of PinsonPositionMeasurementProcessor added to the fusion
            engine.
        channel:
            Inherited from MeasurementProcessorConfig. The name of the channel from
            which the PVA measurements originate. This corresponds to the
            `source_identifier` field on the ``pntos.api.Message`` class.
        state_block_labels:
            Inherited from MeasurementProcessorConfig. The labels of the state blocks
            this measurement processor will use. This should be a single
            PinsonStateBlock.
        aux_channels:
            Inherited from MeasurementProcessorConfig. Optional channels to map to this
            measurement processor's `receive_aux_data` method. This field is set to a
            constant value of `('INERTIAL_PVA',)`, since this MP requires inertial PVA
            aux data.
        lever_arm:
            The 3-D vector from the platform frame to the sensor frame, in the platform
            frame (m).
    """

    # INHERITED FIELDS
    group: str

    identifier: str = field(default='pinson_posvel', init=False)

    label: str

    channel: str

    state_block_labels: tuple[str, ...]

    aux_channels: tuple[str, ...] | None = field(default=('INERTIAL_PVA',), init=False)

    # UNIQUE FIELDS
    lever_arm: tuple[float, float, float]


@dataclass(kw_only=True)
class PinsonVelocityMPConfig(MeasurementProcessorConfig):
    """
    Configuration for a PinsonVelocityMeasurementProcessor.

    This MP relates NED velocity measurements to a PinsonStateBlock modeling inertial
    error-states.

    Attributes:
        group:
            Inherited from MeasurementProcessorConfig. The registry group in which to
            store this config.
        identifier (str):
            Inherited from MeasurementProcessorConfig. The identifier associated with
            the type of measurement processor to use. This field is set to a constant
            value of `pinson_velocity`, the identifier used to select the
            PinsonVelocityMeasurementProcessor in the StandardStateModelingPlugin.
        label:
            Inherited from MeasurementProcessorConfig. The unique label to associate
            with the instance of PinsonPositionMeasurementProcessor added to the fusion
            engine.
        channel:
            Inherited from MeasurementProcessorConfig. The name of the channel from
            which the velocity measurements originate. This corresponds to the
            `source_identifier` field on the ``pntos.api.Message`` class.
        state_block_labels:
            Inherited from MeasurementProcessorConfig. The labels of the state blocks
            this measurement processor will use. This should be a single
            PinsonStateBlock.
        aux_channels:
            Inherited from MeasurementProcessorConfig. Optional channels to map to this
            measurement processor's `receive_aux_data` method. This field is set to a
            constant value of `('INERTIAL_PVA',)`, since this MP requires inertial PVA
            aux data.
    """

    # INHERITED FIELDS
    group: str

    identifier: str = field(default='pinson_velocity', init=False)

    label: str

    channel: str

    state_block_labels: tuple[str, ...]

    aux_channels: tuple[str, ...] | None = field(default=('INERTIAL_PVA',), init=False)


@dataclass(kw_only=True)
class PinsonBodyVelocityMPConfig(MeasurementProcessorConfig):
    """
    Configuration for a PinsonBodyVelocityMeasurementProcessor.

    This MP relates sensor-frame velocity measurements to a PinsonStateBlock modeling
    inertial error-states.

    Attributes:
        group:
            Inherited from MeasurementProcessorConfig. The registry group in which to
            store this config.
        label:
            Inherited from MeasurementProcessorConfig. The unique label to associate
            with the instance of PinsonPositionMeasurementProcessor added to the fusion
            engine.
        identifier (str):
            Inherited from MeasurementProcessorConfig. The identifier associated with
            the type of measurement processor to use. This field is set to a constant
            value of `pinson_body_velocity`, the identifier used to select the
            PinsonBodyVelocityMeasurementProcessor in the StandardStateModelingPlugin.
        channel:
            Inherited from MeasurementProcessorConfig. The name of the channel from
            which the velocity measurements originate. This corresponds to the
            `source_identifier` field on the ``pntos.api.Message`` class.
        state_block_labels:
            Inherited from MeasurementProcessorConfig. The labels of the state blocks
            this measurement processor will use. This should be a single
            PinsonStateBlock.
        aux_channels:
            Inherited from MeasurementProcessorConfig. Optional channels to map to this
            measurement processor's `receive_aux_data` method. This field is set to a
            constant value of `('INERTIAL_PVA', 'INERTIAL_FORCES_AND_RATES')`, since
            this MP requires inertial PVA and rate aux data.
        lever_arm:
            The 3-D vector from the platform frame to the sensor frame, in the platform
            frame (m).
        orientation:
            A quaternion representing the rotational difference from the platform frame
            to the sensor frame. The corresponding DCM would be C_platform_to_sensor.
    """

    # INHERITED FIELDS
    group: str

    identifier: str = field(default='pinson_body_velocity', init=False)

    label: str

    channel: str

    state_block_labels: tuple[str, ...]

    aux_channels: tuple[str, ...] | None = field(
        default=('INERTIAL_PVA', 'INERTIAL_FORCES_AND_RATES'), init=False
    )

    lever_arm: tuple[float, float, float]

    orientation: tuple[float, float, float, float]


@dataclass(kw_only=True)
class AltitudeMPConfig(MeasurementProcessorConfig):
    """
    Configuration for a AltitudeMeasurementProcessor.

    This MP relates altitude measurements to a PinsonStateBlock modeling inertial
    error-states and a 1-state FogmStateBlock modeling time-correlated altitude
    measurement errors.

    Attributes:
        group:
            Inherited from MeasurementProcessorConfig. The registry group in which to
            store this config.
        identifier (str):
            Inherited from MeasurementProcessorConfig. The identifier associated with
            the type of measurement processor to use. This field is set to a constant
            value of `pinson_altitude`, the identifier used to select the
            AltitudeMeasurementProcessor in the StandardStateModelingPlugin.
        label:
            Inherited from MeasurementProcessorConfig. The unique label to associate
            with the instance of AltitudeMeasurementProcessor added to the fusion
            engine.
        channel:
            Inherited from MeasurementProcessorConfig. The name of the channel from
            which the altitude measurements originate. This corresponds to the
            `source_identifier` field on the ``pntos.api.Message`` class.
        state_block_labels:
            Inherited from MeasurementProcessorConfig. The labels of the state blocks
            this measurement processor will use. The first should refer to a
            PinsonStateBlock and the second should refer to a 1-state FogmStateBlock
            estimating altitude measurement errors.
        aux_channels:
            Inherited from MeasurementProcessorConfig. Optional channels to map to this
            measurement processor's `receive_aux_data` method. This field is set to a
            constant value of `('INERTIAL_PVA',)`, since this MP requires inertial PVA
            aux data.
    """

    # INHERITED FIELDS
    group: str

    identifier: str = field(default='pinson_altitude', init=False)

    label: str

    channel: str

    state_block_labels: tuple[str, ...]

    aux_channels: tuple[str, ...] | None = field(default=('INERTIAL_PVA',), init=False)


@dataclass(kw_only=True)
class Direction3dToPointsMPConfig(MeasurementProcessorConfig):
    """
    Configuration for a Direction3DToPointsMeasurementProcessor.

    This MP relates direction3d-to-points measurements to a PinsonStateBlock modeling inertial
    error-states.

    Attributes:
        group:
            Inherited from MeasurementProcessorConfig. The registry group in which to
            store this config.
        identifier (str):
            Inherited from MeasurementProcessorConfig. The identifier associated with
            the type of measurement processor to use. This field is set to a constant
            value of `direction3D_to_points`, the identifier used to select the
            Direction3DToPointsMeasurementProcessor in the StandardStateModelingPlugin.
        label:
            Inherited from MeasurementProcessorConfig. The unique label to associate
            with the instance of Direction3DToPointsMeasurementProcessor added to the fusion
            engine.
        channel:
            Inherited from MeasurementProcessorConfig. The name of the channel from
            which the direction3d-to-points measurements originate. This corresponds to the
            `source_identifier` field on the ``pntos.api.Message`` class.
        state_block_labels:
            Inherited from MeasurementProcessorConfig. The labels of the state blocks
            this measurement processor will use. This should be a single
            PinsonStateBlock.
        aux_channels:
            Inherited from MeasurementProcessorConfig. Optional channels to map to this
            measurement processor's `receive_aux_data` method. This field is set to a
            constant value of `('INERTIAL_PVA',)`, since this MP requires inertial PVA
            aux data.
        lever_arm:
            The 3-D vector from the platform frame to the sensor frame, in the platform
            frame (m).
        orientation:
            A quaternion representing the rotational difference from the platform frame
            to the sensor frame. The corresponding DCM would be C_platform_to_sensor.
    """

    # INHERITED FIELDS
    group: str

    identifier: str = field(default='direction3D_to_points', init=False)

    label: str

    channel: str

    state_block_labels: tuple[str, ...]

    aux_channels: tuple[str, ...] | None = field(default=('INERTIAL_PVA',), init=False)

    lever_arm: tuple[float, float, float]

    orientation: tuple[float, float, float, float]


@dataclass(kw_only=True)
class PositionMPConfig(MeasurementProcessorConfig):
    """
    Configuration for a PositionMeasurementProcessor.

    This MP relates 3-D position measurements to a state block that estimates position
    and a 3-state FogmStateBlock modeling time-correlated NED position measurement
    errors.

    Attributes:
        group:
            Inherited from MeasurementProcessorConfig. The registry group in which to
            store this config.
        identifier (str):
            Inherited from MeasurementProcessorConfig. The identifier associated with
            the type of measurement processor to use. This field is set to a constant
            value of `position`, the identifier used to select the
            PositionMeasurementProcessor in the StandardStateModelingPlugin.
        label:
            Inherited from MeasurementProcessorConfig. The unique label to associate
            with the instance of PositionMeasurementProcessor added to the fusion
            engine.
        channel:
            Inherited from MeasurementProcessorConfig. The name of the channel from
            which the position measurements originate. This corresponds to the
            `source_identifier` field on the ``pntos.api.Message`` class.
        state_block_labels:
            Inherited from MeasurementProcessorConfig. The labels of the state blocks
            this measurement processor will use. The first should refer to a state block
            where the first 3 states model LLH position and the second should refer to a
            3-state FogmStateBlock estimating NED position measurement errors.
        aux_channels:
            Inherited from MeasurementProcessorConfig. Optional channels to map to this
            measurement processor's `receive_aux_data` method. This field is set to a
            constant value of None, since this MP requires no aux data.
        lever_arm:
            The 3-D vector from the platform frame to the sensor frame, in the platform
            frame (m).
    """

    # INHERITED FIELDS
    group: str

    identifier: str = field(default='position', init=False)

    label: str

    channel: str

    state_block_labels: tuple[str, ...]

    aux_channels: tuple[str, ...] | None = field(default=None, init=False)

    # UNIQUE FIELDS
    lever_arm: tuple[float, float, float]


@dataclass
class FeedbackConfig(BaseConfig):
    """Configuration specifying when to perform inertial resets.

    Attributes:
        group (str): Inherited from BaseConfig. Registry group in which to store this
            config.

        time_trigger (float): Minimum time b/w inertial resets, in seconds. If set to 0,
            will perform a reset after every measurement update, provided
            pos_error_threshold has also been surpassed.

        pos_error_threshold (float): Minimum estimate, in meters, of any of the inertial
            position error states required to trigger a reset. If set to 0, will perform
            a reset after every measurement update, provided time_threshold has also
            been surpassed.
    """

    # INHERITED FIELDS
    group: str

    # UNIQUE FIELDS
    time_threshold: float = 0.0
    pos_error_threshold: float = 0.0


@dataclass
class TutorialOrchestrationConfig(BaseConfig):
    """
    Configuration that dictates what channels will be used by the orchestration plugin.
    """

    position_channel: str
    """
    The name of the position channel whose messages will be used for alignment and the fusion engine.
    """

    velocity_channel: str = 'unused'
    """
    The name of the velocity channel whose messages will be used for measurement updates in the fusion engine.
    """

    group: str = field(default='config/orchestration', init=False)


@dataclass(kw_only=True)
class StandardOrchestrationConfig(BaseConfig):
    """
    Configuration for the orchestration plugin.

    Includes additional config groups for data that assists with instantiating core orchestration
    components such as the measurement processor and state block.
    """

    group: str = field(default='config/orchestration', init=False)

    best_sol_channel: str
    """
    The channel on which to output the best solution of the filter.
    """

    imu_sol_channel: str
    """
    The channel on which to output the imu solution of the filter.
    """

    alignment_channels: tuple[str, ...]
    """
    A series of channels whose messages are to be used during initialization.
    """

    pinson_sb_config: PinsonStateBlockConfig
    """
    The pinson state block config that will be used to create the primary state block
    representing the error model of the inertial navigation system.
    """

    additional_sb_configs: tuple[StateBlockConfig, ...] | None = None
    """
    A series of state block configs to use in addition to the core pinson state block.
    """

    vsb_configs: tuple[VirtualStateBlockConfig, ...] | None = None
    """
    A series of virtual state block configs to use in the fusion engine.
    """

    mp_configs: tuple[MeasurementProcessorConfig, ...] | None = None
    """
    A series of measurement processor configs to use in the fusion engine.
    """

    inertial_config: InertialConfig
    """
    An inertial config that contains inertial buffering and mechanization information.
    """

    feedback_config: FeedbackConfig | None = None
    """
    Optional config specifying when to perform inertial resets. If None, will apply feedback after every measurement update.
    """

    alignment_config: BaseConfig
    """
    A config that contains information used to set up the initialization strategy.
    """

    preprocessor_configs: tuple[PreprocessorConfig, ...] | None = None
    """
    A series of preprocessor configs to use. (optional)
    """

    max_prop_interval: float = 2.0
    """
    Maximum interval in seconds over which to propagate states. Intervals longer than
    this will be broken up into segments.
    """

    publish_before_update: bool = False
    """Whether to publish filter and inertial solution right before each update.

    If True, will publish to registry and through transport.

    NOTE: It is recommended when enabling this feature that you disable
    `publish_interval` in ControllerConfig, otherwise filter solutions may be published
    out of order.
    """

    publish_after_update: bool = False
    """Whether to publish filter and inertial solution right after each update.

    If True, will publish to registry and through transport. If inertial feedback is
    enabled, it will be applied after the filter update, but before publishing the
    solution.

    NOTE: It is recommended when enabling this feature that you disable
    `publish_interval` in ControllerConfig, otherwise filter solutions may be published
    out of order.
    """
