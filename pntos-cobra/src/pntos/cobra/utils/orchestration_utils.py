from typing import Callable, Tuple, Union

from aspn23 import (
    MeasurementPositionVelocityAttitude,
    MeasurementPositionVelocityAttitudeErrorModel,
    TypeHeader,
    TypeTimestamp,
)
from numpy import array, float64, zeros
from numpy.typing import NDArray
from scipy.linalg import block_diag

from pntos.api import (
    EstimateWithCovariance,
    InertialInitializationStrategy,
    InertialPlugin,
    InitialInertialSolution,
    InitializationPlugin,
    InitializationStatus,
    LoggingLevel,
    Message,
    Preprocessor,
    StandardFusionEngine,
    StandardInertialMechanization,
)

from .navigation import (
    correct_dcm_with_tilt,
    dcm_to_quat,
    east_to_delta_lon,
    north_to_delta_lat,
    quat_to_dcm,
)
from .plugins import SortedPlugins


def set_up_preprocessors(
    sorted_plugins: SortedPlugins,
    preprocessor_ids: list[str],
    preprocessor_groups: list[str],
) -> list[Preprocessor]:
    """
    Finds and creates a list of preprocessors based on the information in ``preprocessor_ids`` and ``preprocessor_groups``.

    Args:
        sorted_plugins (SortedPlugins): A `SortedPlugins` instance.
        preprocessor_ids (list[str]): The identifiers for the desired preprocessors (e.g. imu_rotator).
        preprocessor_groups (list[str]): Config groups that point to registry locations storing preprocessor information.

    Returns:
        list[Preprocessor]
    """
    preprocessors = []
    for identifier, config_group in zip(preprocessor_ids, preprocessor_groups):
        for plugin in sorted_plugins.preprocessor_plugins:
            for idx in range(len(plugin.preprocessor_identifiers)):
                if plugin.preprocessor_identifiers[idx] == identifier:
                    preprocessor = plugin.new_preprocessor(idx, config_group)
                    if preprocessor is not None:
                        preprocessors.append(preprocessor)
    return preprocessors


def set_up_initializer(
    initialization_plugin: InitializationPlugin,
    alignment_config_group: str,
    log_func: Callable[[LoggingLevel, str], None],
) -> InertialInitializationStrategy | None:
    """Set up inertial initialization strategy, and initialize filter solution if initializer is immediately ready."""
    # Set up initializer
    init_strategy: InertialInitializationStrategy | None = (
        initialization_plugin.new_initialization_strategy(
            InertialInitializationStrategy, config_group=alignment_config_group
        )
    )
    if init_strategy is None:
        log_func(
            LoggingLevel.ERROR,
            'InertialInitializationStrategy not supported by '
            + f'{initialization_plugin}. Unable to continue.',
        )
        return None
    return init_strategy


def initialization_ready(
    initialization_state: InitializationStatus,
    initializer: InertialInitializationStrategy,
) -> bool:
    """
    Utility function to poll the state of the init strategy plugin.

    Populates initialization_state with the relevant :class:`pntos.api.InitializationStatus`.
    """
    initialization_state = initializer.request_current_status()
    return initialization_state is InitializationStatus.INITIALIZED_GOOD


def send_inertial_aux_to_measurement_processor(
    inertial: StandardInertialMechanization,
    fusion_engine: StandardFusionEngine,
    time: TypeTimestamp,
    mp_label: str,
    log_func: Callable[[LoggingLevel, str], None],
) -> None:
    """Send the current inertial solution to the specified measurement processor."""
    pva_message = inertial.request_solution(time)
    if pva_message is None:
        log_func(
            LoggingLevel.ERROR,
            f'Cannot send inertial aux to measurement processor. Solution not available at time {time.elapsed_nsec / 1e9:.9f}s',
        )
        return
    imu = inertial.request_forces_and_rates(time)
    if imu is None:
        log_func(
            LoggingLevel.ERROR,
            f'Cannot send inertial aux to measurement processor. Forces and rates not available at time {time}',
        )
        return
    imu_message = Message(imu.forces_and_rates, 'Orchestration forces and rates')
    fusion_engine.give_measurement_processor_aux_data(
        mp_label, [pva_message, imu_message]
    )


