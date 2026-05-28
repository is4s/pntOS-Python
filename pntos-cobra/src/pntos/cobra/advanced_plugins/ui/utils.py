"""
Registry management utilities for Cobra UI.

This module contains utility classes for managing pntOS registry subscriptions,
callbacks, and update aggregation.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from threading import Event, Lock, RLock
from typing import Any, Generic, TypeVar

from pntos.api import Mediator, Registry, RegistryValueTypeUnion
from pntos.api.plugins.common import KeyValueStore
from pntos.cobra.utils import MutableValueView, ValueType
from pydantic.types import UUID4

from .models import (
    ChunkUpdate,
    KeyUpdate,
    Snapshot,
    Subscription,
    Write,
)

_T = TypeVar('_T')


class SequenceBuffer(Generic[_T]):
    _next_id: int
    _key: Callable[[_T], int]
    _pending: dict[int, _T]

    def __init__(self, key: Callable[[_T], int]) -> None:
        self._next_id = 0
        self._key = key
        self._pending = {}

    def add(self, item: _T) -> list[_T]:
        self._pending[self._key(item)] = item
        out: list[_T] = []
        while self._next_id in self._pending:
            out.append(self._pending.pop(self._next_id))
            self._next_id += 1
        return out


class LockedSequenceGenerator:
    """Thread-safe sequence ID generator."""

    _n: int
    _lock: Lock

    def __init__(self) -> None:
        self._n = 0
        self._lock = Lock()

    def reset(self) -> None:
        """Reset the sequence counter to zero."""
        with self._lock:
            self._n = 0

    @property
    def next(self) -> int:
        """Get the next sequence ID."""
        with self._lock:
            out = self._n
            self._n += 1
        return out


@dataclass
class Emit:
    """WebSocket emission event."""

    event: str
    message: str | dict[str, Any]


class KeyInfo(MutableValueView[ValueType], Generic[ValueType]):
    _subscriptions: dict[UUID4, Subscription]
    """All subscriptions for this key with ``SubscriptionMode.LAST``"""
    _do_not_update_front_end: Event
    """
    If set, the next callback will be assumed to be a write from the front-end or some
    other write that we do not want to send front-end updates for, and the next callback
    will not trigger a front-end update.
    """

    def __init__(
        self,
        registry: Registry,
        group: str,
        key: str,
        callback_registrar: 'CallbackRegistrar',
    ) -> None:
        self._subscriptions = {}
        self._callback_registrar: CallbackRegistrar = callback_registrar
        self._do_not_update_front_end = Event()
        super().__init__(registry, group, key, None)  # type: ignore[arg-type]

    def _callback(self, group: str, keys: list[str], kv: KeyValueStore) -> None:
        super()._callback(group, keys, kv)
        if self._do_not_update_front_end.is_set():
            # Front-end write or set_value(): we don't need to track this one
            self._do_not_update_front_end.clear()
            return
        self._callback_registrar.register_change(self)  # type: ignore[arg-type]

    def add(self, subscription: Subscription) -> None:
        """Adds subscription to this key."""
        # TODO: Implement SubscriptionMode.ALL
        if subscription.id in self._subscriptions:
            return  # Duplicate
        self._subscriptions[subscription.id] = subscription

    def remove(self, subscription_id: UUID4) -> None:
        if subscription_id in self._subscriptions:
            self._subscriptions.pop(subscription_id)

    def _batch_start(self, kv: KeyValueStore | None = None) -> KeyValueStore:
        # Assume this is initiated by set_value() -> we don't want to trigger a
        # front-end update
        self._do_not_update_front_end.set()
        return super()._batch_start(kv)

    @property
    def subscription_ids(self) -> Sequence[UUID4]:
        return list(self._subscriptions.keys())


class CallbackRegistrar:
    """
    Responsible for tracking which keys have new value and communicating that to the
    registry manager.

    Particularly, the registry manager should wait for the ``data`` event to be set,
    then call ``pop()`` to receive a full dictionary of all keys that have changed since
    the last ``pop()``. This object should also be handed to all ``KeyInfo`` objects so
    that their callbacks can register that their value changed via
    ``register_change()``.
    """

    _lock: RLock
    _dict: dict[str, dict[str, KeyInfo[RegistryValueTypeUnion]]]
    data: Event
    """An event signalling that ``pop()`` with yield a non-empty dictionary."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._dict = {}
        self.data = Event()

    def register_change(self, key_info: KeyInfo[RegistryValueTypeUnion]) -> None:
        """
        Register that there is new data at ``KeyInfo``.

        This method is thread-safe.
        """
        with self._lock:
            self.data.set()
            if group := self._dict.get(key_info.group):
                current = group.setdefault(key_info.key, key_info)
                if current is not key_info:
                    raise RuntimeError(
                        f'Multiple KeyInfo objects at group, key: {key_info.group}, {key_info.key}'
                    )
                return
            self._dict.setdefault(key_info.group, {})[key_info.key] = key_info

    def pop(self) -> dict[str, dict[str, KeyInfo[RegistryValueTypeUnion]]]:
        """
        Pops a map of all group-keys that changed since last pop.

        This method is thread-safe.
        """
        with self._lock:
            out = self._dict
            self._dict = {}
            self.data.clear()
        return out


