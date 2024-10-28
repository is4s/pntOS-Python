from threading import Thread
from time import sleep

import numpy as np
from aspn23 import (
    MeasurementPosition,
    MeasurementPositionErrorModel,
    MeasurementPositionReferenceFrame,
    TypeHeader,
    TypeTimestamp,
)

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
            header = TypeHeader(0, 0, 0, 0)
            time = TypeTimestamp(0)
            frame = MeasurementPositionReferenceFrame.GEODETIC
            error_model = MeasurementPositionErrorModel.NONE
            aspn_msg = MeasurementPosition(
                header,
                time,
                frame,
                None,
                None,
                None,
                np.empty(0),
                error_model,
                np.empty(0),
                [],
            )

            # Send a new ASPN message we've received to the system
            my_plugin.mediator.process_pntos_message(
                Message(aspn_msg, source_identifier="channel_foo")
            )
        else:
            break
