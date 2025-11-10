import contextlib
import unittest

from aspn23 import (
    TypeTimestamp,
)
from numpy import float64
from numpy.typing import NDArray
from pntos.api import (
    CommonPlugin,
    ControllerPlugin,
    CrossCovariances,
    EstimateWithCovariance,
    FusionEngineType,
    FusionPlugin,
    FusionStrategyPlugin,
    FusionStrategyType,
    InertialInitializationStrategy,
    InertialPlugin,
    InertialType,
    InitialInertialSolution,
    InitializationMotionNeeded,
    InitializationPlugin,
    InitializationStatus,
    InitializationType,
    LoggingLevel,
    LoggingPlugin,
    Mediator,
    Message,
    MessageStreamConfig,
    OrchestrationPlugin,
    Registry,
    StandardDynamicsModel,
    StandardFusionEngine,
    StandardFusionStrategy,
    StandardMeasurementModel,
    StandardMeasurementProcessor,
    StandardStateBlock,
    StandardStateModelProvider,
    StateModelingPlugin,
    StateModelProviderType,
    TransportPlugin,
    UiPlugin,
    VirtualStateBlock,
)
from pntos.cobra import (
    StandardControllerPlugin,
    StandardLoggingPlugin,
    StandardRegistryPlugin,
)
from pntos.cobra.internal import StandardMediator

FOUND_ERROR = False
ERROR_MESSAGE = ''


class DummyInitializationPlugin(InitializationPlugin):
    def __init__(self, identifier: str) -> None:
        self.identifier = identifier

    def init_plugin(
        self,
        plugin_resources_location: str | None = None,
        mediator: Mediator | None = None,
    ) -> None:
        self.mediator = mediator

    def shutdown_plugin(self) -> None:
        return

    def is_initialization_type_supported(self, type: type[InitializationType]) -> bool:
        return True

    def new_initialization_strategy(
        self, type: type[InitializationType], config_group: str | None = None
    ) -> InitializationType | None:
        if issubclass(type, InertialInitializationStrategy):
            return DummyInertialInitializationStrategy()
        return None


class DummyInertialPlugin(InertialPlugin):
    def __init__(self, identifier: str) -> None:
        self.identifier = identifier

    def init_plugin(
        self,
        plugin_resources_location: str | None = None,
        mediator: Mediator | None = None,
    ) -> None:
        self.mediator = mediator

    def shutdown_plugin(self) -> None:
        return

    def is_inertial_type_supported(self, type: type[InertialType]) -> bool:
        return True

    def new_inertial(
        self,
        type: type[InertialType],
        solution: Message,
        config_group: str | None = None,
    ) -> InertialType | None:
        return type()


class DummyFusionPlugin(FusionPlugin):
    def __init__(self, identifier: str) -> None:
        self.identifier = identifier

    def init_plugin(
        self,
        plugin_resources_location: str | None = None,
        mediator: Mediator | None = None,
    ) -> None:
        self.mediator = mediator

    def shutdown_plugin(self) -> None:
        return

    def is_fusion_type_supported(self, type: type[FusionEngineType]) -> bool:
        return True

    def new_fusion_engine(
        self, type: type[FusionEngineType]
    ) -> FusionEngineType | None:
        if issubclass(type, StandardFusionStrategy):
            return DummyStandardFusionEngine()
        return None


