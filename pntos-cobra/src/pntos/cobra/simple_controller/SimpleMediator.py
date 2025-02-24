from aspn23 import TypeTimestamp
from pntos.api import (
    CommonPlugin,
    ControllerPlugin,
    LoggingLevel,
    LoggingPlugin,
    Mediator,
    Message,
    OrchestrationPlugin,
    PluginType,
    Registry,
    TransportPlugin,
)

from .SimpleMessageStreamConfig import SimpleMessageStreamConfig


class SimpleMediator(Mediator):
    logging_plugin: LoggingPlugin | None = None
    transport_plugins: list[TransportPlugin] = []
    orchestration_plugin: OrchestrationPlugin | None = None
    stream_config: SimpleMessageStreamConfig
    registry: Registry
    _log_levels: dict[LoggingLevel, str] = {
        LoggingLevel.DEBUG: 'DEBUG: ',
        LoggingLevel.ERROR: 'ERROR: ',
        LoggingLevel.INFO: 'INFO: ',
        LoggingLevel.WARN: 'WARNING: ',
    }

    def __init__(
        self,
        attached_plugin_identifier: str,
        attached_plugin_type: PluginType,
    ) -> None:
        """
        Simple Cobra Mediator

        Args:
            attached_plugin_identifier (str): The identifier field of the plugin this
                mediator is assigned to.
            attached_plugin_type (PluginType | None): The abstract plugin type of the
                plugin this mediator is assigned to.
        """
        self._attached_plugin_type: PluginType = attached_plugin_type
        self._attached_plugin_identifier: str = attached_plugin_identifier

    def get_filter_description_list(self) -> list[str]:
        assert (
            self.orchestration_plugin is not None
        ), 'Orchestration plugin used before initialized and passed to mediator.'
        return self.orchestration_plugin.get_filter_description_list()

    def request_solutions(
        self,
        solution_times: list[TypeTimestamp],
        filter_description: str | None = None,
    ) -> list[Message]:
        assert (
            self.orchestration_plugin is not None
        ), 'Orchestration plugin used before initialized and passed to mediator.'
        return self.orchestration_plugin.request_solutions(
            solution_times, filter_description
        )

    def process_pntos_message(self, message: Message) -> None:
        # TODO (#65): Implement buffering for sequenced stream
        assert (
            self.orchestration_plugin is not None
        ), 'Orchestration plugin used before initialized and passed to mediator.'
        if self.stream_config.is_sequenced(type(message.wrapped_message)):
            self.log_message(
                LoggingLevel.ERROR,
                'Sequenced message stream not supported. '
                + 'Immediate streaming all messages.',
            )
        self.orchestration_plugin.process_pntos_message(message, False)

    def broadcast_aspn_message(
        self,
        message: Message,
        transport: str | None = None,
        destination_identifier: str | None = None,
    ) -> None:
        assert (
            len(self.transport_plugins) != 0
        ), 'Transport plugin used before initialized and passed to mediator.'
        for transport_plugin in self.transport_plugins:
            if transport is None or transport_plugin.identifier == transport:
                transport_plugin.broadcast_message(message, destination_identifier)
        else:
            self.log_message(
                LoggingLevel.WARN,
                f'Transport "{transport}" not found. Unable to broadcast message.',
            )

    def log_message(self, level: LoggingLevel, message: str) -> None:
        if self.logging_plugin is None:
            print(f'[{self._attached_plugin_type}] {self._log_levels[level]} {message}')
            return
        self.logging_plugin.log(
            self._attached_plugin_type,
            self._attached_plugin_identifier,
            level,
            message,
        )
