"""Python API of pntOS."""

from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from aspn23 import TypeTimestamp
from numpy.typing import NDArray

from .common import CommonPlugin, EstimateWithCovariance, Message
from .inertial import StandardInertialErrors


class InitializationStatus(Enum):
    """
    An enumeration that allows the user to know the initialization status.

    Caution:
        **Unstable**: This feature is unstable and is not yet considered part of the stable pntOS
        API. Usage of this feature is highly discouraged in non-experimental code, and its
        definition may change at any time.
    """

    WAITING = 0
    """Waiting to start initialization process."""

    INITIALIZING_COARSE = 1
    """Attempting to initialize and produce a navigation solution."""

    INITIALIZING_FINE = 2
    """
    A coarse initialization has been calculated by the algorithm, and the initialization is being
	tested or adjusted before producing a navigation solution.
    """

    INITIALIZED_GOOD = 3
    """
    We have a good initialization.

    The provided solution can be used to kickoff inertial and fusion.
    """

    INITIALIZATION_FAILED = 4
    """The initialization process failed in some way, and may attempt to restart."""


class InitializationMotionNeeded(Enum):
    """
    An enumeration that specifies what type of motion is required by the initialization strategy.

    Caution:
        **Unstable**: This feature is unstable and is not yet considered part of the stable pntOS
        API. Usage of this feature is highly discouraged in non-experimental code, and its
        definition may change at any time.
    """

    NO_MOTION = 0
    """Stationary data is needed."""

    MOTION_NEEDED = 1
    """Dynamic data is needed."""

    ANY_MOTION = 2
    """No particular type of motion is required."""


class CommonInitializationStrategy(Protocol):
    """
    A common base type for initialization algorithms.

    Caution:
        **Unstable**: This feature is unstable and is not yet considered part of the stable pntOS
        API. Usage of this feature is highly discouraged in non-experimental code, and its
        definition may change at any time.
    """

    def request_motion_needed(self) -> InitializationMotionNeeded:
        """
        Check the type of motion (if any) needed.

        Returns:
            InitializationMotionNeeded
        """
        pass

    def request_current_status(self) -> InitializationStatus:
        """
        Check the current initialization status.

        Returns:
            InitializationStatus
        """
        pass

    def process_pntos_message(self, message: Message) -> None:
        """
        Incorporate a new message into the initialization algorithm.

        Args:
            message (Message)
        """
        pass


@dataclass
class InitialInertialSolution:
    """
    Holds both the current solution, inertial errors (and their covariance), and the current status.

    Coupling these avoids time-of-check to time-of-use (TOCTOU) issues.

    Attributes:
        solution (Message | None): The initial solution.
        inertial_errors (StandardInertialErrors | None): The inertial errors.
        inertial_error_covariance (NDArray | None): The covariance matrix associated with the terms
            in ``inertial_errors``.
        status (InitializationStatus): Indicates the current initialization status. Should be
            checked before using any of the other fields.

    Caution:
        **Unstable**: This feature is unstable and is not yet considered part of the stable pntOS
        API. Usage of this feature is highly discouraged in non-experimental code, and its
        definition may change at any time.
    """

    solution: Message | None
    inertial_errors: StandardInertialErrors | None
    inertial_error_covariance: NDArray | None
    status: InitializationStatus


class InertialInitializationStrategy(CommonInitializationStrategy, Protocol):
    """
    Generates an initial ASPN solution from sensor data.

    Caution:
        **Unstable**: This feature is unstable and is not yet considered part of the stable pntOS
        API. Usage of this feature is highly discouraged in non-experimental code, and its
        definition may change at any time.
    """

    def request_solution(self) -> InitialInertialSolution:
        """
        Get the current initial solution.

        Returns:
            InitialInertialSolution
        """
        pass


@dataclass
class InitialEstimateWithCovariance:
    """
    Holds both the current estimate and its associated covariance as well as the current status.

    Coupling these avoids time-of-check to time-of-use (TOCTOU) issues.

    Attributes:
        time (TypeTimestamp): The time at which ``estimate_with_covariance`` is valid.
        estimate_with_covariance (EstimateWithCovariance | None): The current estimate of the
            initial solution. Check ``status`` for its validity (can be ``None`` if ``status`` is
            anything other than ``INITIALIZED_GOOD``).
        status (InitializationStatus): Indicates the current initialization status. Should be
            checked before using ``estimate_with_covariance``.

    Caution:
        **Unstable**: This feature is unstable and is not yet considered part of the stable pntOS
        API. Usage of this feature is highly discouraged in non-experimental code, and its
        definition may change at any time.
    """

    time: TypeTimestamp
    estimate_with_covariance: EstimateWithCovariance | None
    status: InitializationStatus


class EwcInitializationStrategy(CommonInitializationStrategy):
    """
    Generates an initial estimate-with-covariance (EWC) solution from sensor data.

    Caution:
        **Unstable**: This feature is unstable and is not yet considered part of the stable pntOS
        API. Usage of this feature is highly discouraged in non-experimental code, and its
        definition may change at any time.
    """

    def request_solution(self) -> InitialEstimateWithCovariance | None:
        """
        Get the current initial solution.

        Returns:
            InitialEstimateWithCovariance | None: The current initial solution. Will be ``None`` if
            the initialization strategy has not yet finished. Use
            :meth:`CommonInitializationStrategy.request_current_status` to check current status of
            the strategy. If the status is ``INITIALIZING_FINE`` or ``INITIALIZED_GOOD``, then the
            result is guaranteed to not be ``None``.
        """
        pass


InitializationType = InertialInitializationStrategy | EwcInitializationStrategy


class InitializationPlugin(CommonPlugin, Protocol):
    """
    An implementation of an initialization plugin.

    This plugin generates :class:`CommonInitializationStrategy` instances which may be used to
    generate an initial solution from additional external sensor data, such as IMU data.

    Caution:
        **Unstable**: This feature is unstable and is not yet considered part of the stable pntOS
        API. Usage of this feature is highly discouraged in non-experimental code, and its
        definition may change at any time.
    """

    def is_initialization_type_supported(self, type: InitializationType) -> bool:
        """
        Check if given ``InitializationType`` is supported.

        Args:
            type (InitializationType)

        Returns:
            bool: ``True`` if the plugin supports a given type of mechanization, ``False``
            otherwise.
        """
        pass

    def new_initialization_strategy(
        self, type: InitializationType, config_group: str | None = None
    ) -> CommonInitializationStrategy | None:
        """
        Create an instance of :class:`CommonInitializationStrategy`.

        Args:
            type (InitializationType): Specifies the type of initializer that the returned value
                will support. For example, if the user passes in
                ``INERTIAL_INITIALIZATION_STRATEGY``, then the returned value will be an instance of
                :class:`InertialInitializationStrategy`. If ``type`` is unsupported by the plugin,
                then ``None`` will be returned. Please use :meth:`is_initialization_type_supported`
                to check if the type is supported by the plugin.
            config_group (str | None, optional): An optional parameter which can be used to specify
                which group in the config should be used to set up the new initialization strategy.
                This allows for multiple initialization strategy instances to exist with unique
                settings.

        Returns:
            CommonInitializationStrategy | None: The new initialization strategy instance. Returns
            ``None`` if ``type`` is unsupported by this plugin (this can be checked using
            :meth:`is_initialization_type_supported`) or if ``config_group`` is invalid.
        """
        pass
