from aspn23 import TypeTimestamp

from pntos.api import (
    CommonPlugin,
    ControllerPlugin,
    LoggingLevel,
    Mediator,
    Message,
    Registry,
    TransportPlugin,
)


class SimpleControllerPlugin(ControllerPlugin):
    def __init__(self, identifier: str):
        self.identifier = identifier

    def init_plugin(
        self,
        plugin_resources_location: str | None = None,
        mediator: Mediator | None = None,
    ) -> None:
        pass

    def shutdown_plugin(self) -> None:
        pass

    identifier: str

    def take_control(
        self,
        plugins: list[CommonPlugin],
        plugin_resources_locations: list[str | None] | None = None,
        initial_config: str | None = None,
    ) -> None:
        pass


class SimpleMediator(Mediator):
    transport_plugins: list[TransportPlugin]
    registry: Registry

    def __init__(self, registry: Registry, transport_plugins: list[TransportPlugin]):
        self.registry = registry
        self.transport_plugins = transport_plugins

    def get_filter_description_list(self) -> list[str]:
        return []

    def request_solutions(
        self, solution_times: list[TypeTimestamp], filter_description: str | None = None
    ) -> list[Message]:
        return []

    def process_pntos_message(self, message: Message) -> None:
        pass

    def broadcast_aspn_message(
        self,
        message: Message,
        transport: str | None = None,
        destination_identifier: str | None = None,
    ) -> None:
        pass

    def log_message(self, level: LoggingLevel, message: str) -> None:
        pass
