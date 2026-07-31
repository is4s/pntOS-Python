import argparse
import contextlib
import inspect
import re
import shlex
import subprocess
import typing
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from rich import print as rich_print
from rich.tree import Tree as RichTree
from textual import on
from textual.app import App, ComposeResult
from textual.widgets import Tree as TextualTree
from textual.widgets.tree import TreeNode
from typing_extensions import override

from pntos.api import (
    CommonPlugin,
    ControllerPlugin,
    FusionPlugin,
    FusionStrategyPlugin,
    InertialPlugin,
    InitializationPlugin,
    LoggingLevel,
    LoggingPlugin,
    Mediator,
    OrchestrationPlugin,
    PlatformIntegrationPlugin,
    PluginType,
    PreprocessorPlugin,
    RegistryPlugin,
    StandardStateModelProvider,
    StateModelingPlugin,
    StateModelProviderType,
    TransportPlugin,
    UiPlugin,
    UtilityPlugin,
)

from ..dummy_plugins.DummyMediator import DummyMediator  # noqa: TID252


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
    if isinstance(plugin, FusionPlugin):
        return FusionPlugin
    if isinstance(plugin, FusionStrategyPlugin):
        return FusionStrategyPlugin
    if isinstance(plugin, InertialPlugin):
        return InertialPlugin
    if isinstance(plugin, InitializationPlugin):
        return InitializationPlugin
    if isinstance(plugin, LoggingPlugin):
        return LoggingPlugin
    if isinstance(plugin, OrchestrationPlugin):
        return OrchestrationPlugin
    if isinstance(plugin, PlatformIntegrationPlugin):
        return PlatformIntegrationPlugin
    if isinstance(plugin, PreprocessorPlugin):
        return PreprocessorPlugin
    if isinstance(plugin, RegistryPlugin):
        return RegistryPlugin
    if isinstance(plugin, StateModelingPlugin):
        return StateModelingPlugin
    if isinstance(plugin, TransportPlugin):
        return TransportPlugin
    if isinstance(plugin, UiPlugin):
        return UiPlugin
    if isinstance(plugin, UtilityPlugin):
        return UtilityPlugin
    raise TypeError(f'Plugin of type {type(plugin).__name__} has no base plugin type.')


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


class _CatalogLoggingPlugin(LoggingPlugin):
    """
    This logger is used to catch any errors that occur when in the catalog function when attempting to introspect plugins, in order to display
    an error message in the tree, as opposed to giving no indication that introspecting was attempted at all.
    """

    def __init__(self) -> None:
        self.error: str | None = None

    @override
    def init_plugin(
        self,
        plugin_resources_location: str | None = None,
        mediator: Mediator | None = None,
    ) -> None:
        pass

    @override
    def log(
        self,
        source_plugin_type: PluginType,
        source_plugin_identifier: str,
        level: LoggingLevel,
        message: str,
    ) -> None:
        """
        If the passed LoggingLevel is an error, that is saved to this plugin's internal error variable.
        """
        if level == LoggingLevel.ERROR:
            self.error = message

    @override
    def shutdown_plugin(self) -> None:
        pass


def cobra_catalog() -> None:
    """
    Launches a textual app (or simply prints a tree to the terminal) that contains a tree view of all implemented
    plugins, sorted by type. An example output could be::

        All Available Plugins
        ├── ControllerPlugins
        │   ├── DummyControllerPlugin
        │   ├── StandardControllerPlugin
        │   └── BuscatControllerPlugin
        ├── FusionPlugins
        │   └── StandardFusionPlugin
        └── FusionStrategyPlugins
            └── EkfFusionStrategyPlugin
    """
    # A list of all Plugin Types/Categories to be queried through
    plugin_types: list[PluginType] = [
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
        UtilityPlugin,
    ]
    parser = argparse.ArgumentParser(
        description='Allows the user to view available plugins in a hierarchial structure.',
        epilog="controls: 'q'=quit | 'enter'=open file | 'space'=expand/shrink tree item",
    )
    parser.add_argument(
        '--match',
        '-m',
        default='.*',
        help='ReGex pattern for matching outputted plugins. Ex: "Tutorial*"',
    )
    parser.add_argument(
        '--type',
        '-t',
        default=None,
        help='Specific category you want to view all plugins within. Ex: "ControllerPlugin"',
    )
    parser.add_argument(
        '-p',
        '--print',
        action='store_true',
        help='If specified, will print the plugin tree directly to the terminal as opposed to launching an interactive app.',
    )
    parser.add_argument(
        '-e',
        '--editor-incantation',
        default='code',
        help="The editor incantation for opening paths. {code, pycharm, vim, etc.} If a node is selected that is associated with a particular file, the program will call '[EXECUTABLE] [FILEPATH]'.",
    )
    parser.add_argument(
        '-n',
        '--no-open',
        action='store_true',
        help='If specified, the app will not support clicking or enter to open plugin files.',
    )
    args, _ = parser.parse_known_args()
    if args.print:
        print_plugin_tree(args, plugin_types)
    else:
        catalog_app = Catalog()
        catalog_app.args = args
        catalog_app.plugin_types = plugin_types
        catalog_app.run()


