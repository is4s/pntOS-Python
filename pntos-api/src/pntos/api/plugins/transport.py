from typing import Optional, Protocol

from .common import CommonPlugin, Message


class TransportPlugin(CommonPlugin, Protocol):
    """
    Transport plugin.

    A plugin that abstracts a network transport. listening for sensor data off
    the wire and sending data back to the sensors as needed.
    """

    def start_listening(self) -> None:
        """
        Start listening.

        Start listening to the transport that this plugin implements, calling
        the appropriate controller function as data streams in.
        """
        pass

    def stop_listening(self) -> None:
        """
        Disable listening.

        Disable listening to the transport that was previously started in a
        call to `start_listening`.
        """
        pass

    def broadcast_message(self, message: Message, channel_name: Optional[str]) -> None:
        """
        Send a message back out to the sensor from pntOS.

        If `channel_name` is `None` the implementation may decide where `message` should
        be routed, if anywhere. For example, a serial cable might send all messages to a
        single destination.
        """
        pass
