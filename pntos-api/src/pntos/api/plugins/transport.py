from typing import Optional, Protocol

from .common import CommonPlugin, Message


class TransportPlugin(CommonPlugin, Protocol):
    def start_listening(self) -> None:
        pass

    def stop_listening(self) -> None:
        pass

    def broadcast_message(self, message: Message, channel_name: Optional[str]) -> None:
        pass
