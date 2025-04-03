#!/usr/bin/env python3

# Grab the plugins we want off the shelf
from pntos.api import LoggingLevel
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
from pntos.cobra.config import AlignmentConfig, ImuConfig, InertialConfig, SensorConfig

# Set up configuration parameters
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
    AlignmentConfig(
        group='config/default/alignment',
        initial_pos_var=(9.0, 9.0, 9.0),
        initial_vel_var=(0.1, 0.1, 0.1),
        initial_tilt_var=(0.01, 0.01, 0.01),
        initial_accel_bias_var=(1e-10, 1e-10, 1e-10),
        initial_gyro_bias_var=(1e-15, 1e-15, 1e-15),
        initial_accel_bias=(0.00110907, 0.00051052, -0.02826087),
        initial_accel_scale_factor=(0.0, 0.0, 0.0),
        initial_accel_scale_factor_var=(0.0, 0.0, 0.0),
        initial_gyro_bias=(-0.00111542, -0.0016098, -0.00226504),
        initial_gyro_scale_factor=(0.0, 0.0, 0.0),
        initial_gyro_scale_factor_var=(0.0, 0.0, 0.0),
        initial_pos=(0.6941957531255563, -1.4675867257692263, 247.44),
        initial_rpy=(-1.80625601e-02, 3.92176685e-02, 0.13655456),
        initial_time=1741194282.046638768,
        initial_vel=(0.0, 0.0, 0.0),
    ),
    SensorConfig(
        group='config/gp3d_state_modeling',
        lever_arm=(0.0, 0.0, 0.0),
        orientation=(0.0, 0.0, 0.0, 0.0),
        source_identifier='lcm://cobranav/novatel',
        destination_identifier='gps_measurement_processor',
        use_for_alignment=True,
        sensor_name='novatel',
    ),
    InertialConfig(
        group='config/inertial', expected_dt=0.01, inertial_buffer_length=10.0
    ),
]

# Create all of our plugins
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
controller.take_control(
    plugins=plugins, plugin_resources_locations=None, initial_config=None
)
