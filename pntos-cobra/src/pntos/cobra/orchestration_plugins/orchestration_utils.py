from aspn23 import (
    MeasurementImu,
    MeasurementPositionVelocityAttitude,
    MeasurementPositionVelocityAttitudeErrorModel,
    TypeHeader,
    TypeTimestamp,
)
from numpy import array, float64, zeros
from numpy.typing import NDArray
from pntos.api import (
    CommonPlugin,
    InertialInitializationStrategy,
    InitializationStatus,
    LoggingLevel,
    Message,
    StandardInertialMechanization,
)
from pntos.cobra.utils import (
    SortedPlugins,
    correct_dcm_with_tilt,
    dcm_to_quat,
    east_to_delta_lon,
    north_to_delta_lat,
    quat_to_dcm,
    sort_plugins_dataclass,
)
from scipy.linalg import block_diag

from .SimpleGpsOrchestrationPlugin import SimpleGpsOrchestrationPlugin
from .SimpleGpsVelOrchestrationPlugin import SimpleGpsVelOrchestrationPlugin


def sort_and_validate_plugins(
    orch_plugin: SimpleGpsOrchestrationPlugin | SimpleGpsVelOrchestrationPlugin,
    plugin_list: list[CommonPlugin],
) -> None:
    """
    Utility function to sort plugins_list and make sure there is only one of the
    following plugins:
    - FusionPlugin
    - FusionStrategyPlugin
    - InertialPlugin
    - InitializationPlugin
    - StateModelingPlugin
    """
    sorted_plugins: SortedPlugins = sort_plugins_dataclass(plugin_list)
    # Fusion Plugin
    if len(sorted_plugins.fusion_plugins) != 1:
        orch_plugin._log(
            LoggingLevel.ERROR,
            f'Expected one FusionPlugin - received {len(sorted_plugins.fusion_plugins)}'
            + f': {[p.identifier for p in sorted_plugins.fusion_plugins]}',
        )
        return
    orch_plugin.fusion_plugin = sorted_plugins.fusion_plugins[0]

    # Fusion Strategy Plugin
    if len(sorted_plugins.fusion_strategy_plugins) != 1:
        orch_plugin._log(
            LoggingLevel.ERROR,
            'Expected one FusionStrategyPlugin - received '
            + f'{len(sorted_plugins.fusion_strategy_plugins)}',
        )
        return
    orch_plugin.fusion_strategy_plugin = sorted_plugins.fusion_strategy_plugins[0]

    # Inertial Plugin
    if len(sorted_plugins.inertial_plugins) != 1:
        orch_plugin._log(
            LoggingLevel.ERROR,
            f'Expected one InertialPlugin - received '
            + f'{len(sorted_plugins.inertial_plugins)}',
        )
        return
    orch_plugin.inertial_plugin = sorted_plugins.inertial_plugins[0]

    # Initialization Plugin
    if len(sorted_plugins.initialization_plugins) != 1:
        orch_plugin._log(
            LoggingLevel.ERROR,
            'Expected one InitializationPlugin - received '
            + f'{len(sorted_plugins.initialization_plugins)}',
        )
        return
    orch_plugin.initialization_plugin = sorted_plugins.initialization_plugins[0]

    # State Modeling Plugin
    if len(sorted_plugins.state_modeling_plugins) == 0:
        orch_plugin._log(
            LoggingLevel.ERROR,
            f'Expected at least one StateModelingPlugin - received none.',
        )
        return
    orch_plugin.state_modeling_plugins = sorted_plugins.state_modeling_plugins


def set_up_initializer(
    orch_plugin: SimpleGpsOrchestrationPlugin | SimpleGpsVelOrchestrationPlugin,
    alignment_config_group: str,
) -> None:
    """Set up inertial initialization strategy, and initialize filter solution if initializer is immediately ready."""
    # Set up initializer
    init_strategy: InertialInitializationStrategy | None = (
        orch_plugin.initialization_plugin.new_initialization_strategy(
            InertialInitializationStrategy, config_group=alignment_config_group
        )
    )
    if init_strategy is None:
        orch_plugin._log(
            LoggingLevel.ERROR,
            'InertialInitializationStrategy not supported by '
            + f'{orch_plugin.initialization_plugin}. Unable to continue.',
        )
        return None
    orch_plugin.initializer = init_strategy


