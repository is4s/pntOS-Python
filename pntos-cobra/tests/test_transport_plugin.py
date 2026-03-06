import time

import numpy as np
import pytest
from aspn23_lcm import measurement_position_velocity_attitude
from pntos.api import LoggingLevel
from pntos.cobra import LcmTransportPlugin
from pntos.cobra.internal import DummyMediator, StandardMediator, StandardRegistry


def dummy_log(level: LoggingLevel, message: str) -> None:
    pass


@pytest.fixture
def mediator() -> DummyMediator:
    registry = StandardRegistry(dummy_log)
    DummyMediator.registry = registry
    return DummyMediator()


@pytest.fixture
def transport_plugin() -> LcmTransportPlugin:
    return LcmTransportPlugin('python-transport-lcm23-plugin')


def test_initialize_plugin(
    transport_plugin: LcmTransportPlugin, mediator: StandardMediator
) -> None:
    transport_plugin.init_plugin('plugin_path', mediator)
    assert transport_plugin.identifier == 'python-transport-lcm23-plugin'
    assert transport_plugin.mediator is not None


def _test_handler(
    transport_plugin: LcmTransportPlugin, mediator: StandardMediator
) -> None:
    transport_plugin.init_plugin('plugin_path', mediator)
    transport_plugin.start_listening()

    # Flag to capture the response
    received_response = None

    def on_response(channel: str, data: bytes) -> None:
        nonlocal received_response
        pva = measurement_position_velocity_attitude()

        received_response = pva.decode(data)

    assert transport_plugin.lcm is not None

    # Subscribe to the response channel
    transport_plugin.lcm.subscribe('pva', on_response)

    # Create a test message
    test_msg = measurement_position_velocity_attitude()
    test_msg.header.vendor_id = 0
    test_msg.header.device_id = 0
    test_msg.header.context_id = 0
    test_msg.header.sequence_id = 0
    test_msg.time_of_validity.elapsed_nsec = 1000000
    test_msg.reference_frame = 1
    test_msg.p1 = np.deg2rad(39)
    test_msg.p2 = np.deg2rad(-84)
    test_msg.p3 = 1000
    test_msg.v1 = 2
    test_msg.v2 = 3
    test_msg.v3 = 4
    test_msg.quaternion = [1, 0, 0, 0]
    test_msg.num_meas = 1
    test_msg.covariance = [0] * 81
    test_msg.error_model = 0
    test_msg.num_error_model_params = 0
    test_msg.error_model_params = []
    test_msg.num_integrity = 0
    test_msg.integrity = []
    encoded_data = test_msg.encode()

    # Publish the test message to the channel
    transport_plugin.lcm.publish('pva', encoded_data)

    # Wait for message to be processed
    time.sleep(0.1)

    # Verify the response
    assert received_response is not None
    assert isinstance(received_response, measurement_position_velocity_attitude)
    assert received_response.p1 == np.deg2rad(39)
    assert received_response.num_error_model_params == 0

    transport_plugin.shutdown_plugin()
