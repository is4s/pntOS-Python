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
    PreprocessorPlugin,
    RegistryPlugin,
    StateModelingPlugin,
    TransportPlugin,
    UiPlugin,
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
