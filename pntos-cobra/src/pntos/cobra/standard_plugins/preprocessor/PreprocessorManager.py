import re
from typing import NamedTuple, TypeAlias

from pntos.api import Mediator, Message, PreprocessorPlugin
from pntos.api.plugins.preprocessor import Preprocessor
from pntos.cobra.config import PreprocessorConfig

PreprocessorChain: TypeAlias = list[Preprocessor]


class PreprocessorDescriptor(NamedTuple):
    """
    Storage medium that couples a preprocessor with its config's channels.
    """

    preprocessor: Preprocessor
    channels: tuple[str, ...] | None
    regex: bool


class PreprocessorManager:
    def __init__(
        self,
        preprocessor_plugins: list[PreprocessorPlugin],
        preprocessor_configs: tuple[PreprocessorConfig, ...],
        mediator: Mediator,
    ) -> None:
        """
        Initializes preprocessor manager based on the  information from ``preprocessor_configs`` and
        the plugins from ``preprocessor_plugins``.

        Args:
            preprocessor_plugins (list[PreprocessorPlugin]):
            preprocessor_configs (tuple[PreprocessorConfig, ...]):
            mediator (Mediator):
        """
        # Maps channels to a chain of preprocessors
        self._chains: dict[str, PreprocessorChain | None] = {}
        self._descriptors: list[PreprocessorDescriptor] = []
        self._mediator = mediator

        for config in preprocessor_configs:
            preprocessor = PreprocessorManager._find_preprocessor(
                config.identifier, config.group, preprocessor_plugins
            )
            if preprocessor is not None:
                self._descriptors.append(
                    PreprocessorDescriptor(preprocessor, config.channels, config.regex)
                )

    @classmethod
    def _find_preprocessor(
        cls,
        config_identifier: str,
        config_group: str,
        preprocessor_plugins: list[PreprocessorPlugin],
    ) -> Preprocessor | None:
        """
        Find the associated preprocessor with a given identifier, config group, and list of
        preprocessor plugins. Returns None if preprocessor cannot be found with given inputs.

        Args:
            config_identifier (str):
            config_group (str):
            preprocessor_plugins (list[PreprocessorPlugin]):

        Returns:
            Preprocessor | None: _description_
        """
        for plugin in preprocessor_plugins:
            for idx, identifier in enumerate(plugin.preprocessor_identifiers):
                if identifier == config_identifier:
                    return plugin.new_preprocessor(idx, config_group)
        return None

    def _add_preprocessor_chain(self, new_channel: str) -> None:
        """
        Adds a new preprocessing chain to the cache of chains.

        Args:
            new_channel (str): The channel to create the new chain with
        """
        chain_to_create: PreprocessorChain = []
        for descriptor in self._descriptors:
            # If channels is None, the preprocessor will be added to the chain to create
            if not descriptor.channels:
                chain_to_create.append(descriptor.preprocessor)
                continue
            for channel in descriptor.channels:
                # Check if new channel matches regex pattern or exact channel string
                matched = (
                    re.search(channel, new_channel)
                    if descriptor.regex
                    else channel == new_channel
                )
                if matched:
                    chain_to_create.append(descriptor.preprocessor)
                    break

        # Cache the created chain if not empty, otherwise store None
        self._chains[new_channel] = chain_to_create or None

    def preprocess_message(self, message: Message) -> list[Message] | None:
        """
        Given a message, preprocess it using the most suitable/relevant chain of preprocessors.

        Args:
            message (Message): The message to preprocess

        Returns:
            list[Message] | None: The output messages, or None if one of the preprocessors dropped
            the input message.
        """
        out_list = [message]
        channel = message.source_identifier

        if channel not in self._chains:
            self._add_preprocessor_chain(channel)

        preprocessor_chain = self._chains[channel]
        if preprocessor_chain is None:
            return out_list

        for preprocessor in preprocessor_chain:
            if len(out_list) == 0:
                return None
            tmp_list = out_list.copy()
            out_list = []
            for out_message in tmp_list:
                new_messages = preprocessor.process_pntos_message(out_message)
                if new_messages is not None:
                    out_list.extend(new_messages)

        if len(out_list) > 0:
            return out_list
        return None
