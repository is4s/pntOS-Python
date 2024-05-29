# Grab the plugins we want off the shelf

from pntos.cobra import (
    SimpleControllerPlugin,
    SimpleOrchestrationPlugin,
    SimpleRegistryPlugin,
)

# Set up configuration parameters

my_config = {}
my_config["imu_params"] = {"a": 5, "b": "c"}
my_config["lever_arms"] = {"aa": 123}


# Create all of our plugins

plugin_list = [
    SimpleOrchestrationPlugin(identifier="my_orchestration"),
    SimpleRegistryPlugin(identifier="my_registry", config=my_config),
]

controller = SimpleControllerPlugin("my_controller")

# Start the controller, and pass it all of the other plugins to use

controller.init_plugin(None, None)
controller.take_control(plugin_list, [], None)
