from pntos.api import LoggingLevel, Mediator, Message, Preprocessor
from pntos.cobra.config import OutageConfig


class Outage:
    config: OutageConfig
    mediator: Mediator
    active: bool

    def __init__(self, config: OutageConfig, mediator: Mediator) -> None:
        self.config = config
        self.mediator = mediator
        self.active = False

    def update_status(self, time: float) -> None:
        """
        Print status update if needed.

        - time: Current relative time in seconds.
        - mediator: Mediator object for logging messages.
        """
        outage_active = self.config.start_time <= time < self.config.end_time

        if outage_active and not self.active:
            self.mediator.log_message(
                LoggingLevel.INFO,
                f'Beginning outage on channel {self.config.channel} from time {self.config.start_time}s to {self.config.end_time}s (cur_time={time}s).',
            )
            self.active = True
        elif not outage_active and self.active:
            self.mediator.log_message(
                LoggingLevel.INFO,
                f'Ending outage on channel {self.config.channel} at time {time}s.',
            )
            self.active = False


class OutagePreprocessor(Preprocessor):
    """Preprocessor used to induce an outage on a given channel."""

    def __init__(self, mediator: Mediator, outage_config: OutageConfig) -> None:
        self.mediator = mediator
        self.outage = Outage(outage_config, mediator)
        self.first_msg_time_ns: int | None = None

    def process_pntos_message(self, message: Message) -> list[Message] | None:
        if message.source_identifier != self.outage.config.channel:
            return [message]

        aspn_msg = message.wrapped_message
        if not hasattr(aspn_msg, 'time_of_validity'):
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
