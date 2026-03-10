import sys

from pntos.api import (
    CommonPlugin,
    ControllerPlugin,
    LoggingLevel,
    LoggingPlugin,
    Mediator,
    RegistryPlugin,
    TransportPlugin,
    UiPlugin,
)
from pntos.cobra.config import BuscatConfig, config_from_registry
from pntos.cobra.utils import (
    SortedPlugins,
    find_base_plugin_type,
    print_message,
    sort_plugins_dataclass,
    validate_plugins,
)

from .BuscatMediator import BuscatMediator


class BuscatControllerPlugin(ControllerPlugin):
    """
    This is a simple single-threaded Buscat controller plugin.

    The purpose of this plugin is to route one or more data streams from
    :class:`TransportPlugins <pntos.api.TransportPlugin>` back out through one or more
    :class:`TransportPlugins <pntos.api.TransportPlugin>`, as specified in the supplied
    :attr:`BuscatConfig.output_transports <pntos.cobra.config.BuscatConfig.output_transports>`.
    This has the effect of combining multiple data streams and converting all input to the formats
    supported by the output :class:`TransportPlugins <pntos.api.TransportPlugin>`. Note that this
    controller does not do any buffering or sorting of the input data before publishing. It (or more
    specifically, the :class:`BuscatMediator <pntos.cobra.internal.BuscatMediator>`) also does not
    explicitly pass input data to plugins other than :class:`TransportPlugins <pntos.api.TransportPlugin>`,
    and thus will not support sensor fusion without some modification.

    Here are the plugins and corresponding expected number of instances this controller
    looks for:

    - LoggingPlugin - 1
    - RegistryPlugin - 1
    - TransportPlugin - at least 1
    - UiPlugin - any, but only 1 can require the main thread

    It checks for the expected plugins, sets up mediators, and then passes the mediators
    to each plugin in :meth:`pntos.api.CommonPlugin.init_plugin`, then passes off to the
    :meth:`_main` function.

    Inside the main function, calls :meth:`pntos.api.TransportPlugin.start_listening` on
    all transport plugins, checks if the UI needs to update (and passes it the thread if
    so), then waits for a ctrl+c to exit pntOS.
    """

    _plugin_resources_location: str | None

    def __init__(self, identifier: str) -> None:
        """
        Cobra Buscat Controller

        Args:
            identifier (str): The plugin identifier passed to the
                :attr:`pntos.api.CommonPlugin.identifier` field.
        """
        self.identifier = identifier
        self._plugins: list[CommonPlugin] = []
        self._logging_plugin: LoggingPlugin | None = None
        self._transport_plugins: list[TransportPlugin] = []
        self._ui_plugins: list[UiPlugin] = []
        self._registry_plugin: RegistryPlugin | None = None

    def init_plugin(
        self,
        plugin_resources_location: str | None = None,
        mediator: Mediator | None = None,
    ) -> None:
        if mediator is not None:
            self._log(
                LoggingLevel.ERROR, 'Controller plugin should not be passed a mediator.'
            )
        self._plugin_resources_location = plugin_resources_location

    def shutdown_plugin(self) -> None:
        self._log(LoggingLevel.INFO, 'Shutting down all plugins...')

        for plugin in self._plugins:
            # Don't shut down registry and logging plugins before the others
            if not isinstance(plugin, (RegistryPlugin, LoggingPlugin)):
                plugin.shutdown_plugin()

        # Now close the registry and logging plugin last
        if self._registry_plugin is not None:
            self._registry_plugin.shutdown_plugin()
        if self._logging_plugin is not None:
            self._logging_plugin.shutdown_plugin()

    identifier: str

    def take_control(
        self,
        plugins: list[CommonPlugin],
        plugin_resources_locations: list[str | None] | None = None,
        initial_config: str | None = None,
    ) -> None:
        self._plugins = plugins

        # Make sure there are enough plugins to run
        (
            self._registry_plugin,
            self._logging_plugin,
            self._transport_plugins,
            self._ui_plugins,
        ) = self._sort_and_validate_plugins(plugins)

        # Hand mediators controller plugin so that mediators can call "shutdown_plugin"
        # on error.
        BuscatMediator._controller_plugin = self

        # Create separate mediators to pass to each plugin
        mediators = [
            BuscatMediator(p.identifier, find_base_plugin_type(p))
            for p in self._plugins
        ]

        # We need to make sure we got a valid plugin_resources_locations
        if plugin_resources_locations is not None and len(
            plugin_resources_locations
        ) != len(self._plugins):
            self._log(
                LoggingLevel.ERROR,
                'Length of plugin_resources_location '
                + f'({len(plugin_resources_locations)}) does not equal the '
                + f'number of plugins ({len(self._plugins)}). Passing '
                + 'None to all plugins instead.',
            )
            plugin_resources_locations = None

        # Initialize registry plugin first thing
        reg_i = self._plugins.index(self._registry_plugin)
        self._registry_plugin.init_plugin(
            None
            if plugin_resources_locations is None
            else plugin_resources_locations[reg_i],
            mediators[reg_i],
        )

        # Give mediators a registry
        BuscatMediator.registry = self._registry_plugin.new_registry(initial_config)

        # Initialize logger second
        assert self._logging_plugin is not None
        log_i = self._plugins.index(self._logging_plugin)
        self._logging_plugin.init_plugin(
            None
            if plugin_resources_locations is None
            else plugin_resources_locations[log_i],
            mediators[log_i],
        )

        # Give mediators a logging plugin
        BuscatMediator._logging_plugin = self._logging_plugin

        # call init_plugin() on all the other plugins
        for i, plugin in enumerate(self._plugins):
            if i in (reg_i, log_i):
                continue
            plugin.init_plugin(
                plugin_resources_location=None
                if plugin_resources_locations is None
                else plugin_resources_locations[i],
                mediator=mediators[i],
            )

        # Give the mediators other needed plugins
        BuscatMediator._transport_plugins = self._transport_plugins

        # Set the mediators' output transport
        temp_mediator = BuscatMediator(self.identifier, ControllerPlugin)
        config = config_from_registry(BuscatConfig, temp_mediator, 'buscat')
        if config is None:
            self._log(
                LoggingLevel.ERROR,
                'Could not extract BuscatConfig from group "buscat". Cannot initialize Buscat controller plugin.',
            )
            return
        BuscatMediator._output_transports = config.output_transports

        # Pass off to main control loop
        self._main()

    def _sort_and_validate_plugins(
        self, plugins: list[CommonPlugin]
    ) -> tuple[RegistryPlugin, LoggingPlugin, list[TransportPlugin], list[UiPlugin]]:
        """
        Utility function to ensure ``plugins`` contains enough plugins to run pntOS
        Cobra. Then assigns and dispatches them to the relevant fields on the
        controller. Raises a :class:`RuntimeError` if plugins are
        not as expected.
        """
        sorted_plugins: SortedPlugins = sort_plugins_dataclass(plugins)

        if not validate_plugins(
            sorted_plugins,
            self._log,
            registry_plugins=(1, 1),
            logging_plugins=(1, 1),
            transport_plugins=(1, 1000),
        ):
            raise RuntimeError('Not enough plugins to run pntOS.')

        return (
            sorted_plugins.registry_plugins[0],
            sorted_plugins.logging_plugins[0],
            sorted_plugins.transport_plugins,
            sorted_plugins.ui_plugins,
        )

    def _log(self, level: LoggingLevel, message: str) -> None:
        """
        Utility logging method for controller.

        NOTE: This is only intended for log messages originating from the
        controller.
        """
        if self._logging_plugin is None:
            print_message(level, ControllerPlugin.__name__, message)
        else:
            self._logging_plugin.log(ControllerPlugin, self.identifier, level, message)

    def _main(self) -> None:
        """
        The main control of pntOS Cobra.
        """
        for transport in self._transport_plugins:
            transport.start_listening()

        # Run main thread from UI plugin, if needed
        ui_needing_main_thrd = [p for p in self._ui_plugins if p.requires_main_thread()]
        if len(ui_needing_main_thrd) > 1:
            self._log(
                LoggingLevel.ERROR,
                f'Only 1 UiPlugin can require the main thread, but found {len(ui_needing_main_thrd)} needing the main thread. Cannot run pntOS.',
            )
        if ui_needing_main_thrd:
            ui_needing_main_thrd[0].run_main_thread()

        else:  # wait for ctrl + c to exit
            self._log(
                LoggingLevel.INFO,
                'Press Ctrl + C at any time to shut down pntOS...',
            )
            try:
                BuscatMediator._logging_error_event.wait()
            except KeyboardInterrupt:
                self._log(LoggingLevel.INFO, 'Keyboard Interrupt Detected.')

        self.shutdown_plugin()
        if BuscatMediator._logging_error_event.is_set():
            sys.exit(1)
