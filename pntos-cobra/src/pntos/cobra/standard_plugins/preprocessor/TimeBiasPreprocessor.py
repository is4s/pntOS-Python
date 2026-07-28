from aspn23 import (
    AspnBase,
)
from pntos.api import (
    LoggingLevel,
    Mediator,
    Message,
    Preprocessor,
)
from pntos.cobra.utils import has_tov
from typing_extensions import override


class TimeBiasPreprocessor(Preprocessor):
    """Corrects timestamps for a constant bias.

    This preprocessor is useful when a specific sensor produces timestamps with a constant bias. It
    is configured with a constant time bias. All incoming message will have its timestamp subtracted
    by the bias amount.
    """

    _mediator: Mediator
    _time_bias: int

    def __init__(
        self,
        time_bias: int,
        mediator: Mediator,
    ) -> None:
        """
        Args:
            config_group (str): The group in the registry which holds config information for this preprocessor.
            mediator (Mediator): Used to get config information and to perform logging.
        """
        self._mediator = mediator
        self._time_bias = time_bias

    @override
    def process_pntos_message(self, message: Message) -> list[Message] | None:
        aspn_message: AspnBase = message.wrapped_message
        if not has_tov(aspn_message):
            self._mediator.log_message(
                LoggingLevel.WARN,
                f'TimeBiasPreprocessor received a message from channel {message.source_identifier} with no time of validity. Ignoring message.',
            )
            return [message]

        aspn_message.time_of_validity.elapsed_nsec -= self._time_bias

        return [message]
