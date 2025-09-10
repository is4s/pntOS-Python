from dataclasses import fields
from enum import Enum
from inspect import isclass
from typing import Any, TypeVar, get_origin

import numpy as np
from navtk.filtering import ImuModel

from pntos.api import LoggingLevel, Mediator, Registry, RegistryValueTypeUnion

from .BaseConfig import BaseConfig
from .ImuConfig import ImuConfig

ConfigType = TypeVar('ConfigType', bound=BaseConfig)


def imu_model_to_config(model: ImuModel, group: str) -> ImuConfig:
    """
    Stores a provided IMU model inside an :class:`ImuConfig` object.

    Args:
        model (ImuModel): The IMU model to store.
        group (str): The config group the :class:`ImuConfig` object should be stored under in the registry.

    Returns:
        ImuConfig
    """
    return ImuConfig(
        accel_bias_sigma=tuple(model.accel_bias_sigma),
        accel_bias_tau=tuple(model.accel_bias_tau),
        accel_random_walk_sigma=tuple(model.accel_random_walk_sigma),
        gyro_bias_sigma=tuple(model.gyro_bias_sigma),
        gyro_bias_tau=tuple(model.gyro_bias_tau),
        gyro_random_walk_sigma=tuple(model.gyro_random_walk_sigma),
        group=group,
    )


def imu_model_from_config(config: ImuConfig) -> ImuModel:
    """
    Grabs the ``ImuModel`` object nested within the provided :class:`ImuConfig` object.

    Args:
        config (ImuConfig): The :class:`ImuConfig` object to grab an ``ImuModel`` object from.

    Returns:
        ImuModel
    """
    return ImuModel(
        accel_bias_sigma=np.array(config.accel_bias_sigma),
        accel_bias_tau=np.array(config.accel_bias_tau),
        accel_random_walk_sigma=np.array(config.accel_random_walk_sigma),
        gyro_bias_sigma=np.array(config.gyro_bias_sigma),
        gyro_bias_tau=np.array(config.gyro_bias_tau),
        gyro_random_walk_sigma=np.array(config.gyro_random_walk_sigma),
    )


def config_from_registry(
    config_type: type[ConfigType], mediator: Mediator, config_group: str
) -> ConfigType | None:
    """
    A utility function that extracts the requested config from the registry.

    This function is used to extract requested configs loaded into the registry by
    ``config_to_registry``. Since that function converts objects into registry compliant
    types, this function attempts to convert them back to their original type specified
    within the ``config_type`` parameter. If it is unable to do so, it will log the error
    and continue. If the function is unable to grab a field from the registry,
    (e.g. the ``accel_bias_sigma`` in an ImuConfig) the error is considered fatal
    and the function will return ``None``.

    Args:
        config_type (ConfigType): The parameter that specifies which config the user wants to receive.
        mediator (Mediator): A :class:`pntos.api.Mediator` instance.
        config_group (str): The registry group which contains the config being extracted.

    Returns:
        ConfigType | None
    """
    conf_params = [f for f in fields(config_type) if f.name != 'group']
    kv = mediator.registry.batch_start(config_group)
    out: dict[str, RegistryValueTypeUnion | tuple[float, ...] | Enum | BaseConfig] = {}
    fail = False
    for param in conf_params:
        val: RegistryValueTypeUnion | tuple[float, ...] | Enum | BaseConfig | None = kv[
            param.name
        ]
        # Special case: nested config. Identifiable by the first field, which is called `group` and
        # is a str.
        if val is None:
            try:
                first_field = fields(param.type)[0]
                if first_field.name == 'group' and first_field.type is str:
                    kv.batch_end()
                    val = config_from_registry(param.type, mediator, config_group)
                    kv.batch_restart()
            except TypeError:
                pass
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
        elif isclass(param.type) and issubclass(param.type, Enum):
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
    return config_type(**out, group=config_group)


def config_to_registry(config: BaseConfig, mediator: Mediator) -> None:
    """
    A utility function that inserts a config into the registry.

    This function will convert certain types (list[float], list|nd.array[int], Enum, tuple[float])
    unsupported by the registry to the corresponding supported type represented by ``RegistryValueType``.
    It also supports storing nested config objects, though it expects the nested object to have the
    same config group as the outer object.

    Args:
        config (BaseConfig): The config to be stored in the registry.
        mediator (Mediator): A :class:`pntos.api.Mediator` instance.
    """
    conf_params = [f for f in fields(config) if f.name != 'group']
    kv = mediator.registry.batch_start(config.group)

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
        elif isinstance(val_to_store, BaseConfig):
            if val_to_store.group != config.group:
                mediator.log_message(
                    LoggingLevel.WARN,
                    'Nested config uses a different group. It will not be able to be retrieved via config_from_registry',
                )
            kv.batch_end()
            config_to_registry(val_to_store, mediator)
            kv.batch_restart()
            continue
        kv[param.name] = val_to_store
    kv.batch_end()


def _confirm_types(out_val: Any, expected_type: type[Any]) -> bool:
    """
    A helper function which determines if the type of ``out_val`` is equivalent to ``expected_type``.
    If equivalent, returns true otherwise returns false.
    This function supports the case where ``expected_type`` is a generic alias.

    Args:
        out_val (Any): Object whose type is to be validated.
        expected_type (type[Any]): The expected type of `out_val`.

    Returns:
        bool
    """
    out_type = type(out_val)

    # Check if expected_type is generic alias (list[str], tuple[float], ect...)
    if hasattr(expected_type, '__origin__'):
        return out_type is get_origin(expected_type)

    # Otherwise, just see if it's the same type
    return out_type is expected_type