class DummyStandardFusionEngine(StandardFusionEngine):
    _strategy: StandardFusionStrategy
    _time: TypeTimestamp = TypeTimestamp(0)

    @property
    def time(self) -> TypeTimestamp:
        return self._time

    @time.setter
    def time(self, time: TypeTimestamp) -> None:
        self._time = time

    @property
    def strategy(self) -> StandardFusionStrategy | None:
        return self._strategy

    @strategy.setter
    def strategy(self, strategy: StandardFusionStrategy) -> None:
        self._strategy = strategy

    @property
    def num_states(self) -> int:
        return 0

    @property
    def state_block_labels(self) -> list[str] | None:
        pass

    def add_state_block(
        self,
        block: StandardStateBlock,
        initial_estimate_covariance: EstimateWithCovariance,
        cross_covariances: CrossCovariances | None = None,
    ) -> None:
        pass

    def get_state_block_estimate(self, block_label: str) -> NDArray[float64] | None:
        pass

    def get_state_block_covariance(self, block_label: str) -> NDArray[float64] | None:
        pass

    def get_state_block_cross_covariance(
        self, block_label1: str, block_label2: str
    ) -> NDArray[float64] | None:
        pass

    def set_state_block_estimate(
        self, block_label: str, estimate: NDArray[float64]
    ) -> None:
        pass

    def set_state_block_covariance(
        self, block_label: str, covariance: NDArray[float64]
    ) -> None:
        pass

    def set_state_block_cross_covariance(
        self, block_label1: str, block_label2: str, covariance: NDArray[float64]
    ) -> None:
        pass

    def remove_state_block(self, block_label: str) -> None:
        pass

    @property
    def virtual_state_block_target_labels(self) -> list[str] | None:
        pass

    def has_virtual_state_block(self, vsb_target_label: str) -> bool:
        return False

    def add_virtual_state_block(self, virtual_state_block: VirtualStateBlock) -> None:
        pass

    def remove_virtual_state_block(self, vsb_target_label: str) -> None:
        pass

    @property
    def measurement_processor_labels(self) -> list[str] | None:
        pass

    def add_measurement_processor(
        self, processor: StandardMeasurementProcessor
    ) -> None:
        pass

    def remove_measurement_processor(self, processor_label: str) -> None:
        pass

    def propagate(self, time: TypeTimestamp) -> None:
        pass

    def update(self, processor_label: str, message: Message) -> None:
        pass

    def peek_ahead(
        self, time: TypeTimestamp, block_labels: list[str]
    ) -> EstimateWithCovariance | None:
        pass

    def generate_x_and_p(
        self, block_labels: list[str]
    ) -> EstimateWithCovariance | None:
        pass

    def give_state_block_aux_data(
        self, block_label: str, aux: list[Message | None]
    ) -> None:
        pass

    def give_measurement_processor_aux_data(
        self, processor_label: str, aux: list[Message | None]
    ) -> None:
        pass

    def give_virtual_state_block_aux_data(
        self, target_label: str, aux: list[Message | None]
    ) -> None:
        pass

    def clone(self) -> 'DummyStandardFusionEngine':
        return self


class DummyFusionStrategyPlugin(FusionStrategyPlugin):
    def __init__(self, identifier: str) -> None:
        self.identifier = identifier

    def init_plugin(
        self,
        plugin_resources_location: str | None = None,
        mediator: Mediator | None = None,
    ) -> None:
        self.mediator = mediator

    def shutdown_plugin(self) -> None:
        return

    def is_fusion_type_supported(self, fusion_type: type[FusionStrategyType]) -> bool:
        return True

    def new_fusion_strategy(
        self, fusion_type: type[FusionStrategyType]
    ) -> FusionStrategyType | None:
        return DummyStandardFusionStrategy()


class DummyStateModelingPlugin(StateModelingPlugin):
    def __init__(self, identifier: str) -> None:
        self.identifier = identifier

    def init_plugin(
        self,
        plugin_resources_location: str | None = None,
        mediator: Mediator | None = None,
    ) -> None:
        self.mediator = mediator

    def shutdown_plugin(self) -> None:
        return

    def is_fusion_type_supported(self, type: type[StateModelProviderType]) -> bool:
        return True

    def new_state_model_provider(
        self, type: type[StateModelProviderType]
    ) -> StateModelProviderType | None:
        return DummyStandardStateModelProvider()


class DummyStandardStateModelProvider(StandardStateModelProvider):
    def __init__(self) -> None:
        self.processor_identifiers = []
        self.block_identifiers = []
        self.virtual_block_identifiers = []

    def new_processor(
        self,
        processor_index: int,
        engine: StandardFusionEngine | None,
        label: str,
        state_block_labels: list[str],
        config_group: str | None,
    ) -> StandardMeasurementProcessor | None:
        return None

    def new_block(
        self,
        block_index: int,
        engine: StandardFusionEngine | None,
        label: str,
        config_group: str | None,
    ) -> StandardStateBlock | None:
        return None

    def new_virtual_block(
        self,
        virtual_block_index: int,
        source_label: str,
        target_label: str,
        config_group: str | None,
    ) -> VirtualStateBlock | None:
        return None


