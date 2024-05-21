from typing import Protocol

from .common import CommonPlugin


class UiPlugin(CommonPlugin, Protocol):
    def requires_main_thread(self) -> bool:
        pass

    def run_main_thread(self) -> None:
        pass
