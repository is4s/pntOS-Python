from dataclasses import Field, fields
from enum import Enum, IntEnum
from inspect import isclass
from typing import Any, TypeVar, get_args, get_origin

import numpy as np
from navtk.filtering import ImuModel
from numpy.typing import NDArray

from pntos.api import (
    EstimateWithCovariance,
    EstimateWithCovarianceType,
    KeyValueStore,
    LoggingLevel,
    Mediator,
    RegistryValueTypeUnion,
)
from pntos.cobra.utils import convert_ndarray_to_list, convert_ndarray_to_tuple

from .BaseConfig import BaseConfig
from .ImuConfig import ImuConfig

ConfigType = TypeVar('ConfigType', bound=BaseConfig)
"""
The type of any class which inherits from BaseConfig.

Used to tell :meth:`config_from_registry` which type of config class to attempt to get from the
registry.
"""
SUPPORTED_TYPES = {
    int,
    float,
    str,
    bool,
    BaseConfig,
    tuple,
    list,
    Enum,
    IntEnum,
    EstimateWithCovariance,
    np.ndarray,
}
SupportedSeriesTypes = (int, float, str, BaseConfig)
SupportedRegistryTypeUnion = (
    RegistryValueTypeUnion
    | tuple[Any, ...]
    | Enum
    | IntEnum
    | EstimateWithCovariance
    | None
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
    out: dict[str, SupportedRegistryTypeUnion] = {}
    val: SupportedRegistryTypeUnion
    fail = False
    for param in conf_params:
        if not param.init:  # field has constant value, don't set
            continue

        dtype = _get_dtype(param.type)  # type: ignore[arg-type]
        if _is_type_optional(param.type) and not _exists(kv, param.name, dtype):
            out[param.name] = None
            continue
        if issubclass(dtype, EstimateWithCovariance):
            val = EstimateWithCovariance(
                type=EstimateWithCovarianceType(kv['_ewc_type']),  # type: ignore[arg-type]
                estimate=kv['_estimate'],  # type: ignore[arg-type]
                covariance=kv['_covariance'],  # type: ignore[arg-type]
            )
        # Special case: nested config or a series of nested configs
        elif issubclass(dtype, BaseConfig):
            val = _nested_config_from_registry(kv, mediator, param)
        else:
            val = kv[param.name]

        if val is None:
            mediator.log_message(
                LoggingLevel.WARN,
                f'Could not retrieve {param.name} from store',
            )
            fail = True
            continue

        if isinstance(val, np.ndarray):
            # Numerical data series are stored in registry as numpy arrays, but config
            # dataclass supports list, tuple, or numpy array. Convert numpy array from
            # registry into desired dataclass type.
            val = _convert_numerical_series(val, param.type)  # type:ignore[arg-type]
        elif isinstance(val, list):
            # String data series are stored in registry as 1-D lists, but config
            # dataclass supports lists or tuples. Convert list to desired dataclass
            # type.
            val = _convert_series(val, param.type)  # type:ignore[arg-type]

        # Special case: enum. Convert integer back to enum type.
        elif isclass(dtype) and issubclass(dtype, Enum):
            val = dtype(val)

        if not _confirm_types(val, param.type):  # type: ignore[arg-type]
            mismatch_type_msg = f'config_from_registry: Field {param.name} in {config_type.__name__} has the wrong type.\n\tExpected: {param.type}\n\tReceived: {_get_verbose_type(val)}'
            mediator.log_message(LoggingLevel.ERROR, mismatch_type_msg)
            kv.batch_end()
            return None

        out[param.name] = val
    kv.batch_end()
    if fail:
        return None
    return config_type(**out, group=config_group)


def _exists(kv: KeyValueStore, pname: str, ptype: type[Any]) -> bool:
    """
    Determines if a parameter exists in the :class:`pntos.api.KeyValueStore`

    Args:
        kv (KeyValueStore): The KeyValueStore to search in.
        pname (str): The name of the parameter.
        ptype (type[Any]): The type of the parameter.
    """
    if issubclass(ptype, EstimateWithCovariance):
        if '_ewc_type' not in kv:
            return False
    elif issubclass(ptype, BaseConfig):
        group_key = '_' + pname + '_groups'
        if group_key not in kv:
            return False
    elif pname not in kv:
        return False
    return True


def _get_dtype(param_type: type[Any]) -> type[Any]:
    """
    Utility function that returns the most internal data type of a field.

    Args:
        param (Field[Any]): The parameter to examine.

    Returns:
        type[Any]
    """
    dtype = param_type
    args = get_args(param_type)
    while len(args) != 0:
        dtype = args[1] if get_origin(dtype) is np.ndarray else args[0]
        args = get_args(dtype)
    assert isinstance(dtype, type)
    return dtype


def _nested_config_from_registry(
    kv: KeyValueStore,
    mediator: Mediator,
    param: Field[Any],
) -> ConfigType | list[ConfigType] | None:
    """
    Utility function used to handle the instance where the target nested config
    could be singular or a series of config.

    Args:
        kv (KeyValueStore): The KeyValueStore to search in.
        mediator (Mediator): A :class:`pntos.api.Mediator` instance
        param (Field[Any]): The parameter that contains typing information about the original type

    Returns:
        ConfigType | list[ConfigType] | None
    """
    group_key = '_' + param.name + '_groups'
    if group_key not in kv:
        return None
    groups = kv[group_key]
    val = None
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
        val = []
        for group in groups:
            conf = config_from_registry(conf_type, mediator, group)
            if conf is None:
                val = None
                break
            val.append(conf)
    kv.batch_restart()
    return val


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
        if not _is_type_supported(param.type):  # type: ignore[arg-type]
            mediator.log_message(
                LoggingLevel.ERROR,
                f'Support for converting {param.type} to a registry type does not exist. Support must be added or a different type must be used on the config class {type(config)}.',
            )
            kv.batch_end()
            return
        val_to_store = getattr(config, param.name)

        result, val_to_store = _validate_config_value(
            val_to_store, param, type(config), mediator
        )
        if not result:
            kv.batch_end()
            return

        if isinstance(val_to_store, (tuple, list, np.ndarray)):
            if len(val_to_store) > 0:
                if np.issubdtype(type(val_to_store[0]), np.number) or isinstance(
                    val_to_store[0], (tuple, list, np.ndarray)
                ):
                    # convert arrays of numbers to NDArray[float64]
                    val_to_store = np.array(val_to_store, dtype=np.float64)
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


def _validate_config_value(
    val: SupportedRegistryTypeUnion,
    param: Field[Any],
    config_type: type[Any],
    mediator: Mediator,
) -> tuple[bool, Any]:
    """
    A helper function that handles some necessary logic to ensure ``val`` can be stored in the registry.

    Args:
        val (SupportedRegistryTypeUnion): The config value to be examined.
        param (Field[Any]): The config parameter that contains information about what ``val`` should be.
        config_type (type[Any]): The type of config ``val`` and ``param`` originate from, only used for logging.
        mediator (Mediator): A :class:`pntos.api.Mediator` instance.

    Returns:
        A `tuple[bool, Any]` where the first value indicates if the validation was successful and the second value
        is ``val`` or what it gets converted to.
    """
    if _confirm_types(val, param.type):  # type: ignore[arg-type]
        return (True, val)  # Got expected type, everything is good

    # If type mismatch, log a warning and convert to expected type for the following cases:
    #   - got int, expected float
    #   - got list/tuple/ndarray expected list/tuple/ndarray
    # Otherwise error and return failure.
    mismatch_type_msg = f'config_to_registry: Field {param.name} in {config_type.__name__} has the wrong type.\n\tExpected: {param.type}\n\tReceived: {_get_verbose_type(val)}'
    converting_msg = f'{mismatch_type_msg}\nConverting to expected type.'
    # internally convert int to float if type is supposed to be float
    if isinstance(val, int) and param.type is float:
        mediator.log_message(LoggingLevel.WARN, converting_msg)
        val = float(val)
        return (True, val)
    if isinstance(val, (tuple, list, np.ndarray)):
        # don't need to actually convert to expected type now, as all
        # tuples/lists/ndarrays will be converted to the same internal type when storing
        # in the registry.
        mediator.log_message(LoggingLevel.WARN, converting_msg)
        return (True, val)

    # Could not convert to expected type
    mediator.log_message(LoggingLevel.ERROR, mismatch_type_msg)
    return (False, val)


def _confirm_types(
    out_val: SupportedRegistryTypeUnion, expected_type: type[Any]
) -> bool:
    """
    A helper function which determines if the type of ``out_val`` is equivalent to ``expected_type``.
    If equivalent, returns true otherwise returns false.
    This function supports the case where ``expected_type`` is a generic alias.

    Args:
        out_val (SupportedRegistryTypeUnion): Object whose type is to be validated.
        expected_type (type[Any]): The expected type of `out_val`.

    Returns:
        bool
    """

    def check_ndarray_type(actual_type: type[Any], expected_type: type[Any]) -> bool:
        actual_dtype = get_args(actual_type)[0]
        expected_shape, expected_dtype = get_args(expected_type)  # noqa:RUF059
        return actual_dtype == expected_dtype  # type:ignore[no-any-return]

    def check_list_type(actual_type: type[Any], expected_type: type[Any]) -> bool:
        actual_item_type = get_args(actual_type)[0]
        expected_item_type = get_args(expected_type)[0]

        if actual_item_type == expected_item_type:
            return True

        if get_origin(actual_item_type) is list:
            # list of lists
            return check_list_type(actual_item_type, expected_item_type)

        return False

    def check_tuple_type(actual_type: type[Any], expected_type: type[Any]) -> bool:
        args1, args2 = (get_args(actual_type), get_args(expected_type))
        for i, arg1 in enumerate(args1):
            # if at the end of expected_type, iterate over the rest of actual_type
            if i < len(args2):
                arg2 = args2[i]
            org1, org2 = (get_origin(arg1), get_origin(arg2))
            if org1 is tuple and org2 is tuple:
                if not check_tuple_type(arg1, arg2):
                    return False
            elif org1 is None and org2 is None:
                if arg2 is Ellipsis or issubclass(arg1, arg2):
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
        if exp_org is np.ndarray:
            return check_ndarray_type(type_to_compare, expected_type)
        if exp_org is list:
            return check_list_type(type_to_compare, expected_type)
        if exp_org is tuple:
            return check_tuple_type(type_to_compare, expected_type)

        # Otherwise, just see if it's the same type
        return issubclass(type_to_compare, expected_type)

    out_type = _get_verbose_type(out_val)

    if _is_type_optional(expected_type):
        types = get_args(expected_type)
        return any(compare_type(out_type, t) for t in types)

    return compare_type(out_type, expected_type)


def _get_verbose_type(obj: SupportedRegistryTypeUnion) -> type[Any]:
    if isinstance(obj, tuple):
        inner_types = tuple(_get_verbose_type(item) for item in obj)
        return tuple[inner_types]  # type: ignore[valid-type]
    if isinstance(obj, list):
        return list[_get_verbose_type(obj[0])]  # type: ignore[misc,return-value]
    if isinstance(obj, np.ndarray):
        return np.ndarray[np.dtype[obj.dtype]]  # type: ignore[misc,no-any-return,name-defined]
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
    # if type is a tuple or list, check the type of each value it contains
    if origin is list:
        return _validate_list_type(type_to_compare)
    if origin is tuple:
        return _validate_tuple_type(type_to_compare)
    if origin is np.ndarray:
        shape, dtype = get_args(type_to_compare)  # noqa: RUF059
        dtype = get_args(dtype)[0]
        return dtype in (np.float64, np.int64)
    # we support lists of one of the following types: int, str, float, BaseConfig
    if origin is not None:
        return False
    return type_to_compare in SUPPORTED_TYPES or issubclass(
        type_to_compare, (Enum, IntEnum, BaseConfig)
    )


def _validate_list_type(list_type: type[Any]) -> bool:
    """
    A recursive function that checks if the type of the input ``list`` is supported by
    ``config_from_registry`` and ``config_to_registry``.

    Args:
        list_type (type[Any]): The list type-hint to be checked.

    Returns:
        bool
    """
    item_type = get_args(list_type)[0]
    if get_origin(item_type) is list:
        return _validate_list_type(item_type)

    return issubclass(item_type, SupportedSeriesTypes)


def _validate_tuple_type(tuple_type: type[Any], rec_call: bool = False) -> bool:
    """
    A recursive function that checks each type of the input ``tuple`` and determines if
    they are supported by ``config_from_registry`` and ``config_to_registry``.

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
            elif (
                arg not in SupportedSeriesTypes
                and arg is not Ellipsis
                and not issubclass(arg, BaseConfig)
            ):
                return False
        else:
            return False
    return True


def _convert_numerical_series(
    val: NDArray,  # type: ignore[type-arg]
    output_type: type[Any],
) -> list | tuple | NDArray:  # type: ignore[type-arg]
    """Convert numpy array of numbers to desired type when extracting from registry.

    Possible output types are:
    - list of ints
    - tuple of ints
    - numpy array of ints
    - list of floats
    - tuple of floats
    - numpy array of floats (No conversion necessary)

    Note that these could be multidimensional arrays.
    """
    dtype = _get_dtype(output_type)  # type of individual values (int or float)
    if _is_type_optional(output_type):
        output_type = get_args(output_type)[0]
    series_type = get_origin(output_type)
    if series_type is list:
        return convert_ndarray_to_list(val, dtype)
    if series_type is tuple:
        return convert_ndarray_to_tuple(val, dtype)

    return val.astype(dtype)  # return numpy array as-is


def _convert_series(
    val: list[Any], output_type: type[list[Any] | tuple[Any]]
) -> list[Any] | tuple[Any]:
    """Convert list of values to desired type when extracting from registry.

    Possible output types are:
    - list[Any] (No conversion necessary)
    - tuple[Any]
    """
    if _is_type_optional(output_type):
        output_type = get_args(output_type)[0]

    if get_origin(output_type) is tuple:
        return tuple(val)

    return val  # return list as-is
