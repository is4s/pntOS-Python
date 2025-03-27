from math import isclose

import numpy as np
from aspn23 import (
    MeasurementImu,
    MeasurementImuImuType,
    MeasurementPositionVelocityAttitude,
    MeasurementPositionVelocityAttitudeErrorModel,
    MeasurementPositionVelocityAttitudeReferenceFrame,
    TypeHeader,
    TypeTimestamp,
)
from navtk.navutils import calculate_gravity_schwartz, rpy_to_quat
from pntos.api import (
    ExternalInertial,
    InertialFrame,
    InertialPlugin,
    InertialSolutionRangeType,
    LoggingLevel,
    Message,
    StandardInertialMechanization,
)
from pntos.cobra import SimpleInertialPlugin
from pntos.cobra.config import InertialConfig, config_to_registry
from pntos.cobra.internal import SimpleMediator, SimpleRegistry


def generate_header() -> TypeHeader:
    return TypeHeader(0, 0, 0, 0)


LATITUDE = 0.69
LONGITUDE = -0.8
ALTITUDE = 0


def generate_imu(time: TypeTimestamp) -> Message:
    header = generate_header()
    imu = MeasurementImu(
        header,
        time,
        MeasurementImuImuType.INTEGRATED,
        # Force due to gravity
        -calculate_gravity_schwartz(ALTITUDE, LATITUDE) / 1e2,
        # Zeroes, except for a bit in the y-axis to simulate earth's rotation (magnitude of vector
        # is less important than direction for this test). Nonzero values to avoid singularities in
        # covariance calculation.
        np.array([1e-12, 1e-6, 1e-12]) / 1e2,
        [],
    )
    return Message(imu, '')


def generate_pva() -> Message:
    header = TypeHeader(
        0,
        0,
        0,
        0,
    )
    time = TypeTimestamp(0)
    initial_covariance = np.eye(9)
    pva = MeasurementPositionVelocityAttitude(
        header=header,
        time_of_validity=time,
        reference_frame=MeasurementPositionVelocityAttitudeReferenceFrame.GEODETIC,
        p1=LATITUDE,
        p2=LONGITUDE,
        p3=ALTITUDE,
        v1=0,
        v2=0,
        v3=0,
        quaternion=rpy_to_quat(np.array([0, 0, 0])),
        covariance=initial_covariance,
        error_model=MeasurementPositionVelocityAttitudeErrorModel.NONE,
        error_model_params=np.array([]),
        integrity=[],
    )
    return Message(pva, '')


def assert_pva_equal(
    pva1: MeasurementPositionVelocityAttitude, pva2: MeasurementPositionVelocityAttitude
) -> None:
    assert pva1.time_of_validity.elapsed_nsec == pva2.time_of_validity.elapsed_nsec
    assert pva1.p1 == pva2.p1
    assert pva1.p2 == pva2.p2
    assert pva1.p3 == pva2.p3
    assert pva1.v1 == pva2.v1
    assert pva1.v2 == pva2.v2
    assert pva1.v3 == pva2.v3
    assert pva1.quaternion is not None
    assert pva2.quaternion is not None
    assert np.allclose(pva1.quaternion, pva2.quaternion)


def assert_pva_close_but_unequal(
    pva1: MeasurementPositionVelocityAttitude, pva2: MeasurementPositionVelocityAttitude
) -> None:
    assert pva1.p1 is not None
    assert pva2.p1 is not None
    assert pva2.p1 != pva1.p1
    assert isclose(pva2.p1, pva1.p1)

    assert pva1.p2 is not None
    assert pva2.p2 is not None
    assert pva2.p2 != pva1.p2
    assert isclose(pva2.p2, pva1.p2)

    assert pva1.p3 is not None
    assert pva2.p3 is not None
    assert pva2.p3 != pva1.p3
    assert isclose(pva2.p3, pva1.p3, abs_tol=1e-12)

    assert pva1.v1 is not None
    assert pva2.v1 is not None
    assert pva2.v1 != pva1.v1
    assert isclose(pva2.v1, pva1.v1, abs_tol=1e-5)

    assert pva1.v2 is not None
    assert pva2.v2 is not None
    assert pva2.v2 != pva1.v2
    assert isclose(pva2.v2, pva1.v2, abs_tol=1e-5)

    assert pva1.v3 is not None
    assert pva2.v3 is not None
    assert pva2.v3 != pva1.v3
    assert isclose(pva2.v3, pva1.v3, abs_tol=1e-5)

    assert pva1.quaternion is not None
    assert pva2.quaternion is not None
    assert np.all(pva2.quaternion != pva1.quaternion)
    assert np.allclose(pva1.quaternion, pva2.quaternion, atol=1e-5)


def dummy_log(level: LoggingLevel, message: str) -> None:
    pass


