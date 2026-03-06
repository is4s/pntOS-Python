from aspn23 import (
    TypeTimestamp,
)
from pntos.api import (
    CommonPlugin,
    Mediator,
    Message,
    MessageStreamConfig,
    OrchestrationPlugin,
)
from pntos.api.plugins.common import LoggingLevel


class DummyOrchestrationPlugin(OrchestrationPlugin):
    """
    A very simple :class:`~pntos.api.OrchestrationPlugin` implementation that mimics a fully
    functional system by accepting inputs and echoing these inputs as outputs through a
    :class:`~pntos.api.Mediator`. Though additonal plugins may be supplied to this instance
    they are not used in any way.
    """

    mediator: Mediator | None
    """:class:`~pntos.api.Mediator` instance used to handle callbacks."""
    _plugins: list[CommonPlugin]
    """All plugins this instance is managing."""
    _last_message: Message | None
    """The last message received by :meth:`process_pntos_message`. """

    def __init__(self, identifier: str) -> None:
        self.identifier = identifier
        self._plugins = []
        self._last_message = None
        self.mediator = None

    def init_plugin(
        self,
        plugin_resources_location: str | None = None,
        mediator: Mediator | None = None,
    ) -> None:
        """
        Basic plugin initialization.

        Args:
            plugin_resources_location (str | None): Unused.
            mediator (Mediator | None): The mediator this instance should use.
        """
        self.mediator = mediator

    def shutdown_plugin(self) -> None:
        self.mediator = None

    def init_orchestration_plugin(
        self, plugins: list[CommonPlugin] | None, stream_config: MessageStreamConfig
    ) -> None:
        """
        Secondary initialization for :class:`~pntos.api.OrchestrationPlugin` s, providing a set of
        fully initialized plugins for this instance to manage.

        Args:
            plugins (list[CommonPlugin] | None): Plugins to manage. If not `None`, will overwrite
                any previously provided list of plugins.
            stream_config (MessageStreamConfig): Unused in this implementation.
        """
        if plugins is not None:
            self._plugins = plugins

    def process_pntos_message(self, message: Message, sequenced: bool) -> None:
        """
        Simulates processing of data. In this dummy implementation messages are only stored locally
        to form the basis of the 'solution' provided by :meth:`request_solutions`.

        Args:
            message (Message): The message to process.
            sequenced (bool): Unused.
        """
        if self.mediator:
            self.mediator.log_message(
                level=LoggingLevel.INFO,
                message=f'Orchestration processing message from {message.source_identifier}',
            )
        self._last_message = message

    @property
    def filter_description_list(self) -> list[str]:
        """
        List of descriptors for solutions this instance may provide through :meth:`request_solutions`.

        In this dummy implementation the only available solution is an echo of the last message
        provided to :meth:`process_pntos_message`; as such this list is length 1 and contains only
        `LAST_MESSAGE`. Note that although :attr:`~pntos.api.OrchestrationPlugin.filter_description_list`
        spells out a convention that entries in this list should follow, this class ignores it.
        """
        return ['LAST_MESSAGE']

    def request_solutions(
        self,
        solution_times: list[TypeTimestamp],
        filter_description: str | None = None,
    ) -> list[Message | None] | None:
        """
        Returns one or more solutions, if possible.

        Args:
            solution_times (list[TypeTimestamp]): Times at which to generate solutions. As this dummy
                implementation doesn't have a time history to draw solutions from there is no
                attempt to generate solutions at the requested times; rather this argument will only
                determine the number of solution copies returned.
            filter_description (str | None): Description of filter to pull solutions from. Passing
                `None` skips any attempt at matching :attr:`filter_description_list` and will result
                in a valid return if possible.

        Returns:
            None if :meth:`process_pntos_message` has not been passed a valid message, or if
            `filter_description` is a `str` but not a member of :attr:`filter_description_list`.
            Otherwise, a list containing `N` copies of the last received :class:`~pntos.api.Message`,
            where `N` is the length of `solution_times`.
        """
        if not self._last_message:
            return None
        if (
            filter_description
            and filter_description not in self.filter_description_list
        ):
            return None
        return [self._last_message] * len(solution_times)
