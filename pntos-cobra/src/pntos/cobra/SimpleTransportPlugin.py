from threading import Thread
from time import sleep

from aspn23.measurement_position import MeasurementPosition

from pntos.api import Mediator, TransportPlugin
from pntos.api.plugins.common import Message


class SimpleTransportPlugin(TransportPlugin):
    def __init__(self, identifier: str):
        self.identifier = identifier

    def init_plugin(
        self, plugin_resources_location: str | None, mediator: Mediator | None
    ) -> None:
        assert mediator is not None
        self.mediator = mediator

    def shutdown_plugin(self) -> None:
        pass

    def start_listening(self) -> None:
        self.listening = True
        Thread(target=listen_for_messages).start()

    def stop_listening(self) -> None:
        self.listening = False

    def broadcast_message(self, message: Message, channel_name: str | None) -> None:
        pass

    mediator: Mediator
    listening: bool
    identifier: str


def listen_for_messages(my_plugin: SimpleTransportPlugin):
    while True:
        sleep(0.1)
        if my_plugin.listening:
            # Create a new ASPN measurement
            aspn_msg = MeasurementPosition()

            # Send a new ASPN message we've received to the system
            my_plugin.mediator.process_pntos_message(
                Message(aspn_msg, source_identifier="channel_foo")
            )
        else:
            break
