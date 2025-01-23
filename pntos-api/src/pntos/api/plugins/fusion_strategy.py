"""Python API of pntOS."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, TypeVar

from numpy import float64
from numpy.typing import NDArray

from pntos.api import CommonPlugin


@dataclass
class StandardDynamicsModel:
    """
    A description of the propagation dynamics for a set of states.

    This model assumes that the state space :math:`x` can be propagated forward in time by the
    equation:

    .. math::
        x_k = g(x_{k-1}) + w_k

    where :math:`x_k` is the set of states at time :math:`k`, :math:`g` is an arbitrary function,
    and :math:`w_k` is additive white Gaussian noise.

    Attributes:
        g (Callable[[NDArray[float64]], NDArray[float64]]): A function that propagates forward in time a set of
            states.
        Phi (NDArray[float64]): The first-order Taylor series expansion (Jacobian) of the function :math:`g`.
        Qd (NDArray[float64]): The covariance matrix of :math:`w_k`.
    """

    g: Callable[[NDArray[float64]], NDArray[float64]]
    Phi: NDArray[float64]
    Qd: NDArray[float64]


@dataclass
class StandardMeasurementModel:
    """
    A description of how a measurement relates to a state space.

    This model assumes that the relationship between the measurement and state vector is well
    modeled by the equation:

    .. math::
        z=h(x) + v

    where :math:`z` is the measurement itself, :math:`x` is the set of states being estimated,
    :math:`h` is an arbitrary function, and :math:`v` is additive white Gaussian noise.

    Attributes:
        z (NDArray[float64]): A column vector containing the measurement itself.
        h (Callable[[NDArray[float64]], NDArray[float64]]): A function that maps the state space to measurement space.
        H (NDArray[float64]): The first-order Taylor series expansion (i.e. Jacobian) of the function h.
        R (NDArray[float64]): The covariance matrix of :math:`v`.
    """

    z: NDArray[float64]
    h: Callable[[NDArray[float64]], NDArray[float64]]
    H: NDArray[float64]
    R: NDArray[float64]


class StandardFusionStrategy(ABC):
    """
    A Fusion strategy making linearized Bayesian assumptions.

    An implementation of the standard fusion strategy that is capable of
    Bayesian inference on a linearized discrete-time system with Gaussian noise
    inputs (e.g. an EKF).

    At a fundamental level, this class manages an estimate of a state space as
    it propagates (changes over time) and updates (incorporates new measurements
    and observations). An estimate of a set of values (states) is stored and
    maintained within this object. The estimate is then mutated and updated over
    time by the various method calls.

    A typical usage pattern of this class is as follows:

    1. The user adds a set of states by calling the :meth:`add_states` method. As part
       of this step, the user all passes in initial conditions for the estimate.
       The fusion strategy is now storing an estimate of the states, set to the
       initial conditions.
    2. The user propagates this estimate forward in time by calling the
       :meth:`propagate` method. For example, if the initial conditions were the
       estimates of the states at time 0.0s, but we now want to know the
       estimate of the values at time 5.0s, the user would call :meth:`propagate` with
       a dynamics model parameter that specifies how to take an estimate at time
       0.0 and use it to compute the estimate at time 5.0.
    3. The user updates this estimate by using observations of the states at the
       current time. For example, if the filter is currently propagated to time
       5.0s and a measurement is received that observes the states' values at
       time 5.0s, the user would call :meth:`update` with a measurement model
       parameter that describes how to take the current estimate at 5.0s and
       incorporate the new information from the measurement.
    4. At any point, when the user wants to know the latest estimate given all
       the propagate/updates that have occurred, they may call :meth:`get_estimate`.
    """

    @abstractmethod
    def get_num_states(self) -> int:
        """
        Get the total number of states this filter is estimating.

        The count will initially be zero, until :meth:`add_states` is called.

        Returns:
            int: Number of states being estimated in this filter.
        """
        ...

    @abstractmethod
    def add_states(
        self,
        initial_estimate: NDArray[float64],
        initial_covariance: NDArray[float64],
        cross_covariance: NDArray[float64] | None = None,
    ) -> int:
        """
        Add new states to this filter.

        Increases number of filter states and set the initial conditions of the new states. Returns
        index of the first added state. If ``cross_covariance`` is ``None``, cross covariance between
        the existing states and the added states will be set to zeroes.

        Args:
            initial_estimate (NDArray[float64]): The initial estimate to populate the new states with.
            initial_covariance (NDArray[float64]): The initial covariance matrix used to initialize the
                uncertainty of the new states.
            cross_covariance (NDArray[float64] | None): A covariance matrix that describes the cross terms
                between the new states and all previous states. If ``None``, the cross-terms will be
                set to zero.

        Returns:
            int: Number of states being added to this filter.
        """
        ...

    @abstractmethod
    def remove_states(self, first_index: int, count: int) -> None:
        """
        Removes a set of states from the filter.

        Args:
            first_index (int): Index of the first state to be removed.
            count (int): The number of states to be removed.
        """
        ...

    @abstractmethod
    def get_estimate(self) -> NDArray[float64] | None:
        """
        Get the current internal estimate managed by this strategy.

        This class manages a current estimate that is initially populated by :meth:`add_states` and
        then is modified iteratively by :meth:`propagate`, :meth:`update`, and other method calls.
        This method returns the current estimate, incorporating all changes made by previous method
        calls to this strategy.

        Returns:
            NDArray[float64] | None: An estimate if available. Returns ``None`` if no states have been added
            yet.
        """

    @abstractmethod
    def set_estimate_slice(self, new_estimate: NDArray[float64], first_index: int) -> None:
        """
        Set a slice of the state estimates to a given set of values.

        This class manages a current estimate that is initially populated by :meth:`add_states` and
        then is modified iteratively by :meth:`propagate`, :meth:`update`, and other method calls.
        This method allows for manually overriding the current estimate. Sets a block of states to
        new values, starting with ``first_index`` and overwriting a number of states equal to the
        length of ``new_estimate``.

        Args:
            new_estimate (NDArray[float64]): The new estimate values that will overwrite the previous values.
            first_index (int): The index of the first state to overwrite.
        """
        ...

    @abstractmethod
    def get_covariance(self) -> NDArray[float64] | None:
        """
        Get the covariance of the current estimate.

        This class manages a current estimate that is initially populated by :meth:`add_states` and
        then is modified iteratively by :meth:`propagate`, :meth:`update`, and other method calls.
        In addition to the estimate itself, a covariance of the current estimate is computed. This
        method returns this covariance, incorporating all changes made by previous method calls to
        this strategy.

        Returns:
            NDArray[float64] | None: The covariance of the current estimate. Returns ``None`` if no states
            have been added yet.
        """

    @abstractmethod
    def set_covariance_slice(
        self, new_covariance: NDArray[float64], first_row: int, first_col: int
    ) -> None:
        """
        Set a slice of the covariance matrix to a given set of values.

        This class manages a current estimate that is initially populated by :meth:`add_states` and
        then is modified iteratively by :meth:`propagate`, :meth:`update`, and other method calls.
        In addition to the estimate itself, a covariance of the current estimate is computed.

        Allows for manually overriding the current covariance matrix. Sets a block of the covariance
        matrix to new values. The overwritten values are those in a rectangular area defined by the
        upper left corner at ``first_row``, ``first_col`` and extending down and right to cover an
        area equal to the size of ``new_covariance``.

        Args:
            new_covariance (NDArray[float64]): The new covariance values that will overwrite a slice of the
                previous covariance matrix.
            first_row (int): The row of the first value to overwrite.
            first_col (int): The column of the first value to overwrite.
        """
        ...

    @abstractmethod
    def propagate(self, dynamics_model: StandardDynamicsModel) -> None:
        """
        Propagates the estimate of the state space forward in time.

        This method assumes that a state space is already initialized with a set
        of states via the :meth:`add_states` method. The ``dynamics_model`` parameter
        includes a description of how the current state estimate can be
        propagated from the current time to a new time. Note that the actual
        numerical values of the current/new times are not specified anywhere, as
        that information is not needed to perform the computation. This method
        then takes the current state space estimate and the ``dynamics_model`` and
        uses both to compute an estimate at the new time. The new estimate
        clobbers the old estimate managed by this class, and be acquired by
        calling :meth:`get_estimate`.

        Args:
            dynamics_model (StandardDynamicsModel)
        """
        ...

    @abstractmethod
    def update(self, measurement_model: StandardMeasurementModel) -> None:
        """
        Updates the estimate of the state space, incorporating a new measurement.

        This method assumes that a state space is already initialized with a set of states via the
        :meth:`add_states` method. The ``measurement_model`` parameter includes both the measurement
        itself and a description of how the measurement relates to the state space. This method then
        takes the current state space estimate and updates it using information from the
        ``measurement_model``. The updated estimate can be acquired by calling :meth:`get_estimate`.

        Args:
            measurement_model (StandardMeasurementModel): The measurement with which to update the
                filter, as well as a model that describes how the measurement relates to the states
                this strategy is estimating.
        """

    @abstractmethod
    def clone(self) -> 'StandardFusionStrategy':
        """
        Create a deep copy of this object.

        The returned object will have all state copied, such that the original
        and newly returned objects are entirely separate from each other. A
        typical use case for this method is when a fault is detected in a
        running filter, and the user wants to experiment on the filter while
        still preserving the original state. In this case, the user may `clone`
        a new filter to experiment with, but continue to have the original
        available to go back to.

        Returns:
            StandardFusionStrategy: A deep copy of the object.
        """
        ...


FusionStrategyType = TypeVar('FusionStrategyType', StandardFusionStrategy, Any)


class FusionStrategyPlugin(CommonPlugin, ABC):
    """
    A plugin that provides computational engines for estimation.

    At the high level, a fusion strategy is a computation engine that knows how
    to estimating one or more states, given a set of observations/measurements.
    For example, the EKF equations are an implementation of a fusion strategy.
    This plugin is a factory that produces fusion strategies on demand, which is
    useful for multi-filter approaches where the system may need several fusion
    strategies running simultaneously.

    There are many ways to model sensor fusion, including very simple (linear
    Kalman filter) and complex (neural networks, factor graphs, etc.). This
    plugin aims to allow any and all of those models to be represented. It
    achieves this by having multiple fusion strategies, so that the user may select
    what kind of fusion they want. Currently, only the :class:`StandardFusionStrategy` is
    implemented, which is suitable for EKFs and filters that have similar
    interfaces to an EKF (such as a UKF). However, more strategy types are
    planned to be added in the future.
    """

    @abstractmethod
    def is_fusion_type_supported(self, fusion_type: type[FusionStrategyType]) -> bool:
        """
        Check if a particular fusion strategy is supported by :meth:`new_fusion_strategy`.

        The :meth:`new_fusion_strategy` factory method on this class can create
        one or more types of fusion strategy. However, :class:`FusionStrategyPlugin`
        may not support all types (they must support at least one). Therefore,
        when a user receives a :class:`FusionStrategyPlugin`, they should:

        1. Initialize the plugin by calling :meth:`.init_plugin` (see :class:`CommonPlugin` for more
           information).
        2. Call :meth:`is_fusion_type_supported` to check that the plugin supports the
           type that the user wants to use.
        3. If :meth:`is_fusion_type_supported` returned True, call the :meth:`new_fusion_strategy`
           factory method to get a new fusion strategy of the desired fusion strategy.
        4. Proceed to use the fusion strategy to do estimation.

        Args:
            fusion_type (type[FusionStrategyType]): The fusion strategy type we are checking.

        Returns:
            bool: Whether or not we support the requested ``fusion_type``.
        """
        ...

    @abstractmethod
    def new_fusion_strategy(
        self, fusion_type: type[FusionStrategyType]
    ) -> FusionStrategyType | None:
        """
        Create a new fusion strategy of the requested type.

        Users must first ensure that the fusion strategy is supported by calling
        :meth:`is_fusion_type_supported`.

        Args:
            fusion_type (type[FusionStrategyType]): The type of fusion strategy that we want
            returned.

        Returns:
            FusionStrategyType | None: The newly created fusion strategy, which is an
            implementation of the type specified by ``fusion_type``. For example, if the user calls
            :meth:`new_fusion_strategy` with a ``fusion_type`` of ``StandardFusionStrategy``, then
            the returned object will be an implementation of :class:`StandardFusionStrategy`.
        """
        ...
