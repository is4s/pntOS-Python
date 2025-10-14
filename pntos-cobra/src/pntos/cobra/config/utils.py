from dataclasses import fields
from enum import Enum
from inspect import isclass
from typing import Any, TypeVar, get_args, get_origin

import numpy as np
from navtk.filtering import ImuModel
from numpy.typing import NDArray

from pntos.api import (
    EstimateWithCovariance,
    EstimateWithCovarianceType,
    LoggingLevel,
    Mediator,
    RegistryValueTypeUnion,
)
from pntos.cobra.utils import convert_ndarray_to_tuple

from .BaseConfig import BaseConfig
from .ImuConfig import ImuConfig

ConfigType = TypeVar('ConfigType', bound=BaseConfig)
SUPPORTED_TYPES = set(
    (int, float, str, bool, BaseConfig, tuple, Enum, EstimateWithCovariance)
)
SupportedTupleTypes = set((int, float, str, BaseConfig))


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
        accel_bias_initial_sigma=tuple(model.accel_bias_initial_sigma),
        gyro_bias_initial_sigma=tuple(model.gyro_bias_initial_sigma),
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
        accel_bias_initial_sigma=np.array(config.accel_bias_initial_sigma),
        gyro_bias_initial_sigma=np.array(config.gyro_bias_initial_sigma),
    )


def config_from_registry(  # noqa: PLR0915
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
            if '_ewc_type' not in kv:
                out[param.name] = None
                continue
            val = EstimateWithCovariance(
                type=EstimateWithCovarianceType(kv['_ewc_type']),
                estimate=kv['_estimate'],  # type: ignore[arg-type]
                covariance=kv['_covariance'],  # type: ignore[arg-type]
            )
        # Special case: nested config or a series of nested configs
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
                    if conf is None:
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
            dtype = None
            p_args = get_args(param.type)
            p_org = get_origin(p_args[0])
            while p_org is not None:
                p_args = get_args(p_args[0])
                p_org = get_origin(p_org)
            dtype = p_args[0]
            val = convert_ndarray_to_tuple(val, dtype)
        elif isinstance(val, list):
            val = tuple(val)  # type: ignore[arg-type]
        # Special case: enum. Convert integer back to enum type.
        elif isclass(param.type) and issubclass(param.type, Enum):
            val = param.type(val)

        if not _confirm_types(val, param.type):  # type: ignore[arg-type]
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

    This function verifies that all series of data are within tuples and converts them to a registry equivalent.
    It will convert an ``int`` to a ``float`` if the field is type hinted as a ``float``.
    It also supports storing nested config objects and the API defined :class:`pntos.api.EstimateWithCovariance`.

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
                f'Support for converting {param.type} to a registry type does not exist. Support must be added or a different type must be used on the config class {type(config)}.',
            )
            kv.batch_end()
            return
        val_to_store = getattr(config, param.name)
        # internally convert int to float if type is supposed to be float
        if isinstance(val_to_store, int) and param.type is float:
            mediator.log_message(
                LoggingLevel.WARN,
                f'Expected field {param.name} in {type(config)} to have type {param.type} '
                + f'but received {type(val_to_store)} from registry. Converting to {param.type}.',
            )
            val_to_store = float(val_to_store)
        # log warning if user provided a non-tuple series
        if isinstance(val_to_store, (list, np.ndarray)):
            mediator.log_message(
                LoggingLevel.WARN,
                f'Expected series to be a tuple but received a {type(val_to_store)}. '
                + 'Conversion to a supported registry type will be attempted.',
            )
        # compare user provided type with the validated config type hint
        if not isinstance(
            val_to_store, (tuple, list, np.ndarray)
        ) and not _confirm_types(val_to_store, param.type):
            mediator.log_message(
                LoggingLevel.ERROR,
                f'Expected field {param.name} in {type(config)} to have type {param.type} '
                + f'but received {type(val_to_store)} from registry.',
            )
            kv.batch_end()
            return None
        if isinstance(val_to_store, (tuple, list, np.ndarray)):
            if len(val_to_store) > 0:
                # convert numerical tuples to ndarray; we only support multi dimensional numerical tuples
                if np.issubdtype(type(val_to_store[0]), np.number) or isinstance(
                    val_to_store[0], (tuple, list, np.ndarray)
                ):
                    val_to_store = np.array(val_to_store, dtype=float)
                elif isinstance(val_to_store[0], str):
                    val_to_store = list(val_to_store)
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


