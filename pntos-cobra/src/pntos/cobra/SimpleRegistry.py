from typing import Callable, List

from pntos.api.plugins.common import KeyValueStore, Registry

from .kv import PyKv


class SimpleRegistry(Registry):
    kv: PyKv

    def batch_start(self, group: str) -> KeyValueStore:
        self.kv.locked = group
        return self.kv

    def get_group_array(self) -> List[str]:
        return dir(self.store)

    def has_group(self, group: str) -> bool:
        return self.store.get(group) != None

    def request_notify_new_group(self, callback: Callable[[str], None]) -> bool:
        return super().request_notify_new_group(callback)
