from typing import Protocol

from .common import CommonPlugin


class UiPlugin(CommonPlugin, Protocol):
    """
    A plugin for a UI that is integrated directly into pntOS. While it is
    always possible to write a GUI that listens to pntOS outputs and interacts
    with it externally, this plugin allows users to write a GUI that has direct
    access to pntOS via the plugin API. This allows for low latency and high
    performance GUI/UIs to be generated. Note that this plugin is designed for
    developer/research style UIs and not production environments. A user
    display in a production environment is better modeled as a
    `PlatformIntegrationPlugin`, as that is designed to represent requests from
    the system and not simply status updates. Note that this plugin explicitly
    has no fixed function pointers in it, and instead receives data from the
    system by interacting with the mediator passed to it during initialization.
    """

    def requires_main_thread(self) -> bool:
        pass

    def run_main_thread(self) -> None:
        pass
