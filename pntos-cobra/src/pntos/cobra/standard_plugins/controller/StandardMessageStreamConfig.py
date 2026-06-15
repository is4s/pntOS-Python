from typing import ClassVar

from aspn23 import AspnBase
from pntos.api import MessageStreamConfig
from pntos.cobra.config import BufferMode


class StandardMessageStreamConfig(MessageStreamConfig):
    """
    This is a simple message stream config implementation. As with the :class:`StandardMediator` it
    is considered as apart of the :class:`pntos.cobra.StandardControllerPlugin` implementation which allows the controller
    to access private members and functions when necessary. All other plugins should adhere to API
    compliant functions.
    """

    # Map message type and optional source identifier to buffer mode
    _buffer_mode: ClassVar[dict[tuple[type[AspnBase], str | None], BufferMode]] = {}
    _default_mode: BufferMode = BufferMode.IMMEDIATE

    def __init__(self) -> None:
        """
        Standard Cobra Message Stream Config

        By default, all messages are immediately streamed.
        """

    def sequenced_stream_add(
        self, message_type: type[AspnBase], source_identifier: str | None = None
    ) -> None:
        key = (message_type, source_identifier)
        self._buffer_mode[key] = BufferMode.SEQUENCED

    def sequenced_stream_remove(
        self, message_type: type[AspnBase], source_identifier: str | None = None
    ) -> None:
        key = (message_type, source_identifier)
        self._buffer_mode.pop(key, None)

    def sequenced_stream_all(self, enable: bool) -> None:
        # TODO: Implement `enable` parameter - currently ambiguous (#66)
        self._buffer_mode.clear()
        self._default_mode = BufferMode.SEQUENCED

    def immediate_stream_add(
        self, message_type: type[AspnBase], source_identifier: str | None = None
    ) -> None:
        key = (message_type, source_identifier)
        self._buffer_mode[key] = BufferMode.IMMEDIATE

    def immediate_stream_remove(
        self, message_type: type[AspnBase], source_identifier: str | None = None
    ) -> None:
        key = (message_type, source_identifier)
        self._buffer_mode.pop(key, None)

    def immediate_stream_all(self, enable: bool) -> None:
        # TODO: Implement `enable` parameter - currently ambiguous (#66)
        self._buffer_mode.clear()
        self._default_mode = BufferMode.IMMEDIATE

    def _is_sequenced(
        self, message_type: type[AspnBase], source_identifier: str | None = None
    ) -> bool:
        """
        Returns true if the requested type will be streamed sequentially, and
        False if the requested type will be immediately streamed.
        """
        key = (message_type, source_identifier)
        if key in self._buffer_mode:
            return self._buffer_mode[key] == BufferMode.SEQUENCED

        key = (message_type, None)
        if key in self._buffer_mode:
            return self._buffer_mode[key] == BufferMode.SEQUENCED

        return self._default_mode == BufferMode.SEQUENCED
