from typing import Callable

from pntos.api import (
    KeyValueStore,
    LoggingLevel,
    Mediator,
    RegistryValueTypeUnion,
    UtilityPlugin,
)
from pntos.cobra.utils import save_to_hdf5_file

GROUP_TO_WATCH = 'diagnostics'
OUTPUT_FILE = './OUTPUT.hdf5'


class SimpleDiagnosticLogPlugin(UtilityPlugin):
    _store: dict[str, list[RegistryValueTypeUnion]] = {}

    def __init__(self, identifier: str, output_file: str = './OUTPUT.hdf5') -> None:
        """
        Simple plugin to save any values put into the ``diagnostics`` group in the
        registry to an output HDF5 file (``OUTPUT_FILE``).

        If any other plugin wants to store values to the output, all the plugin has to
        do is write the values to any key within the ``diagnostics`` group. However,
        there are a two constraints:
        - All values assigned to a given key must be of the same type.
        - If the value for a given key is ``list[str]`` or ``NDArray[float64]``, the
        length must not change each update of the value at that key.

        Args:
            identifier (str): The plugin identifier passed to the
            :meth:`CommonPlugin.identifier` field.
        """
        self.identifier = identifier
        self._output_file = output_file

    def init_plugin(
        self,
        plugin_resources_location: str | None = None,
        mediator: Mediator | None = None,
    ) -> None:
        if mediator is None:
            print('ERROR: SimpleDiagnosticLogPlugin requires a mediator.')
            return
        self.mediator: Mediator = mediator

        kv = self.mediator.registry.batch_start(GROUP_TO_WATCH)
        kv.request_notify(None, self._callback)
        kv.batch_end()

    def shutdown_plugin(self) -> None:
        if self._store:
            save_to_hdf5_file(self._output_file, self._store, self.mediator)
            self.mediator.log_message(
                LoggingLevel.INFO, f'Created diagnostics log file: {self._output_file}'
            )

    def _callback(self, group: str, keys: list[str], kv: KeyValueStore) -> None:
        for key in keys:
            val = kv[key]
            if val is not None:
                if key not in self._store:
                    self._store[key] = [val]
                else:
                    self._store[key].append(val)
