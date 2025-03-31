import unittest
from typing import List

import numpy as np
from aspn23 import (
    AspnBase,
    MeasurementAltitude,
    MeasurementAngularVelocity,
    MeasurementHeading,
    MeasurementImu,
    MeasurementImuImuType,
    MeasurementPositionVelocityAttitude,
    MeasurementPositionVelocityAttitudeErrorModel,
    MeasurementPositionVelocityAttitudeReferenceFrame,
    MeasurementSatnav,
    TypeHeader,
    TypeTimestamp,
)
from numpy import float64
from numpy.typing import NDArray
from pntos.api import (
    CrossCovariances,
    EstimateWithCovariance,
    EstimateWithCovarianceType,
    FusionEngineType,
    FusionPlugin,
    FusionStrategyPlugin,
    FusionStrategyType,
    InertialForcesRates,
    InertialFrame,
    InertialInitializationStrategy,
    InertialPlugin,
    InertialSolutionRangeType,
    InertialType,
    InitialInertialSolution,
    InitializationMotionNeeded,
    InitializationPlugin,
    InitializationStatus,
    InitializationType,
    LoggingLevel,
    Mediator,
    Message,
    OrchestrationPlugin,
    Registry,
    StandardDynamicsModel,
    StandardFusionEngine,
    StandardFusionStrategy,
    StandardInertialErrors,
    StandardInertialMechanization,
    StandardMeasurementModel,
    StandardMeasurementProcessor,
    StandardStateBlock,
    StandardStateModelProvider,
    StateModelingPlugin,
    StateModelProviderType,
    VirtualStateBlock,
)
from pntos.cobra import (
    SimpleOrchestrationPlugin,
    SimpleRegistryPlugin,
)
from pntos.cobra.internal import SimpleMessageStreamConfig

# Test globals
FOUND_ERROR = False
ERROR_MESSAGE = ''
EXPECTED_ERROR_MESSAGE = ''
ALIGNMENT_STATE = InitializationStatus.INITIALIZED_GOOD

# Solution Channels
BEST_SOL_CHANNEL = '/solution/pntos/best'
IMU_SOL_CHANNEL = '/solution/pntos/imu'

# Sensor input channels
IMU_CHANNEL = '/sensor/sagem/imu'
GPS_CHANNEL = '/sensor/ublox-neo-m9n-update/geodetic_pos'

# Process_pntos_message mapping
MEASUREMENT_CHANNELS = [GPS_CHANNEL]
ALIGNMENT_CHANNELS = [GPS_CHANNEL, IMU_CHANNEL]

# State block parameters
STATE_BLOCK_LABEL = 'pinson15'
STATE_BLOCK_CONFIG_GROUP = 'config/inertial_state'

# Measurement processor parameters
MEASUREMENT_PROCESSOR_ID = 'pinson_position'
MEASUREMENT_PROCESSOR_LABEL = 'gps'
MEASUREMENT_PROCESSOR_CONFIG_GROUP = 'config/gp3d_state_modeling'

# Inertial parameters
INERTIAL_GROUP = 'config/inertial'
INERTIAL_CHANNEL = IMU_CHANNEL


class DummyInitializationPlugin(InitializationPlugin):
    def __init__(self, identifier: str) -> None:
        self.identifier = identifier

    def init_plugin(
        self,
        plugin_resources_location: str | None = None,
        mediator: Mediator | None = None,
    ) -> None:
        self.mediator = mediator

    def shutdown_plugin(self) -> None:
        return

    def is_initialization_type_supported(self, type: type[InitializationType]) -> bool:
        return True

    def new_initialization_strategy(
        self, type: type[InitializationType], config_group: str | None = None
    ) -> InitializationType | None:
        if issubclass(type, InertialInitializationStrategy):
            return DummyInertialInitializationStrategy()
        else:
            return None


