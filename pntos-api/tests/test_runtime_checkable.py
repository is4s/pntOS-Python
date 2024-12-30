import pntos.api as api


def test() -> None:
    """
    Ensure that isinstance and issubclass work on various objects and classes, respectively.

    This essentially tests for the existence of the @runtime_checkable decorator.
    """
    assert isinstance(MockControllerPlugin(), api.ControllerPlugin)
    assert isinstance(MockFusionPlugin(), api.FusionPlugin)
    assert isinstance(MockFusionStrategyPlugin(), api.FusionStrategyPlugin)
    assert isinstance(MockInertialPlugin(), api.InertialPlugin)
    assert isinstance(MockInitializationPlugin(), api.InitializationPlugin)
    assert isinstance(MockLoggingPlugin(), api.LoggingPlugin)
    assert isinstance(MockOrchestrationPlugin(), api.OrchestrationPlugin)
    assert isinstance(MockPlatformIntegrationPlugin(), api.PlatformIntegrationPlugin)
    assert isinstance(MockPreprocessorPlugin(), api.PreprocessorPlugin)
    assert isinstance(MockRegistryPlugin(), api.RegistryPlugin)
    assert isinstance(MockStateModelingPlugin(), api.StateModelingPlugin)
    assert isinstance(MockTransportPlugin(), api.TransportPlugin)
    assert isinstance(MockUiPlugin(), api.UiPlugin)

    assert issubclass(api.StandardInertialMechanization, api.CommonInertial)
    assert issubclass(api.ExternalInertial, api.CommonInertial)
    assert issubclass(
        api.InertialInitializationStrategy, api.CommonInitializationStrategy
    )
    assert issubclass(api.EwcInitializationStrategy, api.CommonInitializationStrategy)


class MockControllerPlugin(api.ControllerPlugin):
    identifier = ''

    def init_plugin(self, plugin_resources_location=None, mediator=None):
        return

    def shutdown_plugin(self):
        return

    def take_control(
        self, plugins, plugin_resources_locations=None, initial_config=None
    ):
        return


class MockFusionPlugin(api.FusionPlugin):
    identifier = ''

    def init_plugin(self, plugin_resources_location=None, mediator=None):
        return

    def shutdown_plugin(self):
        return

    def is_fusion_type_supported(self, type):
        return False

    def new_fusion_engine(self, type):
        return None


class MockFusionStrategyPlugin(api.FusionStrategyPlugin):
    identifier = ''

    def init_plugin(self, plugin_resources_location=None, mediator=None):
        return

    def shutdown_plugin(self):
        return

    def is_fusion_type_supported(self, fusion_type):
        return False

    def new_fusion_strategy(self, fusion_type):
        return None


class MockInertialPlugin(api.InertialPlugin):
    identifier = ''

    def init_plugin(self, plugin_resources_location=None, mediator=None):
        return

    def shutdown_plugin(self):
        return

    def is_inertial_type_supported(self, type):
        return False

    def new_inertial(self, type, solution, config_group=None):
        return None


class MockInitializationPlugin(api.InitializationPlugin):
    identifier = ''

    def init_plugin(self, plugin_resources_location=None, mediator=None):
        return

    def shutdown_plugin(self):
        return

    def is_initialization_type_supported(self, type):
        return False

    def new_initialization_strategy(self, type, config_group=None):
        return None


class MockLoggingPlugin(api.LoggingPlugin):
    identifier = ''

    def init_plugin(self, plugin_resources_location=None, mediator=None):
        return

    def shutdown_plugin(self):
        return

    def log(self, source_plugin_type, source_plugin_identifier, level, message):
        return


class MockOrchestrationPlugin(api.OrchestrationPlugin):
    identifier = ''

    def init_plugin(self, plugin_resources_location=None, mediator=None):
        return

    def shutdown_plugin(self):
        return

    def init_orchestration_plugin(self, plugins, stream_config):
        return

    def get_filter_description_list(self):
        return None

    def process_pntos_message(self, message, sequenced):
        return

    def request_solutions(self, solution_times, filter_description=None):
        return None


class MockPlatformIntegrationPlugin(api.PlatformIntegrationPlugin):
    identifier = ''

    def init_plugin(self, plugin_resources_location=None, mediator=None):
        return

    def shutdown_plugin(self):
        return

    def take_control(
        self, plugins, plugin_resources_locations=None, initial_config=None
    ):
        return


class MockPreprocessorPlugin(api.PreprocessorPlugin):
    identifier = ''

    def init_plugin(self, plugin_resources_location=None, mediator=None):
        return

    def shutdown_plugin(self):
        return

    preprocessor_identifiers = ['']

    def new_preprocessor(self, preprocessor_index, config_group=None):
        return None


class MockRegistryPlugin(api.RegistryPlugin):
    identifier = ''

    def init_plugin(self, plugin_resources_location=None, mediator=None):
        return

    def shutdown_plugin(self):
        return

    def new_registry(self, initial_config=None):
        return None


class MockStateModelingPlugin(api.StateModelingPlugin):
    identifier = ''

    def init_plugin(self, plugin_resources_location=None, mediator=None):
        return

    def shutdown_plugin(self):
        return

    def is_fusion_type_supported(self, type):
        return False

    def new_state_model_provider(self, type):
        return None


class MockTransportPlugin(api.TransportPlugin):
    identifier = ''

    def init_plugin(self, plugin_resources_location=None, mediator=None):
        return

    def shutdown_plugin(self):
        return

    def broadcast_message(self, message, channel_name=None):
        return

    def start_listening(self):
        return

    def stop_listening(self):
        return


class MockUiPlugin(api.UiPlugin):
    identifier = ''

    def init_plugin(self, plugin_resources_location=None, mediator=None):
        return

    def shutdown_plugin(self):
        return

    def requires_main_thread(self):
        return False

    def run_main_thread(self):
        return


if __name__ == '__main__':
    test()