class DummyStandardFusionStrategy(StandardFusionStrategy):
    @property
    def num_states(self) -> int:
        return 0

    def add_states(
        self,
        initial_estimate: NDArray[float64],
        initial_covariance: NDArray[float64],
        cross_covariance: NDArray[float64] | None = None,
    ) -> int:
        return 0

    def remove_states(self, first_index: int, count: int) -> None:
        pass

    @property
    def estimate(self) -> NDArray[float64] | None:
        return None

    def set_estimate_slice(
        self, new_estimate: NDArray[float64], first_index: int
    ) -> None:
        pass

    @property
    def covariance(self) -> NDArray[float64] | None:
        pass

    def set_covariance_slice(
        self,
        new_covariance: NDArray[float64],
        first_row: int,
        first_col: int | None = None,
    ) -> None:
        pass

    def propagate(self, dynamics_model: StandardDynamicsModel) -> None:
        pass

    def update(self, measurement_model: StandardMeasurementModel) -> None:
        pass

    def clone(self) -> 'DummyStandardFusionStrategy':
        return self


class DummyInertialInitializationStrategy(InertialInitializationStrategy):
    def request_solution(self) -> InitialInertialSolution:
        return InitialInertialSolution(
            None, None, None, InitializationStatus.INITIALIZED_GOOD
        )

    def request_motion_needed(self) -> InitializationMotionNeeded:
        return InitializationMotionNeeded.ANY_MOTION

    def request_current_status(self) -> InitializationStatus:
        return InitializationStatus.INITIALIZED_GOOD

    def process_pntos_message(self, message: Message) -> None:
        pass


class ExitThread(Exception):
    pass


class DummyUiPlugin(UiPlugin):
    def __init__(self, identifier: str) -> None:
        self.identifier = identifier
        self.timer = None

    def init_plugin(
        self,
        plugin_resources_location: str | None = None,
        mediator: Mediator | None = None,
    ) -> None:
        self.mediator = mediator

    def shutdown_plugin(self) -> None:
        return

    def requires_main_thread(self) -> bool:
        return True

    def run_main_thread(self) -> None:
        raise ExitThread


class DummyMediator(Mediator):
    registry: Registry

    @property
    def filter_description_list(self) -> list[str]:
        return []

    def request_solutions(
        self,
        solution_times: list[TypeTimestamp],
        filter_description: str | None = None,
    ) -> list[Message | None] | None:
        return None

    def process_pntos_message(self, message: Message) -> None:
        return

    def broadcast_aspn_message(
        self,
        message: Message,
        transport: str | None = None,
        destination_identifier: str | None = None,
    ) -> None:
        return

    def log_message(self, level: LoggingLevel, message: str) -> None:
        if level is LoggingLevel.ERROR:
            global ERROR_MESSAGE
            ERROR_MESSAGE = message
            FOUND_ERROR = True
            assert not FOUND_ERROR, ERROR_MESSAGE


class DummyTransportPlugin(TransportPlugin):
    def __init__(self, identifier: str) -> None:
        self.identifier = identifier

    def init_plugin(
        self,
        plugin_resources_location: str | None = None,
        mediator: Mediator | None = None,
    ) -> None:
        self.mediator = mediator

    def shutdown_plugin(self) -> None:
        return

    def start_listening(self) -> None:
        pass

    def stop_listening(self) -> None:
        pass

    def broadcast_message(
        self, message: Message, channel_name: str | None = None
    ) -> None:
        pass


class DummyOrchestrationPlugin(OrchestrationPlugin):
    def __init__(self, identifier: str) -> None:
        self.identifier = identifier

    def init_plugin(
        self,
        plugin_resources_location: str | None = None,
        mediator: Mediator | None = None,
    ) -> None:
        self.mediator = mediator

    def shutdown_plugin(self) -> None:
        return

    def init_orchestration_plugin(
        self, plugins: list[CommonPlugin] | None, stream_config: MessageStreamConfig
    ) -> None:
        pass

    def process_pntos_message(self, message: Message, sequenced: bool) -> None:
        pass

    @property
    def filter_description_list(self) -> list[str]:
        return []

    def request_solutions(
        self,
        solution_times: list[TypeTimestamp],
        filter_description: str | None = None,
    ) -> list[Message | None] | None:
        return None


