"""
ConstantStateBlock.

Models a clock bias (seconds), drift (seconds/second), and optional drift rate (seconds/second^2).
"""

import numpy as np
from aspn23 import TypeTimestamp
from numpy import float64
from numpy.typing import NDArray
from pntos.api import (
    EstimateWithCovariance,
    Mediator,
    Message,
    StandardDynamicsModel,
    StandardStateBlock,
)


class ConstantStateBlock(StandardStateBlock):
    """
    Estimates 1 or more "constant" states, i.e. states with no dynamics.
    """

    def __init__(
        self,
        label: str,
        mediator: Mediator,
        num_states: int,
        Q: NDArray[float64] | None = None,
    ) -> None:
        self._mediator = mediator
        self.label = label
        self.num_states = num_states
        self._Q = Q if Q is not None else np.zeros((num_states, num_states))

    def receive_aux_data(self, _: list[Message | None]) -> None:
        pass

    def generate_dynamics(
        self,
        x_and_p: EstimateWithCovariance,
        time_from: TypeTimestamp,
        time_to: TypeTimestamp,
    ) -> StandardDynamicsModel:
        """Return a constant dynamics model, where g(x) = x."""
        dt = (time_to.elapsed_nsec - time_from.elapsed_nsec) * 1e-9
        Phi = np.eye(self.num_states)
        Qd = self._Q * dt  # Use first order discretization strategy

        def g(x: NDArray[float64]) -> NDArray[float64]:
            return Phi @ x

        return StandardDynamicsModel(g=g, Phi=Phi, Qd=Qd)