class DummyStandardInertialMechanization(StandardInertialMechanization):
    message: Message | None = None

    def request_solution_message_type(self) -> type[AspnBase]:
        return MeasurementImu

    def request_current_solution(self) -> Message:
        return Message(
            MeasurementPositionVelocityAttitude(
                header=TypeHeader(0, 1, 2, 3),
                time_of_validity=TypeTimestamp(1000),
                covariance=np.zeros((9, 9)),
                error_model=MeasurementPositionVelocityAttitudeErrorModel.NONE,
                error_model_params=np.array([]),
                integrity=[],
                p1=1.0,
                p2=2.0,
                p3=3.0,
                v1=1.1,
                v2=2.1,
                v3=3.1,
                quaternion=np.array([1.0, 1.1, 1.2, 1.3]),
                reference_frame=MeasurementPositionVelocityAttitudeReferenceFrame.GEODETIC,
            ),
            GPS_CHANNEL,
        )

    def request_solution(self, time: TypeTimestamp) -> Message | None:
        return self.request_current_solution()

    def request_solutions(
        self, time: list[TypeTimestamp], type: InertialSolutionRangeType
    ) -> list[Message] | None:
        return [self.request_current_solution()]

    def is_time_in_range(self, time: TypeTimestamp) -> bool:
        return True

    def request_earliest_time(self) -> TypeTimestamp:
        return TypeTimestamp(0)

    def request_latest_time(self) -> TypeTimestamp:
        return TypeTimestamp(1000)

    def request_process_pntos_message_types(self) -> list[type[AspnBase]]:
        return []

    def request_forces_and_rates(
        self, time: TypeTimestamp
    ) -> InertialForcesRates | None:
        return InertialForcesRates(
            MeasurementImu(
                TypeHeader(0, 1, 2, 3),
                TypeTimestamp(1000),
                MeasurementImuImuType.INTEGRATED,
                np.array([0.0, 0.1, 0.2]),
                np.array([1.0, 1.1, 1.2]),
                [],
            ),
            InertialFrame.INERTIAL_FRAME_NED,
        )

    def request_average_forces_and_rates(
        self, time1: TypeTimestamp, time2: TypeTimestamp
    ) -> InertialForcesRates | None:
        return None

    def process_pntos_message(self, message: Message) -> None:
        self.message = message
        return

    def request_reset_message_types(self) -> list[type[AspnBase]] | None:
        return None

    def reset_solution(self, message: Message) -> None:
        return None

    def correct_sensor_errors(
        self, time: TypeTimestamp, errors: StandardInertialErrors
    ) -> None:
        return None

    def request_sensor_errors(
        self, time: TypeTimestamp
    ) -> StandardInertialErrors | None:
        return StandardInertialErrors(
            np.array([0.1, 0.2, 0.3]),
            np.array([0.4, 0.5, 0.6]),
            np.array([0.7, 0.8, 0.9]),
            np.array([1.0, 1.1, 1.2]),
        )


class DummyInertialPlugin(InertialPlugin):
    def __init__(self, identifier: str) -> None:
        self.identifier = identifier

    def init_plugin(
        self,
        plugin_resources_location: str | None = None,
        mediator: Mediator | None = None,
    ) -> None:
        self.mediator = mediator

    def shutdown_plugin(self) -> None:
        return

    def is_inertial_type_supported(self, type: type[InertialType]) -> bool:
        return True

    def new_inertial(
        self,
        type: type[InertialType],
        solution: Message,
        config_group: str | None = None,
    ) -> InertialType | None:
        return DummyStandardInertialMechanization()


class DummyFusionPlugin(FusionPlugin):
    def __init__(self, identifier: str) -> None:
        self.identifier = identifier

    def init_plugin(
        self,
        plugin_resources_location: str | None = None,
        mediator: Mediator | None = None,
    ) -> None:
        self.mediator = mediator

    def shutdown_plugin(self) -> None:
        return

    def is_fusion_type_supported(self, type: type[FusionEngineType]) -> bool:
        return True

    def new_fusion_engine(
        self, type: type[FusionEngineType]
    ) -> FusionEngineType | None:
        if issubclass(type, StandardFusionEngine):
            return DummyStandardFusionEngine()
        else:
            return None