class CatalogTree(ABC):
    """Abstract interface for different tree options for the `catalog` command."""

    @abstractmethod
    def add_branch(
        self, label: str, data: Path | None = None, expand: bool = False
    ) -> 'CatalogTree':
        """Adds a nested node that can contain further sub-nodes."""

    @abstractmethod
    def add_leaf(self, label: str, data: Path | None = None) -> None:
        """Adds a terminal leaf node."""


class PrintTree(CatalogTree):
    """Wrapper for RichTree"""

    def __init__(self, root: RichTree) -> None:
        self.root_tree = root

    @override
    def add_branch(
        self, label: str, data: Path | None = None, expand: bool = False
    ) -> 'PrintTree':
        # simulate the same way the newly created sub-tree is returned when .add() is called on a RichTree
        child_node = self.root_tree.add(label)
        return PrintTree(child_node)

    @override
    def add_leaf(self, label: str, data: Path | None = None) -> None:
        self.root_tree.add(label)


class TerminalTree(CatalogTree):
    """Wrapper for TextualTree."""

    def __init__(self, root: TreeNode) -> None:
        self.root_node = root

    @override
    def add_branch(
        self, label: str, data: Path | None = None, expand: bool = False
    ) -> 'TerminalTree':
        # simulate the same way the newly created sub-tree is returned when .add() is called on a TerminalTree
        child_node = self.root_node.add(label, data, expand=expand)
        return TerminalTree(child_node)

    @override
    def add_leaf(self, label: str, data: Path | None = None) -> None:
        self.root_node.add_leaf(label, data)


def extend_state_modeling_plugins(
    plugin_type_tree: CatalogTree, plugin: PluginType
) -> bool:
    """
    Attach to the plugin_type_tree a state modeling plugin with all its providers.
    """
    if not issubclass(plugin, StateModelingPlugin):
        return False

    # state modeling plugins have providers we want to view in their sub trees
    plugin_tree = plugin_type_tree.add_branch(
        plugin.__name__, Path(inspect.getfile(plugin)), expand=False
    )
    provider_added = False
    try:
        plugin_obj: StateModelingPlugin = plugin(identifier='temp')  # ty:ignore[unknown-argument]
        for model_type in StateModelProviderType.__constraints__:
            if model_type != Any:
                logger = _CatalogLoggingPlugin()
                plugin_obj.init_plugin(mediator=DummyMediator([logger]))
                mod_provider = plugin_obj.new_state_model_provider(
                    model_type  # ty:ignore[invalid-argument-type]
                )

                if logger.error is not None:
                    plugin_tree.add_leaf('Error: ' + logger.error)
                if mod_provider:
                    # if it's a standard state model, there's 3 categories we want to include
                    if issubclass(type(mod_provider), StandardStateModelProvider):
                        provider_tree = plugin_tree.add_branch(
                            type(mod_provider).__name__
                        )

                        mps = mod_provider.processor_identifiers
                        if mps:
                            mp_tree = provider_tree.add_branch('Measurement Processors')
                            for mp in mps:
                                mp_tree.add_leaf(mp)

                        sbs = mod_provider.block_identifiers
                        if sbs:
                            sb_tree = provider_tree.add_branch('State Blocks')
                            for sb in sbs:
                                sb_tree.add_leaf(sb)

                        vsbs = mod_provider.virtual_block_identifiers
                        if vsbs:
                            vsb_tree = provider_tree.add_branch('Virtual State Blocks')
                            for vsb in vsbs:
                                vsb_tree.add_leaf(vsb)
                    else:
                        plugin_tree.add_leaf(type(mod_provider).__name__)
                    provider_added = True
        if not provider_added:
            plugin_tree.add_leaf('No Providers found')
    except AttributeError:
        plugin_tree.add_leaf('Unable to view all Providers')
    return True


