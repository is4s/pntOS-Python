from math import isclose

import numpy as np
from aspn23 import (
    MeasurementImu,
    MeasurementImuImuType,
    MeasurementPosition,
    MeasurementPositionErrorModel,
    MeasurementPositionReferenceFrame,
    MeasurementPositionVelocityAttitude,
    TypeHeader,
    TypeTimestamp,
)
from navtk.filtering import hg1700_model
from navtk.navutils import quat_to_rpy
from pntos.api import (
    EwcInitializationStrategy,
    InertialInitializationStrategy,
    InitializationMotionNeeded,
    InitializationPlugin,
    InitializationStatus,
    LoggingLevel,
    Message,
)
from pntos.cobra import StaticAlignInitializationPlugin
from pntos.cobra.config import config_to_registry, imu_model_to_config
from pntos.cobra.config.ManualHeadingAlignmentConfig import (
    ManualHeadingAlignmentConfig,
)
from pntos.cobra.config.StaticAlignmentConfig import (
    AlignmentStrategy,
    StaticAlignmentConfig,
)
from pntos.cobra.internal import SimpleMediator, StandardRegistry


def generate_header() -> TypeHeader:
    return TypeHeader(0, 0, 0, 0)


LATITUDE = 1
LONGITUDE = 2
ALTITUDE = 3


def generate_position(time: TypeTimestamp) -> Message:
    header = generate_header()
    position = MeasurementPosition(
        header,
        time,
        MeasurementPositionReferenceFrame.GEODETIC,
        LATITUDE,
        LONGITUDE,
        ALTITUDE,
        np.eye(3),
        MeasurementPositionErrorModel.NONE,
        np.array([]),
        [],
    )
    return Message(position, '')


def generate_imu(time: TypeTimestamp) -> Message:
    header = generate_header()
    dt = 1e-2  # 100Hz
    imu = MeasurementImu(
        header,
        time,
        MeasurementImuImuType.INTEGRATED,
        # Force mainly due to gravity, but nonzero in all axes to avoid singularities
        np.array([1e-12, 1e-12, -9.81]) * dt,
        # Zeroes, except for a bit in the y-axis to simulate earth's rotation (magnitude of vector
        # is less important than direction for this test). Nonzero values to avoid singularities in
        # covariance calculation.
        np.array([1e-12, 1e-4, 1e-12]) * dt,
        [],
    )
    return Message(imu, '')


def _test_aligner(
    plugin: StaticAlignInitializationPlugin,
    config_group: str,
    static_time: float,
    strategy: AlignmentStrategy,
) -> None:
    # Create initialization strategy
    aligner = plugin.new_initialization_strategy(
        InertialInitializationStrategy, config_group
    )
    assert aligner is not None
    assert aligner.request_current_status() == InitializationStatus.INITIALIZING_COARSE
    assert aligner.request_motion_needed() == InitializationMotionNeeded.NO_MOTION
    solution = aligner.request_solution()
    assert solution.solution is None
    assert solution.inertial_error_covariance is None
    assert solution.inertial_errors is None
    assert solution.status == InitializationStatus.INITIALIZING_COARSE

    # Process messages until alignment
    pos_dt_centiseconds = 100  # 1 Hz
    align_time_centiseconds = int(static_time) * 100
    for ii in range(align_time_centiseconds + 1):
        time = TypeTimestamp(ii * 10000000)  # convert centiseconds to nanoseconds
        aligner.process_pntos_message(generate_imu(time))
        # Add a position measurement every 100 iterations (but not on the last, since it has aligned
        # already)
        if ii % pos_dt_centiseconds == 0 and ii != align_time_centiseconds:
            aligner.process_pntos_message(generate_position(time))

    assert aligner.request_current_status() == InitializationStatus.INITIALIZED_GOOD
    solution = aligner.request_solution()

    assert solution.solution is not None
    assert solution.solution.source_identifier == 'Cobra initializer'

    pva: MeasurementPositionVelocityAttitude = solution.solution.wrapped_message
    assert pva.time_of_validity.elapsed_nsec == align_time_centiseconds * 10000000
    assert pva.p1 is not None
    assert pva.p2 is not None
    assert pva.p3 is not None
    assert isclose(pva.p1, LATITUDE)
    assert isclose(pva.p2, LONGITUDE)
    assert isclose(pva.p3, ALTITUDE)
    assert pva.v1 == 0
    assert pva.v2 == 0
    assert pva.v3 == 0
    assert pva.quaternion is not None
    rpy = quat_to_rpy(pva.quaternion)
    # Should be level, but facing the direction of the earth's rotation.
    assert np.allclose(rpy, np.array([0, 0, -np.pi / 2]))

    # Check PVA covariance
    covariance = pva.covariance
    np.fill_diagonal(covariance, 0)
    assert np.allclose(covariance, np.zeros((9, 9)))

    # Check IMU error covariance
    covariance = solution.inertial_error_covariance
    np.fill_diagonal(covariance, 0)
    assert np.allclose(covariance, np.zeros((6, 6)))

    if strategy == AlignmentStrategy.STATIC:
        assert solution.inertial_errors is None
    else:
        assert solution.inertial_errors is not None

    assert solution.status == InitializationStatus.INITIALIZED_GOOD


def dummy_log(level: LoggingLevel, message: str) -> None:
    pass


def test() -> None:
    # Set up registry and mediator
    plugin = StaticAlignInitializationPlugin('Cobra static align initialization plugin')

    registry = StandardRegistry(dummy_log)
    mediator = SimpleMediator(plugin.identifier, InitializationPlugin)
    SimpleMediator.registry = registry

    # Set up and test plugin.
    plugin.init_plugin(None, mediator)

    assert plugin.identifier == 'Cobra static align initialization plugin'
    assert plugin.is_initialization_type_supported(InertialInitializationStrategy)
    assert not plugin.is_initialization_type_supported(EwcInitializationStrategy)

    # Create config for pure static alignment and test pure static alignment.
    static_time = 120.0
    group = 'test/config/static_align'
    imu_config = imu_model_to_config(
        model=hg1700_model(),
        group=group,
    )
    config = StaticAlignmentConfig(
        strategy=AlignmentStrategy.STATIC,
        static_time=static_time,
        imu_model=imu_config,
        group=group,
    )
    config_to_registry(config, mediator)
    _test_aligner(plugin, group, config.static_time, config.strategy)

    # Modify config for manual heading alignment and test it.
    config.strategy = AlignmentStrategy.MANUAL_HEADING
    config_to_registry(config, mediator)

    heading_config = ManualHeadingAlignmentConfig(
        heading=-np.pi / 2, heading_sigma=0.017453292519943295, group=group
    )
    config_to_registry(heading_config, mediator)
    _test_aligner(plugin, group, config.static_time, config.strategy)


if __name__ == '__main__':
    test()
