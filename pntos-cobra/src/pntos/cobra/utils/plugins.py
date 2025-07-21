import re
from dataclasses import dataclass, field
from typing import Callable

from pntos.api import (
    CommonPlugin,
    ControllerPlugin,
    FusionPlugin,
    FusionStrategyPlugin,
    InertialPlugin,
    InitializationPlugin,
    LoggingLevel,
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
    utility_plugins: list[UtilityPlugin] = field(default_factory=list)


def sort_plugins_dataclass(plugins: list[CommonPlugin]) -> SortedPlugins:
    """
    Utility function to alphabetically sort all of the plugins manually.

    plugins (list[CommonPlugin]): The list of plugins to sort.

    Returns:
        SortedPlugins
    """
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
        elif isinstance(plugin, UtilityPlugin):
            sorted_data.utility_plugins.append(plugin)
    return sorted_data


def validate_plugins(
    sorted_plugins: SortedPlugins,
    log_func: Callable[[LoggingLevel, str], None],
    **kwargs: tuple[int, int],
) -> bool:
    """
    A utility function that (for each type) verifies the number of expected plugins against the plugin counts in ``sorted_plugins``.
    Accepted keyword arguments are in the formatting `[num|min]_[plugin_type]` (e.g. `num_fusion_plugins`, `min_fusion_plugins`). The
    `num_*` parameters specify an exact match, whereas the `min_*` specify a minimum number of plugins. Only one should be used for any
    given plugin type.

    Args:
        sorted_plugins (SortedPlugins): A ``SortedPlugins`` instance containing fields of plugins to validate.
        log_func (Callable[[LoggingLevel, str], None]): The logging function to use within this method.
        **kwargs: Keyword arguments mapping plugin type names (as strings) to an expected number of plugins.
            At least one plugin type must be specified.

    Returns:
    bool: `True` if all expected plugin counts match the actual counts; `False` otherwise.
    """
    accepted_args = {
        'controller_plugins',
        'fusion_plugins',
        'fusion_strategy_plugins',
        'inertial_plugins',
        'initialization_plugins',
        'logging_plugins',
        'orchestration_plugins',
        'platform_integration_plugins',
        'preprocessor_plugins',
        'registry_plugins',
        'state_modeling_plugins',
        'transport_plugins',
        'ui_plugins',
        'utility_plugins',
    }
    if not kwargs:
        log_func(
            LoggingLevel.ERROR,
            'No plugins were given criteria to validate. At least one plugin must be validated',
        )
        return False

    for name, (min, max) in kwargs.items():
        if name not in accepted_args:
            log_func(
                LoggingLevel.ERROR,
                f'Unknown argument: {name}\nList of accepted args: {list(accepted_args)}',
            )
            return False

        plugin_count = len(getattr(sorted_plugins, name))
        if plugin_count < min or plugin_count > max:
            if min == max:
                log_func(
                    LoggingLevel.ERROR,
                    f'Expected {min} {name} but received {plugin_count}',
                )
            else:
                log_func(
                    LoggingLevel.ERROR,
                    f'Expected between {min} to {max} {name} but received {plugin_count}',
                )
            return False
    return True


def find_base_plugin_type(plugin: CommonPlugin) -> PluginType:
    """
    Utility function to determine the base type of the ``plugin`` parameter.
    Will raise a ``TypeError`` if the base type cannot be determined.

    Args:
        plugin (CommonPlugin): Any type of plugin.
    """
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
    elif isinstance(plugin, UtilityPlugin):
        return UtilityPlugin
    else:
        raise TypeError(
            f'Plugin of type {type(plugin).__name__} has no base plugin type.'
        )


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
                        log_func(
                            LoggingLevel.ERROR,
                            f'Expected one {t.__name__}, but received {n_plugins_of_type_t}.',
                        )
                        return
                    setattr(self, t_snake, plugins_of_type_t[0])

    """
    return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
