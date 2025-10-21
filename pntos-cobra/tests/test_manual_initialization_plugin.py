import numpy as np
from aspn23 import (
    MeasurementPositionVelocityAttitude,
)
from navtk.navutils import quat_to_rpy
from pntos.api import (
    CommonPlugin,
    EwcInitializationStrategy,
    InertialInitializationStrategy,
    InitializationMotionNeeded,
    InitializationStatus,
    LoggingLevel,
    LoggingPlugin,
    Mediator,
)
from pntos.cobra import TutorialInitializationPlugin
from pntos.cobra.config import ManualAlignmentConfig, config_to_registry
from pntos.cobra.internal import StandardMediator, StandardRegistry


def dummy_log(level: LoggingLevel, message: str) -> None:
    pass


class DummyPlugin(CommonPlugin):
    def __init__(self, identifier: str) -> None:
        self.identifier = identifier

    def init_plugin(
        self,
        plugin_resources_location: str | None = None,
        mediator: Mediator | None = None,
    ) -> None:
        pass

    def shutdown_plugin(self) -> None:
        pass


def test() -> None:
    # Setup
    dummy_plugin = DummyPlugin('dummy plugin')
    registry = StandardRegistry(dummy_log)
    mediator = StandardMediator(dummy_plugin.identifier, LoggingPlugin)
    StandardMediator.registry = registry
    plugin = TutorialInitializationPlugin('Cobra simple initialization plugin')

    pos = (1, 2, 3)
    vel = (4, 5, 6)
    rpy = (0.123, 0.456, 0.789)
    accel_bias = (10, 11, 12)
    gyro_bias = (13, 14, 15)
    accel_scale_factor = (16, 17, 18)
    gyro_scale_factor = (19, 20, 21)

    time = 1.23

    pos_var = (10, 20, 30)
    vel_var = (40, 50, 60)
    tilt_var = (70, 80, 90)
    accel_bias_var = (100, 110, 120)
    gyro_bias_var = (130, 140, 150)
    accel_scale_factor_var = (160, 170, 180)
    gyro_scale_factor_var = (190, 200, 210)

    config = ManualAlignmentConfig(
        initial_pos=pos,
        initial_vel=vel,
        initial_rpy=rpy,
        initial_accel_bias=accel_bias,
        initial_gyro_bias=gyro_bias,
        initial_accel_scale_factor=accel_scale_factor,
        initial_gyro_scale_factor=gyro_scale_factor,
        initial_time=time,
        initial_pos_var=pos_var,
        initial_vel_var=vel_var,
        initial_tilt_var=tilt_var,
        initial_accel_bias_var=accel_bias_var,
        initial_gyro_bias_var=gyro_bias_var,
        initial_accel_scale_factor_var=accel_scale_factor_var,
        initial_gyro_scale_factor_var=gyro_scale_factor_var,
        group='test',
    )

    config_to_registry(config, mediator)

    assert plugin.identifier == 'Cobra simple initialization plugin'

    plugin.init_plugin(None, mediator)

    assert plugin.is_initialization_type_supported(InertialInitializationStrategy)
    assert not plugin.is_initialization_type_supported(EwcInitializationStrategy)

    # Create initialization strategy
    aligner = plugin.new_initialization_strategy(
        InertialInitializationStrategy, config.group
    )
    assert aligner is not None
    assert isinstance(aligner, InertialInitializationStrategy)
    assert aligner.request_current_status() == InitializationStatus.INITIALIZED_GOOD
    assert aligner.request_motion_needed() == InitializationMotionNeeded.ANY_MOTION

    solution = aligner.request_solution()

    assert solution.solution is not None
    assert solution.solution.source_identifier == 'Cobra simple initialization'

    pva = solution.solution.wrapped_message
    assert isinstance(pva, MeasurementPositionVelocityAttitude)
    assert int(time * 1e9) == pva.time_of_validity.elapsed_nsec
    assert (pva.p1, pva.p2, pva.p3) == pos
    assert (pva.v1, pva.v2, pva.v3) == vel
    assert pva.quaternion is not None
    assert np.allclose(quat_to_rpy(pva.quaternion), rpy)
    variances = np.concatenate(
        (np.array(pos_var), np.array(vel_var), np.array(tilt_var))
    )
    covariance = np.diag(variances)
    assert np.allclose(pva.covariance, covariance)

    assert solution.inertial_error_covariance is not None
    assert np.allclose(
        accel_bias_var,
        np.diagonal(solution.inertial_error_covariance[0:3, 0:3]),
    )
    assert np.allclose(
        gyro_bias_var, np.diagonal(solution.inertial_error_covariance[3:6, 3:6])
    )
    if len(solution.inertial_error_covariance) >= 9:
        assert np.allclose(
            accel_scale_factor_var,
            np.diagonal(solution.inertial_error_covariance[6:9, 6:9]),
        )
    if len(solution.inertial_error_covariance) >= 12:
        assert np.allclose(
            gyro_scale_factor_var,
            np.diagonal(solution.inertial_error_covariance[9:12, 9:12]),
        )
    assert solution.inertial_errors is not None
    assert np.allclose(solution.inertial_errors.accel_biases, np.array(accel_bias))
    assert np.allclose(solution.inertial_errors.gyro_biases, np.array(gyro_bias))
    assert np.allclose(
        solution.inertial_errors.accel_scale_factors,
        np.array(accel_scale_factor),
    )
    assert np.allclose(
        solution.inertial_errors.gyro_scale_factors, np.array(gyro_scale_factor)
    )
    assert solution.status == InitializationStatus.INITIALIZED_GOOD


if __name__ == '__main__':
    test()
