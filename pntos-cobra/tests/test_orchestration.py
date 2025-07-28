import unittest

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
from navtk.navutils import rpy_to_quat
from numpy import float64
from pntos.api import (
    FusionEngineType,
    FusionPlugin,
    FusionStrategyPlugin,
    FusionStrategyType,
    InertialPlugin,
    InertialType,
    InitializationPlugin,
    InitializationStatus,
    InitializationType,
    Message,
    OrchestrationPlugin,
    StateModelingPlugin,
    StateModelProviderType,
)
from pntos.api.plugins.registry import RegistryPlugin
from pntos.cobra import (
    EkfFusionStrategyPlugin,
    SimpleGpsInsStateModelingPlugin,
    SimpleGpsOrchestrationPlugin,
    StandardFusionPlugin,
    StandardInertialPlugin,
    StandardRegistryPlugin,
    TutorialInitializationPlugin,
)
from pntos.cobra.config import (
    FogmConfig,
    ImuConfig,
    InertialConfig,
    ManualAlignmentConfig,
    OrchestrationConfig,
    SensorConfig,
)
from pntos.cobra.internal import SimpleMediator, SimpleMessageStreamConfig

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
align_config = ManualAlignmentConfig(
    group='config/default/alignment',
    initial_pos_var=(0, 0, 0),
    initial_vel_var=(0, 0, 0),
    initial_tilt_var=(0, 0, 0),
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
my_config = [
    ImuConfig(
        group='config/inertial_state',
        accel_bias_sigma=(3.924e-5, 3.924e-5, 3.924e-5),
        accel_bias_tau=(1800.0, 1800.0, 1800.0),
        accel_random_walk_sigma=(3.887e-6, 3.887e-6, 3.887e-6),
        gyro_bias_sigma=(8.848e-5, 8.848e-5, 8.848e-5),
        gyro_bias_tau=(1800.0, 1800.0, 1800.0),
        gyro_random_walk_sigma=(1.7277877e-7, 1.7277877e-7, 1.7277877e-7),
    ),
    align_config,
    SensorConfig(
        group='config/gp3d_state_modeling',
        lever_arm=(0.0, 0.0, 0.0),
        orientation=(0.0, 0.0, 0.0, 0.0),
        use_for_alignment=True,
        sensor_name='novatel',
    ),
    InertialConfig(
        group='config/inertial',
        expected_dt=0.01,
        channel='/sensor/vn-100/imu',
        C_imu_to_platform=((1, 0, 0), (0, 1, 0), (0, 0, 1)),
        inertial_buffer_length=10.0,
    ),
    FogmConfig(
        group='config/pos_sensor_error',
        sigma=(1.5, 1.5, 10.0),
        tau=(30.0, 30.0, 300000.0),
    ),
    OrchestrationConfig(
        gps_channel='/sensor/ublox-ZED-F9T/position',
        group='config/orchestration',
    ),
]


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
        self.orchestration_plugin: OrchestrationPlugin = SimpleGpsOrchestrationPlugin(
            'SimpleGpsOrchestrationPlugin'
        )
        self.initialization_plugin: InitializationPlugin = TutorialInitializationPlugin(
            'Cobra Simple Initialization Plugin'
        )
        self.inertial_plugin: InertialPlugin = StandardInertialPlugin(
            'Cobra Simple Inertial Plugin'
        )
        self.fusion_plugin: FusionPlugin = StandardFusionPlugin(
            'Cobra Simple Fusion Plugin'
        )
        self.fusion_strategy_plugin: FusionStrategyPlugin = EkfFusionStrategyPlugin(
            'Cobra Simple Fusion Strategy Plugin'
        )
        self.state_modeling_plugin: StateModelingPlugin = (
            SimpleGpsInsStateModelingPlugin('Cobra Simple State Modeling Plugin')
        )
        self.registry_plugin: StandardRegistryPlugin = StandardRegistryPlugin(
            'StandardRegistryPlugin'
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

        registry_plugin = StandardRegistryPlugin('Simple registry', config=my_config)
        mediator = SimpleMediator(registry_plugin.identifier, RegistryPlugin)
        registry_plugin.init_plugin(mediator=mediator)
        registry = registry_plugin.new_registry()
        SimpleMediator.registry = registry
        SimpleMediator._controller_plugin = None
        # Run init_plugin on all the plugins
        for plugin in plugins:
            plugin.init_plugin(mediator=mediator)

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
                covariance=np.zeros([9, 9]),
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
            print('m1 {}'.format(m1))
            print('m2 {}'.format(m2))
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
        assert solutions is not None
        assert len(solutions) == 1
        print(solutions[0])
        print(expected_solution)
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
            assert solutions is not None
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
