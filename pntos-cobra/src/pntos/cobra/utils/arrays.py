from numpy import float64
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


def is_symmetric(mat: NDArray[float64], rtol: float = 1e-5, atol: float = 1e-8) -> bool:
    rows = mat.shape[0]
    for row in range(rows):
        for col in range(1, rows):
            a = mat[row, col]
            precision = atol + (rtol * abs(a))
            if abs(mat[row, col] - a) > precision:
                return False

    return True
