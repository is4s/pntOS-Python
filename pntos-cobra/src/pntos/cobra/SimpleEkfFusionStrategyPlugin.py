import numpy as np
from numpy.typing import NDArray

from pntos.api import (
    FusionStrategyPlugin,
    FusionStrategyType,
    LoggingLevel,
    Mediator,
    StandardDynamicsModel,
    StandardFusionStrategy,
    StandardMeasurementModel,
)
from pntos.cobra.utils import is_symmetric, validate_array


class SimpleEkfFusionStrategy(StandardFusionStrategy):
    """
    This is a simple Extended Kalman Filter (EKF) sensor fusion strategy.

    It is capable of Bayesian inference on a linearized discrete-time system with Gaussian noise inputs.
    """

    def __init__(self, mediator: Mediator) -> None:
        """
        Simple Extended Kalman Filter Fusion Strategy

        Args:
            mediator (Mediator): A :class:`pntos.api.Mediator` instance.
        """
        self._x: NDArray[np.float64] = np.zeros(
            [0, 1], dtype=np.float64
        )  # State vector  (num_states x 1)
        self._P: NDArray[np.float64] = np.zeros(
            [0, 0], dtype=np.float64
        )  # Covariance matrix  (num_states x num_states)
        self._num_states = 0
        self._mediator = mediator

    def get_num_states(self) -> int:
        return self._num_states

    def add_states(
        self,
        initial_estimate: NDArray,
        initial_covariance: NDArray,
        cross_covariance: NDArray | None = None,
    ) -> int:
        validate_array(initial_estimate, self._mediator, dims=2, cols=1)

        num_new_states = initial_estimate.shape[0]

        validate_array(
            initial_covariance,
            self._mediator,
            dims=2,
            rows=num_new_states,
            cols=num_new_states,
        )

        # Add to state vector
        # New state vector looks like
        #         --                --
        #         |      self.x      |
        # x_new = |                  |
        #         | initial_estimate |
        #         --                --
        self._x = np.concatenate([self._x, initial_estimate])

        # New covariance matrix looks like:
        #         --                                        --
        #         | self.P                cross_covariance   |
        # P_new = |                                          |
        #         | cross_covariance^T    initial_covariance |
        #         --                                        --
        # Get cross covariance
        C = np.zeros((self._num_states, num_new_states))
        if cross_covariance is not None:
            validate_array(
                cross_covariance,
                self._mediator,
                dims=2,
                rows=self._num_states,
                cols=num_new_states,
            )
            C = cross_covariance

        self._P = np.block([[self._P, C], [C.T, initial_covariance]])

        # Save off index of first state added
        index_of_first_state_added = self._num_states

        # Increment the number of states
        self._num_states += num_new_states

        return index_of_first_state_added

    def remove_states(self, first_index: int, count: int) -> None:
        # Make sure states exist
        if first_index + count > self._num_states:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'Tried to remove states [{first_index}:{first_index + count}] but '
                + f'state vector is only length {self._num_states}.',
            )

        # Delete states
        i_delete = slice(first_index, first_index + count)
        self._x = np.delete(self._x, i_delete, axis=0)
        self._P = np.delete(np.delete(self._P, i_delete, axis=0), i_delete, axis=1)

        # Update num_states
        self._num_states -= count

    def get_estimate(self) -> NDArray | None:
        if self._num_states == 0:
            return None
        else:
            return self._x

    def set_estimate_slice(self, new_estimate: NDArray, first_index: int) -> None:
        validate_array(new_estimate, self._mediator, dims=2, cols=1)

        n = new_estimate.shape[0]
        if first_index + n > self._num_states:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                'estimate slice exceeds size of current state vector.',
            )

        self._x[first_index : first_index + n] = new_estimate

    def get_covariance(self) -> NDArray | None:
        if self._num_states == 0:
            return None
        else:
            return self._P

    def set_covariance_slice(
        self, new_covariance: NDArray, first_row: int, first_col: int
    ) -> None:
        validate_array(new_covariance, self._mediator, dims=2)

        last_row = first_row + new_covariance.shape[0]
        last_col = first_col + new_covariance.shape[1]

        if last_row > self._num_states or last_col > self._num_states:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'Covariance slice spans [{first_row}:{last_row}, {first_col}:{last_col}]'
                + f', but full covariance matrix is only {self._num_states}x{self._num_states}.',
            )

        self._P[first_row:last_row, first_col:last_col] = new_covariance

    def _symmetrize_covariance(self, rtol: float = 1e-5, atol: float = 1e-8) -> None:
        """Produces and replaces the covariance matrix with a symmetric one, if it was not already symmetric."""
        if not is_symmetric(self._P, self._mediator, rtol, atol):
            self._P = 0.5 * (self._P + self._P.T)

    def propagate(self, dynamics_model: StandardDynamicsModel) -> None:
        self._symmetrize_covariance()

        # Check sizes of Phi and Qd matrices
        validate_array(
            dynamics_model.Phi,
            self._mediator,
            dims=2,
            rows=self._P.shape[0],
            cols=self._P.shape[1],
        )
        validate_array(
            dynamics_model.Qd,
            self._mediator,
            dims=2,
            rows=self._P.shape[0],
            cols=self._P.shape[1],
        )

        # Propagate the state: x_new = g(x_old)
        self._x = dynamics_model.g(self._x)

        # Propagate the covaraince (P_new = Phi * P * Phi^T + Qd)
        self._P = (
            dynamics_model.Phi @ self._P @ dynamics_model.Phi.T + dynamics_model.Qd
        )

    def update(self, measurement_model: StandardMeasurementModel) -> None:
        validate_array(measurement_model.z, self._mediator, dims=2, cols=1)
        num_meas = measurement_model.z.shape[0]

        validate_array(
            measurement_model.H,
            self._mediator,
            dims=2,
            rows=num_meas,
            cols=self._num_states,
        )
        validate_array(
            measurement_model.R,
            self._mediator,
            dims=2,
            rows=num_meas,
            cols=num_meas,
        )

        # Calculate residual(s)
        h_x = measurement_model.h(self._x)
        validate_array(h_x, self._mediator, dims=2, rows=num_meas, cols=1)
        resid = measurement_model.z - h_x

        # Calculate residual covariance
        resid_cov = (
            measurement_model.H @ self._P @ measurement_model.H.T + measurement_model.R
        )

        # Calculate Kalman gain
        K = self._P @ measurement_model.H.T @ np.linalg.inv(resid_cov)

        # State update
        self._x = self._x + K @ resid

        # Covariance update
        self._P = (np.eye(self._P.shape[0]) - K @ measurement_model.H) @ self._P


