from dataclasses import dataclass, field

from pntos.api import EstimateWithCovariance

from .BaseConfig import BaseConfig
from .FogmConfig import FogmConfig
from .ImuConfig import ImuConfig
from .InertialConfig import InertialConfig
from .PreprocessorConfig import PreprocessorConfig
from .SensorConfig import SensorConfig
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

    aux_channels: tuple[str, ...] | None = None

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

    aux_channels: tuple[str, ...] | None = None

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
class SensorMeasurementProcessorConfig(MeasurementProcessorConfig):
    """
    Configuration used to create a generic sensor measurement processor.
    """

    # INHERITED FIELDS
    group: str

    identifier: str

    label: str

    channel: str

    state_block_labels: tuple[str, ...]

    aux_channels: tuple[str, ...] | None = None

    # UNIQUE FIELDS
    sensor_config: SensorConfig
    """
    A nested config that contains sensor info.

    See SensorConfig.py for more information.
    """


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

    group: str


@dataclass(kw_only=True)
class StandardOrchestrationConfig(BaseConfig):
    """
    Configuration for the orchestration plugin.

    Includes additional config groups for data that assists with instantiating core orchestration
    components such as the measurement processor and state block.
    """

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

    group: str
