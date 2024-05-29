from pntos.cobra import (
    SimpleControllerPlugin,
    SimpleOrchestrationPlugin,
    SimpleRegistryPlugin,
)
from pntos.cppsdk import LoadCppPlugin

my_config = {}
my_config["imu_params"] = {"a": 5, "b": "c"}
my_config["lever_arms"] = {"aa": 123}

# List of all the plugins we've loaded, except the controller
plugin_list = [
    SimpleOrchestrationPlugin(identifier="my_orchestration"),
    SimpleRegistryPlugin(identifier="my_registry", config=my_config),
    LoadCppPlugin("libviper.so.1", plugin_name="viper_transport_lcm"),
]

controller = SimpleControllerPlugin("my_controller")
controller.init_plugin(None, None)
controller.take_control(plugin_list, [], None)
