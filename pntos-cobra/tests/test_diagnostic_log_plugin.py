from pathlib import Path

import numpy as np
from aspn23 import (
    MeasurementPositionVelocityAttitude,
    MeasurementPositionVelocityAttitudeErrorModel,
    MeasurementPositionVelocityAttitudeReferenceFrame,
    TypeHeader,
    TypeTimestamp,
)
from pntos.api import (
    LoggingPlugin,
    Message,
    RegistryPlugin,
    RegistryValueTypeUnion,
    UtilityPlugin,
)
from pntos.cobra import (
    DiagnosticLogPlugin,
    StandardLoggingPlugin,
    StandardRegistryPlugin,
)
from pntos.cobra.internal import StandardMediator
from pntos.cobra.utils import load_from_hdf5_file

TEST_FILE = Path('./DELETEME.hdf5')


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
            elif not compare_messages(value1, value2, depth + 1):
                return False
        return True
    return m1 == m2


def test_diagnostic_log_plugin() -> None:
    plugin = DiagnosticLogPlugin('Diagnostic Log Plugin', output_file=TEST_FILE)
    mediator = StandardMediator(plugin.identifier, UtilityPlugin)

    registry_plugin = StandardRegistryPlugin('Registry Plugin')
    registry_mediator = StandardMediator(registry_plugin.identifier, RegistryPlugin)
    registry_plugin.init_plugin(mediator=registry_mediator)

    StandardMediator.registry = registry_plugin.new_registry()

    logging_plugin = StandardLoggingPlugin('Logging Plugin')
    logging_mediator = StandardMediator(logging_plugin.identifier, LoggingPlugin)
    logging_plugin.init_plugin(mediator=logging_mediator)

    StandardMediator._logging_plugin = logging_plugin

    plugin.init_plugin(mediator=mediator)

    test_dict: dict[str, RegistryValueTypeUnion] = {
        'str': 'Hello',
        'list-str': ['I', 'am', 'a', 'list', 'of', 'strings'],
        'int': np.random.randint(-1e9, 1e9),  # type: ignore[call-overload]
        'float': np.random.randn() * np.random.randint(-1e9, 1e9),  # type: ignore[call-overload]
        'bool': np.random.rand() > 0.5,
        'numpy array': np.random.randn(30),
        'message': generate_random_pva_message(),
    }

    # Set a set of values in the registry under the diagnostics key
    kv = StandardMediator.registry.batch_start('diagnostics')
    for key, val in test_dict.items():
        kv[key] = val
    kv.batch_end()

    # Make sure the output file doesn't exist
    if TEST_FILE.exists():
        TEST_FILE.unlink()

    # Shutdown the plugin to see if the output file is generated
    plugin.shutdown_plugin()

    assert TEST_FILE.exists()

    # Load in the file and make sure it's all correct
    result_dict = load_from_hdf5_file(TEST_FILE, mediator.log_message)

    for key, received_list in result_dict.items():
        # Make sure we only received one value in the received list
        assert len(received_list) == 1
        received_val = received_list[0]

        # Make sure there is a corresponding value in our test dictionary
        assert key in test_dict
        test_val = test_dict[key]
        assert type(received_val) is type(test_val)

        # Make sure values are the same
        if isinstance(received_val, np.ndarray):
            np.allclose(test_val, received_val)  # type: ignore[arg-type]
        elif isinstance(received_val, Message):
            compare_messages(test_val, received_val)
        else:
            assert test_val == received_val

    # Don't forget to remove the file
    TEST_FILE.unlink()