def _confirm_types(out_val: Any, expected_type: type[Any]) -> bool:  # noqa: ANN401
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

    def compare_tuples(tuple1: type[Any], tuple2: type[Any]) -> bool:
        args1, args2 = (get_args(tuple1), get_args(tuple2))
        for i, arg1 in enumerate(args1):
            # if at the end of tuple2, iterate over the rest of tuple1
            if i < len(args2):
                arg2 = args2[i]
            org1, org2 = (get_origin(arg1), get_origin(arg2))
            if org1 is tuple and org2 is tuple:
                if not compare_tuples(arg1, arg2):
                    return False
            elif org1 is None and org2 is None:
                if arg1 == arg2:
                    continue
                if arg2 is Ellipsis:
                    continue
                return False
            elif org1 is tuple and org2 is None:
                if not _validate_tuple_type(arg1):
                    return False
                continue
            else:
                return False
        return True

    def compare_type(type_to_compare: type[Any], expected_type: type[Any]) -> bool:
        if str(type_to_compare) == str(expected_type):
            return True

        exp_org = get_origin(expected_type)
        ret_org = get_origin(type_to_compare)
        if exp_org != ret_org:
            return False
        # Check if expected_type is series
        if exp_org is tuple:
            return compare_tuples(type_to_compare, expected_type)

        # Otherwise, just see if it's the same type
        return issubclass(type_to_compare, expected_type)

    out_type = _get_verbose_type(out_val)

    if _is_type_optional(expected_type):
        types = get_args(expected_type)
        for t in types:
            if compare_type(out_type, t):
                return True
        return False

    return compare_type(out_type, expected_type)


def _get_verbose_type(obj: Any) -> Any:
    if isinstance(obj, tuple):
        inner_types = tuple(_get_verbose_type(item) for item in obj)
        return tuple[inner_types]  # type: ignore[valid-type]
    return type(obj)


def _is_type_optional(field_type: type[Any] | str) -> bool:
    """
    A helper function that determines if the provided type is optional i.e. contains `| None`.

    Args:
        field_type (type[Any] | str): The type to be checked.

    Returns:
        bool
    """
    if isinstance(field_type, type):
        return False
    types = get_args(field_type)
    return any(t is type(None) for t in types)


def _is_type_supported(field_type: type[Any]) -> bool:
    """
    A helper function that determines if the provided type is supported by ``config_from_registry``
    and ``config_to_registry``.

    Args:
        field_type (type[Any] | str): The type to be checked.

    Returns:
        bool
    """
    type_to_compare = field_type
    if _is_type_optional(type_to_compare):
        type_to_compare = get_args(type_to_compare)[0]
    origin = get_origin(type_to_compare)
    # if type is a tuple, check each type it contains
    if origin is tuple:
        return _validate_tuple_type(type_to_compare)
    # we support lists of one of the following types: int, str, float, BaseConfig
    elif origin is not None:
        return False
    return type_to_compare in SUPPORTED_TYPES or issubclass(
        type_to_compare, (Enum, BaseConfig)
    )


def _validate_tuple_type(tuple_type: type[Any], rec_call: bool = False) -> bool:
    """
    A recursive function that checks each type of the input ``tuple`` and determines
    if they are supported by ``config_from_registry`` and ``config_to_registry``.

    Args:
        tuple_type (type[Any]): The tuple type-hint to be checked.

    Returns:
        bool
    """
    args = get_args(tuple_type)
    first_arg = args[0]
    for arg in args:
        if arg != first_arg and arg is not Ellipsis:
            return False
        arg_org = get_origin(arg)
        if arg_org is tuple:
            if not _validate_tuple_type(arg, True):
                return False
        elif arg_org is None:
            if rec_call:
                if arg not in {int, float, Ellipsis}:
                    return False
            else:
                if (
                    arg not in SupportedTupleTypes
                    and arg is not Ellipsis
                    and not issubclass(arg, BaseConfig)
                ):
                    return False
        else:
            return False
    return True
