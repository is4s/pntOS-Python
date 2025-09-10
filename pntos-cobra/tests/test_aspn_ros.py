import os
import time

import numpy as np
import pytest


@pytest.mark.skipif(
    'ROS_VERSION' not in os.environ, reason='Skip in non-ROS environments.'
)
def test_aspn_ros() -> None:
    # ROS and ASPN-ROS imports should work here
    import rclpy  # type: ignore[import-not-found]
    from aspn23 import (
        MeasurementPositionVelocityAttitude,
        MeasurementPositionVelocityAttitudeErrorModel,
        MeasurementPositionVelocityAttitudeReferenceFrame,
        TypeHeader,
        TypeTimestamp,
    )
    from aspn23_ros_utils import AspnMsg, AspnRosNode  # type: ignore[import-not-found]

    rclpy.init()
    node = AspnRosNode('test_aspn_ros')

    expected = MeasurementPositionVelocityAttitude(
        header=TypeHeader(vendor_id=1, device_id=1, context_id=1, sequence_id=0),
        time_of_validity=TypeTimestamp(elapsed_nsec=time.time_ns()),
        reference_frame=MeasurementPositionVelocityAttitudeReferenceFrame.ECI,
        p1=1.0,
        p2=2.0,
        p3=3.0,
        v1=4.0,
        v2=5.0,
        v3=6.0,
        quaternion=np.zeros(4),
        covariance=np.zeros(36).reshape(6, 6),
        error_model=MeasurementPositionVelocityAttitudeErrorModel.NONE,
        error_model_params=np.array([]),
        integrity=[],
    )
    received = None

    def aspn_cb(msg: AspnMsg) -> None:
        nonlocal received
        received = msg

    # Publish and receive the message over ROS
    topic = '/test_aspn_ros/pva'
    node.subscribe_aspn(aspn_cb, topic, msg_type=type(expected))
    node.publish_aspn(expected, topic)

    # Wait for message to come to be received
    rclpy.spin_once(node, timeout_sec=1.0)

    # Ensure received message matches original message
    #   Note: can't use "assert expected == received" because np.arrays have an
    #   overridden equality operator
    assert isinstance(received, MeasurementPositionVelocityAttitude)
    for attr, value in expected.__dict__.items():
        if isinstance(value, np.ndarray):
            assert np.array_equal(value, getattr(received, attr))
            continue
        assert value == getattr(received, attr)
