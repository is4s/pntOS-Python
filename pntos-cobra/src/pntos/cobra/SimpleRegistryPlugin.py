import builtins
import os
import pickle
from typing import (
    Any,
    Callable,
    Dict,
    ItemsView,
    Iterator,
    KeysView,
    ValuesView,
)

import numpy as np
from numpy import float64
from numpy.typing import NDArray

from pntos.api import (
    KeyValueStore,
    KeyValueStoreDataFormat,
    LoggingLevel,
    Mediator,
    Message,
    Registry,
    RegistryPlugin,
    RegistryValueType,
    RegistryValueTypeUnion,
)
from pntos.cobra.config import BaseConfig, config_to_registry

REGISTRY_DATA_FORMAT = KeyValueStoreDataFormat.UNSPECIFIED
REGISTRY_SEPARATOR = ', '
DEFAULT_PERMANENCY_DIR = './registry_permanency_files/'


class SimpleKeyValueStore(KeyValueStore):
    """
    Implementation note: This implementation deviates from the python dictionary
    in that it heavily favors logging out errors and continuing on over raising
    exceptions. Exceptions are reserved only for truly fatal and unrecoverable
    errors. For example, instead of raising a ``KeyValue`` error for a key that
    does not exist in the store, the ``SimpleKeyValueStore`` just logs out an
    error message and returns None.
    """

    _store: dict[str, RegistryValueTypeUnion]
    _callbacks: dict[None | str, list[Callable[[str, list[str], KeyValueStore], None]]]
    _permanent_keys: set[str]
    _set_permanent: bool
    _modified_keys: set[str]
    data_format: KeyValueStoreDataFormat = REGISTRY_DATA_FORMAT
    _plugin_resources_location: str | None
    _group: str
    _permanency_file: str
    _permanency_dir: str
    _batch_live: bool
    _log: Callable[[LoggingLevel, str], None]
    _batch_err: str = (
        'Tried to use KeyValueStore outside of batch operation.'
        + ' (Make sure to use `batch_start`/`batch_restart` and `batch_end`)'
    )
    # An encoding that can handle any byte value
    _encoding = 'latin_1'

    def __init__(
        self,
        group: str,
        log_func: Callable[[LoggingLevel, str], None],
        plugin_resources_location: str | None = None,
    ) -> None:
        super().__init__()
        self._group = group
        self._set_permanent = False
        self._permanent_keys = set([])
        self._callbacks = {}
        self._modified_keys = set([])
        self._batch_live = True
        self._log = log_func
        self._plugin_resources_location = plugin_resources_location
        self.type_conversion: dict[Any, dict[Any, Any]] = {
            str: {
                list: self._return_list_str,
                int: self._return_int,
                bool: self._return_bool,
                float: self._return_float,
                np.ndarray: None,
                Message: None,
            },
            list: {
                str: self._return_str,
                int: None,
                bool: None,
                float: None,
                np.ndarray: self._return_array,
                Message: None,
            },
            int: {
                str: self._return_str,
                list: self._return_list_str,
                bool: None,
                float: self._return_float,
                np.ndarray: self._return_array,
                Message: None,
            },
            bool: {
                str: self._return_str,
                list: self._return_list_str,
                int: self._return_int,
                float: self._return_float,
                np.ndarray: self._return_array,
                Message: None,
            },
            float: {
                str: self._return_str,
                list: self._return_list_str,
                int: None,
                bool: None,
                np.ndarray: self._return_array,
                Message: None,
            },
            np.ndarray: {
                str: None,
                list: self._return_list_str,
                int: None,
                bool: None,
                float: None,
                Message: None,
            },
            Message: {
                str: None,
                list: None,
                int: None,
                bool: None,
                float: None,
                np.ndarray: None,
            },
        }
        """
        Usage: ``type_conversion[type_in_store][requested_return_type] ->
        requested_return_type | None``

        Will be None is conversion is not supported or conversion failed.
        """

        # Set up permanency
        if self._plugin_resources_location is not None:
            self._permanency_file = (
                self._plugin_resources_location + self._group + '.pkl'
            )
        else:
            self._permanency_file = DEFAULT_PERMANENCY_DIR + self._group + '.pkl'
        self._permanency_dir = os.path.dirname(self._permanency_file)
        if not os.path.exists(self._permanency_dir):
            os.makedirs(self._permanency_dir)
        if os.path.exists(self._permanency_file):
            with open(self._permanency_file, 'rb') as file:
                self._store = pickle.load(file)
        else:
            self._store = {}

    def keys(self) -> KeysView[str]:
        self._check_batch_operation()
        return self._store.keys()

    def __contains__(self, key: str) -> bool:
        """Wrapper function for dictionary-like kvstore."""
        self._check_batch_operation()
        return key in self._store

    def __setitem__(self, key: str, value: RegistryValueTypeUnion) -> None:
        """Wrapper function for dictionary-like kvstore."""
        self._check_batch_operation()
        self.set_value(key, value)

    def __getitem__(self, key: str) -> RegistryValueTypeUnion | None:
        self._check_batch_operation()
        if key in self._store:
            return self._store[key]
        self._log(
            LoggingLevel.ERROR,
            f"The key '{key}' is not found in the SimpleKeyValueStore.",
        )
        return None

    def __delitem__(self, key: str) -> None:
        self._check_batch_operation()
        if key in self._store:
            del self._store[key]
        else:
            self._log(
                LoggingLevel.ERROR,
                f'Key {key} does not exist in store. Unable to delete.',
            )
        if key in self._modified_keys:
            self._modified_keys.remove(key)
        if key in self._callbacks:
            del self._callbacks[key]
        if key in self._permanent_keys:
            self._permanent_keys.remove(key)

    def __len__(self) -> int:
        return len(self._store)

    def get_value(
        self, key: str, type: type[RegistryValueType]
    ) -> RegistryValueType | None:
        self._check_batch_operation()
        if key in self._store:
            val = self._store[key]
            if isinstance(val, type):  # Conversion not necessary - just return
                return val
            else:  # Conversion necessary
                convert = self.type_conversion[builtins.type(val)][type]
                if convert is not None:
                    out = convert(val)
                    if isinstance(out, type):
                        return out
                    else:
                        self._log(
                            LoggingLevel.ERROR,
                            'Unable to convert from type '
                            + f'{builtins.type(val)}'
                            + f' to type {type}.',
                        )
                else:
                    self._log(
                        LoggingLevel.ERROR,
                        f'Conversion from type {builtins.type(val)}'
                        + f' to type {type} unsupported.',
                    )

            return None
        self._log(LoggingLevel.ERROR, f'Key error - key {key} not in store.')
        return None

    def _return_str(self, val: Any) -> str | None:
        """Utility function for type conversion"""
        try:
            return str(val)
        except:
            return None

    def _return_list_str(self, val: Any) -> list[str] | None:
        """Utility function for type conversion"""
        try:
            if isinstance(val, np.ndarray):
                out = val.tolist()
                return [str(x) for x in out]
            else:
                return [str(val)]
        except:
            pass
        return None

    def _return_int(self, val: Any) -> int | None:
        """Utility function for type conversion"""
        try:
            return int(val)
        except:
            return None

    def _return_bool(self, val: Any) -> bool | None:
        """Utility function for type conversion"""
        try:
            return bool(val)
        except:
            return None

    def _return_float(self, val: Any) -> float | None:
        """Utility function for type conversion"""
        try:
            return float(val)
        except:
            return None

    def _return_array(self, val: Any) -> NDArray[float64] | None:
        """Utility function for type conversion"""
        # First see if it's one of the number types - return as array with length 1
        if isinstance(val, (int, bool, float)):
            number = self._return_float(val)
            if number is not None:
                return np.array([number], dtype=float64)

        # See if it's a list[str] with strings that can be converted to floats
        if isinstance(val, list):
            try:
                numbers = [float(x) for x in val]
                return np.array(numbers, dtype=float64)
            except:
                pass
        return None

    def get_raw(self, key: str | None = None) -> bytes | None:
        self._check_batch_operation()
        if key is None:
            self._log(
                LoggingLevel.ERROR,
                'This implementation requires a key to be passed to get_raw.',
            )
            return None
        out = self.get_value(key, str)
        if isinstance(out, str):
            return out.encode(self._encoding)
        else:
            if key not in self._store:
                self._log(
                    LoggingLevel.ERROR,
                    f'Key {key} does not exist in group {self._group}.',
                )
            else:
                self._log(
                    LoggingLevel.ERROR,
                    f'Value at key {key} cannot be converted to string.',
                )
            return None

    def set_value(self, key: str, value: RegistryValueTypeUnion) -> None:
        self._check_batch_operation()
        if not self._check_valid_type(value):
            self._log(
                LoggingLevel.ERROR,
                f'Received invalid type {type(value)}. Expected {RegistryValueTypeUnion}.',
            )
            return
        if self._set_permanent:
            self._permanent_keys.add(key)
        if key in self._store:
            store_val = self._store[key]
            if store_val is value:
                return  # Don't need to change anything
        self._modified_keys.add(key)
        self._store[key] = value
        return

    def set_raw(self, key: str | None, bytes: bytes) -> None:
        self._check_batch_operation()
        if key is None:
            self._log(
                LoggingLevel.ERROR,
                'This implementation requires a key to be passed to set_raw.',
            )
            return
        self[key] = bytes.decode(self._encoding)

    def remove_key(self, key: str) -> bool:
        self._check_batch_operation()
        del self[key]
        return True

    def batch_end(self) -> None:
        self._check_batch_operation()

        # Save any permanent keys
        if len(self._permanent_keys) != 0:
            permanent_dict = {}
            for key in self._permanent_keys:
                permanent_dict[key] = self._store[key]
            with open(self._permanency_file, 'wb') as file:
                pickle.dump(permanent_dict, file)

        # Turn off permanency (so that a restart doesn't keep writing permanent)
        self.set_permanent(False)

        # Run through non-keyed callbacks
        if None in self._callbacks:
            for callback in self._callbacks[None]:
                callback(self._group, list(self._modified_keys), self)

        # Run through keyed callbacks
        keys_per_callback: dict[
            Callable[[str, list[str], KeyValueStore], None], list[str]
        ] = {}
        for k in self._modified_keys:
            if k in self._callbacks:
                for callback in self._callbacks[k]:
                    if callback in keys_per_callback:
                        keys_per_callback[callback].append(k)
                    else:
                        keys_per_callback[callback] = [k]

        for callback in keys_per_callback:
            callback(self._group, keys_per_callback[callback], self)

        self._modified_keys = set([])
        self._batch_live = False
        return

    def batch_restart(self) -> None:
        if self._batch_live:
            self._log(
                LoggingLevel.ERROR,
                'Tried to restart batch while batch was in progress.',
            )
            return
        self._batch_live = True
        self._modified_keys = set([])
        return

    def request_notify(
        self,
        key: str | None,
        callback: Callable[[str, list[str], KeyValueStore], None],
    ) -> bool:
        self._check_batch_operation()
        if key not in self._callbacks:
            self._callbacks[key] = [callback]
        else:
            self._callbacks[key].append(callback)
        return True

    def remove_notify(
        self,
        key: str | None,
        callback: Callable[[str, list[str], KeyValueStore], None],
    ) -> bool:
        self._check_batch_operation()
        while key in self._modified_keys:
            self._modified_keys.remove(key)
        if key in self._callbacks:
            removed_any: bool = False
            while callback in self._callbacks[key]:
                self._callbacks[key].remove(callback)
                removed_any = True
            return removed_any
        else:
            return False

    def __iter__(self) -> Iterator[str]:
        self._check_batch_operation()
        return iter(self._store)

    def clear(self) -> None:
        self._check_batch_operation()
        self._store.clear()
        self._callbacks = {}
        self._modified_keys = set([])
        self._permanent_keys = set([])

    def values(self) -> ValuesView[RegistryValueTypeUnion]:
        self._check_batch_operation()
        return self._store.values()

    def items(self) -> ItemsView[str, RegistryValueTypeUnion]:
        self._check_batch_operation()
        return self._store.items()

    def set_permanent(self, permanent: bool) -> bool:
        self._check_batch_operation()
        self._set_permanent = permanent
        return True

    def get_type(self, key: str) -> type[RegistryValueTypeUnion] | None:
        self._check_batch_operation()
        if key in self._store:
            val = self._store[key]
            out_type = type(val)
            if self._check_valid_type(val):
                if isinstance(val, list):
                    return list[str]
                elif isinstance(val, np.ndarray):
                    return NDArray[float64]
                else:
                    return out_type
            else:
                self._log(
                    LoggingLevel.ERROR,
                    f'Invalid type {out_type} detected in the registry.',
                )
        return None

    def _check_batch_operation(self) -> None:
        """A Utility function to enforce batch operation per the API."""
        if not self._batch_live:
            self._log(LoggingLevel.ERROR, self._batch_err)

    def _check_valid_type(self, value: Any) -> bool:
        if isinstance(value, list):
            return all([isinstance(i, str) for i in value])
        if isinstance(value, np.ndarray):
            return bool(value.dtype == np.float64)
        return isinstance(value, (int, bool, float, Message, str))


