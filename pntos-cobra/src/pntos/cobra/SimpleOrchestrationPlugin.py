from typing import List, Optional

from aspn23 import TypeTimestamp

from pntos.api import Mediator, OrchestrationPlugin
from pntos.api.plugins.common import CommonPlugin, Message
from pntos.api.plugins.orchestration import MessageStreamConfig


class SimpleOrchestrationPlugin(OrchestrationPlugin):
    def __init__(self, identifier: str):
        self.identifier = identifier

    def init_plugin(
        self,
        plugin_resources_location: Optional[str] = None,
        mediator: Optional[Mediator] = None,
    ) -> None:
        pass

    def shutdown_plugin(self) -> None:
        pass

    identifier: str

    def init_orchestration_plugin(
        self, plugins: List[CommonPlugin], stream_config: MessageStreamConfig
    ) -> None:
        stream_config.immediate_stream_all(True)

    def process_pntos_message(self, message: Message, sequenced: bool) -> None:
        pass

    def get_filter_description_list(self) -> List[str]:
        return []

    def request_solutions(
        self, solution_times: List[TypeTimestamp], filter_description: str | None = None
    ) -> List[Message]:
        return []
