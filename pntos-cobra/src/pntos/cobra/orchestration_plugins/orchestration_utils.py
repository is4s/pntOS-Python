from aspn23 import (
    MeasurementPositionVelocityAttitude,
    MeasurementPositionVelocityAttitudeErrorModel,
    TypeHeader,
    TypeTimestamp,
)
from numpy import array, float64, zeros
from numpy.typing import NDArray
from pntos.api import (
    CommonPlugin,
    LoggingLevel,
    Message,
    OrchestrationPlugin,
)
from pntos.cobra.utils import (
    SortedPlugins,
    sort_plugins_dataclass,
    correct_dcm_with_tilt,
    dcm_to_quat,
    east_to_delta_lon,
    north_to_delta_lat,
    quat_to_dcm,
)


def sort_and_validate_plugins(
    orch_plugin: OrchestrationPlugin,
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


def send_inertial_aux_to_measurement_processor(
    orch_plugin: OrchestrationPlugin, time: TypeTimestamp, mp_label: str
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
    orch_plugin: OrchestrationPlugin, sb_label: str
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


def dispatch_to_fusion_engine(
    orch_plugin: OrchestrationPlugin,
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