def initialization_ready(
    orch_plugin: SimpleGpsOrchestrationPlugin | SimpleGpsVelOrchestrationPlugin,
) -> bool:
    """
    Utility function to poll the state of the init strategy plugin.

    Populates orch_plugin.initialization_state with the relevant :class:`InitializationStatus`.
    """
    orch_plugin.initialization_state = orch_plugin.initializer.request_current_status()
    return orch_plugin.initialization_state is InitializationStatus.INITIALIZED_GOOD


def send_inertial_aux_to_measurement_processor(
    orch_plugin: SimpleGpsOrchestrationPlugin | SimpleGpsVelOrchestrationPlugin,
    time: TypeTimestamp,
    mp_label: str,
) -> None:
    """Send the current inertial solution to the specified measurement processor."""
    pva_message = orch_plugin.inertial.request_solution(time)
    if pva_message is None:
        orch_plugin._log(
            LoggingLevel.ERROR,
            f'Cannot send inertial aux to measurement processor. Solution not available at time {time}',
        )
        return
    orch_plugin.fusion_engine.give_measurement_processor_aux_data(
        mp_label, [pva_message]
    )


def send_inertial_aux_to_pinson(
    orch_plugin: SimpleGpsOrchestrationPlugin | SimpleGpsVelOrchestrationPlugin,
    sb_label: str,
) -> None:
    """Send the current inertial solution and forces to the Pinson15 state-block."""
    time = orch_plugin.fusion_engine.time

    pva_message = orch_plugin.inertial.request_solution(time)
    if pva_message is None:
        orch_plugin._log(
            LoggingLevel.ERROR,
            f'Cannot send inertial aux to pinson block. Solution not available at time {time}',
        )
        return
    imu = orch_plugin.inertial.request_forces_and_rates(time)
    if imu is None:
        orch_plugin._log(
            LoggingLevel.ERROR,
            f'Cannot send inertial aux to pinson block. Forces not available at time {time}',
        )
        return
    imu_message = Message(imu.forces_and_rates, 'Orchestration forces and rates')

    orch_plugin.fusion_engine.give_state_block_aux_data(
        sb_label, [pva_message, imu_message]
    )


def rotate_imu_meas(
    orch_plugin: SimpleGpsOrchestrationPlugin | SimpleGpsVelOrchestrationPlugin,
    imu: MeasurementImu,
) -> None:
    """Rotate IMU measurement into platform frame.

    Args:
        message (MeasurementImu): IMU ASPN message to rotate.
    """
    imu.meas_accel = orch_plugin.C_inertial_to_platform @ imu.meas_accel
    imu.meas_gyro = orch_plugin.C_inertial_to_platform @ imu.meas_gyro


def generate_initial_inertial_solution(
    orch_plugin: SimpleGpsOrchestrationPlugin | SimpleGpsVelOrchestrationPlugin,
    sb_label: str,
    inertial_group: str,
) -> None:
    """Get initial inertial solution and use it to set up the inertial."""
    orch_plugin.init_solution = orch_plugin.initializer.request_solution()

    if (
        orch_plugin.init_solution.solution is None
        or orch_plugin.init_solution.inertial_errors is None
        or orch_plugin.init_solution.inertial_error_covariance is None
    ):
        orch_plugin._log(
            LoggingLevel.ERROR,
            'Invalid InitialInertialSolution returned from init strategy - unable to proceed.',
        )
        return

    if not isinstance(
        orch_plugin.init_solution.solution.wrapped_message,
        MeasurementPositionVelocityAttitude,
    ):
        orch_plugin._log(
            LoggingLevel.ERROR,
            'Expected PVA solution from init strategy - unable to proceed.',
        )
        return

    inertial_init_message = Message(
        orch_plugin.init_solution.solution.wrapped_message, 'python orchestration'
    )

    inertial: StandardInertialMechanization | None = (
        orch_plugin.inertial_plugin.new_inertial(
            StandardInertialMechanization,
            inertial_init_message,
            inertial_group,
        )
    )
    if inertial is None:
        orch_plugin._log(
            LoggingLevel.ERROR,
            'StandardInertialMechanization not supported by inertial '
            + f'({orch_plugin.inertial_plugin.identifier})',
        )
        return

    orch_plugin.inertial = inertial

    orch_plugin.inertial.correct_sensor_errors(
        orch_plugin.init_solution.solution.wrapped_message.time_of_validity,
        orch_plugin.init_solution.inertial_errors,
    )

    pva_cov = orch_plugin.init_solution.solution.wrapped_message.covariance  # 9x9
    bias_cov = orch_plugin.init_solution.inertial_error_covariance  # 6x6
    init_pinson_cov = block_diag(pva_cov, bias_cov)
    orch_plugin.fusion_engine.set_state_block_covariance(
        sb_label,
        init_pinson_cov,
    )

    init_time = orch_plugin.init_solution.solution.wrapped_message.time_of_validity
    orch_plugin.fusion_engine.time = init_time

    orch_plugin._send_inertial_aux_to_pinson()

    orch_plugin._log(
        LoggingLevel.INFO,
        f'Aligned filter at {init_time}.',
    )


