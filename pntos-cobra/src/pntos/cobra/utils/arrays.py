from numpy import allclose, eye, float64
from numpy.typing import NDArray

from pntos.api import EstimateWithCovariance, LoggingLevel, Mediator


def validate_array(
    arr: NDArray[float64],
    mediator: Mediator,
    name: str,
    dims: int | None = None,
    rows: int | None = None,
    cols: int | None = None,
) -> None:
    """
    Validate the dimensionality and/or length of a 1-D or 2-D numpy array.

    Sends error log messages through the mediator if validation fails.

    Args:
        arr (NDArray[float64]): The array to validate.
        mediator (Mediator): Mediator to use for logging any error messages.
        name (str): Name of array to be included in any error messages.
        dims (int | None, optional): Expected number of dimensions, or None to ignore dimensions. Defaults to None.
        rows (int | None, optional): Expected number of rows, or None to ignore rows. Defaults to None.
        cols (int | None, optional): Expected number of cols, or None to ignore cols. Defaults to None.
    """
    if dims is not None and arr.ndim != dims:
        mediator.log_message(
            LoggingLevel.ERROR,
            f'Expected {dims} dimensions for {name}, but got {arr.ndim}',
        )

    if rows is not None and cols is not None:
        expected_shape = (rows, cols)
        if arr.shape != expected_shape:
            mediator.log_message(
                LoggingLevel.ERROR,
                f'Expected shape {expected_shape} for {name}, but got {arr.shape}',
            )
    elif rows is not None and arr.shape[0] != rows:
        mediator.log_message(
            LoggingLevel.ERROR,
            f'Expected {rows} rows for {name}, but got {arr.shape[0]}.',
        )
    elif cols is not None and arr.shape[1] != cols:
        mediator.log_message(
            LoggingLevel.ERROR,
            f'Expected {cols} cols for {name}, but got {arr.shape[1]}.',
        )


def is_symmetric(
    mat: NDArray[float64], mediator: Mediator, rtol: float = 1e-5, atol: float = 1e-8
) -> bool:
    """
    This function will compare a matrix with its transpose and determine if the two are equivalent within a provided tolerance.
    If the two are equivalent, the matrix is symmetric and this function returns ``True``, else returns ``False``.

    NOTE: Symmetry requires a matrix to be square, if ``mat`` is not a 2-D square matrix this function will log an error and return ``False``.

    Args:
        mat (NDArray[float64]): The matrix to be examined.
        rtol (float): A coefficient multiplied with every value in the matrix to generate a relative tolerance.
        atol (float): An absolute value added directly the relative tolerance which creates an overall tolerance.

    Returns:
        bool
    """
    shape = mat.shape
    if len(shape) == 2 and shape[0] == shape[1]:  # noqa: PLR2004
        return allclose(mat, mat.T, rtol, atol)
    mediator.log_message(
        LoggingLevel.ERROR,
        f'Expected matrix to be 2D and square but got shape {shape}',
    )
    return False


def validate_manual_ewc(
    ewc: EstimateWithCovariance, num_states: int, mediator: Mediator
) -> EstimateWithCovariance | None:
    est = ewc.estimate
    cov = ewc.covariance

    # validate and convert estimate
    if est.ndim < 1 or est.ndim > 2:  # noqa: PLR2004
        mediator.log_message(
            LoggingLevel.ERROR,
            f'Estimate could not be converted to column vector. Expected 1 or 2 dimensions but got {est.ndim}.',
        )
        return None
    if len(est) != num_states:
        mediator.log_message(
            LoggingLevel.ERROR,
            f'Expected estimate to have {num_states} states but got {len(est)}.',
        )
        return None
    if est.ndim == 2 and est.shape[1] != 1:  # noqa: PLR2004
        mediator.log_message(
            LoggingLevel.ERROR,
            f'Expected estimate to be a column vector but got a matrix of shape {est.shape}.',
        )
        return None
    if est.ndim == 1:
        est = est.reshape(-1, 1)  # convert to column vector

    # validate and convert covariance
    if cov.ndim < 1 or cov.ndim > 2:  # noqa: PLR2004
        mediator.log_message(
            LoggingLevel.ERROR,
            f'Covariance could not be converted to square matrix. Expected 1 or 2 dimensions but got {cov.ndim}.',
        )
        return None
    if len(cov) != num_states:
        mediator.log_message(
            LoggingLevel.ERROR,
            f'Expected covariance to correspond to {num_states} states but it instead corresponds to {len(cov)} states.',
        )
        return None
    if cov.ndim == 2 and cov.shape[0] != cov.shape[1]:  # noqa: PLR2004
        mediator.log_message(
            LoggingLevel.ERROR,
            f'Expected covariance to be a square matrix but got shape {cov.shape}.',
        )
        return None
    if cov.ndim == 1:
        cov = eye(num_states) * cov

    return EstimateWithCovariance(ewc.type, est, cov)