def extend_preprocessor_plugin(
    plugin_type_tree: CatalogTree, plugin: PluginType
) -> bool:
    """
    Attach to the plugin_type_tree a preprocessor plugin with all its preprocessor options.
    """
    if not issubclass(plugin, PreprocessorPlugin):
        return False
    # preprocessor plugins have preprocessors we want to view
    plugin_tree = plugin_type_tree.add_branch(
        plugin.__name__, Path(inspect.getfile(plugin)), expand=False
    )
    preprocessor_added = False
    try:
        plugin_obj: PreprocessorPlugin = plugin(identifier='temp')  # ty:ignore[unknown-argument]
        for p in plugin_obj.preprocessor_identifiers:
            preprocessor_added = True
            plugin_tree.add_leaf(p)
        if not preprocessor_added:
            plugin_tree.add_leaf('No Preprocessors found')
    except AttributeError:
        plugin_tree.add_leaf('Unable to view all Preprocessors')
    return True


_specific_extensions: list[Callable[[CatalogTree, PluginType], bool]] = [
    extend_state_modeling_plugins,
    extend_preprocessor_plugin,
]
"""
Instead of adding just the plugin, if it matches an extension type add the plugin *and* corresponding subtree with information.
The format of an extension function should:
    Check if it's the wanted plugin type
        If not, return false
        If it is, add the subtree (including the plugin name as the root of that subtree) to the passed CatalogTree, then return true.

Note that there should only be one extension function per plugin type.
"""


def build_plugin_tree(
    tree: CatalogTree, args: argparse.Namespace, plugin_types: list[PluginType]
) -> None:
    """
    Assembles a tree where each category (top-level plugin type) has
    children that represent all plugins in the project that
    inherit from that type.
    Additionally, some plugins have additional internal properties that are displayed (collapsed if supported by the tree type)
    """
    for plugin_type in plugin_types:
        # check if a type filter was provided, and use it if it was
        if args.type and args.type != (plugin_type.__name__):
            continue

        plugins = get_subclasses(plugin_type)
        if not plugins:
            continue

        plugin_type_tree = None
        for plugin in plugins:
            # use the match filter, will be '*' if not user specified so everything will match.
            if re.match(args.match, plugin.__name__):
                if plugin_type_tree is None:
                    # create the category branch
                    plugin_type_tree = tree.add_branch(
                        plugin_type.__name__ + 's', expand=True
                    )
                matched_an_extender = False
                # if the plugin matched with any of the types looked for in the extensions, it was added in that extension function as a branch
                for extender_function in _specific_extensions:
                    matched_an_extender = matched_an_extender or extender_function(
                        plugin_type_tree, plugin
                    )
                # if it did not match any of the tree_extenders, add it as a leaf
                if not matched_an_extender:
                    plugin_type_tree.add_leaf(
                        plugin.__name__, Path(inspect.getfile(plugin))
                    )


def print_plugin_tree(args: argparse.Namespace, plugin_types: list[PluginType]) -> None:
    """Prints a rich tree of the available plugins, in a hierarchal structure, to the terminal. Contents can be filtered.

    Args:
        args (argparse.Namespace): Parsed command line arguments that contain filters for plugin name and type.
        plugin_types (list[PluginType]): A list containing all base plugin types/categories to be searched through.
    """

    tree = RichTree('All Available Plugins')
    build_plugin_tree(PrintTree(tree), args, plugin_types)

    rich_print(tree)


class Catalog(App[Path]):
    """
    The app class for the textual app "catalog"
    """

    BINDINGS: typing.ClassVar = [
        ('ctrl+c', 'quit', 'Quit the application'),
        ('q', 'quit', 'Quit the application'),
    ]

    plugin_types: list[PluginType]
    """A list containing all base plugin types/categories to be searched through."""
    args: argparse.Namespace
    """Parsed command line arguments that contain filters for plugin name and type."""

    @override
    def compose(self) -> ComposeResult:
        tree: TextualTree[Path] = TextualTree('All Available Plugins')
        build_plugin_tree(TerminalTree(tree.root), self.args, self.plugin_types)

        tree.root.expand()
        yield tree

    @on(TextualTree.NodeSelected)
    def on_tree_node_selected(self, event: TextualTree.NodeSelected) -> None:
        file_path = event.node.data

        if not self.args.no_open and file_path:
            with contextlib.suppress(FileNotFoundError):
                cmd = [*shlex.split(self.args.editor_incantation), str(file_path)]
                subprocess.run(cmd, check=False)


def get_subclasses(base_class: PluginType) -> set[PluginType]:
    """
    Takes a class and returns a set with all subclasses (recursively)

    Args:
        base_class (type[object]): A class object, seen as `<class xyz>`. This is the "parent" object.

    Returns:
        set[type[object]]: A set containing the class of every subclass (recursive) of the original class.
    """
    subclasses = set()
    work = [base_class]
    while work:
        parent = work.pop()
        for child in parent.__subclasses__():
            if child not in subclasses:
                subclasses.add(child)
                work.append(child)
    return subclasses
