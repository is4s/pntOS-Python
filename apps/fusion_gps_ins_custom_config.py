# Grab the plugins we want off the shelf

from pntos.cobra import (
    SimpleControllerPlugin,
    SimpleOrchestrationPlugin,
    SimpleRegistryPlugin,
)
from pntos.cobra.config import (
    AlignmentConfig,
    ImuConfig,
    SensorConfig,
)

# Set up configuration parameters manually by convention, with
# additional custom config

my_config = [
    ImuConfig(
        group="/my/custom/imu/group",
        accel_bias_sigma=(0.0098, 0.0098, 0.0098),
        accel_bias_tau=(3600.0, 3600.0, 3600.0),
        accel_rw_sigma=(0.001, 0.001, 0.001),
        gyro_bias_sigma=(1.234e-6, 1.234e-6, 1.234e-6),
        gyro_bias_tau=(3600.0, 3600.0, 3600.0),
        gyro_rw_sigma=(0.001, 0.001, 0.001),
    ),
    AlignmentConfig(
        group="/my/custom/alignment/group",
        initialPosCov=(9.0, 9.0, 9.0),
        initialVelCov=(0.1, 0.1, 0.1),
        initialTiltCov=(0.01, 0.01, 0.01),
        initialAccelBiasCov=(9.604e-5, 9.604e-5, 9.604e-5),
        initialGyroBiasCov=(2.3504074e-11, 2.3504074e-11, 2.3504074e-11),
    ),
    SensorConfig(
        group="/my/custom/sensor/group",
        lever_arm=(0.0, 0.0, 0.0),
        orientation=(0.0, 0.0, 0.0, 0.0),
        source_identifier="lcm://cobranav/novatel",
        destination_identifier="gps_measurement_processor",
        use_for_alignment=True,
        sensor_name="novatel",
    ),
    "/some/other/group",
    {
        "some_key": "some_value",
        "my_value": (1, 2, 3),
        "some_other": ((1, 2, 3), (1, 2, 3)),
    },
    "/some/other/group2",
    {"some_other_key": "some_other_value"},
]


# Create all of our plugins

controller = SimpleControllerPlugin(identifier="my_controller")
orchestration = SimpleOrchestrationPlugin(identifier="my_orchestration")
registry = SimpleRegistryPlugin(identifier="my_registry", config=my_config)

# Start the controller, and pass it all of the other plugins to use

controller.init_plugin(None, None)
controller.take_control([orchestration, registry], [], None)