def send_inertial_aux_to_pinson(
    inertial: StandardInertialMechanization,
    fusion_engine: StandardFusionEngine,
    sb_label: str,
    log_func: Callable[[LoggingLevel, str], None],
) -> None:
    """
    Send the current inertial solution, forces, and rates to the state block with the specified label.

    This aux data is needed by the Pinson15 state block to propagate.
    """
    time = fusion_engine.time

    pva_message = inertial.request_solution(time)
    if pva_message is None:
        log_func(
            LoggingLevel.ERROR,
            f'Cannot send inertial aux to pinson block. Solution not available at time {time.elapsed_nsec / 1e9:.9f}s',
        )
        return
    imu = inertial.request_forces_and_rates(time)
    if imu is None:
        log_func(
            LoggingLevel.ERROR,
            f'Cannot send inertial aux to pinson block. Forces not available at time {time.elapsed_nsec / 1e9:.9f}s',
        )
        return
    imu_message = Message(imu.forces_and_rates, 'Orchestration forces and rates')

    fusion_engine.give_state_block_aux_data(sb_label, [pva_message, imu_message])


def has_valid_time(
    init_solution: InitialInertialSolution | None,
    fusion_engine: StandardFusionEngine,
    message: Message,
    log_func: Callable[[LoggingLevel, str], None],
) -> bool:
    """
    Utility function which returns true if the message's time of validity is greater
    than the current fusion engine time.
    """
    # If we haven't received an initial solution, then any time counts:
    if init_solution is None:
        return True

    measurement = message.wrapped_message
    # get time - check for old messages
    if hasattr(measurement, 'time_of_validity'):
        message_time = measurement.time_of_validity.elapsed_nsec
        if fusion_engine.time.elapsed_nsec <= message_time:
            return True
        else:  # Discard old messages
            log_func(
                LoggingLevel.DEBUG,
                f'Received old message at time {message_time * 1e-9:.9f}s on channel'
                + f' {message.source_identifier}. Filter is at time '
                + f'{fusion_engine.time.elapsed_nsec * 1e-9:.9f}s. Discarding message',
            )
            return False
    else:
        log_func(
            LoggingLevel.ERROR,
            f'Measurement of type {type(measurement)} does not contain '
            + '"time_of_validity" field.',
        )
        return False


def get_dead_reckoning_solution(
    inertial: StandardInertialMechanization,
    time: TypeTimestamp,
    imu_sol_chan: str,
    log_func: Callable[[LoggingLevel, str], None],
) -> Message | None:
    """
    Utility function to request the IMU-only dead-reckoning solution. Returns
    ``None`` if the inertial is unable to provide a solution for the requested time.
    """
    message = inertial.request_solution(time)
    if message is not None:
        return Message(message.wrapped_message, imu_sol_chan)
    else:
        log_func(
            LoggingLevel.ERROR,
            'Unable to get PVA message from inertial.'
            + ' Cannot generate DEAD_RECKONING solution.',
        )
        return None


