from typing import Optional, Protocol

from .common import CommonPlugin, Registry


class RegistryPlugin(CommonPlugin, Protocol):
    def new_registry(self, initial_config: Optional[str]) -> Registry:
        pass