class SimpleEkfFusionStrategyPlugin(FusionStrategyPlugin):
    """
    This is a simple fusion strategy plugin. It functions as a factory that produces fusion strategies,
    although it currently only supports the EKF fusion strategy.
    """

    _mediator: Mediator

    def __init__(self, identifier: str):
        """
        A Simple Extended Kalman Filter Fusion Strategy Plugin

        Args:
            identifier (str): The plugin identifier passed to the
                :meth:`pntos.api.CommonPlugin.identifier` field.
        """
        self.identifier = identifier

    def init_plugin(
        self,
        plugin_resources_location: str | None = None,
        mediator: Mediator | None = None,
    ) -> None:
        if mediator is not None:
            self._mediator = mediator

    def shutdown_plugin(self) -> None:
        pass

    def is_fusion_type_supported(self, fusion_type: type[FusionStrategyType]) -> bool:
        return fusion_type == StandardFusionStrategy

    def new_fusion_strategy(
        self, fusion_type: type[FusionStrategyType]
    ) -> FusionStrategyType | None:
        if self.is_fusion_type_supported(fusion_type):
            return SimpleEkfFusionStrategy(self._mediator)
        else:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'Fusion strategy type {fusion_type.__name__} not currently supported. '
                + 'Make sure to call FusionStrategyPlugin.is_fusion_type_supported before '
                + 'requesting a new fusion strategy.',
            )
            return None
