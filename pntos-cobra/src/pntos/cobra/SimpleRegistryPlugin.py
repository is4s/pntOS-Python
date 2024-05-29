from typing import Any, Callable, Dict, List, Optional

from pntos.api import (
    KeyValueStore,
    KeyValueStoreDataFormat,
    Mediator,
    Message,
    NDArray,
    Registry,
    RegistryPlugin,
    RegistryValueTypes,
    float64,
)


class SimpleRegistryPlugin(RegistryPlugin):
    def __init__(
        self,
        identifier: str,
        config: Dict[str, Dict[str, Any]] | None,
    ):
        self.identifier = identifier

    def init_plugin(
        self, plugin_resources_location: Optional[str], mediator: Optional[Mediator]
    ) -> None:
        pass

    def shutdown_plugin(self) -> None:
        pass

    identifier: str

    def new_registry(self, initial_config: str | None) -> Registry:
        return SimpleRegistry()


class SimpleRegistry(Registry):
    groups: Dict[str, KeyValueStore] = {}
    """Maps group names to objects storing all the key/values in that group.
    """

    def batch_start(self, group: str) -> KeyValueStore:
        if group not in self.groups:
            self.groups[group] = SimpleKeyValueStore()
        return self.groups[group]

    def get_group_array(self) -> List[str]:
        return list(self.groups.keys())

    def has_group(self, group: str) -> bool:
        return group in self.groups

    def request_notify_new_group(self, callback: Callable[[str], None]) -> bool:
        return False


class SimpleKeyValueStore(KeyValueStore):
    store: dict[
        str, str | List[str] | int | bool | float | NDArray[float64] | Message
    ] = {}
    data_format = KeyValueStoreDataFormat.UNSPECIFIED

    def get_key_array(self) -> List[str]:
        return list(self.store.keys())

    def has_key(self, key: str) -> bool:
        return key in self.store

    def get_value(
        self, key: str, type: type[RegistryValueTypes]
    ) -> RegistryValueTypes | None:
        out = self.store[key]
        if isinstance(out, type):
            return out
        else:
            return None

    def get_raw(self, key: str | None) -> bytes | None:
        return None

    def set_value(self, key: str, value: RegistryValueTypes) -> None:
        self.store[key] = value

    def set_raw(self, key: str | None, bytes: bytes) -> None:
        pass

    def remove_key(self, key: str) -> bool:
        if key in self.store:
            del self.store[key]
            return True
        return False

    def batch_end(self) -> None:
        pass

    def batch_restart(self) -> None:
        pass

    def request_notify(
        self, key: str | None, callback: Callable[[str, List[str], KeyValueStore], None]
    ) -> bool:
        return False

    def remove_notify(
        self, key: str | None, callback: Callable[[str, List[str], KeyValueStore], None]
    ) -> bool:
        return False

    def set_permanent(self, permanent: bool) -> bool:
        return False
