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
        accel_bias_sigma=(0.0098, 0.0098, 0.0098),
        accel_bias_tau=(3600.0, 3600.0, 3600.0),
        accel_random_walk_sigma=(0.001, 0.001, 0.001),
        gyro_bias_sigma=(1.234e-6, 1.234e-6, 1.234e-6),
        gyro_bias_tau=(3600.0, 3600.0, 3600.0),
        gyro_random_walk_sigma=(0.001, 0.001, 0.001),
    ),
    AlignmentConfig(
        group='config/default/alignment',
        initial_pos_var=(9.0, 9.0, 9.0),
        initial_vel_var=(0.1, 0.1, 0.1),
        initial_tilt_var=(0.01, 0.01, 0.01),
        initial_accel_bias_var=(9.604e-5, 9.604e-5, 9.604e-5),
        initial_gyro_bias_var=(2.3504074e-11, 2.3504074e-11, 2.3504074e-11),
        initial_accel_bias=(0.0, 0.0, 0.0),
        initial_accel_scale_factor=(0.0, 0.0, 0.0),
        initial_accel_scale_factor_var=(0.0, 0.0, 0.0),
        initial_gyro_bias=(0.0, 0.0, 0.0),
        initial_gyro_scale_factor=(0.0, 0.0, 0.0),
        initial_gyro_scale_factor_var=(0.0, 0.0, 0.0),
        initial_pos=(0.6941957531255563, -1.4675867257692263, 247.44),
        initial_rpy=(0.0, 0.0, 0.0),
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
