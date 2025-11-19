from abc import abstractmethod
from collections.abc import Callable
from typing import Any

from aspn23 import (
    MeasurementPositionVelocityAttitude,
    MeasurementPositionVelocityAttitude as PVA,
    MeasurementPositionVelocityAttitudeErrorModel,
    TypeHeader,
    TypeTimestamp,
)
from numpy import array, float64
from numpy.typing import NDArray

from pntos.api import (
    EstimateWithCovariance,
    InertialInitializationStrategy,
    InertialPlugin,
    InitialInertialSolution,
    InitializationPlugin,
    InitializationStatus,
    LoggingLevel,
    Message,
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
        # Discard old messages
        log_func(
            LoggingLevel.DEBUG,
            f'Received old message at time {message_time * 1e-9:.9f}s on channel'
            + f' {message.source_identifier}. Filter is at time '
            + f'{fusion_engine.time.elapsed_nsec * 1e-9:.9f}s. Discarding message',
        )
        return False
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
) -> tuple[StandardInertialMechanization, InitialInertialSolution] | None:
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


class CacheEntry:
    """An entry in a cache storing a filter value at a specific time."""

    _value: Any | None
    _time_of_validity: TypeTimestamp | None
    _fusion_engine: StandardFusionEngine

    def __init__(self, fusion_engine: StandardFusionEngine) -> None:
        """Constructor.

        Args:
            fusion_engine (pntos.api.StandardFusionEngine): Filter instance used to get current time.
        """
        self._value = None
        self._time_of_validity = None
        self._fusion_engine = fusion_engine

    def is_valid(self) -> bool:
        """Check if cache entry is valid.

        Returns:
            True if entry exists at the current filter time, False otherwise.
        """
        return (
            self._time_of_validity is not None
            and self._time_of_validity.elapsed_nsec
            == self._fusion_engine.time.elapsed_nsec
        )

    @abstractmethod
    def recalculate(self, cache: 'Cache') -> None:
        """Recalculate the current cache entry.

        Args:
            cache (Cache): Cache in which this entry is stored. Can be used to grab entries that this entry is dependent on.
        """

    def clear(self) -> None:
        """Clear the current cache entry.

        Clearing an entry forces the stored value to be recalculated the next time it is requested.
        """
        self._value = None
        self._time_of_validity = None

    def get(self, cache: 'Cache') -> Any | None:  # noqa: ANN401
        """Get the current cache entry, recalculating if needed.

        Args:
            cache (Cache): Cache in which this entry is stored. Can be used to grab entries that this entry is dependent on.

        Returns:
            The current cache entry if available, otherwise None.
        """
        if not self.is_valid():
            self.recalculate(cache)
        return self._value


class InertialSolutionEntry(CacheEntry):
    """Cache entry for inertial solution."""

    _value: Message | None
    _inertial: StandardInertialMechanization

    def __init__(
        self,
        fusion_engine: StandardFusionEngine,
        inertial: StandardInertialMechanization,
        solution_channel: str,
        log_func: Callable[[LoggingLevel, str], None],
    ) -> None:
        """Constructor.

        Args:
            fusion_engine (pntos.api.StandardFusionEngine): Filter instance used to get current time.
            inertial (pntos.api.StandardInertialMechanization): Inertial instance used to get inertial solution at a specific time.
            solution_channel (str): Source identifier to attach to inertial solution.
            log_func (Callable[[LoggingLevel, str], None]): Function used for logging messages.
        """
        super().__init__(fusion_engine)
        self._inertial = inertial
        self._solution_channel = solution_channel
        self._log_func = log_func

    def recalculate(self, cache: 'Cache') -> None:
        """
        Calculate and store the inertial solution at the current filter time.

        Args:
            cache (Cache): Cache in which this entry is stored. Not needed for calculating inertial solution.

        """
        filter_time = self._fusion_engine.time
        solution = get_dead_reckoning_solution(
            self._inertial,
            filter_time,
            self._solution_channel,
            self._log_func,
        )

        self._value = solution
        self._time_of_validity = filter_time


