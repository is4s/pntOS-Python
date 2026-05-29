import sys

from pntos.api import (
    CommonPlugin,
    ControllerPlugin,
    LoggingLevel,
    LoggingPlugin,
    Mediator,
    OrchestrationPlugin,
    RegistryPlugin,
    TransportPlugin,
    UiPlugin,
)
from pntos.cobra.config import ControllerConfig, config_from_registry
from pntos.cobra.utils import (
    SortedPlugins,
    UiMediatorInterface,
    find_base_plugin_type,
    print_message,
    sort_plugins_dataclass,
    validate_plugins,
)

from .StandardMediator import StandardMediator
from .StandardMessageStreamConfig import StandardMessageStreamConfig


class StandardControllerPlugin(ControllerPlugin):
    """
    This is a simple single-threaded controller plugin.

    Here are the plugins and corresponding expected number of instances this controller
    looks for:

    - FusionPlugin - at least 1
    - FusionStrategyPlugin - at least 1
    - InertialPlugin - at least 1
    - InitializationPlugin - at least 1
    - LoggingPlugin - 1
    - OrchestrationPlugin - 1
    - RegistryPlugin - 1
    - TransportPlugin - at least 1
    - UiPlugin - any, but only 1 can require the main thread

    It checks for the expected plugins, sets up mediators, and then passes the mediators
    to each plugin in :meth:`pntos.api.CommonPlugin.init_plugin`, initializes the
    orchestration plugin, then passes off to the :meth:`_main` function.

    Inside the main function, calls :meth:`pntos.api.TransportPlugin.start_listening` on
    all transport plugins, checks if the UI needs to update (and passes it the thread if
    so), then waits for a ctrl+c to exit pntOS.

    The TransportPlugins will initiate the necessary filtering through their calls to
    :meth:`pntos.api.Mediator.process_pntos_message`.
    """

    _plugin_resources_location: str | None

    def __init__(self, identifier: str) -> None:
        """
        Cobra Standard Controller

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
            orchestration_plugin,
            self._ui_plugins,
            plugins_for_orchestration,
        ) = self._sort_and_validate_plugins(plugins)

        # Hand mediators controller plugin so that mediators can call "shutdown_plugin"
        # on error.
        StandardMediator._controller_plugin = self

        # initialize stream config and hand to mediator
        stream_config = StandardMessageStreamConfig()
        StandardMediator._stream_config = stream_config

        # Create separate mediators to pass to each plugin
        mediators = [
            StandardMediator(p.identifier, find_base_plugin_type(p))
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
        StandardMediator.registry = self._registry_plugin.new_registry(initial_config)
        StandardMediator._ui_interface = UiMediatorInterface(StandardMediator.registry)

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
        StandardMediator._logging_plugin = self._logging_plugin

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
        StandardMediator._transport_plugins = self._transport_plugins
        StandardMediator._orchestration_plugin = orchestration_plugin

        # Give the orchestration the plugins it needs
        orchestration_plugin.init_orchestration_plugin(
            plugins_for_orchestration, stream_config
        )

        # Extract controller-specific config
        temp_mediator = StandardMediator(self.identifier, ControllerPlugin)
        config = config_from_registry(
            ControllerConfig, temp_mediator, ControllerConfig.group
        )
        if config is None:
            self._log(
                LoggingLevel.ERROR,
                'Could not extract ControllerConfig from group "controller". Cannot initialize controller plugin.',
            )
            return
        StandardMediator._buffer_time_nsec = int(config.buffer_length_sec * 1e9)
        if config.publish_interval is not None:
            StandardMediator._publish_interval_ns = int(config.publish_interval * 1e9)

        # Pass off to main control loop
        self._main()

    def _sort_and_validate_plugins(
        self, plugins: list[CommonPlugin]
    ) -> tuple[
        RegistryPlugin,
        LoggingPlugin,
        list[TransportPlugin],
        OrchestrationPlugin,
        list[UiPlugin],
        list[CommonPlugin],
    ]:
        """
        Utility function to ensure ``plugins`` contains enough plugins to run pntOS
        Cobra. Then assigns and dispatches them to the relevant fields on the
        controller. Raises a :class:`RuntimeError` if plugins are
        not as expected.
        """
        sorted_plugins: SortedPlugins = sort_plugins_dataclass(plugins)
        plugins_for_orchestration: list[CommonPlugin] = []

        if not validate_plugins(
            sorted_plugins,
            self._log,
            registry_plugins=(1, 1),
            logging_plugins=(1, 1),
            orchestration_plugins=(1, 1),
            transport_plugins=(1, 1000),
            fusion_plugins=(1, 1000),
        ):
            raise RuntimeError('Not enough plugins to run pntOS.')

        # Collect plugins to pass to orchestration
        plugins_for_orchestration.extend(sorted_plugins.fusion_plugins)
        plugins_for_orchestration.extend(sorted_plugins.fusion_strategy_plugins)
        plugins_for_orchestration.extend(sorted_plugins.inertial_plugins)
        plugins_for_orchestration.extend(sorted_plugins.initialization_plugins)
        plugins_for_orchestration.extend(sorted_plugins.state_modeling_plugins)
        plugins_for_orchestration.extend(sorted_plugins.preprocessor_plugins)

        return (
            sorted_plugins.registry_plugins[0],
            sorted_plugins.logging_plugins[0],
            sorted_plugins.transport_plugins,
            sorted_plugins.orchestration_plugins[0],
            sorted_plugins.ui_plugins,
            plugins_for_orchestration,
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
                StandardMediator._logging_error_event.wait()
            except KeyboardInterrupt:
                self._log(LoggingLevel.INFO, 'Keyboard Interrupt Detected.')

        self.shutdown_plugin()
        if StandardMediator._logging_error_event.is_set():
            sys.exit(1)
