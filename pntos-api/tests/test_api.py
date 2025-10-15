from abc import ABC

from pntos import api


def assert_is_only_instance(plugin: api.CommonPlugin, expected_type: type[ABC]) -> None:
    """Asserts that the given plugin is of the expected type and no other."""
    assert issubclass(expected_type, api.CommonPlugin)
    all_plugin_types = [
        api.ControllerPlugin,
        api.FusionPlugin,
        api.FusionStrategyPlugin,
        api.InertialPlugin,
        api.InitializationPlugin,
        api.LoggingPlugin,
        api.OrchestrationPlugin,
        api.PlatformIntegrationPlugin,
        api.PreprocessorPlugin,
        api.RegistryPlugin,
        api.StateModelingPlugin,
        api.TransportPlugin,
        api.UiPlugin,
    ]
    assert isinstance(plugin, expected_type)
    all_plugin_types.remove(expected_type)
    for other_type in all_plugin_types:
        assert not isinstance(plugin, other_type)


def test_inheritance() -> None:
    """Ensure that isinstance and issubclass work on various objects and classes, respectively."""
    assert_is_only_instance(MockControllerPlugin(), api.ControllerPlugin)
    assert_is_only_instance(MockFusionPlugin(), api.FusionPlugin)
    assert_is_only_instance(MockFusionStrategyPlugin(), api.FusionStrategyPlugin)
    assert_is_only_instance(MockInertialPlugin(), api.InertialPlugin)
    assert_is_only_instance(MockInitializationPlugin(), api.InitializationPlugin)
    assert_is_only_instance(MockLoggingPlugin(), api.LoggingPlugin)
    assert_is_only_instance(MockOrchestrationPlugin(), api.OrchestrationPlugin)
    assert_is_only_instance(
        MockPlatformIntegrationPlugin(), api.PlatformIntegrationPlugin
    )
    assert_is_only_instance(MockPreprocessorPlugin(), api.PreprocessorPlugin)
    assert_is_only_instance(MockRegistryPlugin(), api.RegistryPlugin)
    assert_is_only_instance(MockStateModelingPlugin(), api.StateModelingPlugin)
    assert_is_only_instance(MockTransportPlugin(), api.TransportPlugin)
    assert_is_only_instance(MockUiPlugin(), api.UiPlugin)

    assert issubclass(api.StandardInertialMechanization, api.CommonInertial)
    assert issubclass(api.ExternalInertial, api.CommonInertial)

    assert issubclass(
        api.InertialInitializationStrategy, api.CommonInitializationStrategy
    )
    assert issubclass(api.EwcInitializationStrategy, api.CommonInitializationStrategy)


def test_type_parameters() -> None:
    """Ensure that type parameters work as expected."""
    fusion_plugin = MockFusionPlugin()
    fusion_plugin.is_fusion_type_supported(api.StandardFusionEngine)
    fusion_plugin.new_fusion_engine(api.StandardFusionEngine)

    fusion_strategy_plugin = MockFusionStrategyPlugin()
    fusion_strategy_plugin.is_fusion_type_supported(api.StandardFusionStrategy)
    fusion_strategy_plugin.new_fusion_strategy(api.StandardFusionStrategy)

    inertial_plugin = MockInertialPlugin()
    inertial_plugin.is_inertial_type_supported(api.StandardInertialMechanization)
    inertial_plugin.new_inertial(
        api.StandardInertialMechanization, api.Message(None, ''), None
    )

    initialization_plugin = MockInitializationPlugin()
    initialization_plugin.is_initialization_type_supported(
        api.InertialInitializationStrategy
    )
    initialization_plugin.new_initialization_strategy(
        api.InertialInitializationStrategy
    )

    logging_plugin = MockLoggingPlugin()
    logging_plugin.log(api.LoggingPlugin, 'test', api.LoggingLevel.DEBUG, 'test')


class MockControllerPlugin(api.ControllerPlugin):
    identifier = ''

    def init_plugin(self, plugin_resources_location=None, mediator=None) -> None:  # type: ignore
        return

    def shutdown_plugin(self) -> None:
        return

    def take_control(  # type: ignore
        self,
        plugins,
        plugin_resources_locations=None,
        initial_config=None,
    ) -> None:
        return


class MockFusionPlugin(api.FusionPlugin):
    identifier = ''

    def init_plugin(self, plugin_resources_location=None, mediator=None) -> None:  # type: ignore
        return

    def shutdown_plugin(self) -> None:
        return

    def is_fusion_type_supported(self, type: type[api.FusionEngineType]) -> bool:
        return False

    def new_fusion_engine(
        self, type: type[api.FusionEngineType]
    ) -> api.FusionEngineType | None:
        return None


