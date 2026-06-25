"""
Data models for Cobra UI.

This module contains all Pydantic models, enums, and dataclasses used throughout
the Cobra UI package for representing registry data, subscriptions, and updates.
"""

from pydantic import BaseModel, ConfigDict
from pydantic.types import UUID4

from .types import DeSerializableRegistryValue, SerializableRegistryValue


class Subscription(BaseModel):
    """
    All data necessary to subscribe/unsubscribe to a certain group/key in the registry
    with a specific mode (stream behavior).
    """

    id: UUID4
    group: str
    key: str


class KeyUpdate(BaseModel):
    """
    Used to notify the front-end of the new value at a certain
    group/key in the registry.
    """

    val: SerializableRegistryValue
    subscription_ids: list[str]
    sequence_id: int
    model_config = ConfigDict(arbitrary_types_allowed=True)


class ChunkUpdate(BaseModel):
    """
    Communicates a "chunk" of ``updates`` to the front-end.
    """

    updates: dict[str, dict[str, KeyUpdate]]
    model_config = ConfigDict(arbitrary_types_allowed=True)


class Snapshot(BaseModel):
    """
    A snapshot of the values at all currently-subscribed group/keys in the
    registry.
    """

    data: dict[str, dict[str, SerializableRegistryValue]]
    model_config = ConfigDict(arbitrary_types_allowed=True)


class Write(BaseModel):
    """
    A batch write request from the front-end with updated values to write at various
    group/keys in the registry.
    """

    data: dict[str, dict[str, DeSerializableRegistryValue]]
    sequence_id: int
    model_config = ConfigDict(arbitrary_types_allowed=True)
