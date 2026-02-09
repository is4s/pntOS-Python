import pytest
from aspn23 import (
    TypeTimestamp,
)
from pntos.api import (
    CommonPlugin,
    ControllerPlugin,
    LoggingLevel,
    Mediator,
    Message,
    Registry,
    TransportPlugin,
    UiPlugin,
    UtilityPlugin,
)
from pntos.cobra import (
    BuscatControllerPlugin,
    StandardLoggingPlugin,
    StandardRegistryPlugin,
)
from pntos.cobra.config import BaseConfig, BuscatConfig
from pntos.cobra.internal import BuscatMediator

FOUND_ERROR = False
ERROR_MESSAGE = ''


class DummyUtilityPlugin(UtilityPlugin):
    def __init__(self, identifier: str) -> None:
        self.identifier = identifier
        self.timer = None

    def init_plugin(
        self,
        plugin_resources_location: str | None = None,
        mediator: Mediator | None = None,
    ) -> None:
        self.mediator = mediator

    def shutdown_plugin(self) -> None:
        return


class DummyUiPlugin(UiPlugin):
    def __init__(self, identifier: str) -> None:
        self.identifier = identifier
        self.timer = None

    def init_plugin(
        self,
        plugin_resources_location: str | None = None,
        mediator: Mediator | None = None,
    ) -> None:
        self.mediator = mediator

    def shutdown_plugin(self) -> None:
        return

    def requires_main_thread(self) -> bool:
        return True

    def run_main_thread(self) -> None:
        pass


class DummyMediator(Mediator):
    registry: Registry

    @property
    def filter_description_list(self) -> list[str]:
        return []

    def request_solutions(
        self,
        solution_times: list[TypeTimestamp],
        filter_description: str | None = None,
    ) -> list[Message | None] | None:
        return None

    def process_pntos_message(self, message: Message) -> None:
        return

    def broadcast_aspn_message(
        self,
        message: Message,
        transport: str | None = None,
        destination_identifier: str | None = None,
    ) -> None:
        return

    def log_message(self, level: LoggingLevel, message: str) -> None:
        if level is LoggingLevel.ERROR:
            global ERROR_MESSAGE
            ERROR_MESSAGE = message
            FOUND_ERROR = True
            assert not FOUND_ERROR, ERROR_MESSAGE


class DummyTransportPlugin(TransportPlugin):
    def __init__(self, identifier: str) -> None:
        self.identifier = identifier

    def init_plugin(
        self,
        plugin_resources_location: str | None = None,
        mediator: Mediator | None = None,
    ) -> None:
        assert mediator is not None
        self.mediator = mediator

    def shutdown_plugin(self) -> None:
        return

    def start_listening(self) -> None:
        print(f'Processing message from {self.identifier}')
        msg = Message(None, '')
        self.mediator.process_pntos_message(msg)

    def stop_listening(self) -> None:
        pass

    def broadcast_message(
        self, message: Message, channel_name: str | None = None
    ) -> None:
        print(f'Publishing message from {self.identifier}')


@pytest.fixture
def controller_plugin(capsys: pytest.CaptureFixture[str]) -> BuscatControllerPlugin:
    plugin = BuscatControllerPlugin('Buscat Controller Plugin')
    plugin.init_plugin()

    return plugin


@pytest.fixture
def plugin_list() -> list[CommonPlugin]:
    my_config: list[BaseConfig] = [
        BuscatConfig(group='buscat', output_transports=('Transport 1',))
    ]

    return [
        StandardRegistryPlugin('Standard Registry Plugin', my_config),
        StandardLoggingPlugin('Standard Logging Plugin'),
        DummyTransportPlugin('Transport 1'),
        DummyTransportPlugin('Transport 2'),
        DummyUiPlugin('UI Plugin'),
        DummyUtilityPlugin('Other Plugin'),
    ]


def assert_no_warnings_or_errors(output: str) -> None:
    assert 'WARN' not in output
    assert 'ERROR' not in output


def test_init_plugin(
    controller_plugin: BuscatControllerPlugin, capsys: pytest.CaptureFixture[str]
) -> None:
    """
    Validate that controller plugin was initialized without any warnings or errors
    """
    assert_no_warnings_or_errors(capsys.readouterr().out)


def test_init_plugin_with_mediator(capsys: pytest.CaptureFixture[str]) -> None:
    """
    Should log error as controller shouldn't be passed a mediator.
    """
    plugin = BuscatControllerPlugin('Buscat Controller Plugin')
    mediator = DummyMediator()
    plugin.init_plugin(mediator=mediator)

    output = capsys.readouterr().out
    assert 'Controller plugin should not be passed a mediator' in output


def test_buscat(
    controller_plugin: BuscatControllerPlugin,
    plugin_list: list[CommonPlugin],
    capsys: pytest.CaptureFixture[str],
) -> None:
    output = capsys.readouterr().out
    assert_no_warnings_or_errors(output)  # no warnings/errors during initialization

    controller_plugin.take_control(plugin_list)

    output = capsys.readouterr().out
    assert_no_warnings_or_errors(output)  # no warnings/errors after taking control

    expected_output = []
    output_transports = BuscatMediator._output_transports
    expected_output.append('Processing message from Transport 1')
    expected_output.append(f'Publishing message from {output_transports[0]}')
    expected_output.append('Processing message from Transport 2')
    expected_output.append(f'Publishing message from {output_transports[0]}')

    for line in output.split('\n'):
        if expected_output and line == expected_output[0]:
            expected_output.pop(0)
    assert expected_output == []

    print(output)


def test_mediator_filter_description_list(
    controller_plugin: BuscatControllerPlugin,
) -> None:
    mediator = BuscatMediator(controller_plugin.identifier, ControllerPlugin)
    assert mediator.filter_description_list == []
