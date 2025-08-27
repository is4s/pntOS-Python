from aspn23 import (
    TypeTimestamp,
)
from numpy import diagflat, eye, float64
from numpy.typing import NDArray
from pntos.api.plugins.common import (
    EstimateWithCovariance,
    LoggingLevel,
    Mediator,
    Message,
)
from pntos.api.plugins.state_modeling import StandardDynamicsModel, StandardStateBlock
from scipy.linalg import expm


class FogmBlock(StandardStateBlock):
    """A StateBlock that represents 'n' first-order Gauss-Markov processes."""

    _mediator: Mediator
    _F: NDArray[float64]
    _Q: NDArray[float64]
    _I: NDArray[float64]

    def __init__(
        self,
        label: str,
        mediator: Mediator,
        sigmas: NDArray[float64],
        taus: NDArray[float64],
    ):
        """
        Constructor

        Args:
            label (str): Label for this block.
            mediator (Mediator): A :class:`pntos.api.Mediator` instance.
            sigmas (NDArray[float64]): Nx1 array of FOGM noise sigmas; units will vary.
            taus (NDArray[float64]): Nx1 array of FOGM time constants, in seconds. Must be positive.
        """
        if sigmas.size == 0 or taus.size == 0:
            mediator.log_message(
                LoggingLevel.ERROR,
                'FogmBlock sigmas (shape {}) or taus (shape {}) arguments are empty.'.format(
                    sigmas.shape, taus.shape
                ),
            )
            raise RuntimeError()

        if sigmas.shape != taus.shape:
            mediator.log_message(
                LoggingLevel.ERROR,
                'FogmBlock sigmas {} and taus {} arguments have a size mismatch.'.format(
                    sigmas.shape, taus.shape
                ),
            )
            raise RuntimeError()

        if any(taus <= 0):
            mediator.log_message(
                LoggingLevel.ERROR,
                'FogmBlock taus arguments must be positive, got {}.'.format(taus),
            )
            raise RuntimeError()

        self.label = label
        self.num_states = taus.size
        self._mediator = mediator
        self._F = diagflat(-1.0 / taus)
        self._Q = diagflat(2.0 * pow(sigmas, 2.0) / taus)
        self._I = eye(self.num_states)

    def receive_aux_data(self, aux: list[Message]) -> None:
        """Receive aux data. Unused for this class.

        Args:
            aux (list[Message]): List of messages.
        """

        self._mediator.log_message(
            LoggingLevel.WARN, f'FogmBlock does not require aux data.'
        )

    def generate_dynamics(
        self,
        x_and_p: EstimateWithCovariance,
        time_from: TypeTimestamp,
        time_to: TypeTimestamp,
    ) -> StandardDynamicsModel | None:
        dt = (time_to.elapsed_nsec - time_from.elapsed_nsec) / 1e9
        # Under most typical circumstances a first-order integration of Phi would be sufficient
        # but can be in serious error for dt >> tau; second order suffers from same problem
        # Q is constant over the interval
        Phi = expm(self._F * dt)
        Qd = 0.5 * (Phi @ self._Q @ Phi.T + self._Q) * dt

        def g(x: NDArray[float64]) -> NDArray[float64]:
            return Phi @ x

        return StandardDynamicsModel(g, Phi, Qd)
