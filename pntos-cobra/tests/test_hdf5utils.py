import os

import numpy as np
from aspn23 import (
    MeasurementPositionVelocityAttitude,
    MeasurementPositionVelocityAttitudeErrorModel,
    MeasurementPositionVelocityAttitudeReferenceFrame,
    TypeHeader,
    TypeTimestamp,
)
from pntos.api import Message, RegistryValueTypeUnion, UtilityPlugin
from pntos.cobra.internal import SimpleMediator
from pntos.cobra.utils import load_from_hdf5_file, save_to_hdf5_file

TEST_FILE = './DELETEME.hdf5'


def generate_random_pva_message(source_identifier: str = 'source') -> Message:
    return Message(
        MeasurementPositionVelocityAttitude(
            header=TypeHeader(
                np.random.randint(0, 10),
                np.random.randint(0, 10),
                np.random.randint(0, 10),
                np.random.randint(0, 10),
            ),
            time_of_validity=TypeTimestamp(np.random.randint(0, 1000)),
            reference_frame=MeasurementPositionVelocityAttitudeReferenceFrame.GEODETIC,
            p1=np.random.standard_normal(),
            p2=np.random.standard_normal(),
            p3=np.random.standard_normal(),
            v1=np.random.standard_normal(),
            v2=np.random.standard_normal(),
            v3=np.random.standard_normal(),
            quaternion=np.random.rand(4),
            covariance=np.random.rand(9, 9),
            error_model=MeasurementPositionVelocityAttitudeErrorModel.NONE,
            error_model_params=np.array([]),
            integrity=[],
        ),
        source_identifier=source_identifier,
    )


def compare_messages(m1: object, m2: object, depth: int = 0) -> bool:
    """
    The numpy arrays in Message objects do not seem to compare nicely with "==". This is
    a hacky workaround to run np.all() on any np elements, and run normal comparison
    otherwise.
    """
    if hasattr(m1, '__dict__') and depth < 3:
        for attr in m1.__dict__:
            value1 = getattr(m1, attr)
            value2 = getattr(m2, attr)

            if isinstance(value1, np.ndarray) and isinstance(value2, np.ndarray):
                if not np.allclose(value1, value2):
                    return False
            else:
                if not compare_messages(value1, value2, depth + 1):
                    return False
        return True
    else:
        return m1 == m2


def test_hdf5_to_and_from() -> None:
    test_dict: dict[str, list[RegistryValueTypeUnion]] = {
        'str': ['Hello', 'World!', '42'],
        'list[str]': [['I', 'am'], ['a', 'list'], ['of', 'strings']],
        'int': [1, -4, 2798],
        'float': [0.0, 1.0, 5.384, -18743.2698],
        'bool': [True, True, True, True, False, True],
        'ndarray': [np.array([i, i**2, i**3]) for i in range(3, 7)],
        'message': [generate_random_pva_message() for i in range(20)],
    }
    mediator = SimpleMediator('testing', UtilityPlugin)
    save_to_hdf5_file(TEST_FILE, test_dict, mediator)
    res_dict = load_from_hdf5_file(TEST_FILE, mediator)
    for test_key, test_val in test_dict.items():
        assert test_key in res_dict
        res_val = res_dict[test_key]
        assert type(test_val) == type(res_val)
        assert len(test_val) == len(res_val)
        assert type(test_val[0]) == type(res_val[0])
        if isinstance(test_val[0], Message):
            for test_v, res_v in zip(test_val, res_val, strict=True):
                assert compare_messages(test_v, res_v)
        elif isinstance(test_val[0], np.ndarray):
            for test_v, res_v in zip(test_val, res_val, strict=True):
                assert np.array_equal(test_v, res_v)  # type: ignore[arg-type]
        else:
            for test_v, res_v in zip(test_val, res_val, strict=True):
                assert test_v == res_v

    os.remove(TEST_FILE)
