from aspn23 import TypeTimestamp
from numpy import float64, zeros
from numpy.typing import NDArray
from pntos.api import (
    EstimateWithCovariance,
    LoggingLevel,
    Mediator,
    Message,
    VirtualStateBlock,
)

EXPECTED_COV_DIM = 2


class StateExtractor(VirtualStateBlock):
    """
    A VirtualStateBlock that extracts and returns a series of states from an input estimate and covariance.
    """

    _mediator: Mediator
    _jac: NDArray[float64]
    source: str
    target: str

    def __init__(
        self,
        mediator: Mediator,
        source: str,
        target: str,
        incoming_state_size: int,
        indices: list[int],
    ) -> None:
        """
        Args:
            mediator (Mediator): A class:`pntos.api.Mediator` instance
            source (str): The label associated with the representation this instance can transform *from*
            target (str): The label associated with the representation this instance can transform *to*
            incoming_state_size (int): The number of states in the StateBlock `source` refers to
            indices (list[int]): The series of indices that correspond to states to extract from `source` and comprise `target`
        """
        if incoming_state_size <= 0:
            mediator.log_message(
                LoggingLevel.ERROR,
                f'StateExtractor argument "incoming_state_size" must be greater than 0. Received {incoming_state_size}',
            )
            raise RuntimeError

        ind_count = len(indices)
        if ind_count == 0:
            mediator.log_message(
                LoggingLevel.ERROR,
                'Must provide at least 1 index for an element to keep.',
            )
            raise RuntimeError

        for index in indices:
            if index >= incoming_state_size:
                mediator.log_message(
                    LoggingLevel.ERROR,
                    f'Invalid index provided in list of indices. Value {index} exceeds the length of the expected state vector.',
                )
                raise RuntimeError

        unique = set(indices)
        if len(unique) != ind_count:
            mediator.log_message(LoggingLevel.ERROR, 'Repeat indices are not allowed.')
            raise RuntimeError

        self._mediator = mediator
        self.source = source
        self.target = target
        self._jac = zeros((ind_count, incoming_state_size), dtype=float64)
        for i in range(ind_count):
            self._jac[i, indices[i]] = 1.0

    def receive_aux_data(self, aux: list[Message | None]) -> None:
        self._mediator.log_message(
            LoggingLevel.WARN,
            'StateExtractor does not require aux data. This method is unimplemented.',
        )

    def convert(
        self,
        estimate_with_covariance: EstimateWithCovariance,
        time: TypeTimestamp,
    ) -> EstimateWithCovariance:
        if estimate_with_covariance.covariance.ndim != EXPECTED_COV_DIM:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'Expected covariance matrix to be 2D, but received {estimate_with_covariance.covariance.ndim} dimensions. Cannot convert.',
            )
            raise RuntimeError
        state = self.convert_estimate(estimate_with_covariance.estimate, time)
        cov = (self._jac @ estimate_with_covariance.covariance) @ self._jac.T
        return EstimateWithCovariance(estimate_with_covariance.type, state, cov)

    def convert_estimate(
        self, estimate: NDArray[float64], time: TypeTimestamp
    ) -> NDArray[float64]:
        if self._jac.shape[1] != estimate.shape[0]:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                'State block to alias does not contain the expected number of states.'
                + f' Expected {self._jac.shape[1]} but received {estimate.shape[0]}.',
            )
            raise RuntimeError

        return self._jac @ estimate

    def jacobian(
        self, estimate: NDArray[float64], time: TypeTimestamp
    ) -> NDArray[float64]:
        return self._jac
