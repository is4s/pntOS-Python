from typing import Callable

from aspn23 import AspnBase
from pntos.api import MessageStreamConfig


class SimpleMessageStreamConfig(MessageStreamConfig):
    # _message_lookup[type(AspnMessage)][source_identifier] -> is_sequenced?
    _override_to_immediate: set[type[AspnBase]] = set([])
    _override_to_sequenced: set[type[AspnBase]] = set([])
    _default_is_sequenced: bool = False  # True -> sequenced, False -> immediate

    def __init__(self) -> None:
        """
        Simple Cobra Message Stream Config

        By default, all messages are immediately streamed.
        """
        pass

    def _handle_source_identifier(self, source_identifier: str | None) -> None:
        if source_identifier is not None:
            print(
                '[MessageStreamConfig] ERROR: Filtering on source '
                + 'identifier is unimplemented.'
            )

    def sequenced_stream_add(
        self, type: type[AspnBase], source_identifier: str | None = None
    ) -> None:
        # TODO: implement source identifier filtering
        self._handle_source_identifier(source_identifier)
        if type in self._override_to_immediate:
            self._override_to_immediate.remove(type)
        self._override_to_sequenced.add(type)

    def sequenced_stream_remove(
        self, type: type[AspnBase], source_identifier: str | None = None
    ) -> None:
        # TODO: implement source identifier filtering
        self._handle_source_identifier(source_identifier)
        if type in self._override_to_sequenced:
            self._override_to_sequenced.remove(type)

    def sequenced_stream_all(self, enable: bool) -> None:
        # TODO: Implement `enable` parameter - currently ambiguous (#66)
        self._override_to_sequenced = set([])
        self._override_to_immediate = set([])
        self._default_is_sequenced = True

    def immediate_stream_add(
        self, type: type[AspnBase], source_identifier: str | None = None
    ) -> None:
        # TODO: implement source identifier filtering
        self._handle_source_identifier(source_identifier)
        if type in self._override_to_sequenced:
            self._override_to_sequenced.remove(type)
        self._override_to_immediate.add(type)

    def immediate_stream_remove(
        self, type: type[AspnBase], source_identifier: str | None = None
    ) -> None:
        # TODO: implement source identifier filtering
        self._handle_source_identifier(source_identifier)
        if type in self._override_to_immediate:
            self._override_to_immediate.remove(type)

    def immediate_stream_all(self, enable: bool) -> None:
        # TODO: Implement `enable` parameter - currently ambiguous (#66)
        self._override_to_sequenced = set([])
        self._override_to_immediate = set([])
        self._default_is_sequenced = False

    def is_sequenced(
        self, type: type[AspnBase], source_identifier: str | None = None
    ) -> bool:
        """
        Returns true if the requested type will be streamed sequentially, and
        False if the requested type will be immediately streamed.
        """
        self._handle_source_identifier(source_identifier)
        if type in self._override_to_immediate:
            return False
        if type in self._override_to_sequenced:
            return True
        # If type is not in either list, return the default
        return self._default_is_sequenced
