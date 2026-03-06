from pntos.api import (
    CommonPlugin,
    ControllerPlugin,
    Mediator,
    OrchestrationPlugin,
    TransportPlugin,
)
from pntos.cobra.internal import DummyMediator, DummyMessageStreamConfig


class DummyControllerPlugin(ControllerPlugin):
    """A ControllerPlugin with minimal capability. Not for use in production code.

    This class performs just the activities required to get a bare-bones
    operable system: basic plugin initialization and shutdown calls, as well as the special
    initialization requirements of :class:`~pntos.api.OrchestrationPlugin` s and
    :class:`~pntos.api.TransportPlugin` s. No other configuration is performed.

    This class uses the similarly limited-in-capability :class:`~pntos.cobra.internal.DummyMediator`
    to enable callbacks between other plugins.
    """

    _mediator: DummyMediator
    """:class:`~pntos.cobra.internal.DummyMediator` instance that holds refs to other plugins."""

    def __init__(self, identifier: str) -> None:
        self.identifier = identifier
        self._mediator = DummyMediator()

    def init_plugin(
        self,
        plugin_resources_location: str | None = None,
        mediator: Mediator | None = None,
    ) -> None:
        """
        Does nothing in this implementation.

        Args:
            plugin_resources_location (str | None): Unused.
            mediator (Mediator | None): Unused.
        """
        return

    def shutdown_plugin(self) -> None:
        """
        Shuts down this plugin and by extension all others.
        """
        for plugin in self._mediator.plugins:
            plugin.shutdown_plugin()

    def take_control(
        self,
        plugins: list[CommonPlugin],
        plugin_resources_locations: list[str | None] | None = None,
        initial_config: str | None = None,
    ) -> None:
        """
        Takes over control initializing all basic plugins, :class:`~pntos.api.OrchestrationPlugin` s,
        and starts all :class:`~pntos.api.TransportPlugin` listener threads.

        Args:
            plugins (list[CommonPlugin]): All plugins to include in the operable system.
            plugin_resources_locations (list[str | None] | None): Unused.
            initial_config (str | None): Unused.
        """
        self._mediator.plugins = plugins
        for plugin in self._mediator.plugins:
            plugin.init_plugin(mediator=DummyMediator(plugins))

        for plugin in self._mediator.plugins:
            if isinstance(plugin, OrchestrationPlugin):
                plugin.init_orchestration_plugin(
                    plugins=self._mediator.plugins,
                    stream_config=DummyMessageStreamConfig(),
                )

        for plugin in self._mediator.plugins:
            if isinstance(plugin, TransportPlugin):
                plugin.start_listening()
