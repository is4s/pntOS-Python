from aspn23 import (
    AspnBase,
    TypeTimestamp,
)
from pntos.api import (
    LoggingLevel,
    Mediator,
    Message,
    Preprocessor,
)
from pntos.cobra.utils import has_tov
from typing_extensions import override


class TimeAdjusterPreprocessor(Preprocessor):
    _mediator: Mediator
    _last_nsec: int | None
    _expected_dt_nsec: int
    _tolerance_nsec: int

    def __init__(
        self,
        expected_dt_nsec: int,
        mediator: Mediator,
    ) -> None:
        self._mediator = mediator
        self._last_nsec = None
        self._expected_dt_nsec = expected_dt_nsec
        self._tolerance_nsec = int(0.0001 * 1e9)

    @override
    def process_pntos_message(self, message: Message) -> list[Message] | None:
        msg: AspnBase = message.wrapped_message
        if not has_tov(msg):
            self._mediator.log_message(
                LoggingLevel.WARN,
                f'TimeAdjusterPreprocessor received a message from channel {message.source_identifier} with no time of validity. Ignoring message.',
            )
            return [message]

        curr_nsec: int = msg.time_of_validity.elapsed_nsec
        if self._last_nsec is None:
            self._last_nsec = curr_nsec
            return [message]

        is_valid_time: bool = (
            abs((curr_nsec - self._last_nsec) - self._expected_dt_nsec)
            < self._tolerance_nsec
        )
        if not is_valid_time:
            synthetic_time: int = self._last_nsec + self._expected_dt_nsec
            msg.time_of_validity = TypeTimestamp(synthetic_time)
            self._last_nsec = synthetic_time
        else:
            self._last_nsec = curr_nsec

        return [message]
