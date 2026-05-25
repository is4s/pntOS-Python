from copy import deepcopy

import numpy as np
from aspn23 import MeasurementPositionVelocityAttitude as Pva
from pntos.api import (
    InertialInitializationStrategy,
    InitialInertialSolution,
    InitializationMotionNeeded,
    InitializationPlugin,
    InitializationStatus,
    InitializationType,
    LoggingLevel,
    Mediator,
    Message,
    StandardInertialErrors,
)
from pntos.cobra.config import PvaMessageInitializationConfig, config_from_registry

NSEC_PER_SEC = 1_000_000_000


class PvaMessageInitialization(InertialInitializationStrategy):
    """Grabs initial solution from incoming PVA measurement(s)."""

    config_group: str
    mediator: Mediator
    _initial_solution: InitialInertialSolution

    def __init__(
        self,
        mediator: Mediator,
        start_time: float | None,
        initial_pva_channel: str,
        initial_pva_sigma: tuple[
            float, float, float, float, float, float, float, float, float
        ]
        | None,
        accel_bias_sigma: tuple[float, float, float],
        gyro_bias_sigma: tuple[float, float, float],
    ) -> None:
        """
        Constructor.

        Args:
            config_group (str): A :class:`~pntos.cobra.config.PvaMessageAlignmentWithDataConfig` config group.
            mediator (Mediator): A :class:`~pntos.api.Mediator` instance.
        """
        self.mediator = mediator

        self._pva_channel = initial_pva_channel
        self._start_time_ns = (
            int(start_time * NSEC_PER_SEC) if start_time is not None else None
        )
        self._initial_pva_cov = (
            np.diag(np.square(initial_pva_sigma))
            if initial_pva_sigma is not None
            else None
        )
        self._initial_imu_errors = StandardInertialErrors(
            accel_biases=np.zeros(3),
            gyro_biases=np.zeros(3),
            accel_scale_factors=np.zeros(3),
            gyro_scale_factors=np.zeros(3),
        )
        self._initial_imu_error_covariance = np.diag(
            np.square(
                np.concatenate(
                    (
                        np.array(accel_bias_sigma),
                        np.array(gyro_bias_sigma),
                    )
                )
            )
        )

        self._status = InitializationStatus.WAITING

    def request_motion_needed(self) -> InitializationMotionNeeded:
        return InitializationMotionNeeded.ANY_MOTION

    def request_current_status(self) -> InitializationStatus:
        return self._status

    def process_pntos_message(self, message: Message) -> None:
        """Receive PVA from which to set initial solution."""
        if message.source_identifier != self._pva_channel:
            return

        if not isinstance(message.wrapped_message, Pva):
            self.mediator.log_message(
                LoggingLevel.WARN,
                f'PvaMessageInitialization expected message of type {Pva.__name__}, but got {type(message.wrapped_message).__name__}. Cannot process message.',
            )
            return

        cur_time_ns = message.wrapped_message.time_of_validity.elapsed_nsec

        if self._start_time_ns is not None and cur_time_ns < self._start_time_ns:
            # PVA occurs before start time
            return

        # Initialize from current PVA
        initial_pva = deepcopy(message.wrapped_message)
        if self._initial_pva_cov:
            # Override PVA covariance
            initial_pva.covariance = self._initial_pva_cov

        self._initial_solution = InitialInertialSolution(
            solution=Message(initial_pva, 'Initial PVA'),
            inertial_errors=self._initial_imu_errors,
            inertial_error_covariance=self._initial_imu_error_covariance,
            status=InitializationStatus.INITIALIZED_GOOD,
        )

        self._status = InitializationStatus.INITIALIZED_GOOD

    def request_solution(self) -> InitialInertialSolution:
        """Get the initial PVA."""
        return self._initial_solution


class PvaMessageInitializationPlugin(InitializationPlugin):
    """An initialization plugin that generates :class:`~internal.PvaMessageInitialization` instances."""

    mediator: Mediator

    def __init__(self, identifier: str) -> None:
        """
        Cobra Standard Initialization Plugin.

        Args:
            identifier (str): The plugin identifier passed to the
                :attr:`~pntos.api.CommonPlugin.identifier` field.
        """
        self.identifier = identifier

    def init_plugin(
        self,
        plugin_resources_location: str | None = None,
        mediator: Mediator | None = None,
    ) -> None:
        assert mediator is not None
        self.mediator = mediator

    def shutdown_plugin(self) -> None:
        return

    def is_initialization_type_supported(self, itype: InitializationType) -> bool:
        return itype is InertialInitializationStrategy

    def new_initialization_strategy(
        self, type: type[InitializationType], config_group: str | None = None
    ) -> InitializationType | None:
        if issubclass(type, InertialInitializationStrategy):
            if config_group is None:
                self.mediator.log_message(
                    LoggingLevel.ERROR,
                    'new_initialization_strategy() requires valid config_group, got None.',
                )
                return None

            config = config_from_registry(
                PvaMessageInitializationConfig, self.mediator, config_group
            )
            if config is None:
                self.mediator.log_message(
                    LoggingLevel.ERROR,
                    'new_initialization_strategy() could not extract PvaMessageInitializationConfig to create PvaMessageInitialization',
                )
                return None

            return PvaMessageInitialization(
                self.mediator,
                config.start_time,
                config.initial_pva_channel,
                config.initial_pva_sigma,
                config.initial_accel_bias_sigma,
                config.initial_gyro_bias_sigma,
            )

        self.mediator.log_message(LoggingLevel.ERROR, 'Unsupported type requested.')
        return None