def get_best_solution(
    fusion_engine: StandardFusionEngine,
    inertial: StandardInertialMechanization,
    time: TypeTimestamp,
    sb_label: str,
    best_sol_chan: str,
    log_func: Callable[[LoggingLevel, str], None],
) -> Message | None:
    """
    Utility function to request the best fusion strategy solution. Returns
    ``None`` if the fusion engine is unable to provide a solution for the requested time.
    """

    x_and_p: EstimateWithCovariance | None = fusion_engine.peek_ahead(time, [sb_label])
    if x_and_p is None:
        log_func(
            LoggingLevel.WARN,
            f'Cannot get filter solution at time {time.elapsed_nsec * 1e-9:.9f}s. Filter is already at time {fusion_engine.time.elapsed_nsec * 1e-9:.9f}s.',
        )
        return None

    inertial_solution: Message | None = inertial.request_solution(time)

    if inertial_solution is None:
        log_func(
            LoggingLevel.ERROR,
            f'Unable to obtain solution from inertial at time {time.elapsed_nsec * 1e-9:.9f}s. Cannot generate BEST solution.',
        )
        return None

    if not isinstance(
        inertial_solution.wrapped_message,
        MeasurementPositionVelocityAttitude,
    ):
        log_func(
            LoggingLevel.ERROR,
            f'Expected PVA solution from inertial, but got type {type(inertial_solution.wrapped_message)}. Cannot generate BEST solution.',
        )
        return None

    corrected_pva = apply_error_states(
        inertial_solution.wrapped_message, x_and_p.estimate
    )

    covariance = x_and_p.covariance
    corrected_pva.covariance = covariance[:9, :9]

    return Message(corrected_pva, best_sol_chan)


def set_up_inertial_mechanization(
    initializer: InertialInitializationStrategy,
    inertial_plugin: InertialPlugin,
    inertial_group: str,
    log_func: Callable[[LoggingLevel, str], None],
) -> Union[Tuple[StandardInertialMechanization, InitialInertialSolution] | None]:
    """Get initial inertial solution and use it to set up the inertial."""
    init_solution = initializer.request_solution()

    if init_solution.solution is None:
        log_func(
            LoggingLevel.ERROR,
            'Invalid InitialInertialSolution returned from init strategy - unable to proceed.',
        )
        return None

    if not isinstance(
        init_solution.solution.wrapped_message,
        MeasurementPositionVelocityAttitude,
    ):
        log_func(
            LoggingLevel.ERROR,
            'Expected PVA solution from init strategy - unable to proceed.',
        )
        return None

    inertial_init_message = Message(
        init_solution.solution.wrapped_message, 'python orchestration'
    )

    inertial: StandardInertialMechanization | None = inertial_plugin.new_inertial(
        StandardInertialMechanization,
        inertial_init_message,
        inertial_group,
    )
    if inertial is None:
        log_func(
            LoggingLevel.ERROR,
            'StandardInertialMechanization not supported by inertial '
            + f'({inertial_plugin.identifier})',
        )
        return None

    if not (
        init_solution.inertial_errors is None
        or init_solution.inertial_error_covariance is None
    ):
        inertial.correct_sensor_errors(
            init_solution.solution.wrapped_message.time_of_validity,
            init_solution.inertial_errors,
        )
    return inertial, init_solution


def preprocess_message(
    message: Message,
    preprocessors: list[Preprocessor],
    log_func: Callable[[LoggingLevel, str], None],
) -> Message | None:
    """Process the given message by the full chain of preprocessors.

    Note: This function assumes all the preprocessors in the chain will either
    return 0 or 1 messages. Any additional messages will be ignored.

    Args:
        message (Message): The message to process.

    Returns:
        Message | None: The output message, or None if one of the preprocessors dropped the input message.
    """
    for preprocessor in preprocessors:
        messages = preprocessor.process_pntos_message(message)
        if not messages:
            return None
        elif len(messages) > 1:
            log_func(
                LoggingLevel.WARN,
                f'Preprocessor {preprocessor} returned {len(messages)} messages. Ignoring all but the first.',
            )
        message = messages[0]

    return message


