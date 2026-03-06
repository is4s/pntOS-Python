import pytest
from aspn23 import (
    AspnBase,
    MeasurementPositionVelocityAttitude,
    MeasurementPositionVelocityAttitudeErrorModel,
    MeasurementPositionVelocityAttitudeReferenceFrame,
    TypeHeader,
    TypeTimestamp,
)
from numpy import array, eye, ones, zeros
from pntos.api import (
    EstimateWithCovariance,
    EstimateWithCovarianceType,
)
from pntos.api.plugins.common import Message

"""
A collection of shared test fixtures that are automatically available through pytest.
"""


class Trashspn(AspnBase):
    """A basic ASPN message with only the typical time_of_validity field."""

    time_of_validity: TypeTimestamp

    def __init__(self, ns: int = 0) -> None:
        self.time_of_validity = TypeTimestamp(ns)


def gxp(num: int) -> EstimateWithCovariance:
    """Generate an EstimateWithCovariance with a shape that matches num and some junk filler data."""
    return EstimateWithCovariance(
        EstimateWithCovarianceType.EWC_GENERIC, ones((num, 1)) * 0.01, eye(num)
    )


@pytest.fixture
def dummy_msg() -> Message:
    return Message(wrapped_message=Trashspn(), source_identifier='dummy_msg')


@pytest.fixture
def dummy_pva() -> MeasurementPositionVelocityAttitude:
    return MeasurementPositionVelocityAttitude(
        header=TypeHeader(0, 0, 0, 0),
        time_of_validity=TypeTimestamp(0),
        p1=0.0,
        p2=0.0,
        p3=0.0,
        v1=0.0,
        v2=0.0,
        v3=0.0,
        quaternion=array([1.0, 0.0, 0.0, 0.0]),
        covariance=zeros((9, 9)),
        reference_frame=MeasurementPositionVelocityAttitudeReferenceFrame.GEODETIC,
        error_model=MeasurementPositionVelocityAttitudeErrorModel.NONE,
        error_model_params=array([]),
        integrity=[],
    )
