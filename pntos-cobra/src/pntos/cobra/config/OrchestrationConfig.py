from dataclasses import dataclass

from pntos.api import EstimateWithCovariance

from .BaseConfig import BaseConfig
from .FogmConfig import FogmConfig
from .ImuConfig import ImuConfig
from .InertialConfig import InertialConfig
from .PreprocessorConfig import PreprocessorConfig
from .SensorConfig import SensorConfig


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
    """

    estimate_with_covariance: EstimateWithCovariance | None = None
    """
    An optional field that allows an initial estimate and covariance to be associated with the state block.
    """


@dataclass(kw_only=True)
class PinsonStateBlockConfig(StateBlockConfig):
    """
    Configuration used to generate a new pinson state block.
    """

    # INHERITED FIELDS
    group: str

    identifier: str

    label: str

    estimate_with_covariance: EstimateWithCovariance | None = None

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

    identifier: str

    label: str

    estimate_with_covariance: EstimateWithCovariance  # not optional on this block

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

    channel: str
    """
    The name of the channel from which the measurements originate.

    This corresponds to the `source_identifier` field on the ``pntos.api.Message`` class.
    """

    state_block_labels: list[str]
    """
    The labels of the state blocks this measurement processor will use.
    """


@dataclass
class SensorMeasurementProcessorConfig(MeasurementProcessorConfig):
    """
    Configuration used to create a generic sensor measurement processor.
    """

    # INHERITED FIELDS
    group: str

    identifier: str

    label: str

    channel: str

    state_block_labels: list[str]

    # UNIQUE FIELDS
    sensor_config: SensorConfig
    """
    A nested config that contains sensor info.

    See SensorConfig.py for more information.
    """


@dataclass
class TutorialOrchestrationConfig(BaseConfig):
    """
    Configuration that dictates what channels will be used by the orchestration plugin.
    """

    gps_channel: str
    """
    The name of the gps channel whose messages will be used for alignment and the fusion engine.
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

    alignment_channels: list[str]
    """
    List of channels whose messages are to be used during initialization.
    """

    pinson_sb_config: PinsonStateBlockConfig
    """
    The pinson state block config that will be used to create the primary state block
    representing the error model of the inertial navigation system.
    """

    additional_sb_configs: list[StateBlockConfig] | None = None
    """
    A list of state block configs to use in addition to the core pinson state block.
    """

    mp_configs: list[MeasurementProcessorConfig] | None = None
    """
    A list of measurement processor configs to use in the fusion engine.
    """

    inertial_config: InertialConfig
    """
    An inertial config that contains inertial buffering and mechanization information.
    """
    alignment_config: BaseConfig
    """
    A config that contains information used to set up the initialization strategy.
    """

    preprocessor_configs: list[PreprocessorConfig] | None = None
    """
    List of preprocessor configs to use. (optional)
    """

    group: str
