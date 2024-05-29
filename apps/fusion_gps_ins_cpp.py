from pntos.cobra import (
    SimpleControllerPlugin,
    SimpleOrchestrationPlugin,
    SimpleRegistryPlugin,
)
from pntos.cobra.config import (
    AlignmentConfig,
    ImuConfig,
)
from pntos.cppsdk import LoadCppPlugin  # type: ignore

my_config = [
    ImuConfig(
        accel_bias_sigma=(0.0098, 0.0098, 0.0098),
        accel_bias_tau=(3600.0, 3600.0, 3600.0),
        gyro_bias_sigma=(1.234e-6, 1.234e-6, 1.234e-6),
        gyro_bias_tau=(3600.0, 3600.0, 3600.0),
    ),
    AlignmentConfig(
        initialPosCov=(9.0, 9.0, 9.0),
        initialVelCov=(0.1, 0.1, 0.1),
        initialTiltCov=(0.01, 0.01, 0.01),
        initialAccelBiasCov=(9.604e-5, 9.604e-5, 9.604e-5),
        initialGyroBiasCov=(2.3504074e-11, 2.3504074e-11, 2.3504074e-11),
    ),
]

# Create all of our plugins

controller = SimpleControllerPlugin(identifier="my_controller")
orchestration = SimpleOrchestrationPlugin(identifier="my_orchestration")
registry = SimpleRegistryPlugin(identifier="my_registry", config=my_config)
sensor_baronav = LoadCppPlugin("libviper.so.1", "viper_baronav_plugin")

# Start the controller, and pass it all of the other plugins to use

controller.init_plugin(None, None)
controller.take_control([orchestration, registry, sensor_baronav], [], None)