def test() -> None:
    """
    This test attempts to validate the Inertial plugin interface, without getting very involved in
    the actual values. In theory, all the heavy lifting is done by the NavToolkit classes so their
    tests will be verifying the actual values. So many assertions are merely checking for the
    existence of results or changes in results, rather than inspecting the results themselves.
    """

    # Setup
    plugin = SimpleInertialPlugin('Cobra inertial plugin')
    registry = SimpleRegistry(dummy_log)
    mediator = SimpleMediator(plugin.identifier, InertialPlugin)
    SimpleMediator.registry = registry

    config = InertialConfig(expected_dt=0.01, inertial_buffer_length=5.0, group='test')
    config_to_registry(config, mediator)

    assert plugin.identifier == 'Cobra inertial plugin'

    plugin.init_plugin(None, mediator)

    assert plugin.is_inertial_type_supported(StandardInertialMechanization)
    assert not plugin.is_inertial_type_supported(ExternalInertial)

    # Create an inertial
    message = generate_pva()
    pva = message.wrapped_message
    inertial: StandardInertialMechanization | None = plugin.new_inertial(
        StandardInertialMechanization, message, 'test'
    )
    assert inertial is not None

    first_time = TypeTimestamp(0)
    mid_time = TypeTimestamp(int(1e8))
    final_time = TypeTimestamp(int(1.3e8))

    assert inertial.is_time_in_range(first_time)
    assert not inertial.is_time_in_range(mid_time)
    solution = inertial.request_current_solution()
    pva_out = solution.wrapped_message
    assert isinstance(pva_out, MeasurementPositionVelocityAttitude)
    assert isinstance(pva, MeasurementPositionVelocityAttitude)
    assert_pva_equal(pva_out, pva)

    assert inertial.request_earliest_time() == inertial.request_latest_time()
    assert inertial.request_reset_message_types() == [
        MeasurementPositionVelocityAttitude
    ]
    assert (
        inertial.request_solution_message_type() == MeasurementPositionVelocityAttitude
    )

    # Mechanize a few times.
    for ii in range(10):
        inertial.process_pntos_message(generate_imu(TypeTimestamp(int((ii + 1) * 1e7))))

    assert inertial.is_time_in_range(first_time)
    assert inertial.is_time_in_range(mid_time)
    solution = inertial.request_current_solution()
    pva_out = solution.wrapped_message
    assert isinstance(pva_out, MeasurementPositionVelocityAttitude)
    assert isinstance(pva, MeasurementPositionVelocityAttitude)
    assert pva_out.time_of_validity == mid_time

    # Mechanized PVA should be close, but not identical to previous solution.
    assert_pva_close_but_unequal(pva_out, pva)

    assert inertial.request_earliest_time() == first_time
    assert inertial.request_latest_time() == mid_time

    # Reset the solution, then compare the current solution to the one we initialized the inertial
    # with.
    assert isinstance(message.wrapped_message, MeasurementPositionVelocityAttitude)
    message.wrapped_message.time_of_validity = mid_time
    inertial.reset_solution(message)

    solution = inertial.request_current_solution()
    pva_out = solution.wrapped_message
    assert isinstance(pva_out, MeasurementPositionVelocityAttitude)
    assert isinstance(pva, MeasurementPositionVelocityAttitude)
    assert_pva_equal(pva_out, pva)

    # Mechanize a few more times after reset so continuous and best solution types diverge.
    for ii in range(3):
        inertial.process_pntos_message(
            generate_imu(TypeTimestamp(int((ii + 11) * 1e7)))
        )

    # Show that continuous and best solution types are the same before reset, but different after.
    continuous_solutions = inertial.request_solutions(
        [first_time, final_time],
        InertialSolutionRangeType.INERTIAL_NO_UPDATES_WITHIN_RANGE,
    )
    best_solutions = inertial.request_solutions(
        [first_time, final_time], InertialSolutionRangeType.INERTIAL_BEST_KNOWN_SOLUTION
    )
    assert continuous_solutions is not None
    assert best_solutions is not None
    assert isinstance(
        continuous_solutions[0].wrapped_message, MeasurementPositionVelocityAttitude
    )
    assert isinstance(
        continuous_solutions[1].wrapped_message, MeasurementPositionVelocityAttitude
    )
    assert isinstance(
        best_solutions[0].wrapped_message, MeasurementPositionVelocityAttitude
    )
    assert isinstance(
        best_solutions[1].wrapped_message, MeasurementPositionVelocityAttitude
    )
    assert continuous_solutions[0].wrapped_message.time_of_validity == first_time
    assert best_solutions[0].wrapped_message.time_of_validity == first_time
    assert continuous_solutions[1].wrapped_message.time_of_validity == final_time
    assert best_solutions[1].wrapped_message.time_of_validity == final_time

    assert_pva_equal(
        continuous_solutions[0].wrapped_message, best_solutions[0].wrapped_message
    )
    assert_pva_close_but_unequal(
        continuous_solutions[1].wrapped_message, best_solutions[1].wrapped_message
    )

    # Test forces and rates
    inertial_forces_and_rates = inertial.request_forces_and_rates(first_time)
    assert inertial_forces_and_rates is not None
    assert inertial_forces_and_rates.frame == InertialFrame.INERTIAL_FRAME_NED
    forces_and_rates = inertial_forces_and_rates.forces_and_rates
    assert forces_and_rates.time_of_validity == first_time

    # Test average forces and rates
    inertial_forces_and_rates = inertial.request_average_forces_and_rates(
        first_time, final_time
    )
    assert inertial_forces_and_rates is not None
    assert inertial_forces_and_rates.frame == InertialFrame.INERTIAL_FRAME_NED
    forces_and_rates = inertial_forces_and_rates.forces_and_rates
    assert forces_and_rates.time_of_validity.elapsed_nsec > first_time.elapsed_nsec
    assert forces_and_rates.time_of_validity.elapsed_nsec < final_time.elapsed_nsec

    # All initial errors are zero
    inertial_errors = inertial.request_sensor_errors(first_time)
    assert inertial_errors is not None
    assert np.allclose(inertial_errors.accel_biases, np.zeros(3))
    assert np.allclose(inertial_errors.gyro_biases, np.zeros(3))
    assert np.allclose(inertial_errors.accel_scale_factors, np.zeros(3))
    assert np.allclose(inertial_errors.gyro_scale_factors, np.zeros(3))

    # If we make a change, we should get new values out
    inertial_errors.accel_biases = np.ones(3)
    inertial.correct_sensor_errors(first_time, inertial_errors)
    inertial_errors = inertial.request_sensor_errors(first_time)
    assert inertial_errors is not None
    assert np.allclose(inertial_errors.accel_biases, np.ones(3))


if __name__ == '__main__':
    test()
