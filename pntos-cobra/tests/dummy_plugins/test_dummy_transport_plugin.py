from time import sleep

import pytest
from pntos.api.plugins.common import Message
from pntos.cobra import DummyTransportPlugin
from pntos.cobra.internal import (
    DummyMediator,
)


class FlagMediator(DummyMediator):
    got_msg: bool

    def __init__(self) -> None:
        super().__init__()
        self.got_msg = False

    def process_pntos_message(self, message: Message) -> None:
        super().process_pntos_message(message)
        self.got_msg = True


@pytest.fixture
def mediator() -> FlagMediator:
    return FlagMediator()


def test_dummy_transport(mediator: FlagMediator, dummy_msg: Message) -> None:
    plg = DummyTransportPlugin('id')
    plg.init_plugin(mediator=mediator, plugin_resources_location=None)
    assert plg.mediator is not None
    assert plg.identifier == 'id'
    # Does nothing
    plg.broadcast_message(message=dummy_msg)
    plg.start_listening()
    sleep(0.2)
    plg.shutdown_plugin()
    assert mediator.got_msg


def test_dummy_transport_multi_start_thread(
    mediator: FlagMediator, dummy_msg: Message
) -> None:
    plg = DummyTransportPlugin('id')
    plg.init_plugin(mediator=mediator, plugin_resources_location=None)
    assert plg.mediator is not None
    assert plg.identifier == 'id'
    for _ in range(5):
        plg.start_listening()
    plg.shutdown_plugin()
    assert mediator.got_msg


def test_dummy_transport_start_stop_thread(
    mediator: FlagMediator, dummy_msg: Message
) -> None:
    plg = DummyTransportPlugin('id')
    plg.init_plugin(mediator=mediator, plugin_resources_location=None)
    assert plg.mediator is not None
    assert plg.identifier == 'id'
    for _ in range(5):
        plg.start_listening()
        plg.stop_listening()
    plg.start_listening()
    plg.shutdown_plugin()
    assert mediator.got_msg
