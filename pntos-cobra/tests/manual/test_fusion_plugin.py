import numpy as np
import pytest
from aspn23 import (
    MeasurementDeltaPosition,
    MeasurementDeltaPositionErrorModel,
    MeasurementDeltaPositionReferenceFrame,
    TypeHeader,
    TypeTimestamp,
)
from numpy.typing import NDArray
from pntos.api import (
    EstimateWithCovariance,
    EstimateWithCovarianceType,
    FusionPlugin,
    LoggingLevel,
    Message,
    StandardDynamicsModel,
    StandardFusionEngine,
    StandardFusionStrategy,
    StandardMeasurementModel,
    StandardMeasurementProcessor,
    StandardStateBlock,
)
from pntos.cobra import (
    EkfFusionStrategyPlugin,
    StandardFusionPlugin,
)
from pntos.cobra.internal import (
    SimpleMediator,
    StandardFusionEngine as CobraStandardFusionEngine,
    StandardRegistry,
)


# Test Sensor plugin
class _TestStateBlock(StandardStateBlock):
    def __init__(self, label: str) -> None:
        self.label = label
        self.num_states = 4

    def receive_aux_data(self, aux: list[Message | None]) -> None:
        pass

    def generate_dynamics(
        self,
        x_and_p: EstimateWithCovariance,
        time_from: TypeTimestamp,
        time_to: TypeTimestamp,
    ) -> StandardDynamicsModel | None:
        dt = (time_to.elapsed_nsec - time_from.elapsed_nsec) / 1e9
        Phi = np.array([[1, 0, dt, 0], [0, 1, 0, dt], [0, 0, 1, 0], [0, 0, 0, 1]])
        Q = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 2, 0], [0, 0, 0, 2]])

        Qd = Q * dt

        def g(x: NDArray[np.float64]) -> NDArray[np.float64]:
            return Phi @ x

        return StandardDynamicsModel(g, Phi, Qd)


class _TestMeasurementProcessor(StandardMeasurementProcessor):
    def __init__(self, label: str, state_block_labels: list[str]) -> None:
        self.label = label
        self.state_block_labels = state_block_labels

    def receive_aux_data(self, aux: list[Message | None]) -> None:
        pass

    def generate_model(
        self, message: Message, x_and_p: EstimateWithCovariance
    ) -> StandardMeasurementModel | None:
        assert isinstance(message.wrapped_message, MeasurementDeltaPosition)
        delta_pos = message.wrapped_message

        assert delta_pos.term1 is not None
        assert delta_pos.term2 is not None

        z = np.array(
            [[delta_pos.term1 / delta_pos.delta_t, delta_pos.term2 / delta_pos.delta_t]]
        ).reshape(2, 1)

        H = np.zeros((2, 4))
        H[0, 2] = 1
        H[1, 3] = 1

        def h(x: NDArray[np.float64]) -> NDArray[np.float64]:
            return H @ x

        R = delta_pos.covariance

        return StandardMeasurementModel(z, h, H, R)


class GenerateDeltaPosMeasurement:
    def __init__(self, init_time: TypeTimestamp = TypeTimestamp(0)) -> None:
        self.init_time = init_time
        self.x_vel = 2.0
        self.y_vel = 2.0

    def generate_measurement(self, time: TypeTimestamp) -> MeasurementDeltaPosition:
        header = TypeHeader(vendor_id=0, device_id=0, context_id=0, sequence_id=0)
        delta_time = (time.elapsed_nsec - self.init_time.elapsed_nsec) / 1e9
        return MeasurementDeltaPosition(
            header=header,
            time_of_validity=time,
            reference_frame=MeasurementDeltaPositionReferenceFrame.NED,
            delta_t=delta_time,
            term1=self.x_vel * delta_time,
            term2=self.y_vel * delta_time,
            term3=None,
            covariance=np.array([[16, 0], [0, 16]]),
            error_model=MeasurementDeltaPositionErrorModel.NONE,
            error_model_params=np.array([]),
            integrity=[],
        )


def dummy_log(level: LoggingLevel, message: str) -> None:
    pass


def create_state_block(label: str) -> tuple[_TestStateBlock, EstimateWithCovariance]:
    sb = _TestStateBlock(label=label)
    X0 = np.array([[0, 0, 1, 1]]).reshape(4, 1)
    P0 = np.array([[25, 0, 0, 0], [0, 25, 0, 0], [0, 0, 25, 0], [0, 0, 0, 25]])
    x_and_p = EstimateWithCovariance(
        type=EstimateWithCovarianceType.EWC_GENERIC, estimate=X0, covariance=P0
    )

    return sb, x_and_p


@pytest.fixture
def mediator() -> SimpleMediator:
    registry = StandardRegistry(dummy_log)
    mediator = SimpleMediator('Fusion Plugin', FusionPlugin)
    SimpleMediator.registry = registry
    return mediator


@pytest.fixture
def fusion_engine(mediator: SimpleMediator) -> StandardFusionEngine:
    # initialize the fusion plugin
    fusion_plugin = StandardFusionPlugin(identifier='test_fusion_plugin')
    fusion_plugin.init_plugin('test', mediator=mediator)
    fusion_engine: StandardFusionEngine | None = fusion_plugin.new_fusion_engine(
        StandardFusionEngine
    )
    assert fusion_engine is not None
    fusion_strategy_plugin = EkfFusionStrategyPlugin(identifier='test_strategy_plugin')
    fusion_strategy_plugin.init_plugin('test_strategy', mediator=mediator)
    fusion_strategy: StandardFusionStrategy | None = (
        fusion_strategy_plugin.new_fusion_strategy(StandardFusionStrategy)
    )
    assert fusion_strategy is not None

    # Set the strategy
    fusion_engine.strategy = fusion_strategy

    # Add MP and 2 SBs to fusion engine
    sb1, x_and_p1 = create_state_block('sb1')
    sb2, x_and_p2 = create_state_block('sb2')
    fusion_engine.add_state_block(block=sb1, initial_estimate_covariance=x_and_p1)
    fusion_engine.add_state_block(block=sb2, initial_estimate_covariance=x_and_p2)
    delta_pos_mp = _TestMeasurementProcessor(label='mp', state_block_labels=['sb1'])
    fusion_engine.add_measurement_processor(processor=delta_pos_mp)

    return fusion_engine


def test_manual(fusion_engine: CobraStandardFusionEngine) -> None:
    """User test for the Fusion Plugin."""

    delta_pos_generator = GenerateDeltaPosMeasurement()

    # Generate measurements
    for time in np.arange(0.5, 10.0, 0.5):
        time_tag = TypeTimestamp(time * 1e9)
        meas = delta_pos_generator.generate_measurement(time_tag)
        pntos_message = Message(
            wrapped_message=meas, source_identifier='test_xy_vel_sensor'
        )
        # propagate
        fusion_engine.propagate(time_tag)
        # update
        fusion_engine.update(processor_label='track_mp', message=pntos_message)


def test_remove_state_block(fusion_engine: CobraStandardFusionEngine) -> None:
    assert fusion_engine._sb['sb1'].start_index == 0
    assert fusion_engine._sb['sb1'].stop_index == 4
    assert fusion_engine._sb['sb2'].start_index == 4
    assert fusion_engine._sb['sb2'].stop_index == 8

    fusion_engine.remove_state_block('sb1')
    assert fusion_engine._sb['sb2'].start_index == 0
    assert fusion_engine._sb['sb2'].stop_index == 4
