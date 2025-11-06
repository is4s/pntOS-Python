"""
ClockBiasStateBlock.

Models a clock bias (seconds), drift (seconds/second), and optional drift rate (seconds/second^2).
"""

from math import pi

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


class ClockBiasStateBlock(StandardStateBlock):
    """
    Models a clock bias (seconds), drift (seconds/second), and optional drift rate (seconds/second^2).

    Uses allan variance parameters to create a clock model for the system dynamics model covariance matrix.
    """

    def __init__(
        self,
        mediator: Mediator,
        h_0: float,
        h_neg2: float,
        q3: float | None,
    ) -> None:
        self._mediator = mediator
        self.num_states = 2 if q3 is None else 3
        self._h_0 = h_0
        self._h_neg2 = h_neg2
        self._q3 = q3

    def receive_aux_data(self, _: list[Message]) -> None:
        pass

    def generate_dynamics(
        self,
        x_and_p: EstimateWithCovariance,
        time_from: TypeTimestamp,
        time_to: TypeTimestamp,
    ) -> StandardDynamicsModel:
        delta_time = (time_to.elapsed_nsec - time_from.elapsed_nsec) * 1e-9

        if self.num_states == 2:  # noqa: PLR2004
            Phi = np.array([[1, delta_time], [0, 1]])
        else:
            Phi = np.array(
                [
                    [1.0, delta_time, 0.5 * delta_time * delta_time],
                    [0, 1.0, delta_time],
                    [0, 0, 1.0],
                ]
            )

        # Calculate the Qd based on the delta time and allan variance
        Qd = self.calc_Hwang_Brown_Q(self._h_0, self._h_neg2, delta_time)

        if self._q3 is None:
            # 2-state model
            Qd = Qd[:2, :2]
        else:
            # 3-state model
            q_three = np.array(
                [
                    [
                        1 / 20 * self._q3 * delta_time**5,
                        1 / 8 * self._q3 * delta_time**4,
                        1 / 6 * self._q3 * delta_time**3,
                    ],
                    [
                        1 / 8 * self._q3 * delta_time**4,
                        1 / 3 * self._q3 * delta_time**3,
                        1 / 2 * self._q3 * delta_time**2,
                    ],
                    [
                        1 / 6 * self._q3 * delta_time**3,
                        1 / 2 * self._q3 * delta_time**2,
                        self._q3 * delta_time,
                    ],
                ]
            )
            Qd += q_three

        # Define the g(x) propagation function as g(x_(k-1)) = phi * x_(k-1)
        def g(x: NDArray[float64]) -> NDArray[float64]:
            return Phi @ x

        return StandardDynamicsModel(g=g, Phi=Phi, Qd=Qd)

    def calc_Hwang_Brown_Q(
        self, h_0: float, h_n2: float, dt: float
    ) -> NDArray[float64]:
        """
        Calculate the discrete system noise matrix.

        Using the 10.4.1 - 10.4.3 from Introduction to Random Signals And Applied
        Kalman Filtering, second edition.

        Same as Q3 model in navtk block.
        """
        Q_00 = 0.5 * h_0 * dt + (2 / 3) * pi**2 * h_n2 * dt**3
        Q_01 = pi**2 * h_n2 * dt**2
        Q_10 = Q_01
        Q_11 = 2 * pi**2 * h_n2 * dt
        return np.array([[Q_00, Q_01, 0], [Q_10, Q_11, 0], [0, 0, 0]])