class Test_StandardControllerPlugin(unittest.TestCase):
    def __init__(self, name: str) -> None:
        super().__init__(name)

    def set_up_plugins(self) -> None:
        # Instantiate a fresh set of plugins
        self.orchestration_plugin: OrchestrationPlugin = DummyOrchestrationPlugin(
            'DummyOrchestrationPlugin'
        )
        self.initialization_plugin: InitializationPlugin = DummyInitializationPlugin(
            'DummyInitializationPlugin'
        )
        self.inertial_plugin: InertialPlugin = DummyInertialPlugin(
            'DummyInertialPlugin'
        )
        self.fusion_plugin: FusionPlugin = DummyFusionPlugin('DummyFusionPlugin')
        self.fusion_strategy_plugin: FusionStrategyPlugin = DummyFusionStrategyPlugin(
            'DummyFusionStrategyPlugin'
        )
        self.state_modeling_plugin: StateModelingPlugin = DummyStateModelingPlugin(
            'DummyStateModelingPlugin'
        )
        self.registry_plugin: StandardRegistryPlugin = StandardRegistryPlugin(
            'StandardRegistryPlugin'
        )
        self.logging_plugin: LoggingPlugin = StandardLoggingPlugin(
            'StandardLoggingPlugin'
        )
        self.controller: ControllerPlugin = StandardControllerPlugin(
            'StandardControllerPlugin'
        )
        self.ui: UiPlugin = DummyUiPlugin('DummyUiPlugin')
        self.transport: TransportPlugin = DummyTransportPlugin('DummyTransportPlugin')

        self.plugins_list = [
            self.orchestration_plugin,
            self.initialization_plugin,
            self.inertial_plugin,
            self.fusion_plugin,
            self.fusion_strategy_plugin,
            self.state_modeling_plugin,
            self.registry_plugin,
            self.logging_plugin,
            self.ui,
            self.transport,
        ]

    def test_init_plugin_controller_without_mediator_or_resources(self) -> None:
        """
        Just making sure the function can run without crashing.

        TODO: make more robust tests for this method.
        """
        self.set_up_plugins()
        self.controller.init_plugin(None, None)

    def test_init_plugin_controller_with_mediator_without_resources(
        self,
    ) -> None:
        """
        Just making sure the function can run without crashing.

        TODO: make more robust tests for this method.
        """
        self.set_up_plugins()
        mediator = DummyMediator()
        self.controller.init_plugin(mediator=mediator)

    def test_take_control_simple_no_plugin_resources_no_initial_config(
        self,
    ) -> None:
        """
        Just making sure the function can run without crashing.

        TODO: make more robust tests for this method.
        """

        self.set_up_plugins()
        mediator = DummyMediator()
        self.controller.init_plugin(mediator=mediator)
        # Catch ExitThread exception thrown inside DummyUiPlugin.run_main_thread
        with contextlib.suppress(ExitThread):
            self.controller.take_control(self.plugins_list)

    def test_mediator_filter_description_list(self) -> None:
        expected_filter_description_list: list[str] = []
        self.set_up_plugins()
        mediator = StandardMediator(self.controller.identifier, ControllerPlugin)
        orchestration_plugin = DummyOrchestrationPlugin('Dummy orchestration')
        StandardMediator._orchestration_plugin = orchestration_plugin
        filter_description_list = mediator.filter_description_list
        assert len(filter_description_list) == len(expected_filter_description_list)
        for i in range(len(filter_description_list)):
            assert filter_description_list[i] == expected_filter_description_list[i]


def suite() -> unittest.TestSuite:
    suite = unittest.TestSuite()
    tests = [m for m in dir(Test_StandardControllerPlugin) if m.startswith('test_')]
    for test in tests:
        suite.addTest(Test_StandardControllerPlugin(test))
    return suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
