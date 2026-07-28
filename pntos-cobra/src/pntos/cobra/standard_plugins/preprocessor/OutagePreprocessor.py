from pntos.api import LoggingLevel, Mediator, Message, Preprocessor
from pntos.cobra.utils import has_tov
from typing_extensions import override


class Outage:
    mediator: Mediator
    active: bool

    def __init__(self, start_time: float, end_time: float, mediator: Mediator) -> None:
        self.mediator = mediator
        self.active = False

        self._start_time: float = start_time
        self._end_time: float = end_time

    def update_status(self, time: float) -> None:
        """
        Print status update if needed.

        - time: Current relative time in seconds.
        - mediator: Mediator object for logging messages.
        """
        outage_active = self._start_time <= time < self._end_time

        if outage_active and not self.active:
            self.mediator.log_message(
                LoggingLevel.INFO,
                f'Beginning outage from time {self._start_time}s to {self._end_time}s (cur_time={time}s).',
            )
            self.active = True
        elif not outage_active and self.active:
            self.mediator.log_message(
                LoggingLevel.INFO,
                f'Ending outage at time {time}s.',
            )
            self.active = False


class OutagePreprocessor(Preprocessor):
    """Preprocessor used to induce an outage on a given channel."""

    def __init__(self, start_time: float, end_time: float, mediator: Mediator) -> None:
        self.mediator = mediator
        self.outage = Outage(start_time, end_time, mediator)
        self.first_msg_time_ns: int | None = None

    @override
    def process_pntos_message(self, message: Message) -> list[Message] | None:
        aspn_msg = message.wrapped_message
        if not has_tov(aspn_msg):
            self.mediator.log_message(
                LoggingLevel.WARN,
                f'OutagePreprocessor received a message from channel {message.source_identifier} with no time of validity. Ignoring message.',
            )
            return [message]

        cur_ns = aspn_msg.time_of_validity.elapsed_nsec
        if self.first_msg_time_ns is None:
            self.first_msg_time_ns = cur_ns

        # Time (s) since 1st message
        rel_time = (cur_ns - self.first_msg_time_ns) * 1e-9

        # Discard message if outage is active
        self.outage.update_status(rel_time)
        if self.outage.active:
            return None

        return [message]
