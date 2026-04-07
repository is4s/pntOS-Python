import unittest
from contextlib import redirect_stdout
from copy import deepcopy
from io import StringIO

import numpy as np
from aspn23 import (
    AspnBase,
    MeasurementAltitude,
    MeasurementAltitudeErrorModel,
    MeasurementAltitudeReference,
    MeasurementAngularVelocity,
    MeasurementHeading,
    MeasurementImu,
    MeasurementImuImuType,
    MeasurementPosition,
    MeasurementPositionErrorModel,
    MeasurementPositionReferenceFrame,
    MeasurementPositionVelocityAttitude,
    MeasurementPositionVelocityAttitudeErrorModel,
    MeasurementPositionVelocityAttitudeReferenceFrame,
    MeasurementSatnav,
    TypeHeader,
    TypeTimestamp,
)
from navtk.navutils import rpy_to_quat
from numpy import float64
from pntos.api import (
    CommonPlugin,
    EstimateWithCovariance,
    EstimateWithCovarianceType,
    FusionPlugin,
    FusionStrategyPlugin,
    GenXandP,
    InertialPlugin,
    InitializationPlugin,
    InitializationStatus,
    Mediator,
    Message,
    StandardFusionEngine,
    StandardMeasurementProcessor,
    StandardStateBlock,
    StandardStateModelProvider,
    StateModelingPlugin,
    StateModelProviderType,
    VirtualStateBlock,
)
from pntos.api.plugins.registry import RegistryPlugin
from pntos.cobra import (
    EkfFusionStrategyPlugin,
    StandardFusionPlugin,
    StandardGpsInsStateModelingPlugin,
    StandardInertialPlugin,
    StandardOrchestrationPlugin,
    StandardPreprocessorPlugin,
    StandardRegistryPlugin,
    StaticAlignInitializationPlugin,
    TutorialGpsInsStateModelingPlugin,
    TutorialGpsOrchestrationPlugin,
    TutorialInitializationPlugin,
)
from pntos.cobra.config import (
    ControllerConfig,
    FogmConfig,
    FogmStateBlockConfig,
    ImuConfig,
    ImuRotatorConfig,
    InertialConfig,
    ManualAlignmentConfig,
    MeasurementProcessorConfig,
    PinsonStateBlockConfig,
    SensorConfig,
    StandardOrchestrationConfig,
    StaticAlignmentConfig,
    TimeAdjusterConfig,
    TimeBiasConfig,
    TutorialOrchestrationConfig,
)
from pntos.cobra.internal import StandardMediator, StandardMessageStreamConfig

# Test globals
FOUND_ERROR = False
ERROR_MESSAGE = ''
EXPECTED_ERROR_MESSAGE = ''
ALIGNMENT_STATE = InitializationStatus.INITIALIZED_GOOD

# Solution Channels
BEST_SOL_CHANNEL = '/solution/pntos/pva'
IMU_SOL_CHANNEL = '/solution/pntos-imu/pva'

# Sensor input channels
IMU_CHANNEL = '/sensor/vn-100/imu'
GPS_CHANNEL = '/sensor/ublox-ZED-F9T/position'

