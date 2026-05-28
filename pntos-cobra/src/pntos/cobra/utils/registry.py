import builtins
from collections.abc import Sequence
from threading import RLock
from typing import Generic, TypeVar, overload

from pntos.api import (
    KeyValueStore,
    Registry,
    RegistryValueTypeUnion,
)

ValueType = TypeVar('ValueType', bound=RegistryValueTypeUnion)
"""
A ``TypeVar`` bound to ``pntos.api.RegistryValueTypeUnion``. This allows fields of
type ``ValueType`` to be of type ``pntos.api.RegistryValueTypeUnion``, or any subset of
that union.
"""


class GroupsView:
    def __init__(self, registry: Registry) -> None:
        self._groups: list[str] | None = registry.group_array
        registry.request_notify_new_group(self._callback)

    def _callback(self, new_group: str) -> None:
        if self._groups is None:
            self._groups = []
        self._groups.append(new_group)

    @property
    def groups(self) -> Sequence[str] | None:
        return self._groups


class ValueView(Generic[ValueType]):
    @overload
    def __init__(
        self: 'ValueView[RegistryValueTypeUnion]',
        registry: Registry,
        group: str,
        key: str,
        type: None = None,
    ) -> None: ...

    @overload
    def __init__(
        self,
        registry: Registry,
        group: str,
        key: str,
        type: type[ValueType],
    ) -> None: ...

    def __init__(
        self,
        registry: Registry,
        group: str,
        key: str,
        type: type[ValueType] | None = None,
    ) -> None:
        """
        Utility object to expose an automatically-updating registry value.

        On instantiation, this object registers a callback for the value at
        ``group``/``key`` in the registry. This callback simply updates the value
        internally, which allows the ``self.value`` property to always be a synced
        "view" of the value at ``group``/``key``.

        When this object is deleted, it will remove the callback from the registry.

        Args:
            registry (Registry): Registry to view
            group (str): The group in the registry
            key (str): The key in the registry
            type (type[ValueType] | None): The desired/expected type of the
                value at ``group``/``key`` in the registry. If ``None``, the view will
                use union mode and return values as ``RegistryValueTypeUnion``. If a
                specific type is provided, the view will use specific type mode and
                return values as that type. Default: None
        """
        self._group: str = group
        self._key: str = key
        self._type: builtins.type[ValueType] | None = type
        self._value: ValueType | None = None
        self._value_lock: RLock = RLock()
        self._registry: Registry = registry

        kv = self._registry.batch_start(self._group)
        kv.request_notify(self._key, self._callback)
        if self._key in kv:
            if self._type is None:
                self._value = kv[self._key]  # type: ignore[assignment]
            else:
                self._value = kv.get_value(self._key, self._type)  # type: ignore[type-var]
        kv.batch_end()

    def _callback(self, group: str, keys: list[str], kv: KeyValueStore) -> None:
        with self._value_lock:
            if self._type is not None:
                self._value = kv.get_value(self._key, self._type)  # type: ignore[type-var]
                return
            self._value = kv[self._key]  # type: ignore[assignment]

    @property
    def group(self) -> str:
        """``self.value`` is the view of ``self.key`` in this group."""
        return self._group

    @property
    def key(self) -> str:
        """``self.value`` is the view of this key in ``self.group``."""
        return self._key

    @property
    def type(self) -> type[ValueType] | None:
        """Expected/desired type at ``self.group``/``self.key``."""
        return self._type

    @property
    def value(self) -> ValueType | None:
        """The most recent value at ``self.group``/``self.key`` in the registry."""
        return self._value

    def __del__(self) -> None:
        with self._registry.batch_start(self._group) as kv:
            kv.remove_notify(self._key, self._callback)


class BufferedValueView(ValueView[ValueType], Generic[ValueType]):
    """
    A ``ValueView`` that buffers all values at a given group and key in the registry.
    """

    @overload
    def __init__(
        self: 'ValueView[RegistryValueTypeUnion]',
        registry: Registry,
        group: str,
        key: str,
        type: None = None,
    ) -> None: ...

    @overload
    def __init__(
        self,
        registry: Registry,
        group: str,
        key: str,
        type: type[ValueType],
    ) -> None: ...

    def __init__(
        self,
        registry: Registry,
        group: str,
        key: str,
        type: type[ValueType] | None = None,
    ) -> None:
        self._buffer: list[ValueType | None] = []
        self._buffer_lock: RLock = RLock()
        super().__init__(registry, group, key, type)  # type: ignore[arg-type]

    def _callback(self, group: str, keys: list[str], kv: KeyValueStore) -> None:
        with self._value_lock:
            super()._callback(group, keys, kv)
            with self._buffer_lock:
                self._buffer.append(self._value)

    @property
    def buffer(self) -> Sequence[ValueType | None]:
        """Returns a deepcopy of the current buffer."""
        return self._buffer

    def pop(self) -> Sequence[ValueType | None]:
        """Pops all values from this group and key since last ``pop()``."""
        with self._buffer_lock:
            out = self._buffer
            self._buffer = []
        return out


class MutableValueView(ValueView[ValueType], Generic[ValueType]):
    """
    A write-enabled ``ValueView``.

    This simply adds a setter. If no key value store is provided in the setter, a whole
    batch operation will be performed (inefficient for high-datarate values). If a
    ``KeyValueStore`` is provided, it is assumed that the ``KeyValueStore`` is already
    live (``batch_start()`` has been called), and the value is set directly.
    """

    _started_batch: bool

    @overload
    def __init__(
        self: 'ValueView[RegistryValueTypeUnion]',
        registry: Registry,
        group: str,
        key: str,
        type: None = None,
    ) -> None: ...

    @overload
    def __init__(
        self,
        registry: Registry,
        group: str,
        key: str,
        type: type[ValueType],
    ) -> None: ...

    def __init__(
        self,
        registry: Registry,
        group: str,
        key: str,
        type: type[ValueType] | None = None,
    ) -> None:
        super().__init__(registry, group, key, type)  # type: ignore[arg-type]
        self._started_batch = False

    def _batch_start(self, kv: KeyValueStore | None = None) -> KeyValueStore:
        """
        Utility method to handle batch start.

        Allows sub-classes to easily intercept this step.
        """
        if kv is not None:
            return kv
        self._started_batch = True
        return self._registry.batch_start(self._group)

    def _batch_end(self, kv: KeyValueStore) -> None:
        """
        Utility method to handle batch end.

        Allows sub-classes to easily intercept this step.
        """
        if self._started_batch:
            kv.batch_end()
            self._started_batch = False

    def set_value(self, new_value: ValueType, kv: KeyValueStore | None = None) -> None:
        """
        Sets ``new_value`` in the registry.

        Args:
            new_value (RegistryValueType): New value to write in the registry.
            kv (KeyValueStore | None): If provided, writes to this store. Otherwise,
                performs a batch operation. Default: None

        """
        kv = self._batch_start(kv)
        kv[self._key] = new_value
        self._batch_end(kv)


class BufferedMutableValueView(
    MutableValueView[ValueType],
    BufferedValueView[ValueType],
    Generic[ValueType],
):
    """
    A write-enabled ``ValueView`` with buffering for a key in the registry.

    This class inherits both the buffered behavior from ``BufferedValueView`` (e.g.
    ``buffer`` property and ``pop()``) as well as ``set_value()`` from
    ``MutableValueView``.

    Note that the buffer will catch all ``set_value()`` calls.
    """
