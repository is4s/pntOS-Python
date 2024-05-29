from pntos.cobra import (
    SimpleControllerPlugin,
    SimpleOrchestrationPlugin,
    SimpleRegistryPlugin,
)

my_config = {"a": 5, "b": "3"}

# List of all the plugins we've loaded, except the controller
plugin_list = [
    SimpleOrchestrationPlugin(identifier="my_orchestration"),
    SimpleRegistryPlugin(identifier="my_registry", config=my_config),
]

controller = SimpleControllerPlugin("my_controller")
controller.init_plugin(None, None)
controller.take_control(plugin_list, [], None)
