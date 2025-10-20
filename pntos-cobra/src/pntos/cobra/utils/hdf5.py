import pickle
from pathlib import Path

import h5py
import numpy as np
from numpy import float64, int64

from pntos.api import LoggingLevel, Mediator, Message, RegistryValueTypeUnion


def save_to_hdf5_file(
    file: Path,
    store: dict[str, list[RegistryValueTypeUnion]],
    mediator: Mediator,
) -> None:
    """
    Utility function to store a dictionary into an HDF5 file.

    This function is designed to take in a dictionary containing string keys
    corresponding to lists of registry values. The intended use-case for this would be a
    scenario where each key in ``store`` corresponds to a key in a registry group, and
    each time the value changes at a given key in the registry, the changed value is
    appended to the corresponding list in the store.

    This functions makes a few assumptions:
    - Each list contains only one type in ``RegistryValueTypesUnion``.
    - If the type for a given key is ``list[list[str]]`` or ``list[NDArray[float64]]``,
    each element of the outer list is the same length.

    Note:
        While most datasets in the output HDF5 file will be understandable outside of
        Python (say, MATLAB), datasets for ``list[Message]`` types are stored as pickle
        dump objects, packed inside a ``numpy.void()`` object.

    Args:
        file (pathlib.Path): Path to ``.hdf5`` file.
        store (dict[str, list[RegistryValueTypeUnion]]): The dictionary to write to the
            HDF5 file, subject to the above assumptions.
        mediator (Mediator): A :class:`pntos.api.Mediator` instance.
    """
    with h5py.File(file.as_posix(), 'w') as hdf5_file:
        for key, val_list in store.items():
            if val_list:
                # Need to guarantee that all elements of val_list are the same type
                start_type = type(val_list[0])
                if not all(isinstance(val, start_type) for val in val_list):
                    mediator.log_message(
                        LoggingLevel.WARN,
                        'Multiple types within list is not supported.',
                    )
                    return

                if isinstance(val_list[0], str):
                    hdf5_file.create_dataset(
                        key,
                        data=np.array([i.encode('ascii') for i in val_list]),  # type: ignore[union-attr]
                    )
                elif (  # Check for list[list[str]]
                    isinstance(val_list[0], list)
                    and val_list[0]
                    and isinstance(val_list[0][0], str)
                ):
                    hdf5_file.create_dataset(
                        key,
                        data=np.array(
                            [[i.encode('ascii') for i in j] for j in val_list]  # type: ignore[union-attr]
                        ),
                    )
                elif isinstance(val_list[0], bool):
                    hdf5_file.create_dataset(key, data=np.array(val_list, dtype=bool))
                    hdf5_file.attrs[key] = 'bool'
                elif isinstance(val_list[0], int):
                    hdf5_file.create_dataset(key, data=np.array(val_list, dtype=int64))
                elif isinstance(val_list[0], float):
                    hdf5_file.create_dataset(
                        key, data=np.array(val_list, dtype=float64)
                    )
                elif isinstance(val_list[0], np.ndarray):
                    hdf5_file.create_dataset(key, data=val_list)
                elif isinstance(val_list[0], Message):
                    hdf5_file.create_dataset(key, data=np.void(pickle.dumps(val_list)))


def load_from_hdf5_file(
    file: Path, mediator: Mediator
) -> dict[str, list[RegistryValueTypeUnion]]:
    """
    Utility function for loading data from an HDF5 file into python.

    This function is intended to unpack an HDF5 file that was packed by
    :func:`save_to_hdf5_file` into a dictionary of keys and lists of logged values.
    See :func:`save_to_hdf5_file` for more information.

    Args:
        file (pathlib.Path): Path to ``.hdf5`` file.
        mediator (Mediator): A :class:`pntos.api.Mediator` instance.

    Returns:
       dict[str, list[RegistryValueTypeUnion]]
    """
    output: dict[str, list[RegistryValueTypeUnion]] = {}
    with h5py.File(file.as_posix(), 'r') as hdf5_file:
        for key, val in hdf5_file.items():
            if isinstance(val, h5py.Dataset):
                if val.ndim == 0:  # list[Message] is just pickled, so len = 0
                    output[key] = pickle.loads(val[()])
                elif isinstance(val[0], np.bytes_):
                    output[key] = [i.decode('ascii') for i in val]
                elif isinstance(val[0], np.bool_):
                    output[key] = [bool(i) for i in val]
                elif isinstance(val[0], int64):  # type: ignore[misc]
                    output[key] = [int(i) for i in val]
                elif isinstance(val[0], float64):  # type: ignore[misc]
                    output[key] = [float(i) for i in val]
                elif isinstance(val[0], np.ndarray) and isinstance(
                    val[0][0], np.bytes_
                ):
                    output[key] = [[i.decode() for i in v] for v in val]
                elif isinstance(val[0], np.ndarray):
                    output[key] = list(val)
                else:
                    mediator.log_message(
                        LoggingLevel.WARN,
                        f'Conversion not support for type in hdf5 file: {type(val[0])}',
                    )
    return output