@dataclass
class RegistryManager:
    """
    Manages registry subscriptions, callbacks, and update aggregation.

    Handles WebSocket subscriptions to registry keys, processes registry callbacks,
    and aggregates updates for efficient transmission to clients.
    """

    mediator: Mediator
    subscriptions_map: dict[UUID4, Subscription]
    key_info_map: dict[tuple[str, str], KeyInfo[RegistryValueTypeUnion]]
    _seq_id: LockedSequenceGenerator
    _callback_registrar: CallbackRegistrar

    def __init__(self, mediator: Mediator) -> None:
        self.mediator = mediator
        self._seq_id = LockedSequenceGenerator()
        self.subscriptions_map = {}
        self.key_info_map = {}
        self._callback_registrar = CallbackRegistrar()

    def shutdown(self) -> None:
        pass  # Might be useful later

    def subscribe(self, sub: Subscription) -> None:
        """Subscribe to a registry key."""
        self.subscriptions_map[sub.id] = sub
        group_key = (sub.group, sub.key)
        if key_info := self.key_info_map.get(group_key):
            key_info.add(sub)
            return
        new_key_info: KeyInfo[RegistryValueTypeUnion] = KeyInfo(
            self.mediator.registry,
            sub.group,
            sub.key,
            self._callback_registrar,
        )
        self.key_info_map[group_key] = new_key_info
        new_key_info.add(sub)

    def unsubscribe(self, sub: Subscription) -> None:
        """Unsubscribe from a registry key."""
        if sub.id not in self.subscriptions_map:
            return
        del self.subscriptions_map[sub.id]
        group_key = (sub.group, sub.key)
        if key_info := self.key_info_map.get(group_key):
            key_info.remove(sub.id)
            if not key_info.subscription_ids:
                del self.key_info_map[group_key]

    def snapshot(self) -> Snapshot:
        out = Snapshot(data={})
        for (group, key), key_info in self.key_info_map.items():
            value = key_info.value
            if value is None:
                continue
            out.data.setdefault(group, {})[key] = value
        return out

    def write(self, request: Write) -> None:
        """Write a set of values to the registry."""
        print(f'Writing {request.sequence_id}: {request.data}')
        for group, key_val_map in request.data.items():
            kv = self.mediator.registry.batch_start(group)
            for key, value in key_val_map.items():
                group_key = (group, key)
                if key_info := self.key_info_map.get(group_key):
                    key_info.set_value(value, kv)
            kv.batch_end()

    def pop(self, timeout: float | None = None) -> ChunkUpdate | None:
        """
        Pop all pending updates from the callback queue.

        Returns a ChunkUpdate containing both ordered updates (ALL mode)
        and unordered updates (LAST mode).
        """
        self._callback_registrar.data.wait(timeout)
        if not self._callback_registrar.data.is_set():
            return None
        out = ChunkUpdate(
            ordered_updates=[],
            unordered_updates={},
        )
        changed_keys = self._callback_registrar.pop()
        for group, key_map in changed_keys.items():
            out_group = out.unordered_updates.setdefault(group, {})
            for key, key_info in key_map.items():
                value = key_info.value
                if value is None:
                    continue
                    # TODO: handle when key is deleted (key_info.value == None)
                out_group[key] = KeyUpdate(
                    val=value,
                    subscription_ids=[str(id) for id in key_info.subscription_ids],
                    sequence_id=self._seq_id.next,
                )
        return out
