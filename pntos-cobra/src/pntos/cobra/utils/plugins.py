import re
from dataclasses import dataclass, field
from typing import TypeVar

from pntos.api import (
    CommonPlugin,
    ControllerPlugin,
    FusionPlugin,
    FusionStrategyPlugin,
    InertialPlugin,
    InitializationPlugin,
    LoggingPlugin,
    OrchestrationPlugin,
    PlatformIntegrationPlugin,
    PluginType,
    PreprocessorPlugin,
    RegistryPlugin,
    StateModelingPlugin,
    TransportPlugin,
    UiPlugin,
    UtilityPlugin,
)


@dataclass
class SortedPlugins:
    controller_plugins: list[ControllerPlugin] = field(default_factory=list)
    fusion_plugins: list[FusionPlugin] = field(default_factory=list)
    fusion_strategy_plugins: list[FusionStrategyPlugin] = field(default_factory=list)
    inertial_plugins: list[InertialPlugin] = field(default_factory=list)
    initialization_plugins: list[InitializationPlugin] = field(default_factory=list)
    logging_plugins: list[LoggingPlugin] = field(default_factory=list)
    orchestration_plugins: list[OrchestrationPlugin] = field(default_factory=list)
    platform_integration_plugins: list[PlatformIntegrationPlugin] = field(
        default_factory=list
    )
    preprocessor_plugins: list[PreprocessorPlugin] = field(default_factory=list)
    registry_plugins: list[RegistryPlugin] = field(default_factory=list)
    state_modeling_plugins: list[StateModelingPlugin] = field(default_factory=list)
    transport_plugins: list[TransportPlugin] = field(default_factory=list)
    ui_plugins: list[UiPlugin] = field(default_factory=list)


def sort_plugins_dataclass(plugins: list[CommonPlugin]) -> SortedPlugins:
    sorted_data = SortedPlugins()

    for plugin in plugins:
        if isinstance(plugin, ControllerPlugin):
            sorted_data.controller_plugins.append(plugin)
        elif isinstance(plugin, FusionPlugin):
            sorted_data.fusion_plugins.append(plugin)
        elif isinstance(plugin, FusionStrategyPlugin):
            sorted_data.fusion_strategy_plugins.append(plugin)
        elif isinstance(plugin, InertialPlugin):
            sorted_data.inertial_plugins.append(plugin)
        elif isinstance(plugin, InitializationPlugin):
            sorted_data.initialization_plugins.append(plugin)
        elif isinstance(plugin, LoggingPlugin):
            sorted_data.logging_plugins.append(plugin)
        elif isinstance(plugin, OrchestrationPlugin):
            sorted_data.orchestration_plugins.append(plugin)
        elif isinstance(plugin, PlatformIntegrationPlugin):
            sorted_data.platform_integration_plugins.append(plugin)
        elif isinstance(plugin, PreprocessorPlugin):
            sorted_data.preprocessor_plugins.append(plugin)
        elif isinstance(plugin, RegistryPlugin):
            sorted_data.registry_plugins.append(plugin)
        elif isinstance(plugin, StateModelingPlugin):
            sorted_data.state_modeling_plugins.append(plugin)
        elif isinstance(plugin, TransportPlugin):
            sorted_data.transport_plugins.append(plugin)
        elif isinstance(plugin, UiPlugin):
            sorted_data.ui_plugins.append(plugin)

    return sorted_data


def find_base_plugin_type(plugin: CommonPlugin) -> PluginType:
    if isinstance(plugin, ControllerPlugin):
        return ControllerPlugin
    elif isinstance(plugin, FusionPlugin):
        return FusionPlugin
    elif isinstance(plugin, FusionStrategyPlugin):
        return FusionStrategyPlugin
    elif isinstance(plugin, InertialPlugin):
        return InertialPlugin
    elif isinstance(plugin, InitializationPlugin):
        return InitializationPlugin
    elif isinstance(plugin, LoggingPlugin):
        return LoggingPlugin
    elif isinstance(plugin, OrchestrationPlugin):
        return OrchestrationPlugin
    elif isinstance(plugin, PlatformIntegrationPlugin):
        return PlatformIntegrationPlugin
    elif isinstance(plugin, PreprocessorPlugin):
        return PreprocessorPlugin
    elif isinstance(plugin, RegistryPlugin):
        return RegistryPlugin
    elif isinstance(plugin, StateModelingPlugin):
        return StateModelingPlugin
    elif isinstance(plugin, TransportPlugin):
        return TransportPlugin
    elif isinstance(plugin, UiPlugin):
        return UiPlugin
    else:
        return UtilityPlugin


def camel_to_snake(name: str) -> str:
    """
    Utility function to go from class name to SortedPlugins data field name.

    Example:
        This is particularly useful for iterating through a list of plugin types when
        paired with getattr and setattr on a controller or orchestration plugin::

            def _sort_and_validate_plugins(self, plugins: list[CommonPlugin]) -> None:
                sorted_plugins: SortedPlugins = sort_plugins_dataclass(plugins)
                expected_plugin_types = [LoggingPlugin, OrchestrationPlugin, ...]
                for t in expected_plugin_types:
                    t_snake = camel_to_snake(t.__name__)
                    plugins_of_type_t = getattr(sorted_plugins, t_snake + 's')
                    n_plugins_of_type_t = len(plugins_of_type_t)
                    if n_plugins_of_type_t != 1:
                        self._log(
                            LoggingLevel.ERROR,
                            f'Expected one {t.__name__}, but received {n_plugins_of_type_t}.',
                        )
                        return
                    setattr(self, t_snake, plugins_of_type_t[0])

    """
    return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()


class PluginDiscoveryError(Exception):
    def __init__(self, *args) -> None:  # type: ignore[no-untyped-def]
        super().__init__(*args)