align_config = ManualAlignmentConfig(
    group='config/default/alignment',
    initial_pos_var=(0.1, 0.1, 0.1),
    initial_vel_var=(1e-3, 1e-3, 1e-3),
    initial_tilt_var=(5e-4, 5e-4, 5e-4),
    initial_accel_bias_var=(1e-10, 1e-10, 1e-10),
    initial_gyro_bias_var=(1e-15, 1e-15, 1e-15),
    initial_accel_bias=(-0.00212767, 0.00059081, -0.05242679),
    initial_accel_scale_factor=(0.0, 0.0, 0.0),
    initial_accel_scale_factor_var=(0.0, 0.0, 0.0),
    initial_gyro_bias=(-0.00165402, -0.00157491, -0.00133498),
    initial_gyro_scale_factor=(0.0, 0.0, 0.0),
    initial_gyro_scale_factor_var=(0.0, 0.0, 0.0),
    initial_pos=(0.6939183923297865, -1.4680111371692746, 222.561),
    initial_rpy=(0.0012876203558051373, -0.05315453753188288, 0.10972323851917268),
    initial_time=0.0,
    initial_vel=(0.0, 0.0, 0.0),
)
C_imu_to_platform = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
inertial_config = InertialConfig(
    group='config/inertial',
    expected_dt=0.01,
    channels=(IMU_CHANNEL,),
    C_imu_to_platform=C_imu_to_platform,
    inertial_buffer_length=10.0,
)
imu_config = ImuConfig(
    group='config/inertial_state',
    accel_bias_sigma=(2.4e-3, 2.4e-3, 2.4e-3),
    accel_bias_tau=(300.0, 300.0, 300.0),
    accel_random_walk_sigma=(3.887e-6, 3.887e-6, 3.887e-6),
    gyro_bias_sigma=(2e-4, 2e-4, 2e-4),
    gyro_bias_tau=(500.0, 500.0, 500.0),
    gyro_random_walk_sigma=(9.9e-4, 9.9e-4, 6.7e-5),
)
tutorial_config = [
    imu_config,
    align_config,
    SensorConfig(
        group='config/gp3d_state_modeling',
        lever_arm=(0.0, 0.0, 0.0),
        orientation=(0.0, 0.0, 0.0, 0.0),
        sensor_name='novatel',
    ),
    inertial_config,
    FogmConfig(
        group='config/pos_sensor_error',
        sigma=(1.5, 1.5, 2.0),
        tau=(300.0, 300.0, 200.0),
    ),
    TutorialOrchestrationConfig(
        gps_channel=GPS_CHANNEL,
        group='config/orchestration',
    ),
    TimeAdjusterConfig(
        group='config/time_adjuster',
        channel_to_correct=IMU_CHANNEL,
        expected_dt_nsec=int(0.01 * 1e9),
    ),
    ImuRotatorConfig(
        group='config/imu_rotator',
        channel=IMU_CHANNEL,
        C_imu_to_platform=C_imu_to_platform,
    ),
    TimeBiasConfig(
        group='config/time_bias',
        channels_to_correct=(
            '/sensor/ublox-ZED-F9T/position',
            '/sensor/ublox-ZED-F9T/velocity',
        ),
        time_bias=int(0 * 1e9),
    ),
]

standard_config = [
    ControllerConfig(group='controller'),
    StandardOrchestrationConfig(
        best_sol_channel=BEST_SOL_CHANNEL,
        imu_sol_channel=IMU_SOL_CHANNEL,
        alignment_channels=(GPS_CHANNEL, IMU_CHANNEL),
        pinson_sb_config=PinsonStateBlockConfig(
            group='config/pinson_block',
            label='pinson15',
            imu_model=imu_config,
        ),
        additional_sb_configs=(
            FogmStateBlockConfig(
                group='config/pos_fogm_block',
                label='pos_sensor_error',
                estimate_with_covariance=EstimateWithCovariance(
                    type=EstimateWithCovarianceType.EWC_GENERIC,
                    estimate=np.zeros((3,)),
                    covariance=(np.eye(3) * 9.0),
                ),
                fogm_model=FogmConfig(
                    group='config/pos_sensor_error',
                    sigma=(1.5, 1.5, 2.0),
                    tau=(300.0, 300.0, 200.0),
                ),
            ),
        ),
        mp_configs=(
            MeasurementProcessorConfig(
                group='config/mock_mp1',
                identifier='mock_mp',
                label='mock_mp1',
                state_block_labels=('mock_sb',),
                channel='mock_channel',
            ),
            MeasurementProcessorConfig(
                group='config/mock_mp2',
                identifier='mock_mp',
                label='mock_mp2',
                state_block_labels=('mock_sb',),
                channel='mock_channel',
            ),
        ),
        inertial_config=inertial_config,
        alignment_config=align_config,
        preprocessor_configs=(
            ImuRotatorConfig(
                group='config/rotator',
                channel=IMU_CHANNEL,
                C_imu_to_platform=C_imu_to_platform,
            ),
        ),
        group='config/orchestration',
    ),
]

