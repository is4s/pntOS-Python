from numpy import allclose, float64
from numpy.typing import NDArray

from pntos.api import LoggingLevel, Mediator


def validate_array(
    arr: NDArray[float64],
    mediator: Mediator,
    dims: int | None = None,
    rows: int | None = None,
    cols: int | None = None,
) -> None:
    """
    Validate the dimensionality and/or length of a 1-D or 2-D numpy array.

    Sends error log messages through the mediator if validation fails.

    Args:
        arr (NDArray[float64]): The array to validate.
        dims (int | None, optional): Expected number of dimensions, or None to ignore dimensions. Defaults to None.
        rows (int | None, optional): Expected number of rows, or None to ignore rows. Defaults to None.
        cols (int | None, optional): Expected number of cols, or None to ignore cols. Defaults to None.
    """
    if dims is not None and arr.ndim != dims:
        mediator.log_message(
            LoggingLevel.ERROR,
            f'Expected {dims} dimensions, but got {arr.ndim}',
        )

    if rows is not None and cols is not None:
        expected_shape = (rows, cols)
        if arr.shape != expected_shape:
            mediator.log_message(
                LoggingLevel.ERROR,
                f'Expected shape {expected_shape}, but got {arr.shape}',
            )
    elif rows is not None and arr.shape[0] != rows:
        mediator.log_message(
            LoggingLevel.ERROR,
            f'Expected {rows} rows, but got {arr.shape[0]}.',
        )
    elif cols is not None and arr.shape[1] != cols:
        mediator.log_message(
            LoggingLevel.ERROR,
            f'Expected {cols} rows, but got {arr.shape[1]}.',
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
    if len(shape) == 2:
        if shape[0] == shape[1]:
            return allclose(mat, mat.T, rtol, atol)
    mediator.log_message(
        LoggingLevel.ERROR,
        f'Expected matrix to be 2D and square but got shape {shape}',
    )
    return False
