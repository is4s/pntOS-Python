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
        self.mediator = mediator

    def shutdown_plugin(self) -> None:
        self.mediator = None

    def init_orchestration_plugin(
        self, plugins: list[CommonPlugin] | None, stream_config: MessageStreamConfig
    ) -> None:
        if plugins is not None:
            self._plugins = plugins

    def process_pntos_message(self, message: Message, sequenced: bool) -> None:
        if self.mediator:
            self.mediator.log_message(
                level=LoggingLevel.INFO,
                message=f'Orchestration processing message from {message.source_identifier}',
            )
        self._last_message = message

    @property
    def filter_description_list(self) -> list[str]:
        return ['LAST_MESSAGE']

    def request_solutions(
        self,
        solution_times: list[TypeTimestamp],
        filter_description: str | None = None,
    ) -> list[Message | None] | None:
        if not self._last_message:
            return None
        if (
            filter_description
            and filter_description not in self.filter_description_list
        ):
            return None
        return [self._last_message] * len(solution_times)
