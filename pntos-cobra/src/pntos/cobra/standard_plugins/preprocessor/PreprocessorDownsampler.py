from numpy import array
from pntos.api import (
    LoggingLevel,
    Mediator,
    Message,
    Preprocessor,
)
from pntos.cobra.config import (
    DownsamplerConfig,
    config_from_registry,
)


class PreprocessorDownsampler(Preprocessor):
    """
    A downsampling preprocessor that periodically discards certain messages.

    It collects a list of channels and factors from the registry and allows 1 out of
    every ``N`` messages to pass through. This is done for every channel ``c`` and factor
    ``N``. Where ``c = channel[i]`` and ``N = factor[i]``.
    """

    _downsampling_factors: dict[str, int]
    _update_counters: dict[str, int]

    def __init__(self, config_group: str, mediator: Mediator) -> None:
        """
        Cobra Downsampler Preprocessor

        Args:
            config_group (str): The :class:`pntos.cobra.config.DownsamplerConfig` config group.
            mediator (Mediator): A :class:`pntos.api.Mediator` instance.
        """
        self._downsampling_factors = {}
        self._update_counters = {}
        self.mediator = mediator
        config = config_from_registry(DownsamplerConfig, mediator, config_group)

        if config is None:
            self.mediator.log_message(
                LoggingLevel.ERROR,
                'Unable to retrieve config from registry.',
            )
            return

        channels = config.channels_to_downsample
        factors = array(config.downsampling_factors, dtype=int)
        chan_len = len(channels)
        fac_len = len(factors)

        if chan_len != fac_len:
            self.mediator.log_message(
                LoggingLevel.WARN,
                f'Channels to downsample has {chan_len} elements, '
                + f'but downsampling factors has {fac_len}. '
                + 'Downsampling will be disabled.',
            )
            return

        for idx in range(chan_len):
            channel = channels[idx]
            if factors[idx] < 0:
                self.mediator.log_message(
                    LoggingLevel.WARN,
                    f'Downsampling factor of {factors[idx]} '
                    + f'for channel "{channel}" cannot be negative. '
                    + 'Channel will not be downsampled.',
                )
            else:
                self._downsampling_factors[channel] = factors[idx]
                # Setting to -1 so the first message is always processed
                self._update_counters[channel] = -1

    def process_pntos_message(self, message: Message) -> list[Message] | None:
        identifier = message.source_identifier
        if identifier not in self._downsampling_factors:
            return [message]

        # Keep 1 out of every N messages on the current channel
        # where N = factor.
        factor = self._downsampling_factors[identifier]
        count = self._update_counters[identifier]
        self._update_counters[identifier] = (count + 1) % factor

        if self._update_counters[identifier] != 0:
            return None

        return [message]
