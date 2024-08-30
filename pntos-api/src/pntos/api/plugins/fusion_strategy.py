from dataclasses import dataclass
from typing import Callable, Optional, Protocol, runtime_checkable

from numpy.typing import NDArray

from .common import CommonPlugin, FusionType


@runtime_checkable
class FusionStrategy(Protocol):
    """A computation engine for doing raw estimation."""

    pass


@dataclass
class StandardDynamicsModel:
    g: Callable[[NDArray], NDArray]
    Phi: NDArray
    Qd: NDArray


class StandardMeasurementModel(Protocol):
    z: NDArray
    h: Callable[[NDArray], NDArray]
    H: NDArray
    R: NDArray


@runtime_checkable
class StandardFusionStrategy(FusionStrategy, Protocol):
    """A Fusion strategy making linearized Bayesian assumptions.

        An implementation of the standard fusion strategy is capable of Bayesian
    inference on a linearized discrete-time system with Gaussian noise inputs
    (e.g. an EKF).
    """

    def get_num_states(self) -> int:
        """Return the total number of states added to this filter.

        Returns:
            int: Number of stats being estimated in this filter.
        """
        ...

    def add_states(
        self,
        initial_estimate: NDArray,
        initial_covariance: NDArray,
        cross_covariance: Optional[NDArray],
    ) -> int:
        """Add new states to this filter.

        Increases number of filter states and set the initial conditions of the new states.  Returns index of the first added state. If \p cross_covariance is NULL, cross
            covariance between the existing states and the added states will be set to zeroes.

        Args:
            initial_estimate (NDArray): The initial estimate to populate the new states with.
            initial_covariance (NDArray): The initial covariance matrix used to initialize the uncertainty of the new states.
            cross_covariance (Optional[NDArray]): A covariance matrix that describes the cross terms between the new states and all previous states. If `None`, the cross-terms will be set to zero.

        Returns:
            int: Number of stats being added to this filter.
        """
        ...

    def remove_states(self, first_index: int, count: int) -> None:
        """Removes a set of states from the filter

        Args:
            first_index (int): Index of the first state to be removed
            count (int): The number of states to be removed.
        """
        ...

    def get_estimate(self) -> Optional[NDArray]: ...

    def set_estimate_slice(self, new_estimate: NDArray, first_index: int) -> None: ...

    def get_covariance(self) -> Optional[NDArray]: ...

    def set_covariance_block(
        self, new_covariance: NDArray, first_row: int, first_col: int
    ) -> None: ...

    def set_covariance_slice(self, new_covariance: NDArray, first_state: int) -> None:
        pass

    def propagate(self, dynamics_model: StandardDynamicsModel) -> None: ...

    def update(self, measurement_model: StandardMeasurementModel) -> None: ...

    def clone(self) -> "StandardFusionStrategy": ...


class FusionStrategyPlugin(CommonPlugin, Protocol):
    """A plugin that provides computational engines for estimation.

    At the high level, a fusion strategy is an algorithm that knows how to
    perform sensor fusion by estimating one or more states, given a set of
    observations/measurements. For example, the EKF equations are an
    implementation of a fusion strategy. This plugin is a factory that produces
    fusion strategies on demand, which is useful for multi-filter approaches
    where the system may need several fusion strategies running simultaneously.

    There are many ways to model sensor fusion, including very simple (linear
    Kalman filter) and complex (neural networks, factor graphs, etc.). This
    plugin aims to allow any and all of those models to be represented. It
    achieves this by having multiple FusionTypes, so that the user may select
    what kind of fusion they want. Currently, only the StandardFusionStrategy is
    implemented, which is suitable for EKFs and filters that have similar
    interfaces to an EKF (such as a UKF).
    """

    def is_fusion_type_supported(self, fusion_type: FusionType) -> bool: ...

    def new_fusion_strategy(self, fusion_type: FusionType) -> FusionStrategy: ...
