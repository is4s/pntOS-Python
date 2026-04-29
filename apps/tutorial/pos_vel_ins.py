#!/usr/bin/env python3

import sys

# API imports
from pntos.api import LoggingLevel

# Import Cobra plugins and config structs
from pntos.cobra import (
    EkfFusionStrategyPlugin,
    LcmLogTransportPlugin,
    StandardControllerPlugin,
    StandardFusionPlugin,
    StandardInertialPlugin,
    StandardLoggingPlugin,
    StandardPreprocessorPlugin,
    StandardRegistryPlugin,
    TutorialInitializationPlugin,
    TutorialPosInsStateModelingPlugin,
    TutorialPosVelOrchestrationPlugin,
    UiLogPlottingPlugin,
)
from pntos.cobra.config import (
    AspnVersion,
    ControllerConfig,
    FogmConfig,
    FusionEngineConfig,
    ImuConfig,
    ImuRotatorConfig,
    InertialConfig,
    LcmLogTransportConfig,
    ManualAlignmentConfig,
    SensorConfig,
    TimeAdjusterConfig,
    TimeBiasConfig,
    TutorialOrchestrationConfig,
    UiLogPlottingConfig,
)
from pntos_python_datasets import EXAMPLE_LCM_LOG

OUTPUT_LOG = sys.argv[1] if len(sys.argv) > 1 else 'pntos_output.log'

# Config setup
C_imu_to_platform = (
    (0.99802515, 0.01772605, 0.06026269),
    (-0.01742059, 0.99983262, -0.00559042),
    (-0.0603517, 0.00452957, 0.9981669),
)
my_config = [
    LcmLogTransportConfig(
        input_file=EXAMPLE_LCM_LOG,
        output_file=OUTPUT_LOG,
        output_version=AspnVersion.V23,
    ),
    ControllerConfig(),
    FusionEngineConfig(),
    ImuConfig(
        group='config/inertial_state',
        accel_bias_sigma=(2.4e-3, 2.4e-3, 2.4e-3),
        accel_bias_tau=(300.0, 300.0, 300.0),
        accel_random_walk_sigma=(3.887e-6, 3.887e-6, 3.887e-6),
        gyro_bias_sigma=(2e-4, 2e-4, 2e-4),
        gyro_bias_tau=(500.0, 500.0, 500.0),
        gyro_random_walk_sigma=(9.9e-4, 9.9e-4, 6.7e-5),
    ),
    ManualAlignmentConfig(
        group='config/default/alignment',
        initial_pos_var=(0.1, 0.1, 0.1),
        initial_vel_var=(1e-3, 1e-3, 1e-3),
        initial_tilt_var=(5e-4, 5e-4, 5e-4),
        initial_accel_bias_var=(5.2e-3, 5.2e-3, 5.2e-3),
        initial_gyro_bias_var=(9e-6, 9e-6, 9e-6),
        initial_accel_bias=(-0.0023383, 0.00085563, -0.05412892),
        initial_accel_scale_factor=(0.0, 0.0, 0.0),
        initial_accel_scale_factor_var=(0.0, 0.0, 0.0),
        initial_gyro_bias=(-0.00160958, -0.00204483, -0.00267885),
        initial_gyro_scale_factor=(0.0, 0.0, 0.0),
        initial_gyro_scale_factor_var=(0.0, 0.0, 0.0),
        initial_pos=(0.6938996038254822, -1.4679920679462133, 225.493),
        initial_rpy=(-0.014713125594312194, -0.040718531449027706, 0.06895795874629593),
        initial_time=1747680879.539799718,
        initial_vel=(0.0, 0.0, 0.0),
    ),
    SensorConfig(
        group='config/gp3d_state_modeling',
        lever_arm=(-0.50, 0.38, -0.05),
        orientation=(0.0, 0.0, 0.0, 0.0),
        sensor_name='position',
    ),
    InertialConfig(
        group='config/inertial',
        expected_dt=0.01,
        channels=('/sensor/vn-100/imu',),
        C_imu_to_platform=C_imu_to_platform,
        inertial_buffer_length=10.0,
    ),
    FogmConfig(
        group='config/pos_sensor_error',
        sigma=(1.5, 1.5, 2.0),
        tau=(300.0, 300.0, 200.0),
    ),
    TutorialOrchestrationConfig(
        position_channel='/sensor/ublox-ZED-F9T/position',
        velocity_channel='/sensor/ublox-ZED-F9T/velocity',
    ),
    TimeAdjusterConfig(
        group='config/time_adjuster',
        channel_to_correct='/sensor/vn-100/imu',
        expected_dt_nsec=int(0.01 * 1e9),
    ),
    UiLogPlottingConfig(
        logfile=OUTPUT_LOG,
        solution_channel='/solution/pntos/pva',
        truth_channel='/sensor/ins-d/pva',
    ),
    ImuRotatorConfig(
        group='config/imu_rotator',
        C_imu_to_platform=C_imu_to_platform,
        channel='/sensor/vn-100/imu',
    ),
    TimeBiasConfig(
        group='config/time_bias',
        channels_to_correct=(
            '/sensor/ublox-ZED-F9T/position',
            '/sensor/ublox-ZED-F9T/velocity',
        ),
        time_bias=int(0.15 * 1e9),
    ),
]
# End Config

# Instantiate all of our plugins
controller = StandardControllerPlugin('Cobra Standard Controller Plugin')
plugins = [
    LcmLogTransportPlugin('Cobra LCM Log Transport Plugin'),
    EkfFusionStrategyPlugin('Cobra EKF Fusion Strategy Plugin'),
    StandardFusionPlugin('Cobra Standard Fusion Plugin'),
    TutorialPosInsStateModelingPlugin('Cobra Tutorial State Modeling Plugin'),
    StandardInertialPlugin('Cobra Standard Inertial Plugin'),
    TutorialInitializationPlugin('Cobra Manual Initialization Plugin'),
    StandardLoggingPlugin(
        'Cobra Standard Logging Plugin',
        global_log_level=LoggingLevel.INFO,  # Switch to `DEBUG` for more informative log output
    ),
    StandardRegistryPlugin('Cobra Standard Registry Plugin', config=my_config),
    StandardPreprocessorPlugin('Cobra Standard Preprocessor Plugin'),
    UiLogPlottingPlugin('Cobra UI Logfile Plotting Plugin'),
    TutorialPosVelOrchestrationPlugin('Cobra Tutorial Orchestration Plugin'),
]

# Start the controller, and pass it all of the other plugins to use
controller.init_plugin()
controller.take_control(plugins)
