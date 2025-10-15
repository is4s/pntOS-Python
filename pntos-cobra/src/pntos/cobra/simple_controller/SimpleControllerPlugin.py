from threading import Event
from typing import ClassVar

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
from pntos.cobra.utils import (
    SortedPlugins,
    find_base_plugin_type,
    sort_plugins_dataclass,
    validate_plugins,
)

from .SimpleMediator import SimpleMediator
from .SimpleMessageStreamConfig import SimpleMessageStreamConfig


class SimpleControllerPlugin(ControllerPlugin):
    """
    This is a simple single-threaded controller plugin.

    Here are the plugins and corresponding expected number of instances this controller
    looks for:

    - FusionPlugin - at least 1
    - FusionStrategyPlugin - at least 1
    - InertialPlugin - at least 1
    - UiPlugin - optionally 1
    - OrchestrationPlugin - only 1
    - InitializationPlugin - at least 1
    - TransportPlugin - at least 1
    - RegistryPlugin - only 1
    - LoggingPlugin - only 1

    It checks for the expected plugins, sets up mediators, and then passes the
    mediators to each plugin in :meth:`pntos.api.CommonPlugin.init_plugin`, initializes the orchestration
    plugin, then passes off to the :meth:`_main` function.

    Inside the main function, calls :meth:`pntos.api.TransportPlugin.start_listening` on all
    transport plugins, checks if the UI needs to update (and passes it the thread if so), then waits
    for a ctrl/cmd+c to exit pntOS.

    The TransportPlugins will initiate the necessary filtering through their calls to
    :meth:`pntos.api.Mediator.process_pntos_message`.
    """

    _plugin_resources_location: str | None

    def __init__(self, identifier: str) -> None:
        """
        Cobra Simple Controller

        Args:
            identifier (str): The plugin identifier passed to the
                :attr:`pntos.api.CommonPlugin.identifier` field.
        """
        self.identifier = identifier
        self._plugins: list[CommonPlugin] = []
        self._logging_plugin: LoggingPlugin | None = None
        self._transport_plugins: list[TransportPlugin] = []
        self._ui_plugin: UiPlugin | None = None
        self._registry_plugin: RegistryPlugin | None = None

        self._log_levels = {
            LoggingLevel.DEBUG: 'DEBUG: ',
            LoggingLevel.ERROR: 'ERROR: ',
            LoggingLevel.INFO: 'INFO: ',
            LoggingLevel.WARN: 'WARNING: ',
        }

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
            self._ui_plugin,
            plugins_for_orchestration,
        ) = self._sort_and_validate_plugins(plugins)

        # Hand mediators controller plugin so that mediators can call "shutdown_plugin"
        # on error.
        SimpleMediator._controller_plugin = self

        # initialize stream config and hand to mediator
        stream_config = SimpleMessageStreamConfig()
        SimpleMediator._stream_config = stream_config

        # Create separate mediators to pass to each plugin
        mediators = [
            SimpleMediator(p.identifier, find_base_plugin_type(p))
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
        SimpleMediator.registry = self._registry_plugin.new_registry(initial_config)

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
        SimpleMediator._logging_plugin = self._logging_plugin

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
        SimpleMediator._transport_plugins = self._transport_plugins
        SimpleMediator._orchestration_plugin = orchestration_plugin

        # Give the orchestration the plugins it needs
        orchestration_plugin.init_orchestration_plugin(
            plugins_for_orchestration, stream_config
        )

        # Pass off to main control loop
        self._main()

    def _sort_and_validate_plugins(
        self, plugins: list[CommonPlugin]
    ) -> tuple[
        RegistryPlugin,
        LoggingPlugin,
        list[TransportPlugin],
        OrchestrationPlugin,
        UiPlugin | None,
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

        # UI Plugin
        if len(sorted_plugins.ui_plugins) != 1:
            self._log(
                LoggingLevel.WARN,
                f'Expected one UiPlugin but received {len(sorted_plugins.ui_plugins)}.'
                + ' Running without a UI plugin.',
            )

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
            None
            if len(sorted_plugins.ui_plugins) != 1
            else sorted_plugins.ui_plugins[0],
            plugins_for_orchestration,
        )

    def _log(self, level: LoggingLevel, message: str) -> None:
        """
        Utility logging method for controller.

        NOTE: This is only intended for log messages originating from the
        controller.
        """
        if self._logging_plugin is None:
            print(self._log_levels[level] + ' [Controller] ' + message)
        else:
            self._logging_plugin.log(ControllerPlugin, self.identifier, level, message)

    def _main(self) -> None:
        """
        The main control of pntOS Cobra.
        """
        for transport in self._transport_plugins:
            transport.start_listening()

        if self._ui_plugin is not None and self._ui_plugin.requires_main_thread():
            # See if UI needs to update
            self._ui_plugin.run_main_thread()

        else:  # wait for ctrl + c to exit
            self._log(
                LoggingLevel.INFO,
                'Press Ctrl + C at any time to shut down pntOS...',
            )
            try:
                SimpleMediator._logging_error_event.wait()
            except KeyboardInterrupt:
                self._log(LoggingLevel.INFO, 'Keyboard Interrupt Detected.')
                pass

        self.shutdown_plugin()
        if SimpleMediator._logging_error_event.is_set():
            exit(1)
        else:
            exit(0)
