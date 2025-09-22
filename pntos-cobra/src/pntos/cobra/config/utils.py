from dataclasses import fields
from enum import Enum
from inspect import isclass
from typing import Any, TypeVar, get_args, get_origin

import numpy as np
from navtk.filtering import ImuModel

from pntos.api import (
    EstimateWithCovariance,
    EstimateWithCovarianceType,
    LoggingLevel,
    Mediator,
    RegistryValueTypeUnion,
)

from .BaseConfig import BaseConfig
from .ImuConfig import ImuConfig

ConfigType = TypeVar('ConfigType', bound=BaseConfig)
SUPPORTED_TYPES = set(
    get_args(RegistryValueTypeUnion) + (tuple[float, ...], Enum, EstimateWithCovariance)
)


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
    out: dict[
        str,
        RegistryValueTypeUnion
        | tuple[float, ...]
        | Enum
        | EstimateWithCovariance
        | None,
    ] = {}
    fail = False
    for param in conf_params:
        if param.name in kv:
            val: (
                RegistryValueTypeUnion
                | tuple[float, ...]
                | Enum
                | EstimateWithCovariance
                | None
            ) = kv[param.name]
        elif (
            param.type == EstimateWithCovariance | None
            or param.type == EstimateWithCovariance
        ):
            if not '_ewc_type' in kv:
                out[param.name] = None
                continue
            val = EstimateWithCovariance(
                type=EstimateWithCovarianceType(kv['_ewc_type']),
                estimate=kv['_estimate'],  # type: ignore[arg-type]
                covariance=kv['_covariance'],  # type: ignore[arg-type]
            )
        # Special case: nested config or list of nested configs
        else:
            group_key = '_' + param.name + '_groups'
            if group_key not in kv:
                if _is_type_optional(param.type):
                    out[param.name] = None
                    continue
                mediator.log_message(
                    LoggingLevel.WARN,
                    f'Could not retrieve {param.name} from store',
                )
                fail = True
                continue

            groups = kv[group_key]
            val = []
            kv.batch_end()
            if isinstance(groups, str):
                if _is_type_optional(param.type):
                    conf_type = get_args(param.type)[0]
                else:
                    conf_type = param.type
                val = config_from_registry(conf_type, mediator, groups)
            elif isinstance(groups, list):
                conf_type = get_args(param.type)[0]
                if _is_type_optional(param.type):
                    conf_type = get_args(conf_type)[0]
                for group in groups:
                    conf = config_from_registry(conf_type, mediator, group)
                    if not conf:
                        fail = True
                        break
                    val.append(conf)
            kv.batch_restart()

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
                f'Expected field {param.name} in {config_type} to have type '
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
    It will convert an ``int`` to a ``float`` if the field is type hinted as a ``float``.
    It also supports storing nested config objects.

    Args:
        config (BaseConfig): The config to be stored in the registry.
        mediator (Mediator): A :class:`pntos.api.Mediator` instance.
    """
    conf_params = [f for f in fields(config) if f.name != 'group']
    kv = mediator.registry.batch_start(config.group)

    for param in conf_params:
        if not _is_type_supported(param.type):
            mediator.log_message(
                LoggingLevel.ERROR,
                f'Support for converting {param.type} to a registry type does not exist. Support must be added or a different type must be used on the config class {type(config)}',
            )
            kv.batch_end()
            return None
        val_to_store = getattr(config, param.name)
        if isinstance(val_to_store, int) and param.type is float:
            val_to_store = float(val_to_store)
        if not _confirm_types(val_to_store, param.type):
            mediator.log_message(
                LoggingLevel.ERROR,
                f'Expected field {param.name} in {type(config)} to have type {param.type} '
                + f'but received {type(val_to_store)} from registry.',
            )
            kv.batch_end()
            return None
        if isinstance(val_to_store, tuple):
            val_to_store = np.array(val_to_store, dtype=np.float64)
        elif isinstance(val_to_store, list) or isinstance(val_to_store, np.ndarray):
            if len(val_to_store) > 0:
                if isinstance(val_to_store[0], (int, float, np.int_)):
                    val_to_store = np.array(val_to_store, dtype=float)
                elif isinstance(val_to_store[0], BaseConfig):
                    nested_groups = []
                    for nested_config in val_to_store:
                        nested_groups.append(nested_config.group)
                        kv.batch_end()
                        config_to_registry(nested_config, mediator)
                        kv.batch_restart()
                    kv['_' + param.name + '_groups'] = nested_groups
                    continue
        elif isinstance(val_to_store, Enum):
            val_to_store = val_to_store.value
        elif isinstance(val_to_store, EstimateWithCovariance):
            kv['_estimate'] = val_to_store.estimate
            kv['_covariance'] = val_to_store.covariance
            kv['_ewc_type'] = val_to_store.type.value
            continue
        elif isinstance(val_to_store, BaseConfig):
            kv.batch_end()
            config_to_registry(val_to_store, mediator)
            kv.batch_restart()
            kv['_' + param.name + '_groups'] = val_to_store.group
            continue
        elif val_to_store is None:
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

    if _is_type_optional(expected_type):
        types = get_args(expected_type)
        valid_type = False
        for t in types:
            if hasattr(t, '__origin__'):
                return out_type is get_origin(t)
            if out_type is t:
                valid_type = True
        if valid_type:
            return True
        else:
            return False

    # Check if expected_type is generic alias (list[str], tuple[float], etc...)
    if hasattr(expected_type, '__origin__'):
        return out_type is get_origin(expected_type)

    # Otherwise, just see if it's the same type
    return issubclass(out_type, expected_type)


def _is_type_optional(field_type: type[Any] | str) -> bool:
    if isinstance(field_type, type):
        return False
    types = get_args(field_type)
    for t in types:
        if t is type(None):
            return True
    return False


def _is_type_supported(field_type: type[Any]) -> bool:
    type_to_compare = field_type
    if _is_type_optional(type_to_compare):
        type_to_compare = get_args(type_to_compare)[0]
    origin = get_origin(type_to_compare)
    # if type is a tuple, check each type it contains
    if origin is tuple:
        return _validate_tuple_type(type_to_compare)
    # we support lists of one of the following types: int, str, float, BaseConfig
    elif origin is list:
        args = get_args(type_to_compare)
        if len(args) != 1:
            return False
        if issubclass(args[0], (int, str, float, BaseConfig)):
            return True
    return type_to_compare in SUPPORTED_TYPES or issubclass(
        type_to_compare, (Enum, BaseConfig)
    )


def _validate_tuple_type(tuple_type: type[Any]) -> bool:
    args = get_args(tuple_type)
    for arg in args:
        arg_org = get_origin(arg)
        if arg_org is tuple:
            if not _validate_tuple_type(arg):
                return False
        elif arg_org is None:
            if arg is not float and arg is not Ellipsis:
                return False
        else:
            return False
    return True
