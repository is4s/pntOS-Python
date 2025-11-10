from typing import ClassVar

from aspn23 import AspnBase
from pntos.api import MessageStreamConfig


class StandardMessageStreamConfig(MessageStreamConfig):
    """
    This is a simple message stream config implementation. As with the :class:`StandardMediator` it
    is considered as apart of the :class:`pntos.cobra.StandardControllerPlugin` implementation which allows the controller
    to access private members and functions when necessary. All other plugins should adhere to API
    compliant functions.
    """

    # _message_lookup[type(AspnMessage)][source_identifier] -> is_sequenced?
    _override_to_immediate: ClassVar[set[type[AspnBase]]] = set()
    _override_to_sequenced: ClassVar[set[type[AspnBase]]] = set()
    _default_is_sequenced: bool = False  # True -> sequenced, False -> immediate

    def __init__(self) -> None:
        """
        Standard Cobra Message Stream Config

        By default, all messages are immediately streamed.
        """

    def _handle_source_identifier(self, source_identifier: str | None) -> None:
        if source_identifier is not None:
            print(
                '[MessageStreamConfig] ERROR: Filtering on source '
                + 'identifier is unimplemented.'
            )

    def sequenced_stream_add(
        self, message_type: type[AspnBase], source_identifier: str | None = None
    ) -> None:
        # TODO: implement source identifier filtering
        self._handle_source_identifier(source_identifier)
        if message_type in self._override_to_immediate:
            self._override_to_immediate.remove(message_type)
        self._override_to_sequenced.add(message_type)

    def sequenced_stream_remove(
        self, message_type: type[AspnBase], source_identifier: str | None = None
    ) -> None:
        # TODO: implement source identifier filtering
        self._handle_source_identifier(source_identifier)
        if message_type in self._override_to_sequenced:
            self._override_to_sequenced.remove(message_type)

    def sequenced_stream_all(self, enable: bool) -> None:
        # TODO: Implement `enable` parameter - currently ambiguous (#66)
        StandardMessageStreamConfig._override_to_sequenced = set()
        StandardMessageStreamConfig._override_to_immediate = set()
        self._default_is_sequenced = True

    def immediate_stream_add(
        self, message_type: type[AspnBase], source_identifier: str | None = None
    ) -> None:
        # TODO: implement source identifier filtering
        self._handle_source_identifier(source_identifier)
        if message_type in self._override_to_sequenced:
            self._override_to_sequenced.remove(message_type)
        self._override_to_immediate.add(message_type)

    def immediate_stream_remove(
        self, message_type: type[AspnBase], source_identifier: str | None = None
    ) -> None:
        # TODO: implement source identifier filtering
        self._handle_source_identifier(source_identifier)
        if message_type in self._override_to_immediate:
            self._override_to_immediate.remove(message_type)

    def immediate_stream_all(self, enable: bool) -> None:
        # TODO: Implement `enable` parameter - currently ambiguous (#66)
        StandardMessageStreamConfig._override_to_sequenced = set()
        StandardMessageStreamConfig._override_to_immediate = set()

        self._default_is_sequenced = False

    def _is_sequenced(
        self, message_type: type[AspnBase], source_identifier: str | None = None
    ) -> bool:
        """
        Returns true if the requested type will be streamed sequentially, and
        False if the requested type will be immediately streamed.
        """
        self._handle_source_identifier(source_identifier)
        if message_type in self._override_to_immediate:
            return False
        if message_type in self._override_to_sequenced:
            return True
        # If type is not in either list, return the default
        return self._default_is_sequenced
