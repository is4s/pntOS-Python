"""Python API of pntOS."""

from typing import List, Optional, Protocol

from pntos.api import CommonPlugin, Message


class Preprocessor(Protocol):
    """
    A preprocessor.

    **UNSTABLE**: This feature is unstable and is not yet considered part of
    the stable pntOS API. Usage of this feature is highly discouraged in
    non-experimental code, and its definition may change at any time.
    """

    def process_pntos_message(self, message: Message) -> List[Message]:
        """
        Process a message.

        `message` - A message to be processed.
        return - A list of `Message`s. Usually this will be a single message, a
        modified version of `message`. It could be `None` if `message` is
        rejected or dropped. The preprocessor could also accumulate several
        messages, returning None for each one then returning an array with
        multiple processed messages.
        """
        pass


class PreprocessorPlugin(CommonPlugin, Protocol):
    """
    An implementation of a preprocessor plugin.

    This plugin generates `Preprocessor` instances which may be used to process incoming messages
    before being distributed to other plugins.

    **UNSTABLE**: This feature is unstable and is not yet considered part of
    the stable pntOS API. Usage of this feature is highly discouraged in
    non-experimental code, and its definition may change at any time.
    """

    preprocessor_identifiers: List[str]
    """
    A list of identifying strings for each kind of `Preprocessor` that this
    `PreprocessorPlugin` can create instances of.
    
    The `preprocessor_index` parameter of `new_preprocessor` is an index into
    this array.
    """

    def new_preprocessor(
        self, preprocessor_index: int, config_group: Optional[str] = None
    ) -> Preprocessor:
        """
        Returns a newly created `Preprocessor`.

        Returns `None` if `preprocessor_index` is greater than or equal to the length of
        `preprocessor_identifiers` or if `config_group` is invalid.

        `preprocessor_index` -  Since the `PreprocessorPlugin` can create
        `preprocessor_identifiers.len()` different kinds of `Preprocessor`, the
        `preprocessor_index` parameter is used to select which kind of
        preprocessor to create a new instance of. The
        `preprocessor_identifiers` field contains identifying strings for the
        kinds of preprocessors. For example, if the plugin can create 45
        different preprocessors, the identifier of the last preprocessor that
        can be created is found in `preprocessor_identifiers[44]`. An instance
        of this preprocessor can be created by calling
        `new_preprocessor(44, ...)`. Note that
        `0 <= preprocessor_index < length of preprocessor_identifiers`.

        `config_group` - Indicates which (if any) parameter group in the
        registry may be used to obtain additional configuration values to
        generate the new preprocessor. If the preprocessor requires no outside
        configuration, `config_group` may be `None`.
        """
        pass
