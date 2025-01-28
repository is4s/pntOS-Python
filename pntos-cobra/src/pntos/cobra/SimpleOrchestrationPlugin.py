from aspn23 import TypeTimestamp

from pntos.api import Mediator, OrchestrationPlugin
from pntos.api.plugins.common import CommonPlugin, Message
from pntos.api.plugins.orchestration import MessageStreamConfig


class SimpleOrchestrationPlugin(OrchestrationPlugin):
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

    def init_orchestration_plugin(
        self, plugins: list[CommonPlugin], stream_config: MessageStreamConfig
    ) -> None:
        stream_config.immediate_stream_all(True)

    def process_pntos_message(self, message: Message, sequenced: bool) -> None:
        pass

    def get_filter_description_list(self) -> list[str]:
        return []

    def request_solutions(
        self, solution_times: list[TypeTimestamp], filter_description: str | None = None
    ) -> list[Message]:
        return []
