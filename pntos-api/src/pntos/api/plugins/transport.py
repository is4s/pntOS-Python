"""Python API of pntOS."""

from abc import ABC, abstractmethod

from pntos.api import CommonPlugin, Message


class TransportPlugin(CommonPlugin, ABC):
    """
    Transport plugin.

    A plugin that abstracts a network transport. listening for sensor data off
    the wire and sending data back to the sensors as needed.
    """

    @abstractmethod
    def start_listening(self) -> None:
        """
        Start listening.

        Start listening to the transport that this plugin implements, calling
        the appropriate controller function as data streams in.
        """
        pass

    @abstractmethod
    def stop_listening(self) -> None:
        """
        Disable listening.

        Disable listening to the transport that was previously started in a
        call to :meth:`start_listening`.
        """
        pass

    @abstractmethod
    def broadcast_message(
        self, message: Message, channel_name: str | None = None
    ) -> None:
        """
        Send a message back out to the sensor from pntOS.

        Args:
            message (Message): The message to send.
            channel_name (str | None, optional): The desired channel. If ``channel_name`` is
                ``None`` the implementation may decide where ``message`` should be routed, if
                anywhere. For example, a serial cable might send all messages to a single
                destination.
        """
        pass
