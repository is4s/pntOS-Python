#!/usr/bin/env python3

# API imports
from pntos.api import LoggingLevel

# Import Cobra plugins and config structs
from pntos.cobra import (
    LcmTransportPlugin,
    SimpleCobraPreprocessorPlugin,
    SimpleControllerPlugin,
    SimpleEkfFusionStrategyPlugin,
    SimpleFusionPlugin,
    SimpleGpsInsStateModelingPlugin,
    SimpleGpsVelOrchestrationPlugin,
    SimpleInertialPlugin,
    SimpleInitializationPlugin,
    SimpleLoggingPlugin,
    SimpleRegistryPlugin,
)
from pntos.cobra.config import (
    FogmConfig,
    ImuConfig,
    InertialConfig,
    LcmTransportConfig,
    ManualAlignmentConfig,
    OrchestrationConfig,
    SensorConfig,
    TimeAdjusterConfig,
)
from pntos.cobra.config.LcmTransportConfig import AspnVersion

# Config setup
my_config = [
    LcmTransportConfig(output_version=AspnVersion.V23, group='config/lcm_transport'),
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
        use_for_alignment=True,
        sensor_name='position',
    ),
    InertialConfig(
        group='config/inertial',
        expected_dt=0.01,
        channel='/sensor/vn-100/imu',
        C_imu_to_platform=(
            (0.99776363, 0.01784622, 0.06441467),
            (-0.01741603, 0.99982216, -0.00723391),
            (-0.06453231, 0.00609588, 0.997897),
        ),
        inertial_buffer_length=10.0,
    ),
    FogmConfig(
        group='config/pos_sensor_error',
        sigma=(1.5, 1.5, 2.0),
        tau=(300.0, 300.0, 200.0),
    ),
    OrchestrationConfig(
        gps_channel='/sensor/ublox-ZED-F9T/position',
        group='config/orchestration',
        velocity_channel='/sensor/ublox-ZED-F9T/velocity',
    ),
    TimeAdjusterConfig(
        group='config/time_adjuster',
        channel_to_correct='/sensor/vn-100/imu',
        expected_dt_nsec=int(0.01 * 1e9),
    ),
]
# End Config

# Instantiate all of our plugins
controller = SimpleControllerPlugin('Cobra Simple Controller Plugin')
plugins = [
    LcmTransportPlugin('Cobra LCM Transport Plugin'),
    SimpleEkfFusionStrategyPlugin('Cobra Simple Fusion Strategy Plugin'),
    SimpleFusionPlugin('Cobra Simple Fusion Plugin'),
    SimpleGpsInsStateModelingPlugin('Cobra Simple State Modeling Plugin'),
    SimpleInertialPlugin('Cobra Simple Inertial Plugin'),
    SimpleInitializationPlugin('Cobra Simple Initialization Plugin'),
    SimpleLoggingPlugin(
        'Cobra Simple Logging Plugin',
        global_log_level=LoggingLevel.INFO,  # Switch to `DEBUG` for more informative log output
    ),
    SimpleGpsVelOrchestrationPlugin('Cobra Simple Orchestration Plugin'),
    SimpleRegistryPlugin('Cobra Simple Registry Plugin', config=my_config),
    SimpleCobraPreprocessorPlugin('Cobra Simple Preprocessor Plugin'),
]

# Start the controller, and pass it all of the other plugins to use
controller.init_plugin()
controller.take_control(plugins)
