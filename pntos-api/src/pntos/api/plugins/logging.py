"""Python API of pntOS."""

from abc import ABC, abstractmethod

from .common import CommonPlugin, LoggingLevel
from .controller import ControllerPlugin
from .fusion import FusionPlugin
from .fusion_strategy import FusionStrategyPlugin
from .inertial import InertialPlugin
from .initialization import InitializationPlugin
from .orchestration import OrchestrationPlugin
from .platform_integration import PlatformIntegrationPlugin
from .preprocessor import PreprocessorPlugin
from .registry import RegistryPlugin
from .state_modeling import StateModelingPlugin
from .transport import TransportPlugin
from .ui import UiPlugin
from .utility import UtilityPlugin

PluginType = (
    type[ControllerPlugin]
    | type[FusionPlugin]
    | type[FusionStrategyPlugin]
    | type[InertialPlugin]
    | type[InitializationPlugin]
    | type['LoggingPlugin']
    | type[OrchestrationPlugin]
    | type[PlatformIntegrationPlugin]
    | type[PreprocessorPlugin]
    | type[RegistryPlugin]
    | type[StateModelingPlugin]
    | type[TransportPlugin]
    | type[UiPlugin]
    | type[UtilityPlugin]
)


class LoggingPlugin(CommonPlugin, ABC):
    """
    Logging plugin.

    A plugin for logging out data to an arbitrary sink (e.g. console, file,
    network, etc.).
    """

    @abstractmethod
    def log(
        self,
        source_plugin_type: PluginType,
        source_plugin_identifier: str,
        level: LoggingLevel,
        message: str,
    ) -> None:
        """
        Log a string to the logging plugin's sink.

        Args:
            source_plugin_type (type[CommonPlugin]): Information on the plugin that sent the logout.
            source_plugin_identifier (str): Information on the plugin that sent the logout.
            level (LoggingLevel): The event severity.
            message (str): The string contents to be logged.
        """
        pass