class EstimateWithCovarianceEntry(CacheEntry):
    """Cache entry for state block estimate and covariance."""

    _value: EstimateWithCovariance | None
    _sb_label: str

    def __init__(
        self,
        fusion_engine: StandardFusionEngine,
        sb_label: str,
    ) -> None:
        """Constructor.

        Args:
            fusion_engine (pntos.api.StandardFusionEngine): Filter instance used to get current time and state block EstimateWithCovariance.
            sb_label (str): Label associated with the state block.
        """
        super().__init__(fusion_engine)
        self._sb_label = sb_label

    def recalculate(self, cache: 'Cache') -> None:
        """
        Calculate and store the state block estimate at the given time.

        Args:
            cache (Cache): Cache in which this entry is stored. Not needed for calculating estimate.
        """
        x_and_p = self._fusion_engine.generate_x_and_p([self._sb_label])

        if x_and_p is None:
            return

        self._value = x_and_p
        self._time_of_validity = self._fusion_engine.time


class FilterSolutionEntry(CacheEntry):
    """Cache entry for filter solution."""

    _value: Message | None
    _inertial_solution_key: str
    _pinson_x_and_p_key: str

    def __init__(
        self,
        fusion_engine: StandardFusionEngine,
        solution_channel: str,
        inertial_solution_key: str,
        pinson_x_and_p_key: str,
    ) -> None:
        """Constructor.

        Args:
            fusion_engine (pntos.api.StandardFusionEngine): Filter instance used to get current time.
            solution_channel (str): Source identifier to attach to filter solution.
            inertial_solution_key (str): Key associated with inertial solution cache entry.
            pinson_x_and_p_key (str): Key associated with pinson state block EstimateWithCovariance entry.
        """
        super().__init__(fusion_engine)
        self._solution_channel = solution_channel
        self._inertial_solution_key = inertial_solution_key
        self._pinson_x_and_p_key = pinson_x_and_p_key

    def recalculate(self, cache: 'Cache') -> None:
        """
        Calculate and store the filter solution at the given time.

        Args:
            cache (Cache): Cache in which this entry is stored. Used to grab inertial solution and pinson state block estimate, which are used to calculate the filter solution.
        """
        x_and_p: EstimateWithCovariance | None = cache.get(self._pinson_x_and_p_key)
        if x_and_p is None:
            return

        inertial_solution: Message | None = cache.get(self._inertial_solution_key)
        if inertial_solution is None:
            return

        assert isinstance(inertial_solution.wrapped_message, PVA)

        corr_pva = apply_error_states(
            inertial_solution.wrapped_message, x_and_p.estimate
        )
        corr_pva.covariance = x_and_p.covariance[:9, :9]

        self._value = Message(corr_pva, self._solution_channel)
        self._time_of_validity = self._fusion_engine.time


class Cache:
    """A container for storing entries of type CacheEntry."""

    def __init__(self) -> None:
        """Constructor."""
        self._entries: dict[str, CacheEntry] = {}

    def set(self, key: str, entry: CacheEntry) -> None:
        """Store cache entry.

        Args:
            key (str): Key associated with cache entry.
            entry (CacheEntry): The entry to store.
        """
        self._entries[key] = entry

    def get(self, key: str) -> Any:  # noqa: ANN401
        """Get a cache entry, recalculating it if necessary.

        Args:
            key (str): Key associated with entry to get.

        Raises:
            KeyError: If key does not exist in cache.

        Returns:
            Any: The entry associated with key.
        """
        if key not in self._entries:
            raise KeyError(f'Key "{key}" does not exist in cache.')

        return self._entries[key].get(self)

    def clear(self, key: str) -> None:
        """Clear a cache entry.

        Note that this doesn't remove the entry from the cache, but clears it such that
        the stored value must be recalculated the next time it is requested.

        Args:
            key (str): The key associated with the entry to clear.

        Raises:
            KeyError: If key does not exist in cache.
        """
        if key not in self._entries:
            raise KeyError(f'Key "{key}" does not exist in cache.')

        entry = self._entries[key]
        entry.clear()
