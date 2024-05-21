from typing import List, Optional, Protocol

from .common import CommonPlugin


class Controller(CommonPlugin, Protocol):
    def take_control(
        self,
        plugins: List[CommonPlugin],
        plugin_resources_locations: List[Optional[str]],
        initial_config: Optional[str],
    ) -> None:
        pass