class DummyStandardFusionEngine(StandardFusionEngine):
    _strategy: StandardFusionStrategy
    _time: TypeTimestamp = TypeTimestamp(0)

    @property
    def time(self) -> TypeTimestamp:
        return self._time

    @time.setter
    def time(self, time: TypeTimestamp) -> None:
        self._time = time

    @property
    def strategy(self) -> StandardFusionStrategy | None:
        return self._strategy

    @strategy.setter
    def strategy(self, strategy: StandardFusionStrategy) -> None:
        self._strategy = strategy

    def get_num_states(self) -> int:
        return 0

    def get_state_block_labels(self) -> List[str] | None:
        pass

    def add_state_block(
        self,
        block: StandardStateBlock,
        initial_estimate_covariance: EstimateWithCovariance,
        cross_covariances: CrossCovariances | None = None,
    ) -> None:
        pass

    def get_state_block_estimate(self, block_label: str) -> NDArray[float64] | None:
        return np.array([[i / 10] for i in range(15)])

    def get_state_block_covariance(self, block_label: str) -> NDArray[float64] | None:
        pass

    def get_state_block_cross_covariance(
        self, block_label1: str, block_label2: str
    ) -> NDArray[float64] | None:
        pass

    def set_state_block_estimate(
        self, block_label: str, estimate: NDArray[float64]
    ) -> None:
        pass

    def set_state_block_covariance(
        self, block_label: str, covariance: NDArray[float64]
    ) -> None:
        pass

    def set_state_block_cross_covariance(
        self, block_label1: str, block_label2: str, covariance: NDArray[float64]
    ) -> None:
        pass

    def remove_state_block(self, block_label: str) -> None:
        pass

    def get_virtual_state_block_target_labels(self) -> List[str] | None:
        pass

    def has_virtual_state_block(self, vsb_target_label: str) -> bool:
        return False

    def add_virtual_state_block(self, virtual_state_block: VirtualStateBlock) -> None:
        pass

    def remove_virtual_state_block(self, vsb_target_label: str) -> None:
        pass

    def get_measurement_processor_labels(self) -> List[str] | None:
        pass

    def add_measurement_processor(
        self, processor: StandardMeasurementProcessor
    ) -> None:
        pass

    def remove_measurement_processor(self, processor_label: str) -> None:
        pass

    def propagate(self, time: TypeTimestamp) -> None:
        pass

    def update(self, processor_label: str, message: Message) -> None:
        pass

    def peek_ahead(
        self, time: TypeTimestamp, block_labels: List[str]
    ) -> EstimateWithCovariance | None:
        return EstimateWithCovariance(
            type=EstimateWithCovarianceType.EWC_GENERIC,
            estimate=np.array([[i / 100] for i in range(15)]),
            covariance=np.zeros((15, 15)),
        )

    def generate_x_and_p(
        self, block_labels: List[str]
    ) -> EstimateWithCovariance | None:
        pass

    def give_state_block_aux_data(self, block_label: str, aux: List[Message]) -> None:
        pass

    def give_measurement_processor_aux_data(
        self, processor_label: str, aux: List[Message]
    ) -> None:
        pass

    def give_virtual_state_block_aux_data(
        self, target_label: str, aux: List[Message]
    ) -> None:
        pass

    def clone(self) -> 'DummyStandardFusionEngine':
        return self


class DummyFusionStrategyPlugin(FusionStrategyPlugin):
    def __init__(self, identifier: str) -> None:
        self.identifier = identifier

    def init_plugin(
        self,
        plugin_resources_location: str | None = None,
        mediator: Mediator | None = None,
    ) -> None:
        self.mediator = mediator

    def shutdown_plugin(self) -> None:
        return

    def is_fusion_type_supported(self, fusion_type: type[FusionStrategyType]) -> bool:
        return True

    def new_fusion_strategy(
        self, fusion_type: type[FusionStrategyType]
    ) -> FusionStrategyType | None:
        return DummyStandardFusionStrategy()


class DummyStateModelingPlugin(StateModelingPlugin):
    def __init__(self, identifier: str) -> None:
        self.identifier = identifier

    def init_plugin(
        self,
        plugin_resources_location: str | None = None,
        mediator: Mediator | None = None,
    ) -> None:
        self.mediator = mediator

    def shutdown_plugin(self) -> None:
        return

    def is_fusion_type_supported(self, type: type[StateModelProviderType]) -> bool:
        return True

    def new_state_model_provider(
        self, type: type[StateModelProviderType]
    ) -> StateModelProviderType | None:
        return DummyStandardStateModelProvider()


