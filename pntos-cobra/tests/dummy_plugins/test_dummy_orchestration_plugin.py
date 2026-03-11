import pytest
from aspn23 import (
    MeasurementPositionVelocityAttitude,
    TypeTimestamp,
)
from conftest import Trashspn
from pntos.api import Message
from pntos.cobra import DummyOrchestrationPlugin
from pntos.cobra.internal import DummyMediator, DummyMessageStreamConfig


@pytest.fixture
def mediator() -> DummyMediator:
    return DummyMediator()


@pytest.fixture
def orch_plugin(mediator: DummyMediator) -> DummyOrchestrationPlugin:
    plg = DummyOrchestrationPlugin('dummy_orchestration')
    plg.init_plugin(mediator=mediator, plugin_resources_location=None)
    return plg


@pytest.fixture
def stream_config() -> DummyMessageStreamConfig:
    cfg = DummyMessageStreamConfig()
    cfg.immediate_stream_all(True)
    cfg.immediate_stream_add(MeasurementPositionVelocityAttitude)
    cfg.immediate_stream_remove(MeasurementPositionVelocityAttitude)
    cfg.sequenced_stream_all(True)
    cfg.sequenced_stream_add(MeasurementPositionVelocityAttitude)
    cfg.sequenced_stream_remove(MeasurementPositionVelocityAttitude)
    return cfg


def test_dummy_orchestration_plugin(
    orch_plugin: DummyOrchestrationPlugin,
    dummy_msg: Message,
    stream_config: DummyMessageStreamConfig,
) -> None:
    assert orch_plugin.mediator is not None
    orch_plugin.init_orchestration_plugin(plugins=[], stream_config=stream_config)
    sol = orch_plugin.request_solutions(solution_times=[], filter_description=None)
    assert sol is not None
    assert len(sol) == 0
    sol = orch_plugin.request_solutions(
        solution_times=[TypeTimestamp(1)], filter_description=None
    )
    assert sol is not None
    assert len(sol) == 1
    assert sol[0] is None
    orch_plugin.process_pntos_message(message=dummy_msg, sequenced=False)
    sol = orch_plugin.request_solutions(
        solution_times=[TypeTimestamp(1)], filter_description='LAST_MESSAGE'
    )
    assert sol is not None
    assert len(sol) == 1
    for x in sol:
        assert x is not None
        assert isinstance(x.wrapped_message, Trashspn)

    sol = orch_plugin.request_solutions(
        solution_times=[TypeTimestamp(1), TypeTimestamp(2)],
        filter_description='LAST_MESSAGE',
    )
    assert sol is not None
    assert len(sol) == 2
    for x in sol:
        assert x is not None
        assert isinstance(x.wrapped_message, Trashspn)
    orch_plugin.shutdown_plugin()
