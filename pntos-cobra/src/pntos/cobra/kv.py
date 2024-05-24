from typing import Any, Callable, Dict, List

from pntos.api.plugins.common import KeyValueStore, ValueType


class PyKv(KeyValueStore):
    store: dict[str, ValueType] = {}
    locked: str | None = None

    def get_key_array(self) -> List[str]:
        return dir(self.store)

    def has_key(self, key: str) -> bool:
        return self.store.get(key) is not None
    
    def get_value(self, key: str, type: type[ValueType]) -> ValueType:
        return self.store.get(key)
    
    def get_raw(self, key: str | None) -> bytes | None:
        return None

    def set_value(self, key: str, value: ValueType) -> None:
        self.store[key] = value

    def set_raw(self, key: str | None, bytes: bytes) -> None:
        pass

    def remove_key(self, key: str) -> bool:
        return self.store.pop(key) is not None

    def batch_end(self) -> None:
        self.locked = None

    def batch_restart(self) -> None:
        pass

    def request_notify(self, key: str | None, callback: Callable[[str, List[str], KeyValueStore], None]) -> bool:
        return False

    def remove_notify(self, key: str | None, callback: Callable[[str, List[str], KeyValueStore], None]) -> bool:
        return False

    def set_permanent(self, permanent: bool) -> bool:
        return False