class SimpleRegistry(Registry):
    groups: Dict[str, SimpleKeyValueStore]
    callbacks: list[Callable[[str], None]]
    _log: Callable[[LoggingLevel, str], None]
    _plugin_resources_location: str | None
    """
    Maps group names to objects storing all the key/values in that group.
    """

    def __init__(
        self,
        log_func: Callable[[LoggingLevel, str], None],
        plugin_resources_location: str | None = None,
    ) -> None:
        super().__init__()
        self.groups = {}
        self.callbacks = []
        self._log = log_func
        self._plugin_resources_location = plugin_resources_location

    def batch_start(self, group: str) -> KeyValueStore:
        if group not in self.groups:
            self.groups[group] = SimpleKeyValueStore(
                group, self._log, self._plugin_resources_location
            )
            for callback in self.callbacks:
                callback(group)
        if self.groups[group]._batch_live:
            self._log(LoggingLevel.ERROR, 'Batch already live.')
        self.groups[group]._batch_live = True
        return self.groups[group]

    def get_group_array(self) -> list[str]:
        return list(self.groups.keys())

    def has_group(self, group: str) -> bool:
        return group in self.groups

    def request_notify_new_group(self, callback: Callable[[str], None]) -> bool:
        self.callbacks.append(callback)
        return True