def dispatch_to_fusion_engine(
    orch_plugin: SimpleGpsOrchestrationPlugin | SimpleGpsVelOrchestrationPlugin,
    message: Message,
    sb_label: str,
) -> None:
    """Send message to the fusion engine to update the filter.

    Applies feedback to inertial solution and biases, and resets pinson error states
    afterward."""
    meas_time = message.wrapped_message.time_of_validity  # type: ignore[attr-defined]
    # Make sure measurement processor has most current aux data before update
    mp_label = orch_plugin.measurement_channels[message.source_identifier]
    send_inertial_aux_to_measurement_processor(orch_plugin, meas_time, mp_label)
    send_inertial_aux_to_pinson(orch_plugin, sb_label)

    # Propagate to measurement time
    orch_plugin.fusion_engine.propagate(meas_time)

    # Update filter.
    orch_plugin.fusion_engine.update(mp_label, message)

    # Feedback states to inertial.
    estimate = orch_plugin.fusion_engine.get_state_block_estimate(sb_label)
    if estimate is None:
        orch_plugin._log(
            LoggingLevel.ERROR,
            'Unable to obtain estimate from fusion engine.',
        )
        return

    cur_time = orch_plugin.fusion_engine.time
    inertial_pva_message = orch_plugin.inertial.request_solution(cur_time)

    if inertial_pva_message is None:
        orch_plugin._log(
            LoggingLevel.ERROR,
            f'Unable to obtain solution from inertial at time {cur_time}.',
        )
        return

    if not isinstance(
        inertial_pva_message.wrapped_message,
        MeasurementPositionVelocityAttitude,
    ):
        orch_plugin._log(
            LoggingLevel.ERROR,
            'Did not receive PVA message from inertial. Received '
            + f'{type(inertial_pva_message.wrapped_message)} instead.',
        )
        return

    inertial_pva = inertial_pva_message.wrapped_message

    corrected_pva = apply_error_states(inertial_pva, estimate)

    message = Message(corrected_pva, 'python orchestration')

    orch_plugin.inertial.reset_solution(message)

    imu_errors = orch_plugin.inertial.request_sensor_errors(cur_time)
    if imu_errors is None:
        orch_plugin._log(
            LoggingLevel.ERROR,
            f'Unable to obtain sensor errors from inertial at time {cur_time}.',
        )
        return

    imu_errors.accel_biases -= estimate[9:12, 0]
    imu_errors.gyro_biases -= estimate[12:15, 0]
    orch_plugin.inertial.correct_sensor_errors(cur_time, imu_errors)

    # Assume zero error in states after applying feedback
    orch_plugin.fusion_engine.set_state_block_estimate(sb_label, zeros((15, 1)))


def apply_error_states(
    pva: MeasurementPositionVelocityAttitude, x: NDArray[float64]
) -> MeasurementPositionVelocityAttitude:
    """Correct PVA using inertial PVA error states."""
    # These fields should never be None unless we already encountered a different
    # error, so assert instead of log
    assert (
        pva.p1 is not None
        and pva.p2 is not None
        and pva.p3 is not None
        and pva.v1 is not None
        and pva.v2 is not None
        and pva.v3 is not None
        and pva.quaternion is not None
    )

    return MeasurementPositionVelocityAttitude(
        TypeHeader(
            pva.header.vendor_id,
            pva.header.device_id,
            pva.header.context_id,
            pva.header.sequence_id,
        ),
        TypeTimestamp(pva.time_of_validity.elapsed_nsec),
        pva.reference_frame,
        pva.p1 + north_to_delta_lat(x[0, 0], pva.p1, pva.p3),
        pva.p2 + east_to_delta_lon(x[1, 0], pva.p1, pva.p3),
        pva.p3 - x[2, 0],
        pva.v1 + x[3, 0],
        pva.v2 + x[4, 0],
        pva.v3 + x[5, 0],
        dcm_to_quat(correct_dcm_with_tilt(quat_to_dcm(pva.quaternion), x[6:9, 0])),
        pva.covariance.copy(),
        MeasurementPositionVelocityAttitudeErrorModel.NONE,
        array([]),
        [],
    )