manual_fogm_config = deepcopy(standard_config)
orch_config: StandardOrchestrationConfig = manual_fogm_config[1]  # type: ignore[assignment]
orch_config.additional_sb_configs[0].estimate_with_covariance = EstimateWithCovariance(  # type: ignore[index]
    type=EstimateWithCovarianceType.EWC_GENERIC,
    estimate=np.zeros((3,)),
    covariance=np.eye(3),
)


class MockMP(StandardMeasurementProcessor):
    def __init__(self, label: str) -> None:
        self.label = label
        self.state_block_labels = []

    def generate_model(self, message: Message, gen_x_and_p_func: GenXandP) -> None:
        print(f'{self.label} received message')

    def receive_aux_data(self, aux: list[Message | None]) -> None:
        pass


class MockStateModelProvider(StandardStateModelProvider):
    def __init__(self) -> None:
        self.block_identifiers = []
        self.virtual_block_identifiers = []
        self.processor_identifiers = ['mock_mp']

    def new_processor(
        self,
        processor_index: int,
        engine: StandardFusionEngine | None,
        label: str,
        state_block_labels: list[str],
        config_group: str | None,
    ) -> StandardMeasurementProcessor | None:
        return MockMP(label)

    def new_block(
        self,
        block_index: int,
        engine: StandardFusionEngine | None,
        label: str,
        config_group: str | None,
    ) -> StandardStateBlock | None:
        return None

    def new_virtual_block(
        self,
        virtual_block_index: int,
        source_label: str,
        target_label: str,
        config_group: str | None,
    ) -> VirtualStateBlock | None:
        return None


class MockStateModelingPlugin(StateModelingPlugin):
    identifier = 'Mock State Modeling Plugin'

    def init_plugin(
        self,
        plugin_resources_location: str | None = None,
        mediator: Mediator | None = None,
    ) -> None:
        return

    def shutdown_plugin(self) -> None:
        return

    def is_fusion_type_supported(self, type: type[StateModelProviderType]) -> bool:
        return False

    def new_state_model_provider(
        self, type: type[StateModelProviderType]
    ) -> StateModelProviderType | None:
        return MockStateModelProvider()


