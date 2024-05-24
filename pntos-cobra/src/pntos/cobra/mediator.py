
from typing import List

from aspn23.type_timestamp import TypeTimestamp
from pntos.api.plugins.common import LoggingLevel, Mediator, Message
from pntos.api.plugins.transport import TransportPlugin

from .registry import PyRegistry


class PyMediator(Mediator):
    transport_plugins: list[TransportPlugin]

    def __init__(self, registry: PyRegistry):
        self.registry = registry

    def get_filter_description_list(self) -> List[str]:
        return super().get_filter_description_list()
    
    def request_solutions(self, solution_times: List[TypeTimestamp], filter_description: str | None) -> List[Message]:
        return super().request_solutions(solution_times, filter_description)
    
    def process_pntos_message(self, message: Message) -> None:
        return super().process_pntos_message(message)
    
    def broadcast_aspn_message(self, message: Message, transport: str | None, destination_identifier: str | None) -> None:
        if transport == None:
            print("No transport passed. Sorry.")
        the_transport = [x for x in self.transport_plugins if x.identifier == transport][0]
        the_transport.broadcast_message(message, ".*")
    
    def log_message(self, level: LoggingLevel, message: str) -> None:
        return super().log_message(level, message)
    
    registry: PyRegistry