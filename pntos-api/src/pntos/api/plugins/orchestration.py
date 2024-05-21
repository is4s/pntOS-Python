from typing import List, Optional, Protocol

from aspn23.type_timestamp import TypeTimestamp

from .common import CommonPlugin, Message


class MessageStreamConfig(Protocol):
    def sequenced_stream_add(
        self, type: type, source_identifier: Optional[str]
    ) -> None:
        pass

    def sequenced_stream_remove(
        self, type: type, source_identifier: Optional[str]
    ) -> None:
        pass

    def sequenced_stream_all(self, enable: bool) -> None:
        pass

    def immediate_stream_add(
        self, type: type, source_identifier: Optional[str]
    ) -> None:
        pass

    def immediate_stream_remove(
        self, type: type, source_identifier: Optional[str]
    ) -> None:
        pass

    def immediate_stream_all(self, enable: bool) -> None:
        pass


class OrchestrationPlugin(CommonPlugin, Protocol):
    def init_orchestration_plugin(
        self, plugins: List[CommonPlugin], stream_config: MessageStreamConfig
    ) -> None:
        pass

    def process_pntos_message(self, message: Message, sequenced: bool) -> None:
        pass

    def get_filter_description_list(self) -> List[str]:
        pass

    def request_solutions(
        self, solution_times: List[TypeTimestamp], filter_description: Optional[str]
    ) -> List[Message]:
        pass
