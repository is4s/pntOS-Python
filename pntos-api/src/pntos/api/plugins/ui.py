"""Python API of pntOS."""

from typing import Protocol

from .common import CommonPlugin


class UiPlugin(CommonPlugin, Protocol):
    """
    A plugin for a UI that is integrated directly into pntOS.

    While it is always possible to write a GUI that listens to pntOS outputs and
    interacts with it externally, this plugin allows users to write a GUI that has
    direct access to pntOS via the plugin API. This allows for low latency and high
    performance GUI/UIs to be generated. Note that this plugin is designed for
    developer/research style UIs and not production environments. A user display in a
    production environment is better modeled as a `PlatformIntegrationPlugin`, as that
    is designed to represent requests from the system and not simply status updates.
    Note that this plugin explicitly has no fixed function pointers in it, and instead
    receives data from the system by interacting with the mediator passed to it during
    initialization.
    """

    def requires_main_thread(self) -> bool:
        """
        Check if this plugin needs to run on the main thread.

        Some systems require GUI applications to run on the main thread. This method can be used to
        query whether or not this plugin must be run on the main thread. If this method returns
        True, then run_main_thread() must be called from the main thread in order to start this
        plugin.
        """
        pass

    def run_main_thread(self) -> None:
        """
        Start plugin on the main thread.

        This method should only be called if requires_main_thread() returns True. This method should
        only be called from the main thread.
        """
        pass
