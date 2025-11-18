from aspn23 import (
    AspnBase,
)
from pntos.api import (
    LoggingLevel,
    Mediator,
    Message,
    Preprocessor,
)
from pntos.cobra.config import (
    TimeBiasConfig,
    config_from_registry,
)


class TimeBiasPreprocessor(Preprocessor):
    """Corrects timestamps for a constant bias.

    This preprocessor is useful when a specific sensor produces timestamps with a constant bias. It
    is configured with a list of channels as well as a constant time bias. Any message whose source
    identifier matches one of the configured channels will have its timestamp subtracted by the bias
    amount.
    """

    _mediator: Mediator
    _channels_to_correct: tuple[str, ...]
    _time_bias: int

    def __init__(
        self,
        config_group: str,
        mediator: Mediator,
    ) -> None:
        """
        Args:
            config_group (str): The group in the registry which holds config information for this preprocessor.
            mediator (Mediator): Used to get config information and to perform logging.
        """
        self._mediator = mediator
        config = config_from_registry(TimeBiasConfig, self._mediator, config_group)
        if config is None:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                'Failed to populate TimeBiasConfig in TimeBiasPreprocessor.',
            )
            return
        self._channels_to_correct = config.channels_to_correct
        self._time_bias = config.time_bias

    def process_pntos_message(self, message: Message) -> list[Message] | None:
        if message.source_identifier not in self._channels_to_correct:
            return [message]

        aspn_message: AspnBase = message.wrapped_message
        if not hasattr(aspn_message, 'time_of_validity'):
            self._mediator.log_message(
                LoggingLevel.WARN,
                f'TimeBiasPreprocessor received a message from channel {message.source_identifier} with no time of validity. Ignoring message.',
            )
            return [message]

        aspn_message.time_of_validity.elapsed_nsec -= self._time_bias

        return [message]
