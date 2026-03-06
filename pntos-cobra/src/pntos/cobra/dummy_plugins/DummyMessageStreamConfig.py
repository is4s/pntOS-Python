from aspn23 import AspnBase
from pntos.api import MessageStreamConfig


class DummyMessageStreamConfig(MessageStreamConfig):
    """A :class:`~pntos.api.MessageStreamConfig` implementation that does nothing but satisfy the
    :func:`~pntos.api.OrchestrationPlugin.init_orchestration_plugin` parameter requirement."""

    def __init__(self) -> None:
        pass

    def sequenced_stream_add(
        self, message_type: type[AspnBase], source_identifier: str | None = None
    ) -> None:
        """
        Does nothing.

        Args:
            message_type (type[AspnBase]): Unused.
            source_identifier (str | None, optional): Unused.
        """

    def sequenced_stream_remove(
        self, message_type: type[AspnBase], source_identifier: str | None = None
    ) -> None:
        """
        Does nothing.

        Args:
            message_type (type[AspnBase]): Unused.
            source_identifier (str | None, optional): Unused.
        """

    def sequenced_stream_all(self, enable: bool) -> None:
        """
        Does nothing.

        Args:
            enable (bool): Unused.
        """

    def immediate_stream_add(
        self, message_type: type[AspnBase], source_identifier: str | None = None
    ) -> None:
        """
        Does nothing.

        Args:
            message_type (type[AspnBase]): Unused.
            source_identifier (str | None, optional): Unused.
        """

    def immediate_stream_remove(
        self, message_type: type[AspnBase], source_identifier: str | None = None
    ) -> None:
        """
        Does nothing.

        Args:
            message_type (type[AspnBase]): Unused.
            source_identifier (str | None, optional): Unused.
        """

    def immediate_stream_all(self, enable: bool) -> None:
        """
        Does nothing.

        Args:
            enable (bool): Unused.
        """
