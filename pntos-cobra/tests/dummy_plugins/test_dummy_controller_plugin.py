from threading import Thread
from time import sleep

import pytest
from aspn23 import TypeTimestamp
from conftest import Trashspn
from pntos.api.plugins.common import CommonPlugin, LoggingLevel, Mediator, Message
from pntos.cobra import (
    DummyControllerPlugin,
    DummyOrchestrationPlugin,
    DummyTransportPlugin,
)
from pntos.cobra.internal import DummyMediator


class DoStuffPlugin(CommonPlugin):
    """A plugin that moves data back and forth through the mediator."""

    mediator: Mediator | None
    do_stuff: bool
    th: Thread | None
    did_log: bool

    def __init__(self, identifier: str) -> None:
        self.identifier = identifier
        self.do_stuff = False
        self.th = None
        self.did_log = False

    def init_plugin(
        self,
        plugin_resources_location: str | None = None,
        mediator: Mediator | None = None,
    ) -> None:
        self.mediator = mediator
        self.do_stuff = True
        self.th = Thread(target=self.interact_with_mediator)
        self.th.start()

    def interact_with_mediator(self) -> None:
        exp_tag = 'LAST_MESSAGE'
        loops = 100
        message = Message(wrapped_message=Trashspn(), source_identifier=self.identifier)
        # This is False initially, but should get flipped if controller calls init_plugin like it should
        assert self.do_stuff
        assert self.mediator
        while self.do_stuff and loops > 0:
            sleep(0.1)
            self.mediator.process_pntos_message(message=message)
            self.mediator.broadcast_aspn_message(message=message)
            old_sol = self.mediator.request_solutions(
                filter_description=exp_tag, solution_times=[TypeTimestamp(0)]
            )
            if old_sol is not None:
                self.mediator.log_message(
                    message=f'Got sol {old_sol[0].source_identifier if old_sol[0] is not None else "None"}',
                    level=LoggingLevel.INFO,
                )
                self.did_log = True
                self.do_stuff = False
            loops -= 1

    def shutdown_plugin(self) -> None:
        self.do_stuff = False
        if self.th:
            self.th.join()


@pytest.fixture
def mediator() -> DummyMediator:
    return DummyMediator()


@pytest.fixture
def controller_plugin() -> DummyControllerPlugin:
    ctrl = DummyControllerPlugin(identifier='controller')
    ctrl.init_plugin()
    return ctrl


@pytest.fixture
def orch_plugin(mediator: DummyMediator) -> DummyOrchestrationPlugin:
    return DummyOrchestrationPlugin('dummy_orchestration')


@pytest.fixture
def trans_plugin() -> DummyTransportPlugin:
    return DummyTransportPlugin('transport')


@pytest.fixture
def stuff_plugin() -> DoStuffPlugin:
    return DoStuffPlugin('do_stuff')


def test_dummy_controller(
    controller_plugin: DummyControllerPlugin,
    orch_plugin: DummyOrchestrationPlugin,
    trans_plugin: DummyTransportPlugin,
    stuff_plugin: DoStuffPlugin,
) -> None:
    # Transport should spit out data which allows orchestration to deliver
    # a solution to the DoStuffPlugin, at which point it should
    # flip the 'did_log' flag. interact_with_mediator loop usually exits
    # on first iteration.
    plugs = [orch_plugin, trans_plugin, stuff_plugin]
    controller_plugin.take_control(plugs)
    assert stuff_plugin.did_log


def test_dummy_slim(
    controller_plugin: DummyControllerPlugin,
    trans_plugin: DummyTransportPlugin,
    stuff_plugin: DoStuffPlugin,
) -> None:
    # Transport is dumping data out, but there is no orchestration for the mediator
    # to hand it to, so DoStuffPlugin cannot get a solution.  interact_with_mediator
    # loop will spin until control returns here after sleep or it hits max number of loops.
    plugs = [trans_plugin, stuff_plugin]
    controller_plugin.take_control(plugs)
    assert not stuff_plugin.did_log