def initialize_filter(
    init_solution: InitialInertialSolution,
    fusion_engine: StandardFusionEngine,
    sb_label: str,
    log_func: Callable[[LoggingLevel, str], None],
) -> None:
    """Update the fusion engine with inertial information to initialize filter."""
    # asserting because the error is handled in set_up_inertial_mechanization
    assert isinstance(init_solution.solution, Message)
    assert isinstance(
        init_solution.solution.wrapped_message,
        MeasurementPositionVelocityAttitude,
    )
    pva_cov = init_solution.solution.wrapped_message.covariance  # 9x9
    bias_cov = init_solution.inertial_error_covariance  # 6x6
    init_pinson_cov = block_diag(pva_cov, bias_cov)
    fusion_engine.set_state_block_covariance(
        sb_label,
        init_pinson_cov,
    )

    init_time = init_solution.solution.wrapped_message.time_of_validity
    fusion_engine.time = init_time

    log_func(
        LoggingLevel.INFO,
        f'Aligned filter at {init_time.elapsed_nsec * 1e-9:.9f}s.',
    )


def dispatch_to_fusion_engine(
    inertial: StandardInertialMechanization,
    fusion_engine: StandardFusionEngine,
    message: Message,
    sb_label: str,
    measurement_channels: dict[str, str],
    log_func: Callable[[LoggingLevel, str], None],
) -> None:
    """
    Send message to the fusion engine to update the filter.

    Applies feedback to inertial solution and biases, and resets pinson error states
    afterward.
    """
    meas_time = message.wrapped_message.time_of_validity  # type: ignore[attr-defined]
    # Make sure measurement processor has most current aux data before update
    mp_label = measurement_channels[message.source_identifier]
    send_inertial_aux_to_measurement_processor(
        inertial, fusion_engine, meas_time, mp_label, log_func
    )
    send_inertial_aux_to_pinson(inertial, fusion_engine, sb_label, log_func)

    # Propagate to measurement time
    fusion_engine.propagate(meas_time)

    # Update filter.
    fusion_engine.update(mp_label, message)

    # Feedback states to inertial.
    estimate = fusion_engine.get_state_block_estimate(sb_label)
    if estimate is None:
        log_func(
            LoggingLevel.ERROR,
            'Unable to obtain estimate from fusion engine.',
        )
        return

    cur_time = fusion_engine.time
    inertial_pva_message = inertial.request_solution(cur_time)

    if inertial_pva_message is None:
        log_func(
            LoggingLevel.ERROR,
            f'Unable to obtain solution from inertial at time {cur_time.elapsed_nsec / 1e9:.9f}s.',
        )
        return

    if not isinstance(
        inertial_pva_message.wrapped_message,
        MeasurementPositionVelocityAttitude,
    ):
        log_func(
            LoggingLevel.ERROR,
            'Did not receive PVA message from inertial. Received '
            + f'{type(inertial_pva_message.wrapped_message)} instead.',
        )
        return

    inertial_pva = inertial_pva_message.wrapped_message

    corrected_pva = apply_error_states(inertial_pva, estimate)

    message = Message(corrected_pva, 'python orchestration')

    inertial.reset_solution(message)

    imu_errors = inertial.request_sensor_errors(cur_time)
    if imu_errors is None:
        log_func(
            LoggingLevel.ERROR,
            f'Unable to obtain sensor errors from inertial at time {cur_time.elapsed_nsec / 1e9:.9f}s.',
        )
        return

    imu_errors.accel_biases -= estimate[9:12, 0]
    imu_errors.gyro_biases -= estimate[12:15, 0]
    inertial.correct_sensor_errors(cur_time, imu_errors)

    # Assume zero error in states after applying feedback
    fusion_engine.set_state_block_estimate(sb_label, zeros((15, 1)))


def apply_error_states(
    pva: MeasurementPositionVelocityAttitude, x: NDArray[float64]
) -> MeasurementPositionVelocityAttitude:
    """
    Correct the inertial's PVA message with the fusion engine's error estimate.

    Args:
        pva (MeasurementPositionVelocityAttitude): The PVA message originating from the inertial solution.
        x (NDArray[float64]): The error estimate originating from the fusion engine's state block.
    """
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