class DummyStandardStateBlock(StandardStateBlock):
    label: str
    num_states: int = 15

    def __init__(self, label: str) -> None:
        self.label = label

    def receive_aux_data(self, aux: list[Message]) -> None:
        return

    def generate_dynamics(
        self,
        x_and_p: EstimateWithCovariance,
        time_from: TypeTimestamp,
        time_to: TypeTimestamp,
    ) -> StandardDynamicsModel | None:
        return None


class DummyStandardMeasurementProcessor(StandardMeasurementProcessor):
    label: str
    state_block_labels: list[str]

    def __init__(self, label: str, state_block_labels: list[str]) -> None:
        self.label = label
        self.state_block_labels = state_block_labels

    def receive_aux_data(self, aux: list[Message]) -> None:
        return

    def generate_model(
        self, message: Message, x_and_p: EstimateWithCovariance
    ) -> StandardMeasurementModel | None:
        return None


class DummyStandardStateModelProvider(StandardStateModelProvider):
    processor_identifiers = [MEASUREMENT_PROCESSOR_ID]
    block_identifiers = [STATE_BLOCK_LABEL]
    virtual_block_identifiers = []

    def new_processor(
        self,
        processor_index: int,
        engine: StandardFusionEngine | None,
        label: str,
        state_block_labels: list[str],
        config_group: str,
    ) -> StandardMeasurementProcessor | None:
        return DummyStandardMeasurementProcessor(label, state_block_labels)

    def new_block(
        self,
        block_index: int,
        engine: StandardFusionEngine | None,
        label: str,
        config_group: str,
    ) -> StandardStateBlock | None:
        return DummyStandardStateBlock(label)

    def new_virtual_block(
        self,
        virtual_block_index: int,
        source_label: str,
        target_label: str,
        config_group: str,
    ) -> VirtualStateBlock | None:
        return None


class DummyStandardFusionStrategy(StandardFusionStrategy):
    def get_num_states(self) -> int:
        return 0

    def add_states(
        self,
        initial_estimate: NDArray[float64],
        initial_covariance: NDArray[float64],
        cross_covariance: NDArray[float64] | None = None,
    ) -> int:
        return 0

    def remove_states(self, first_index: int, count: int) -> None:
        pass

    def get_estimate(self) -> NDArray[float64] | None:
        return None

    def set_estimate_slice(
        self, new_estimate: NDArray[float64], first_index: int
    ) -> None:
        pass

    def get_covariance(self) -> NDArray[float64] | None:
        pass

    def set_covariance_slice(
        self,
        new_covariance: NDArray[float64],
        first_row: int,
        first_col: int,
    ) -> None:
        pass

    def propagate(self, dynamics_model: StandardDynamicsModel) -> None:
        pass

    def update(self, measurement_model: StandardMeasurementModel) -> None:
        pass

    def clone(self) -> 'DummyStandardFusionStrategy':
        return self


class DummyInertialInitializationStrategy(InertialInitializationStrategy):
    """Dummy initialization strategy that simply waits for any message to initialize."""

    status: InitializationStatus

    def __init__(self) -> None:
        self.status = InitializationStatus.INITIALIZED_GOOD

    def request_solution(self) -> InitialInertialSolution:
        return InitialInertialSolution(
            Message(
                wrapped_message=MeasurementPositionVelocityAttitude(
                    header=TypeHeader(
                        vendor_id=0, device_id=1, context_id=2, sequence_id=3
                    ),
                    time_of_validity=TypeTimestamp(elapsed_nsec=1000),
                    reference_frame=MeasurementPositionVelocityAttitudeReferenceFrame.GEODETIC,
                    p1=1.0,
                    p2=2.0000000028949256,
                    p3=2.98,
                    v1=1.1300000000000001,
                    v2=2.14,
                    v3=3.15,
                    quaternion=np.array(
                        [
                            1.9992092093502731,
                            1.9022032841808882,
                            2.057372072808313,
                            0.7091255263879387,
                        ]
                    ),
                    covariance=np.zeros([9, 9]),
                    error_model=MeasurementPositionVelocityAttitudeErrorModel.NONE,
                    error_model_params=np.array([], dtype=float64),
                    integrity=[],
                ),
                source_identifier='/solution/pntos/best',
            ),
            StandardInertialErrors(np.zeros(3), np.zeros(3), np.ones(3), np.ones(3)),
            np.zeros([12, 12]),  # pretend that it's the errors for a Pinson21
            InitializationStatus.INITIALIZED_GOOD,
        )

    def request_motion_needed(self) -> InitializationMotionNeeded:
        return InitializationMotionNeeded.ANY_MOTION

    def request_current_status(self) -> InitializationStatus:
        return self.status

    def process_pntos_message(self, message: Message) -> None:
        pass


