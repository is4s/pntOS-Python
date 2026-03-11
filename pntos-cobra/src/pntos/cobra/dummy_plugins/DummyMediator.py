from aspn23 import (
    TypeTimestamp,
)
from pntos.api import CommonPlugin, LoggingLevel, Mediator, Message, Registry
from pntos.api.plugins.controller import ControllerPlugin
from pntos.api.plugins.logging import LoggingPlugin
from pntos.api.plugins.orchestration import OrchestrationPlugin
from pntos.api.plugins.transport import TransportPlugin
from pntos.cobra.utils.logging import print_message


class DummyMediator(Mediator):
    """A :class:`~pntos.api.Mediator` with minimal capability. Not for use in production code."""

    registry: Registry
    plugins: list[CommonPlugin]

    def __init__(self, plugins: list[CommonPlugin] | None = None) -> None:
        self.plugins = []
        if plugins is not None:
            self.plugins = plugins

    @property
    def filter_description_list(self) -> list[str]:
        """
        Returns the list of strings describing available solutions.

        Returns:
            The :attr:`~pntos.api.OrchestrationPlugin.filter_description_list` of the first
            :class:`~pntos.api.OrchestrationPlugin` found, or an empty list if this instance cannot
            find such a plugin.
        """
        for x in self.plugins:
            if isinstance(x, OrchestrationPlugin):
                return x.filter_description_list
        return []

    def request_solutions(
        self,
        solution_times: list[TypeTimestamp],
        filter_description: str | None = None,
    ) -> list[Message | None] | None:
        """
        Returns requested solutions if possible. Ignores `filter_description`.

        Args:
            solution_times (list[TypeTimestamp]): The times at which to return solutions.
            filter_description (str | None, optional): Unused

        Returns:
            The return of :func:`~pntos.api.OrchestrationPlugin.request_solutions` of the first
            :class:`~pntos.api.OrchestrationPlugin` found, or None if no
            :class:`~pntos.api.OrchestrationPlugin` is available.
        """
        for x in self.plugins:
            if isinstance(x, OrchestrationPlugin):
                return x.request_solutions(solution_times, filter_description)
        return None

    def process_pntos_message(self, message: Message) -> None:
        """
        Passes `message` off to all available :class:`~pntos.api.OrchestrationPlugin` s.

        Args:
            message (Message): Message to process.
        """
        # Find the Orchestration plugin and pass it the message.
        for x in self.plugins:
            if isinstance(x, OrchestrationPlugin):
                orchestration_plugin = x
                orchestration_plugin.process_pntos_message(message, sequenced=False)
                solutions = orchestration_plugin.request_solutions([TypeTimestamp(0)])
                if solutions is not None:
                    self.broadcast_aspn_message(
                        message=solutions[0],
                        destination_identifier=f'{message.source_identifier}_echo',
                    )

    def broadcast_aspn_message(
        self,
        message: Message,
        transport: str | None = None,
        destination_identifier: str | None = None,
    ) -> None:
        """
        Attempt to broadcast a message over all available transports.

        Args:
            message (Message): The message to broadcast.
            transport (str | None): Usually an identifier used to select a specific transport to
                broadcast over. Unused in this implementation.
            destination_identifier (str | None): Additional description of the method of broadcast,
                usually a channel name or similar. If `None` will be changed to `'somewhere'`.
        """
        dest = (
            destination_identifier
            if destination_identifier is not None
            else 'somewhere'
        )
        for x in self.plugins:
            if isinstance(x, TransportPlugin):
                x.broadcast_message(message=message, channel_name=dest)

    def log_message(self, level: LoggingLevel, message: str) -> None:
        logged = False
        for x in self.plugins:
            # Strictly speaking LoggingPlugin wants the type/id of the plugin that
            # generated the message, but we do not have that information in this implementation
            # as it unnecessarily complicates the initialization
            if isinstance(x, LoggingPlugin):
                x.log(ControllerPlugin, 'unknown_dummy', level, message)
                logged = True
        if not logged:
            print_message(level, 'unknown_dummy', message)
