from typing import ClassVar

from aspn23 import TypeTimestamp
from pntos.api import (
    ControllerPlugin,
    LoggingLevel,
    LoggingPlugin,
    Mediator,
    Message,
    PluginType,
    Registry,
    TransportPlugin,
)
from pntos.cobra.standard_plugins.controller.StandardMediator import ExitCode, ExitEvent
from pntos.cobra.utils import print_message


class BuscatMediator(Mediator):
    """
    This is a simple Buscat mediator implementation. It was designed to be used in conjunction with the
    :class:`pntos.cobra.BuscatControllerPlugin` which is why this controller directly access private members.
    It has one public member ``registry`` that other plugins are allowed to access.
    """

    _logging_plugin: LoggingPlugin | None = None
    _output_transports: ClassVar[list[str]] = []
    _transport_plugins: ClassVar[list[TransportPlugin]] = []
    _controller_plugin: ControllerPlugin | None = None
    _exit_event: ExitEvent = ExitEvent()
    _output_channel_prefix: str = ''

    registry: Registry

    def __init__(
        self,
        attached_plugin_identifier: str,
        attached_plugin_type: PluginType,
    ) -> None:
        """
        Buscat Mediator

        Args:
            attached_plugin_identifier (str): The identifier field of the plugin this
                mediator is assigned to.
            attached_plugin_type (PluginType | None): The abstract plugin type of the
                plugin this mediator is assigned to.
        """
        self._attached_plugin_type: PluginType = attached_plugin_type
        self._attached_plugin_identifier: str = attached_plugin_identifier

    @property
    def filter_description_list(self) -> list[str]:
        return []

    def request_solutions(
        self,
        solution_times: list[TypeTimestamp],
        filter_description: str | None = None,
    ) -> list[Message | None] | None:
        pass

    def process_pntos_message(self, message: Message) -> None:
        # pass to designated transport plugin for broadcast
        if message.source_identifier.startswith(self._output_channel_prefix):
            channel = message.source_identifier
        else:
            channel = self._output_channel_prefix + message.source_identifier

        for output_transport in self._output_transports:
            self.broadcast_aspn_message(
                message,
                transport=output_transport,
                destination_identifier=channel,
            )

    def broadcast_aspn_message(
        self,
        message: Message,
        transport: str | None = None,
        destination_identifier: str | None = None,
    ) -> None:
        assert len(self._transport_plugins) != 0, (
            'Transport plugin used before initialized and passed to mediator.'
        )
        sent = False
        for transport_plugin in self._transport_plugins:
            if transport is None or transport_plugin.identifier == transport:
                transport_plugin.broadcast_message(message, destination_identifier)
                sent = True
        if not sent:
            self._log_message(
                LoggingLevel.WARN,
                f'Transport "{transport}" not found. Unable to broadcast message.',
            )

    def log_message(self, level: LoggingLevel, message: str) -> None:
        self._log_message(level, message, self._attached_plugin_type)

    def _log_message(
        self,
        level: LoggingLevel,
        message: str,
        plugin_type: PluginType = ControllerPlugin,
    ) -> None:
        if self._logging_plugin is None:
            print_message(level, plugin_type.__name__, message)
        else:
            self._logging_plugin.log(
                plugin_type,
                self._attached_plugin_identifier,
                level,
                message,
            )
        if level is LoggingLevel.ERROR and self._controller_plugin is not None:
            self._exit_event.set(ExitCode.ERROR)
