#!/usr/bin/env python3

# API imports
from pntos.api import LoggingLevel

# Import Cobra plugins and config structs
from pntos.cobra import (
    Aspn23LcmTransportPlugin,
    SimpleControllerPlugin,
    SimpleEkfFusionStrategyPlugin,
    SimpleFusionPlugin,
    SimpleGpsInsStateModelingPlugin,
    SimpleInertialPlugin,
    SimpleInitializationPlugin,
    SimpleLoggingPlugin,
    SimpleOrchestrationPlugin,
    SimpleRegistryPlugin,
)
from pntos.cobra.config import (
    ImuConfig,
    InertialConfig,
    ManualAlignmentConfig,
    OrchestrationConfig,
    SensorConfig,
)

# Config setup
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
    ManualAlignmentConfig(
        group='config/default/alignment',
        initial_pos_var=(9.0, 9.0, 25.0),
        initial_vel_var=(1e-3, 1e-3, 1e-3),
        initial_tilt_var=(1e-3, 1e-3, 1e-3),
        initial_accel_bias_var=(1e-10, 1e-10, 1e-10),
        initial_gyro_bias_var=(1e-15, 1e-15, 1e-15),
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
        lever_arm=(0.0, 0.0, 0.0),
        orientation=(0.0, 0.0, 0.0, 0.0),
        use_for_alignment=True,
        sensor_name='novatel',
    ),
    InertialConfig(
        group='config/inertial', expected_dt=0.01, inertial_buffer_length=10.0
    ),
    OrchestrationConfig(
        imu_channel='/sensor/vn-100/imu',
        gps_channel='/sensor/ublox-ZED-F9T/position',
        group='config/orchestration',
    ),
]  # End Config

# Instantiate all of our plugins
controller = SimpleControllerPlugin('Cobra Simple Controller Plugin')
plugins = [
    Aspn23LcmTransportPlugin('Cobra Aspn23-lcm Transport Plugin'),
    SimpleEkfFusionStrategyPlugin('Cobra Simple Fusion Strategy Plugin'),
    SimpleFusionPlugin('Cobra Simple Fusion Plugin'),
    SimpleGpsInsStateModelingPlugin('Cobra Simple State Modeling Plugin'),
    SimpleInertialPlugin('Cobra Simple Inertial Plugin'),
    SimpleInitializationPlugin('Cobra Simple Initialization Plugin'),
    SimpleLoggingPlugin(
        'Cobra Simple Logging Plugin',
        global_log_level=LoggingLevel.INFO,  # Switch to `DEBUG` for more informative log output
    ),
    SimpleOrchestrationPlugin('Cobra Simple Orchestration Plugin'),
    SimpleRegistryPlugin('Cobra Simple Registry Plugin', config=my_config),
]

# Start the controller, and pass it all of the other plugins to use
controller.init_plugin()
controller.take_control(plugins)
