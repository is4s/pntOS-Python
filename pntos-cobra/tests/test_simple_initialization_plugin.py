import numpy as np
from aspn23 import (
    MeasurementPositionVelocityAttitude,
)
from pntos.api import (
    EwcInitializationStrategy,
    InertialInitializationStrategy,
    InitializationMotionNeeded,
    InitializationStatus,
    LoggingLevel,
)
from pntos.cobra import SimpleInitializationPlugin
from pntos.cobra.config.AlignmentConfig import AlignmentConfig
from pntos.cobra.SimpleControllerPlugin import SimpleMediator
from pntos.cobra.SimpleRegistryPlugin import SimpleRegistry


def dummy_log(level: LoggingLevel, message: str) -> None:
    pass


def test() -> None:
    # Setup
    registry = SimpleRegistry(dummy_log)
    mediator = SimpleMediator(registry, [])
    plugin = SimpleInitializationPlugin('Cobra simple initialization plugin')

    pos_var = (1, 2, 3)
    vel_var = (4, 5, 6)
    tilt_var = (7, 8, 9)
    accel_bias_var = (10, 11, 12)
    gyro_bias_var = (13, 14, 15)

    config = AlignmentConfig(
        initial_pos_var=pos_var,
        initial_vel_var=vel_var,
        initial_tilt_var=tilt_var,
        initial_accel_bias_var=accel_bias_var,
        initial_gyro_bias_var=gyro_bias_var,
    )

    # TODO (#43) Initialize registry from config object directly once it's supported.
    kvs = registry.batch_start(config.group)
    for attribute in config.__dict__:
        value = getattr(config, attribute)
        # Special case: convert tuples of floats to numpy arrays
        if isinstance(value, tuple):
            value = np.array(value)
        kvs.set_value(attribute, value)
    kvs.batch_end()

    assert plugin.identifier == 'Cobra simple initialization plugin'

    plugin.init_plugin(None, mediator)

    assert plugin.is_initialization_type_supported(InertialInitializationStrategy)
    assert not plugin.is_initialization_type_supported(EwcInitializationStrategy)

    # Create initialization strategy
    # TODO test with config
    aligner = plugin.new_initialization_strategy(
        InertialInitializationStrategy, config.group
    )
    assert aligner is not None
    assert aligner.request_current_status() == InitializationStatus.INITIALIZED_GOOD
    assert aligner.request_motion_needed() == InitializationMotionNeeded.ANY_MOTION

    solution = aligner.request_solution()

    assert solution.solution is not None
    assert solution.solution.source_identifier == 'Cobra simple initialization'

    pva: MeasurementPositionVelocityAttitude = solution.solution.wrapped_message
    assert pva.p1 == 0
    assert pva.p2 == 0
    assert pva.p3 == 0
    assert pva.v1 == 0
    assert pva.v2 == 0
    assert pva.v3 == 0
    assert pva.quaternion is not None
    assert np.allclose(pva.quaternion, np.zeros(4))
    assert np.allclose(pva.covariance, np.eye(9))

    assert solution.inertial_error_covariance is None
    assert solution.inertial_errors is None
    assert solution.status == InitializationStatus.INITIALIZED_GOOD


if __name__ == '__main__':
    test()