class DummyMediator(Mediator):
    registry: Registry

    def get_filter_description_list(self) -> list[str]:
        return []

    def request_solutions(
        self,
        solution_times: list[TypeTimestamp],
        filter_description: str | None = None,
    ) -> list[Message]:
        return []

    def process_pntos_message(self, message: Message) -> None:
        return

    def broadcast_aspn_message(
        self,
        message: Message,
        transport: str | None = None,
        destination_identifier: str | None = None,
    ) -> None:
        return

    def log_message(self, level: LoggingLevel, message: str) -> None:
        if level is LoggingLevel.ERROR:
            ERROR_MESSAGE = message
            FOUND_ERROR = True
            assert (
                not FOUND_ERROR and ERROR_MESSAGE != EXPECTED_ERROR_MESSAGE
            ), ERROR_MESSAGE


class Test_Orchestration(unittest.TestCase):
    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.message_types: list[type[AspnBase]] = [
            MeasurementPositionVelocityAttitude,
            MeasurementAltitude,
            MeasurementAngularVelocity,
            MeasurementHeading,
            MeasurementSatnav,
        ]

    def set_up_plugins(self) -> None:
        # Instantiate a fresh set of plugins
        self.orchestration_plugin: OrchestrationPlugin = SimpleOrchestrationPlugin(
            'SimpleOrchestrationPlugin'
        )
        self.initialization_plugin: InitializationPlugin = DummyInitializationPlugin(
            'DummyInitializationPlugin'
        )
        self.inertial_plugin: InertialPlugin = DummyInertialPlugin(
            'DummyInertialPlugin'
        )
        self.fusion_plugin: FusionPlugin = DummyFusionPlugin('DummyFusionPlugin')
        self.fusion_strategy_plugin: FusionStrategyPlugin = DummyFusionStrategyPlugin(
            'DummyFusionStrategyPlugin'
        )
        self.state_modeling_plugin: StateModelingPlugin = DummyStateModelingPlugin(
            'DummyStateModelingPlugin'
        )
        self.registry_plugin: SimpleRegistryPlugin = SimpleRegistryPlugin(
            'SimpleRegistryPlugin'
        )

        plugins = [
            self.orchestration_plugin,
            self.initialization_plugin,
            self.inertial_plugin,
            self.fusion_plugin,
            self.fusion_strategy_plugin,
            self.state_modeling_plugin,
            self.registry_plugin,
        ]

        # Run init_plugin on all the plugins
        for plugin in plugins:
            plugin.init_plugin(mediator=DummyMediator())

        DummyMediator.registry = self.registry_plugin.new_registry()

    @property
    def test_header(self) -> TypeHeader:
        return TypeHeader(0, 1, 2, 3)

    @property
    def test_timestamp(self) -> TypeTimestamp:
        return TypeTimestamp(100)

    @property
    def expected_pva_best(self) -> Message:
        return Message(
            wrapped_message=MeasurementPositionVelocityAttitude(
                header=TypeHeader(
                    vendor_id=0, device_id=1, context_id=2, sequence_id=3
                ),
                time_of_validity=TypeTimestamp(elapsed_nsec=1000),
                reference_frame=MeasurementPositionVelocityAttitudeReferenceFrame.GEODETIC,
                p1=1.0,
                p2=2.0000000028949256,
                p3=2.98,
                v1=1.1300000000000001,
                v2=2.14,
                v3=3.15,
                quaternion=np.array(
                    [
                        1.9992092093502731,
                        1.9022032841808882,
                        2.057372072808313,
                        0.7091255263879387,
                    ]
                ),
                covariance=np.zeros([9, 9]),
                error_model=MeasurementPositionVelocityAttitudeErrorModel.NONE,
                error_model_params=np.array([], dtype=float64),
                integrity=[],
            ),
            source_identifier='/solution/pntos/best',
        )

    @property
    def expected_pva_dead_reckoning(self) -> Message:
        return Message(
            wrapped_message=MeasurementPositionVelocityAttitude(
                header=TypeHeader(
                    vendor_id=0, device_id=1, context_id=2, sequence_id=3
                ),
                time_of_validity=TypeTimestamp(elapsed_nsec=1000),
                reference_frame=MeasurementPositionVelocityAttitudeReferenceFrame.GEODETIC,
                p1=1.0,
                p2=2.0,
                p3=3.0,
                v1=1.1,
                v2=2.1,
                v3=3.1,
                quaternion=np.array([1.0, 1.1, 1.2, 1.3]),
                covariance=np.zeros((9, 9)),
                error_model=MeasurementPositionVelocityAttitudeErrorModel.NONE,
                error_model_params=np.array([], dtype=float64),
                integrity=[],
            ),
            source_identifier='/solution/pntos/imu',
        )

    def generate_imu_message(self, source_identifier: str = 'source') -> Message:
        return Message(
            MeasurementImu(
                header=self.test_header,
                time_of_validity=self.test_timestamp,
                imu_type=MeasurementImuImuType.INTEGRATED,
                meas_accel=np.array([0.0, 0.1, 0.2]),
                meas_gyro=np.array([1.0, 1.1, 1.2]),
                integrity=[],
            ),
            source_identifier=source_identifier,
        )

    def generate_pva_message(self, source_identifier: str = 'source') -> Message:
        return Message(
            MeasurementPositionVelocityAttitude(
                header=self.test_header,
                time_of_validity=self.test_timestamp,
                reference_frame=MeasurementPositionVelocityAttitudeReferenceFrame.GEODETIC,
                p1=0.1,
                p2=0.2,
                p3=0.3,
                v1=1.1,
                v2=1.2,
                v3=1.3,
                quaternion=np.array([0.0, 0.1, 0.2, 0.3]),
                covariance=np.zeros((9, 9)),
                error_model=MeasurementPositionVelocityAttitudeErrorModel.NONE,
                error_model_params=np.array([]),
                integrity=[],
            ),
            source_identifier=source_identifier,
        )

    def compare_messages(self, m1: object, m2: object, depth: int = 0) -> bool:
        """The numpy arrays in Message objects do not seem to compare nicely
        with "==" after coming out of permanency. This is a hacky workaround to
        run np.all() on any np elements, and run normal comparison otherwise."""
        if hasattr(m1, '__dict__') and depth < 3:
            for attr in m1.__dict__:
                value1 = getattr(m1, attr)
                value2 = getattr(m2, attr)

                if isinstance(value1, np.ndarray) and isinstance(value2, np.ndarray):
                    if not np.allclose(value1, value2):
                        return False
                else:
                    if not self.compare_messages(value1, value2, depth + 1):
                        return False
            return True
        else:
            return m1 == m2

    def test_init_orchestration_plugin_simple(self) -> None:
        """
        Just making sure the function can run without crashing.

        TODO: make more robust tests for this method.
        """
        self.set_up_plugins()
        stream_config = SimpleMessageStreamConfig()
        plugins = [
            self.initialization_plugin,
            self.inertial_plugin,
            self.fusion_plugin,
            self.fusion_strategy_plugin,
            self.state_modeling_plugin,
        ]
        self.orchestration_plugin.init_orchestration_plugin(plugins, stream_config)
        global EXPECTED_ERROR_MESSAGE, ALIGNMENT_STATE
        EXPECTED_ERROR_MESSAGE = ''
        ALIGNMENT_STATE = InitializationStatus.INITIALIZED_GOOD

    def test_process_pntos_message_simple(self) -> None:
        """
        Just making sure the function can run without crashing.

        TODO: make more robust tests for this method.
        """
        self.test_init_orchestration_plugin_simple()  # To get past init_orchestration_plugin()
        message = Message(
            MeasurementPositionVelocityAttitude(
                TypeHeader(0, 0, 0, 0),
                TypeTimestamp(0),
                MeasurementPositionVelocityAttitudeReferenceFrame.ECI,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                np.array([]),
                MeasurementPositionVelocityAttitudeErrorModel.NONE,
                np.array([]),
                [],
            ),
            'Genesis planet',
        )

        self.orchestration_plugin.process_pntos_message(message, False)

    def test_process_pntos_message_alignment(self) -> None:
        self.test_init_orchestration_plugin_simple()

        global ALIGNMENT_STATE
        ALIGNMENT_STATE = InitializationStatus.WAITING

        message = self.generate_imu_message(source_identifier=IMU_CHANNEL)

        self.orchestration_plugin.process_pntos_message(message, False)

    def test_process_pntos_message_just_imu(self) -> None:
        self.test_init_orchestration_plugin_simple()  # To get past init_orchestration_plugin()

        message = self.generate_imu_message(source_identifier=IMU_CHANNEL)

        self.orchestration_plugin.process_pntos_message(message, False)

    def test_process_pntos_message_post_initialization(self) -> None:
        self.test_init_orchestration_plugin_simple()  # To get past init_orchestration_plugin()

        imu_message = self.generate_imu_message(source_identifier=IMU_CHANNEL)

        self.orchestration_plugin.process_pntos_message(imu_message, False)

        pva_message = self.generate_pva_message(source_identifier=GPS_CHANNEL)

        self.orchestration_plugin.process_pntos_message(pva_message, False)

    def test_get_filter_description_list_simple(self) -> None:
        """
        Just making sure the function can run without crashing.

        TODO: make more robust tests for this method.
        """
        self.test_init_orchestration_plugin_simple()  # To get past init_orchestration_plugin()
        filter_description_list = (
            self.orchestration_plugin.get_filter_description_list()
        )
        expected_filter_description_list = [
            'GPS_INS_BEST_ASPN_MEASUREMENT_POSITION_VELOCITY_ATTITUDE_ESTIMATE',
            'GPS_INS_DEAD_RECKONING_ASPN_MEASUREMENT_POSITION_VELOCITY_ATTITUDE_ESTIMATE',
        ]
        assert filter_description_list == expected_filter_description_list

    def test_request_solutions_pre_alignment(self) -> None:
        """
        Just making sure the function can run without crashing.

        TODO: make more robust tests for this method.
        """
        self.test_init_orchestration_plugin_simple()  # To get past init_orchestration_plugin()
        solution_times = [TypeTimestamp(0)]

        solutions = self.orchestration_plugin.request_solutions(solution_times)

    def test_request_solutions_post_alignment(self) -> None:
        self.test_process_pntos_message_just_imu()
        solution_times = [TypeTimestamp(0)]
        expected_solution = self.expected_pva_best

        solutions = self.orchestration_plugin.request_solutions(solution_times)
        assert len(solutions) == 1
        assert self.compare_messages(solutions[0], expected_solution)

    def test_request_solutions_using_filter_descriptions(self) -> None:
        self.test_process_pntos_message_post_initialization()
        solution_times = [TypeTimestamp(0)]
        descriptions = self.orchestration_plugin.get_filter_description_list()
        expected_descriptions = [
            'GPS_INS_BEST_ASPN_MEASUREMENT_POSITION_VELOCITY_ATTITUDE_ESTIMATE',
            'GPS_INS_DEAD_RECKONING_ASPN_MEASUREMENT_POSITION_VELOCITY_ATTITUDE_ESTIMATE',
        ]
        expected_solutions = [self.expected_pva_best, self.expected_pva_dead_reckoning]
        assert descriptions == expected_descriptions
        for expected, description in zip(expected_solutions, descriptions):
            solutions = self.orchestration_plugin.request_solutions(
                solution_times, description
            )
            assert len(solutions) == 1
            assert self.compare_messages(solutions[0], expected), solutions[0]


def suite() -> unittest.TestSuite:
    suite = unittest.TestSuite()
    tests = [m for m in dir(Test_Orchestration) if m.startswith('test_')]
    for test in tests:
        suite.addTest(Test_Orchestration(test))
    return suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
