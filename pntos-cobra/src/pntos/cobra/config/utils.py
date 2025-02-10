from dataclasses import fields
from typing import Any, TypeVar, get_origin

import numpy as np

from pntos.api import LoggingLevel, Mediator, RegistryValueTypeUnion

from .AlignmentConfig import AlignmentConfig
from .ImuConfig import ImuConfig
from .SensorConfig import SensorConfig

ConfigType = TypeVar('ConfigType', AlignmentConfig, ImuConfig, SensorConfig)
ConfigTypeUnion = AlignmentConfig | ImuConfig | SensorConfig


def config_from_registry(
    config_type: type[ConfigType],
    mediator: Mediator,
    config_group: str,
) -> ConfigType | None:
    conf_params = [f for f in fields(config_type)]
    kv = mediator.registry.batch_start(config_group)
    out: dict[str, RegistryValueTypeUnion | tuple[float, ...]] = {}
    fail = False
    for param in conf_params:
        val: RegistryValueTypeUnion | tuple[float, ...] | None = kv[param.name]
        if val is None:
            mediator.log_message(
                LoggingLevel.ERROR,
                f'Could not retrieve {param.name} from store',
            )
            fail = True
            continue

        if isinstance(val, np.ndarray):
            if hasattr(param.type, '__origin__') and get_origin(param.type) is tuple:
                val = tuple(val)

        if not _confirm_types(val, param.type):
            mediator.log_message(
                LoggingLevel.ERROR,
                f'Expected field {param} in {config_type} to have type '
                + f'{param.type} but received {type(val)} from registry.',
            )
            return None

        out[param.name] = val
    kv.batch_end()
    if fail:
        return None
    return config_type(**out)  # type: ignore[arg-type]


def config_to_registry(config: ConfigTypeUnion, mediator: Mediator) -> None:
    conf_params = [f for f in fields(config)]
    kv = mediator.registry.batch_start(config.group)

    for param in conf_params:
        val_to_store = getattr(config, param.name)
        if isinstance(val_to_store, tuple):
            val_to_store = np.array(val_to_store, dtype=np.float64)
        kv[param.name] = val_to_store
    kv.batch_end()


def _confirm_types(out_val: Any, expected_type: type[Any]) -> bool:
    out_type = type(out_val)

    # Check if expected_type is generic alias (list[str], tuple[float], ect...)
    if hasattr(expected_type, '__origin__'):
        return out_type is get_origin(expected_type)

    # Otherwise, just see if it's the same type
    return out_type is expected_type
