import bisect
from threading import Event
from typing import ClassVar

from aspn23 import TypeTimestamp
from pntos.api import (
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
from pntos.cobra.utils import UiMediatorInterface, print_message

from .StandardMessageStreamConfig import StandardMessageStreamConfig


def _get_time(msg: Message) -> int:
    """Returns the time of the message in nanoseconds."""
    return int(msg.wrapped_message.time_of_validity.elapsed_nsec)  # type: ignore[attr-defined]


class StandardMediator(Mediator):
    """
    This is a simple mediator implementation. It was designed to be used in conjunction with the
    :class:`pntos.cobra.StandardControllerPlugin` which is why this controller directly access private members.
    It has one public member ``registry`` that other plugins are allowed to access.
    """

    _logging_plugin: LoggingPlugin | None = None
    _transport_plugins: ClassVar[list[TransportPlugin]] = []
    _orchestration_plugin: OrchestrationPlugin | None = None
    _controller_plugin: ControllerPlugin | None = None
    _stream_config: StandardMessageStreamConfig
    _logging_error_event: Event = Event()
    registry: Registry
    _messages: ClassVar[list[Message]] = []
    _buffer_time_nsec: int
    _last_solution_time: TypeTimestamp | None
    _publish_interval_ns: int | None = None
    _ui_interface: UiMediatorInterface

    def __init__(
        self,
        attached_plugin_identifier: str,
        attached_plugin_type: PluginType,
    ) -> None:
        """
        Standard Cobra Mediator

        Args:
            attached_plugin_identifier (str): The identifier field of the plugin this
                mediator is assigned to.
            attached_plugin_type (PluginType | None): The abstract plugin type of the
                plugin this mediator is assigned to.
        """
        self._attached_plugin_type: PluginType = attached_plugin_type
        self._attached_plugin_identifier: str = attached_plugin_identifier
        self._last_solution_time = None

    @property
    def filter_description_list(self) -> list[str]:
        assert self._orchestration_plugin is not None, (
            'Orchestration plugin used before initialized and passed to mediator.'
        )
        return self._orchestration_plugin.filter_description_list

    def request_solutions(
        self,
        solution_times: list[TypeTimestamp],
        filter_description: str | None = None,
    ) -> list[Message | None] | None:
        assert self._orchestration_plugin is not None, (
            'Orchestration plugin used before initialized and passed to mediator.'
        )
        return self._orchestration_plugin.request_solutions(
            solution_times, filter_description
        )

    def process_pntos_message(self, message: Message) -> None:
        assert self._orchestration_plugin is not None, (
            'Orchestration plugin used before initialized and passed to mediator.'
        )
        if not self._ui_interface.new_mediator_message(message):
            return
        if self._stream_config._is_sequenced(
            type(message.wrapped_message), message.source_identifier
        ):
            bisect.insort(self._messages, message, key=_get_time)
        else:
            self._orchestration_plugin.process_pntos_message(message, False)

        cur_time = message.wrapped_message.time_of_validity  # type: ignore[attr-defined]

        process_until_time = cur_time.elapsed_nsec - self._buffer_time_nsec
        process_until_index = bisect.bisect_left(
            self._messages, process_until_time, key=_get_time
        )
        for m in self._messages[:process_until_index]:
            self._orchestration_plugin.process_pntos_message(m, True)

        StandardMediator._messages = self._messages[process_until_index:]

        # Need to make sure the orchestration has received some messages before we
        # start requesting solutions.
        if self._last_solution_time is None:
            self._last_solution_time = cur_time
            return

        # Print the current solution every second in message time
        if (
            self._publish_interval_ns is not None
            and cur_time.elapsed_nsec - self._last_solution_time.elapsed_nsec
            > self._publish_interval_ns
        ):
            times = [cur_time]
            solution = self.request_solutions(times)
            if solution is not None and solution[0] is not None:
                self._ui_interface.new_mediator_message(solution[0])
                self._log_message(LoggingLevel.DEBUG, f'Got a solution! {solution}')
                for transport in self._transport_plugins:
                    self.broadcast_aspn_message(
                        solution[0],
                        transport=transport.identifier,
                        destination_identifier=solution[0].source_identifier,
                    )
            else:
                self._log_message(
                    LoggingLevel.DEBUG,
                    'Could not receive solution from orchestration.',
                )
            self._last_solution_time = cur_time

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
            self._logging_error_event.set()