class SimpleRegistryPlugin(RegistryPlugin):
    config: list[BaseConfig]
    registries: list[SimpleRegistry]
    log_levels: Dict[LoggingLevel, str] = {
        LoggingLevel.ERROR: 'ERROR',
        LoggingLevel.WARN: 'WARN',
        LoggingLevel.INFO: 'INFO',
        LoggingLevel.DEBUG: 'DEBUG',
    }
    _plugin_resources_location: str | None = None
    mediator: Mediator

    def __init__(self, identifier: str, config: list[BaseConfig] | None = None) -> None:
        self.identifier = identifier
        self.registries = []
        self.config = config if config is not None else []

    def init_plugin(
        self,
        plugin_resources_location: str | None = None,
        mediator: Mediator | None = None,
    ) -> None:
        if mediator is None:
            self._log(LoggingLevel.ERROR, 'This registry requires a mediator.')
            return
        self.mediator = mediator
        self._plugin_resources_location = plugin_resources_location

        # Make sure to only add supported configs to registry

    def shutdown_plugin(self) -> None:
        # Batch-end any open key-value stores
        for registry in self.registries:
            for key in registry.groups:
                if registry.groups[key]._batch_live:
                    registry.groups[key].batch_end()

    identifier: str

    def new_registry(self, initial_config: str | None = None) -> Registry:
        if initial_config is not None:
            self._log(
                LoggingLevel.ERROR,
                'initial_config parameter is unsupported by this '
                + 'implementation; ignoring values.',
            )
        out = SimpleRegistry(self._log, self._plugin_resources_location)

        # Use input config from constructor
        for conf in self.config:
            config_to_registry(conf, out)

        self.registries.append(out)
        return out

    def _log(self, level: LoggingLevel, message: str) -> None:
        if self.mediator is not None:
            self.mediator.log_message(level, message)
        else:
            print(f'[RegistryPlugin] {self.log_levels[level]} {message}.')  # type: ignore[unreachable]