class MockFusionStrategyPlugin(api.FusionStrategyPlugin):
    identifier = ''

    def init_plugin(self, plugin_resources_location=None, mediator=None) -> None:  # type: ignore
        return

    def shutdown_plugin(self) -> None:
        return

    def is_fusion_type_supported(
        self, fusion_type: type[api.FusionStrategyType]
    ) -> bool:
        return False

    def new_fusion_strategy(
        self, fusion_type: type[api.FusionStrategyType]
    ) -> api.FusionStrategyType | None:
        return None


class MockInertialPlugin(api.InertialPlugin):
    identifier = ''

    def init_plugin(self, plugin_resources_location=None, mediator=None) -> None:  # type: ignore
        return

    def shutdown_plugin(self) -> None:
        return

    def is_inertial_type_supported(self, type: type[api.InertialType]) -> bool:
        return False

    def new_inertial(
        self,
        type: type[api.InertialType],
        solution: api.Message,
        config_group: str | None = None,
    ) -> api.InertialType | None:
        return None


class MockInitializationPlugin(api.InitializationPlugin):
    identifier = ''

    def init_plugin(self, plugin_resources_location=None, mediator=None) -> None:  # type: ignore
        return

    def shutdown_plugin(self) -> None:
        return

    def is_initialization_type_supported(
        self, type: type[api.InitializationType]
    ) -> bool:
        return False

    def new_initialization_strategy(
        self, type: type[api.InitializationType], config_group: str | None = None
    ) -> api.InitializationType | None:
        return None


class MockLoggingPlugin(api.LoggingPlugin):
    identifier = ''

    def init_plugin(self, plugin_resources_location=None, mediator=None) -> None:  # type: ignore
        return

    def shutdown_plugin(self) -> None:
        return

    def log(
        self,
        source_plugin_type: api.PluginType,
        source_plugin_identifier: str,
        level: api.LoggingLevel,
        message: str,
    ) -> None:
        return


class MockOrchestrationPlugin(api.OrchestrationPlugin):
    identifier = ''

    def init_plugin(self, plugin_resources_location=None, mediator=None) -> None:  # type: ignore
        return

    def shutdown_plugin(self) -> None:
        return

    def init_orchestration_plugin(self, plugins, stream_config) -> None:  # type: ignore
        return

    def filter_description_list(self) -> None:  # type: ignore
        return None

    def process_pntos_message(self, message, sequenced) -> None:  # type: ignore
        return

    def request_solutions(self, solution_times, filter_description=None) -> None:  # type: ignore
        return None


class MockPlatformIntegrationPlugin(api.PlatformIntegrationPlugin):
    identifier = ''

    def init_plugin(self, plugin_resources_location=None, mediator=None) -> None:  # type: ignore
        return

    def shutdown_plugin(self) -> None:
        return

    def take_control(  # type: ignore
        self, plugins, plugin_resources_locations=None, initial_config=None
    ) -> None:
        return


class MockPreprocessorPlugin(api.PreprocessorPlugin):
    identifier = ''

    def __init__(self) -> None:
        self.preprocessor_identifiers = ['']

    def init_plugin(self, plugin_resources_location=None, mediator=None) -> None:  # type: ignore
        return

    def shutdown_plugin(self) -> None:
        return

    def new_preprocessor(self, preprocessor_index, config_group=None) -> None:  # type: ignore
        return None


class MockRegistryPlugin(api.RegistryPlugin):
    identifier = ''

    def init_plugin(self, plugin_resources_location=None, mediator=None) -> None:  # type: ignore
        return

    def shutdown_plugin(self) -> None:
        return

    def new_registry(self, initial_config=None) -> None:  # type: ignore
        return None


class MockStateModelingPlugin(api.StateModelingPlugin):
    identifier = ''

    def init_plugin(self, plugin_resources_location=None, mediator=None) -> None:  # type: ignore
        return

    def shutdown_plugin(self) -> None:
        return

    def is_fusion_type_supported(self, type) -> bool:  # type: ignore
        return False

    def new_state_model_provider(self, type) -> None:  # type: ignore
        return None


class MockTransportPlugin(api.TransportPlugin):
    identifier = ''

    def init_plugin(self, plugin_resources_location=None, mediator=None) -> None:  # type: ignore
        return

    def shutdown_plugin(self) -> None:
        return

    def broadcast_message(self, message, channel_name=None) -> None:  # type: ignore
        return

    def start_listening(self) -> None:
        return

    def stop_listening(self) -> None:
        return


class MockUiPlugin(api.UiPlugin):
    identifier = ''

    def init_plugin(self, plugin_resources_location=None, mediator=None) -> None:  # type: ignore
        return

    def shutdown_plugin(self) -> None:
        return

    def requires_main_thread(self) -> bool:
        return False

    def run_main_thread(self) -> None:
        return


if __name__ == '__main__':
    test_inheritance()
    test_type_parameters()
