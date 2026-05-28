from dataclasses import fields, is_dataclass
from typing import Annotated, Any

import numpy as np
from pntos.api import RegistryValueTypeUnion
from pydantic import PlainSerializer, PlainValidator


def _serialize_registry_value(value: Any) -> Any:  # noqa: ANN401
    """
    Recursively serialize RegistryValueTypeUnion values for JSON transmission.
    """
    if isinstance(value, np.ndarray):
        return value.tolist()

    # Handle dataclasses (including Message) - will need a cleaner thing at some point
    if is_dataclass(value) and not isinstance(value, type):
        result = {}
        for field in fields(value):
            field_value = getattr(value, field.name)
            result[field.name] = _serialize_registry_value(field_value)
        return result

    if isinstance(value, dict):
        return {k: _serialize_registry_value(v) for k, v in value.items()}

    if isinstance(value, (list, tuple)):
        serialized = [_serialize_registry_value(item) for item in value]
        return serialized  # noqa: RET504

    return value


def _validate_list_of_numbers(value: Any) -> Any:  # noqa: ANN401
    if isinstance(value, list):
        return [_validate_list_of_numbers(val) for val in value]
    if isinstance(value, (float, int, bool)):
        return value
    raise RuntimeError(f'Invalid type: {type(value)}')


def _validate_registry_value(value: Any) -> Any:  # noqa: ANN401
    """
    Validate and deserialize input for RegistryValueTypeUnion.
    """
    if isinstance(value, list):
        if value and all(isinstance(item, str) for item in value):
            return value
        if list_of_nums := _validate_list_of_numbers(value):
            return np.array(list_of_nums, dtype=np.float64)

    if isinstance(value, (int, str, bool, float)):
        return value
    raise RuntimeError(f'Invalid type: {type(value)}')


SerializableRegistryValue = Annotated[
    RegistryValueTypeUnion,
    PlainSerializer(_serialize_registry_value, return_type=Any),
    PlainValidator(_validate_registry_value),
]

# This is very much TODO
DeSerializableRegistryValue = Annotated[
    str
    | list  # type: ignore[type-arg]
    | int
    | bool
    | float,  # Accept any list type (strings or numbers)
    PlainValidator(_validate_registry_value),
]
