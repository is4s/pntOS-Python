from numpy import array

from pntos.api import (
    LoggingLevel,
    Mediator,
    Message,
    Preprocessor,
    PreprocessorPlugin,
)
from pntos.cobra.config import DownsamplerConfig, config_from_registry


class SimplePreprocessorDownsampler(Preprocessor):
    _downsampling_factors: dict[str, int]
    _update_counters: dict[str, int]

    def __init__(self, config_group: str, mediator: Mediator):
        """
        A simple downsampling preprocessor that reduces the amount of data processed.

        It collects a list of channels and factors from the registry and allows 1 out of
        every ``N`` messages to pass through. This is done for every channel ``c`` and factor
        ``N``. Where ``c = channel[i]`` and ``N = factor[i]``.

        Args:
            config_group (str): The config group to be extracted from the registry.
            mediator (Mediator): The mediator that will handle and has access to the
                registry that contains 'config_group'.

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

        if not chan_len == fac_len:
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

        if not self._update_counters[identifier] == 0:
            return None

        return [message]


class SimplePreprocessorDownsamplerPlugin(PreprocessorPlugin):
    mediator: Mediator | None

    def __init__(self, identifier: str):
        """
        A simple downsampler preprocessor plugin that can create
        new instances of the SimplePreprocessorDownsampler class.

        Args:
            identifier (str): The plugin identifier used to set
                this plugin's :attr:`identifier` field.
        """
        self.identifier = identifier
        self.preprocessor_identifiers = ['preprocessor_downsampler']

    def init_plugin(
        self,
        plugin_resources_location: str | None = None,
        mediator: Mediator | None = None,
    ) -> None:
        if mediator is None:
            print('Error: mediator cannot be None')
        self.mediator = mediator

    def shutdown_plugin(self):
        pass

    def new_preprocessor(
        self,
        preprocessor_index: int,
        config_group: str | None = None,
    ) -> Preprocessor | None:
        if self.mediator is None:
            print(
                'Error: mediator is None. '
                + 'PreprocessorPluginDownsampler.init_plugin '
                + 'must be called and passed a valid mediator '
                + 'before new_preprocessor.'
            )
            return None

        if config_group is None:
            self.mediator.log_message(
                LoggingLevel.ERROR,
                'config_group is a required parameter for the '
                + 'PreprocessorPluginDownsampler and cannot be None.',
            )
            return None

        if not 0 <= preprocessor_index < len(self.preprocessor_identifiers):
            self.mediator.log_message(
                LoggingLevel.ERROR,
                f'Invalid preprocessor index of {preprocessor_index}. '
                'SimplePreprocessorDownsamplerPlugin provides '
                f'{len(self.preprocessor_identifiers)} preprocessors.',
            )
            return None

        return SimplePreprocessorDownsampler(config_group, self.mediator)