class Test_Orchestration(unittest.TestCase):
    orchestration_plugin: TutorialGpsOrchestrationPlugin | StandardOrchestrationPlugin

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.message_types: list[type[AspnBase]] = [
            MeasurementPositionVelocityAttitude,
            MeasurementAltitude,
            MeasurementAngularVelocity,
            MeasurementHeading,
            MeasurementSatnav,
        ]

    def instantiate_default_plugins(self, config) -> list:  # type: ignore[type-arg, no-untyped-def]
        self.initialization_plugin: InitializationPlugin = TutorialInitializationPlugin(
            'Cobra Tutorial Initialization Plugin'
        )
        self.inertial_plugin: InertialPlugin = StandardInertialPlugin(
            'Cobra Standard Inertial Plugin'
        )
        self.fusion_plugin: FusionPlugin = StandardFusionPlugin(
            'Cobra Standard Fusion Plugin'
        )
        self.fusion_strategy_plugin: FusionStrategyPlugin = EkfFusionStrategyPlugin(
            'Cobra EKF Fusion Strategy Plugin'
        )
        self.registry_plugin: StandardRegistryPlugin = StandardRegistryPlugin(
            'StandardRegistryPlugin', config=config
        )
        self.preprocessor_plugin: StandardPreprocessorPlugin = (
            StandardPreprocessorPlugin('StandardPreprocessorPlugin')
        )
        return [
            self.initialization_plugin,
            self.inertial_plugin,
            self.fusion_plugin,
            self.fusion_strategy_plugin,
            self.registry_plugin,
            self.preprocessor_plugin,
        ]

    def init_all_plugins(self, plugins: list[CommonPlugin]) -> None:
        mediator = StandardMediator(self.registry_plugin.identifier, RegistryPlugin)
        self.registry_plugin.init_plugin(mediator=mediator)
        registry = self.registry_plugin.new_registry()
        StandardMediator.registry = registry
        StandardMediator._controller_plugin = None
        # Run init_plugin on all the plugins
        for plugin in plugins:
            plugin.init_plugin(mediator=mediator)

    def set_up_tutorial_orchestration(self) -> None:
        plugins = self.instantiate_default_plugins(tutorial_config)
        self.orchestration_plugin = TutorialGpsOrchestrationPlugin(
            'TutorialGpsOrchestrationPlugin'
        )
        self.state_modeling_plugin: StateModelingPlugin = (
            TutorialGpsInsStateModelingPlugin('Cobra Tutorial State Modeling Plugin')
        )
        self.mock_state_modeling_plugin = MockStateModelingPlugin()
        plugins.append(self.orchestration_plugin)
        plugins.append(self.state_modeling_plugin)
        plugins.append(self.mock_state_modeling_plugin)
        self.init_all_plugins(plugins)

    def set_up_standard_orchestration(self) -> None:
        plugins = self.instantiate_default_plugins(standard_config)
        self.orchestration_plugin = StandardOrchestrationPlugin(
            'StandardOrchestrationPlugin'
        )
        self.state_modeling_plugin = StandardGpsInsStateModelingPlugin(
            'Cobra Standard State Modeling Plugin'
        )
        self.mock_state_modeling_plugin = MockStateModelingPlugin()
        plugins.append(self.orchestration_plugin)
        plugins.append(self.state_modeling_plugin)
        plugins.append(self.mock_state_modeling_plugin)
        self.init_all_plugins(plugins)

    def set_up_manual_fogm_orchestration(self) -> None:
        plugins = self.instantiate_default_plugins(manual_fogm_config)
        self.orchestration_plugin = StandardOrchestrationPlugin(
            'StandardOrchestrationPlugin'
        )
        self.state_modeling_plugin = StandardGpsInsStateModelingPlugin(
            'Cobra Standard State Modeling Plugin'
        )
        self.mock_state_modeling_plugin = MockStateModelingPlugin()
        plugins.append(self.orchestration_plugin)
        plugins.append(self.state_modeling_plugin)
        plugins.append(self.mock_state_modeling_plugin)
        self.init_all_plugins(plugins)

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
                    vendor_id=0, device_id=0, context_id=0, sequence_id=0
                ),
                time_of_validity=TypeTimestamp(
                    elapsed_nsec=int(align_config.initial_time * 1e9)
                ),
                reference_frame=MeasurementPositionVelocityAttitudeReferenceFrame.GEODETIC,
                p1=align_config.initial_pos[0],
                p2=align_config.initial_pos[1],
                p3=align_config.initial_pos[2],
                v1=align_config.initial_vel[0],
                v2=align_config.initial_vel[1],
                v3=align_config.initial_vel[2],
                quaternion=rpy_to_quat(
                    np.array(
                        [
                            align_config.initial_rpy[0],
                            align_config.initial_rpy[1],
                            align_config.initial_rpy[2],
                        ]
                    )
                ),
                covariance=np.diag(
                    np.array([0.1, 0.1, 0.1, 1e-3, 1e-3, 1e-3, 5e-4, 5e-4, 5e-4])
                ),
                error_model=MeasurementPositionVelocityAttitudeErrorModel.NONE,
                error_model_params=np.array([], dtype=float64),
                integrity=[],
            ),
            source_identifier=BEST_SOL_CHANNEL,
        )

    @property
    def expected_pva_dead_reckoning(self) -> Message:
        ms = self.expected_pva_best
        ms.source_identifier = IMU_SOL_CHANNEL
        assert isinstance(ms.wrapped_message, MeasurementPositionVelocityAttitude)
        ms.wrapped_message.covariance = np.zeros((9, 9))
        return ms

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
                covariance=np.diag(
                    np.array([0.1, 0.1, 0.1, 1e-3, 1e-3, 1e-3, 5e-4, 5e-4, 5e-4])
                ),
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
                elif not self.compare_messages(value1, value2, depth + 1):
                    return False
            return True
        print(f'm1 {m1}')
        print(f'm2 {m2}')
        return m1 == m2

    def init_orchestration_plugin(self) -> None:
        stream_config = StandardMessageStreamConfig()
        plugins = [
            self.fusion_plugin,
            self.fusion_strategy_plugin,
            self.inertial_plugin,
            self.initialization_plugin,
            self.state_modeling_plugin,
            self.preprocessor_plugin,
            self.mock_state_modeling_plugin,
        ]
        self.orchestration_plugin.init_orchestration_plugin(plugins, stream_config)
        global EXPECTED_ERROR_MESSAGE, ALIGNMENT_STATE
        EXPECTED_ERROR_MESSAGE = ''
        ALIGNMENT_STATE = InitializationStatus.INITIALIZED_GOOD

    def test_init_orchestration_plugin_tutorial(self) -> None:
        self.set_up_tutorial_orchestration()
        self.init_orchestration_plugin()

    def test_init_orchestration_plugin_standard(self) -> None:
        self.set_up_standard_orchestration()
        self.init_orchestration_plugin()

    def test_init_orchestration_plugin_man_fogm(self) -> None:
        self.set_up_manual_fogm_orchestration()
        self.init_orchestration_plugin()

    def test_process_pntos_message_tutorial(self) -> None:
        self.test_init_orchestration_plugin_tutorial()  # To get past init_orchestration_plugin()
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

    def test_process_pntos_message_standard(self) -> None:
        self.test_init_orchestration_plugin_standard()  # To get past init_orchestration_plugin()
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

    def test_one_channel_multiple_mps(self) -> None:
        self.test_init_orchestration_plugin_standard()
        message = Message(
            MeasurementAltitude(
                TypeHeader(0, 0, 0, 0),
                TypeTimestamp(0),
                MeasurementAltitudeReference.MSL,
                100.0,
                10.0,
                MeasurementAltitudeErrorModel.NONE,
                np.array([]),
                [],
            ),
            'mock_channel',
        )
        f = StringIO()
        with redirect_stdout(f):
            self.orchestration_plugin.process_pntos_message(message, False)

        output = f.getvalue().strip()
        assert (
            'mock_mp1 received message' in output
            and 'mock_mp2 received message' in output
        )

    def test_outage_filter_propagation(self) -> None:
        self.test_init_orchestration_plugin_standard()
        for i in range(
            int(inertial_config.inertial_buffer_length / inertial_config.expected_dt)
        ):
            self.orchestration_plugin.process_pntos_message(
                Message(
                    MeasurementImu(
                        header=self.test_header,
                        time_of_validity=TypeTimestamp(
                            i * int(inertial_config.expected_dt * 1e9)
                        ),
                        imu_type=MeasurementImuImuType.INTEGRATED,
                        meas_accel=np.array([0.0, 0.1, 0.2]),
                        meas_gyro=np.array([1.0, 1.1, 1.2]),
                        integrity=[],
                    ),
                    source_identifier=IMU_CHANNEL,
                ),
                False,
            )
        assert (
            self.orchestration_plugin.fusion_engine.time.elapsed_nsec
            == self.orchestration_plugin.inertial_drift_prop_dt  # type: ignore[union-attr]
        )

    def test_process_pntos_message_alignment_tutorial(self) -> None:
        self.test_init_orchestration_plugin_tutorial()

        global ALIGNMENT_STATE
        ALIGNMENT_STATE = InitializationStatus.WAITING

        message = self.generate_imu_message(source_identifier=IMU_CHANNEL)

        self.orchestration_plugin.process_pntos_message(message, False)

    def test_process_pntos_message_just_imu(self) -> None:
        self.test_init_orchestration_plugin_tutorial()  # To get past init_orchestration_plugin()

        message = self.generate_imu_message(source_identifier=IMU_CHANNEL)

        self.orchestration_plugin.process_pntos_message(message, False)

    def test_process_pntos_message_just_imu_standard(self) -> None:
        self.test_init_orchestration_plugin_standard()  # To get past init_orchestration_plugin()

        message = self.generate_imu_message(source_identifier=IMU_CHANNEL)

        self.orchestration_plugin.process_pntos_message(message, False)

    def test_process_pntos_message_post_initialization_tutorial(self) -> None:
        self.test_init_orchestration_plugin_tutorial()  # To get past init_orchestration_plugin()

        imu_message = self.generate_imu_message(source_identifier=IMU_CHANNEL)

        self.orchestration_plugin.process_pntos_message(imu_message, False)

        pva_message = self.generate_pva_message(source_identifier=GPS_CHANNEL)

        self.orchestration_plugin.process_pntos_message(pva_message, False)

    def test_process_pntos_message_post_initialization_standard(self) -> None:
        self.test_init_orchestration_plugin_standard()

        imu_message = self.generate_imu_message(source_identifier=IMU_CHANNEL)

        self.orchestration_plugin.process_pntos_message(imu_message, False)

        pva_message = self.generate_pva_message(source_identifier=GPS_CHANNEL)

        self.orchestration_plugin.process_pntos_message(pva_message, False)

    def test_filter_description_list_tutorial(self) -> None:
        self.test_init_orchestration_plugin_tutorial()  # To get past init_orchestration_plugin()
        filter_description_list = self.orchestration_plugin.filter_description_list
        expected_filter_description_list = [
            'GPS_INS_BEST_ASPN_MEASUREMENT_POSITION_VELOCITY_ATTITUDE_ESTIMATE',
        ]
        assert filter_description_list == expected_filter_description_list

    def test_filter_description_list_standard(self) -> None:
        self.test_init_orchestration_plugin_standard()  # To get past init_orchestration_plugin()
        filter_description_list = self.orchestration_plugin.filter_description_list
        expected_filter_description_list = [
            'GPS_INS_BEST_ASPN_MEASUREMENT_POSITION_VELOCITY_ATTITUDE_ESTIMATE',
            'GPS_INS_DEAD_RECKONING_ASPN_MEASUREMENT_POSITION_VELOCITY_ATTITUDE_ESTIMATE',
        ]
        assert filter_description_list == expected_filter_description_list

    def test_request_solutions_pre_alignment_tutorial(self) -> None:
        self.test_init_orchestration_plugin_tutorial()  # To get past init_orchestration_plugin()
        solution_times = [TypeTimestamp(0)]
        expected_solution = self.expected_pva_best

        solutions = self.orchestration_plugin.request_solutions(solution_times)
        assert solutions is not None
        assert len(solutions) == 1
        assert self.compare_messages(solutions[0], expected_solution)

    def test_request_solutions_pre_alignment_standard(self) -> None:
        self.test_init_orchestration_plugin_standard()  # To get past init_orchestration_plugin()
        solution_times = [TypeTimestamp(0)]
        expected_solution = self.expected_pva_best

        solutions = self.orchestration_plugin.request_solutions(solution_times)
        assert solutions is not None
        assert len(solutions) == 1
        assert self.compare_messages(solutions[0], expected_solution)

    def test_request_solutions_post_alignment(self) -> None:
        self.test_init_orchestration_plugin_tutorial()
        solution_times = [TypeTimestamp(0)]
        expected_solution = self.expected_pva_best

        solutions = self.orchestration_plugin.request_solutions(solution_times)
        assert solutions is not None
        assert len(solutions) == 1
        assert self.compare_messages(solutions[0], expected_solution)

    def test_request_solutions_post_alignment_standard(self) -> None:
        self.test_process_pntos_message_just_imu_standard()
        solution_times = [TypeTimestamp(0)]
        expected_solution = self.expected_pva_best

        solutions = self.orchestration_plugin.request_solutions(solution_times)
        assert solutions is not None
        assert len(solutions) == 1
        assert self.compare_messages(solutions[0], expected_solution)

    def test_request_solutions_using_filter_descriptions(self) -> None:
        self.test_init_orchestration_plugin_tutorial()
        solution_times = [TypeTimestamp(100)]
        descriptions = self.orchestration_plugin.filter_description_list
        expected_descriptions = [
            'GPS_INS_BEST_ASPN_MEASUREMENT_POSITION_VELOCITY_ATTITUDE_ESTIMATE',
        ]
        expected_solutions = [self.expected_pva_best]
        assert descriptions == expected_descriptions
        for expected, description in zip(expected_solutions, descriptions, strict=True):
            solutions = self.orchestration_plugin.request_solutions(
                solution_times, description
            )
            assert solutions is not None
            assert len(solutions) == 1
            assert self.compare_messages(solutions[0], expected), solutions[0]

    def test_request_solutions_using_filter_descriptions_standard(self) -> None:
        self.test_init_orchestration_plugin_standard()
        solution_times = [TypeTimestamp(0)]
        descriptions = self.orchestration_plugin.filter_description_list
        expected_descriptions = [
            'GPS_INS_BEST_ASPN_MEASUREMENT_POSITION_VELOCITY_ATTITUDE_ESTIMATE',
            'GPS_INS_DEAD_RECKONING_ASPN_MEASUREMENT_POSITION_VELOCITY_ATTITUDE_ESTIMATE',
        ]
        expected_solutions = [self.expected_pva_best, self.expected_pva_dead_reckoning]
        assert descriptions == expected_descriptions
        for expected, description in zip(expected_solutions, descriptions, strict=True):
            solutions = self.orchestration_plugin.request_solutions(
                solution_times, description
            )
            assert solutions is not None
            assert len(solutions) == 1
            assert self.compare_messages(solutions[0], expected), solutions[0]

    def generate_position(self, time: TypeTimestamp) -> Message:
        position = MeasurementPosition(
            self.test_header,
            time,
            MeasurementPositionReferenceFrame.GEODETIC,
            1,
            2,
            3,
            np.eye(3),
            MeasurementPositionErrorModel.NONE,
            np.array([]),
            [],
        )
        return Message(position, GPS_CHANNEL)

    def generate_imu(self, time: TypeTimestamp) -> Message:
        dt = 1e-2  # 100Hz
        imu = MeasurementImu(
            self.test_header,
            time,
            MeasurementImuImuType.INTEGRATED,
            np.array([1e-12, 1e-12, -9.81]) * dt,
            np.array([1e-12, 1e-4, 1e-12]) * dt,
            [],
        )
        return Message(imu, IMU_CHANNEL)

    def test_process_pntos_message_before_aligned(self) -> None:
        static_time = 5.0
        align_config = StaticAlignmentConfig(
            group='config/static/alignment',
            static_time=static_time,
            imu_model=imu_config,
        )
        temp_config = deepcopy(standard_config)
        orch_config: StandardOrchestrationConfig = temp_config[1]  # type: ignore[assignment]
        orch_config.alignment_config = align_config
        static_alignment_plugin = StaticAlignInitializationPlugin(
            'Static Alignment Initialization Plugin'
        )
        plugins = self.instantiate_default_plugins(temp_config)
        plugins[0] = static_alignment_plugin
        self.orchestration_plugin = StandardOrchestrationPlugin(
            'StandardOrchestrationPlugin'
        )
        self.state_modeling_plugin = StandardGpsInsStateModelingPlugin(
            'Cobra Standard State Modeling Plugin'
        )
        plugins.append(self.orchestration_plugin)
        plugins.append(self.state_modeling_plugin)
        self.init_all_plugins(plugins)
        self.orchestration_plugin.init_orchestration_plugin(
            plugins, StandardMessageStreamConfig()
        )
        # Process messages until alignment
        pos_dt_centiseconds = 100  # 1 Hz
        align_time_centiseconds = int(static_time) * 100
        for ii in range(align_time_centiseconds + 3):
            time = TypeTimestamp(ii * 10000000)  # convert centiseconds to nanoseconds
            self.orchestration_plugin.process_pntos_message(
                self.generate_imu(time), False
            )
            # Add a position measurement every 100 iterations (but not on the last, since it has aligned
            # already)
            if ii % pos_dt_centiseconds == 0 and ii != align_time_centiseconds:
                self.orchestration_plugin.process_pntos_message(
                    self.generate_position(time), False
                )

        assert (
            self.orchestration_plugin.initializer.request_current_status()
            == InitializationStatus.INITIALIZED_GOOD
        )


def suite() -> unittest.TestSuite:
    suite = unittest.TestSuite()
    tests = [m for m in dir(Test_Orchestration) if m.startswith('test_')]
    for test in tests:
        suite.addTest(Test_Orchestration(test))
    return suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
