from dataclasses import fields
from enum import Enum
from typing import Any, TypeVar, get_origin

import numpy as np

from pntos.api import LoggingLevel, Mediator, Registry, RegistryValueTypeUnion

from .BaseConfig import BaseConfig

ConfigType = TypeVar('ConfigType', bound=BaseConfig)


def config_from_registry(
    config_type: type[ConfigType], mediator: Mediator, config_group: str
) -> ConfigType | None:
    conf_params = [f for f in fields(config_type)]
    kv = mediator.registry.batch_start(config_group)
    out: dict[str, RegistryValueTypeUnion | tuple[float, ...] | Enum] = {}
    fail = False
    for param in conf_params:
        val: RegistryValueTypeUnion | tuple[float, ...] | Enum | None = kv[param.name]
        if val is None:
            mediator.log_message(
                LoggingLevel.WARN,
                f'Could not retrieve {param.name} from store',
            )
            fail = True
            continue

        if isinstance(val, np.ndarray):
            if hasattr(param.type, '__origin__'):
                p_type = get_origin(param.type)
                if p_type is tuple:
                    val = tuple(val)
                elif p_type is list:
                    # Convert numpy array to list
                    if str(param.type) == 'list[int]':
                        # Convert to list of ints
                        val = val.astype(int)
                    val = list(val)
                elif p_type is np.ndarray:
                    if np.dtype[np.int_] in param.type.__args__:
                        # Convert to np array of ints
                        val = val.astype(int)
        # Special case: enum. Convert integer back to enum type.
        elif issubclass(param.type, Enum):
            val = param.type(val)

        if not _confirm_types(val, param.type):
            mediator.log_message(
                LoggingLevel.ERROR,
                f'Expected field {param} in {config_type} to have type '
                + f'{param.type} but received {type(val)} from registry.',
            )
            kv.batch_end()
            return None

        out[param.name] = val
    kv.batch_end()
    if fail:
        return None
    return config_type(**out)  # type: ignore[arg-type]


def config_to_registry(config: BaseConfig, registry: Registry) -> None:
    conf_params = [f for f in fields(config)]
    kv = registry.batch_start(config.group)

    for param in conf_params:
        val_to_store = getattr(config, param.name)
        if isinstance(val_to_store, tuple):
            val_to_store = np.array(val_to_store, dtype=np.float64)
        elif isinstance(val_to_store, list) or isinstance(val_to_store, np.ndarray):
            if len(val_to_store) > 0:
                if isinstance(val_to_store[0], (int, float, np.int_)):
                    val_to_store = np.array(val_to_store, dtype=float)
        elif isinstance(val_to_store, Enum):
            val_to_store = val_to_store.value
        kv[param.name] = val_to_store
    kv.batch_end()


def _confirm_types(out_val: Any, expected_type: type[Any]) -> bool:
    out_type = type(out_val)

    # Check if expected_type is generic alias (list[str], tuple[float], ect...)
    if hasattr(expected_type, '__origin__'):
        return out_type is get_origin(expected_type)

    # Otherwise, just see if it's the same type
    return out_type is expected_type
