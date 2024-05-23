from typing import Callable, List
from pntos.api.plugins.common import KeyValueStore, Registry, ValueType


class PyKv(KeyValueStore):
    store = {}
    locked = []
    
    def get_key_array(self) -> List[str]:
        return dir(self.store)
    
    def has_key(self, key: str) -> bool:
        return self.store.get(key) != None
    
    def get_value(self, key: str, type: type[ValueType]) -> ValueType:
        return type(self.store.get())
    
    def get_raw(self, key: str | None) -> bytes | None:
        pass

    def set_value(self, key: str, value: ValueType) -> None:
        self.store.update(key, value)

    def set_raw(self, key: str | None, bytes: bytes) -> None:
        pass

    def remove_key(self, key: str) -> bool:
        self.store.pop(key)

    def batch_end(self) -> None:
        self.locked.remove()

    def batch_restart(self) -> None:
        locked_values = self.locked
        self.locked.clear()
        self.locked = locked_values

    def request_notify(self, key: str | None, callback: Callable[[str, List[str], KeyValueStore], None]) -> bool:
        pass

    def remove_notify(self, key: str | None, callback: Callable[[str, List[str], KeyValueStore], None]) -> bool:
        pass

    def set_permanent(self, permanent: bool) -> bool:
        pass