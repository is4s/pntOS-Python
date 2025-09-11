from copy import deepcopy

import numpy as np
import pytest
from aspn23 import (
    MeasurementAltitude,
    MeasurementAltitudeErrorModel,
    MeasurementAltitudeReference,
    MeasurementBarometer,
    MeasurementBarometerErrorModel,
    MeasurementImu,
    MeasurementImuImuType,
    TypeHeader,
    TypeTimestamp,
)
from pntos.api import Message, Preprocessor, RegistryPlugin
from pntos.api.plugins.preprocessor import Preprocessor
from pntos.cobra import (
    StandardPreprocessorPlugin,
    StandardRegistryPlugin,
)
from pntos.cobra.config import (
    BarometerToAltitudeConfig,
    BaseConfig,
    DownsamplerConfig,
    ImuRotatorConfig,
    TimeAdjusterConfig,
)
from pntos.cobra.internal import (
    BarometerToAltitudePreprocessor,
    ImuRotationPreprocessor,
    SimpleMediator,
    TimeAdjusterPreprocessor,
)

downsampler_config = DownsamplerConfig(
    channels_to_downsample=['test1', 'test2', 'test3'],
    identifier='downsampler',
    downsampling_factors=[2, 3, -1],
    group='test',
)
inertial_config = ImuRotatorConfig(
    group='/config/imu_rotator',
    identifier='imu_rotator',
    channel='/sensor/imu',
    C_imu_to_platform=((0, 1, 0), (1, 0, 0), (0, 0, -1)),
)
time_adjuster_config = TimeAdjusterConfig(
    group='test',
    identifier='time_adjuster',
    channel_to_correct='/sensor/imu',
    expected_dt_nsec=int(0.01 * 1e9),
)
baro_to_alt_config = BarometerToAltitudeConfig(
    group='baro_test', identifier='baro_converter', channel='/sensor/barometer'
)

config_list: list[BaseConfig] = [
    downsampler_config,
    inertial_config,
    time_adjuster_config,
    baro_to_alt_config,
]

########## Preprocessor Plugin Tests ###############


@pytest.fixture
def mediator() -> SimpleMediator:
    registry_plugin = StandardRegistryPlugin('Standard registry', config=config_list)
    mediator = SimpleMediator(registry_plugin.identifier, RegistryPlugin)
    registry_plugin.init_plugin(mediator=mediator)
    registry = registry_plugin.new_registry()
    SimpleMediator.registry = registry
    return mediator


@pytest.fixture
def preprocessor_plugin(
    mediator: SimpleMediator,
) -> StandardPreprocessorPlugin:
    ds_plugin = StandardPreprocessorPlugin('preprocessor_plugin')
    ds_plugin.init_plugin(mediator=mediator)
    return ds_plugin


def test_plugin_constructor(
    preprocessor_plugin: StandardPreprocessorPlugin,
) -> None:
    assert preprocessor_plugin.identifier == 'preprocessor_plugin'
    assert len(preprocessor_plugin.preprocessor_identifiers) == 4


def test_invalid_mediator() -> None:
    ds_plugin = StandardPreprocessorPlugin('preprocessor_plugin')
    ds_plugin.init_plugin()
    assert not ds_plugin.new_preprocessor(0, 'test')


def test_invalid_index(
    preprocessor_plugin: StandardPreprocessorPlugin,
) -> None:
    assert preprocessor_plugin.new_preprocessor(-1, 'test') is None
    assert (
        preprocessor_plugin.new_preprocessor(
            len(preprocessor_plugin.preprocessor_identifiers), 'test'
        )
        is None
    )


################## Downsampler Tests #################
@pytest.fixture
def downsampler(
    preprocessor_plugin: StandardPreprocessorPlugin,
) -> Preprocessor:
    ds = preprocessor_plugin.new_preprocessor(0, 'test')
    assert ds is not None
    return ds


def create_aspn_altitude(identifier: str) -> Message:
    header = TypeHeader(0, 0, 0, 0)
    time = TypeTimestamp(0)
    alt = MeasurementAltitude(
        header,
        time,
        MeasurementAltitudeReference.HAE,
        200.0,
        0.2,
        MeasurementAltitudeErrorModel.NONE,
        error_model_params=np.array([]),
        integrity=[],
    )

    return Message(alt, identifier)


def assert_aspn_alt_equal(alt1: MeasurementAltitude, alt2: MeasurementAltitude) -> None:
    assert alt1.time_of_validity.elapsed_nsec == alt2.time_of_validity.elapsed_nsec
    assert alt1.altitude == alt2.altitude
    assert alt1.variance == alt2.variance


def test_invalid_config_group(
    preprocessor_plugin: StandardPreprocessorPlugin,
) -> None:
    # No config group
    ds = preprocessor_plugin.new_preprocessor(0)
    assert ds is None
    # Wrong config group
    ds = preprocessor_plugin.new_preprocessor(0, 'invalid')
    assert ds is not None

    t1 = create_aspn_altitude('test1')
    t1_alt_meas = t1.wrapped_message
    assert isinstance(t1_alt_meas, MeasurementAltitude)

    msg_list = ds.process_pntos_message(t1)
    assert msg_list is not None
    assert len(msg_list) > 0
    # Both messages should come through because of invalid config
    assert isinstance(msg_list[0].wrapped_message, MeasurementAltitude)
    assert_aspn_alt_equal(t1_alt_meas, msg_list[0].wrapped_message)
    assert isinstance(msg_list[0].wrapped_message, MeasurementAltitude)
    assert_aspn_alt_equal(t1_alt_meas, msg_list[0].wrapped_message)


def test_bad_channel(
    preprocessor_plugin: StandardPreprocessorPlugin,
) -> None:
    ds = preprocessor_plugin.new_preprocessor(0, 'test')
    assert ds is not None
    bad = create_aspn_altitude('bad')
    bad_alt_meas = bad.wrapped_message
    assert isinstance(bad_alt_meas, MeasurementAltitude)

    # All messages should come through
    msg_list = ds.process_pntos_message(bad)
    assert msg_list is not None
    assert len(msg_list) > 0
    assert isinstance(msg_list[0].wrapped_message, MeasurementAltitude)
    assert_aspn_alt_equal(bad_alt_meas, msg_list[0].wrapped_message)
    msg_list = ds.process_pntos_message(bad)
    assert msg_list is not None
    assert isinstance(msg_list[0].wrapped_message, MeasurementAltitude)
    assert_aspn_alt_equal(bad_alt_meas, msg_list[0].wrapped_message)


def test_channel_one(
    downsampler: Preprocessor,
) -> None:
    t1 = create_aspn_altitude('test1')
    t1_alt_meas = t1.wrapped_message
    assert isinstance(t1_alt_meas, MeasurementAltitude)

    msg_list = downsampler.process_pntos_message(t1)
    assert msg_list is not None
    assert len(msg_list) > 0
    assert isinstance(msg_list[0].wrapped_message, MeasurementAltitude)
    assert_aspn_alt_equal(t1_alt_meas, msg_list[0].wrapped_message)
    msg_list = downsampler.process_pntos_message(t1)
    assert msg_list is None
    msg_list = downsampler.process_pntos_message(t1)
    assert msg_list is not None
    assert len(msg_list) > 0
    assert isinstance(msg_list[0].wrapped_message, MeasurementAltitude)
    assert_aspn_alt_equal(t1_alt_meas, msg_list[0].wrapped_message)
    msg_list = downsampler.process_pntos_message(t1)
    assert msg_list is None


def test_channel_two(
    downsampler: Preprocessor,
) -> None:
    t2 = create_aspn_altitude('test2')
    t2_alt_meas = t2.wrapped_message
    assert isinstance(t2_alt_meas, MeasurementAltitude)

    # 1 every 3 messages should come through
    msg_list = downsampler.process_pntos_message(t2)
    assert msg_list is not None
    assert len(msg_list) > 0
    assert isinstance(msg_list[0].wrapped_message, MeasurementAltitude)
    assert_aspn_alt_equal(t2_alt_meas, msg_list[0].wrapped_message)
    msg_list = downsampler.process_pntos_message(t2)
    assert msg_list is None
    msg_list = downsampler.process_pntos_message(t2)
    assert msg_list is None
    msg_list = downsampler.process_pntos_message(t2)
    assert msg_list is not None
    assert len(msg_list) > 0
    assert isinstance(msg_list[0].wrapped_message, MeasurementAltitude)
    assert_aspn_alt_equal(t2_alt_meas, msg_list[0].wrapped_message)


def test_channel_three(
    downsampler: Preprocessor,
) -> None:
    t3 = create_aspn_altitude('test3')
    t3_alt_meas = t3.wrapped_message
    assert isinstance(t3_alt_meas, MeasurementAltitude)

    # All messages should come through
    msg_list = downsampler.process_pntos_message(t3)
    assert msg_list is not None
    assert len(msg_list) > 0
    assert isinstance(msg_list[0].wrapped_message, MeasurementAltitude)
    assert msg_list is not None
    assert_aspn_alt_equal(t3_alt_meas, msg_list[0].wrapped_message)
    msg_list = downsampler.process_pntos_message(t3)
    assert msg_list is not None
    assert len(msg_list) > 0
    assert isinstance(msg_list[0].wrapped_message, MeasurementAltitude)
    assert_aspn_alt_equal(t3_alt_meas, msg_list[0].wrapped_message)
    msg_list = downsampler.process_pntos_message(t3)
    assert msg_list is not None
    assert len(msg_list) > 0
    assert isinstance(msg_list[0].wrapped_message, MeasurementAltitude)
    assert_aspn_alt_equal(t3_alt_meas, msg_list[0].wrapped_message)


########### IMU Rotator Tests ##############


@pytest.fixture
def imu_rotator_preprocessor(
    preprocessor_plugin: StandardPreprocessorPlugin,
) -> Preprocessor:
    idx = preprocessor_plugin.preprocessor_identifiers.index('imu_rotator')
    preprocessor = preprocessor_plugin.new_preprocessor(idx, '/config/imu_rotator')
    assert preprocessor is not None
    assert isinstance(preprocessor, ImuRotationPreprocessor)
    return preprocessor


@pytest.fixture
def imu_message() -> Message:
    return Message(
        MeasurementImu(
            TypeHeader(0, 1, 2, 3),
            TypeTimestamp(1_000_000_000),
            MeasurementImuImuType.INTEGRATED,
            np.array([0.01, 0.02, 0.03]),
            np.array([0.04, 0.05, 0.06]),
            [],
        ),
        '/sensor/imu',
    )


def test_empty_config_group(
    preprocessor_plugin: StandardPreprocessorPlugin,
) -> None:
    idx = preprocessor_plugin.preprocessor_identifiers.index('imu_rotator')
    invalid_preprocessor = preprocessor_plugin.new_preprocessor(idx)
    assert invalid_preprocessor is None


def test_imu_rotation(
    imu_rotator_preprocessor: Preprocessor, imu_message: Message
) -> None:
    original_message = deepcopy(imu_message)
    assert isinstance(imu_message.wrapped_message, MeasurementImu)
    assert isinstance(original_message.wrapped_message, MeasurementImu)

    out_messages = imu_rotator_preprocessor.process_pntos_message(imu_message)
    assert out_messages is not None
    assert len(out_messages) == 1
    rotated_imu_message = out_messages[0]
    assert isinstance(rotated_imu_message.wrapped_message, MeasurementImu)

    assert not np.allclose(
        original_message.wrapped_message.meas_accel,
        rotated_imu_message.wrapped_message.meas_accel,
    )
    assert not np.allclose(
        original_message.wrapped_message.meas_gyro,
        rotated_imu_message.wrapped_message.meas_gyro,
    )

    DCM = np.array(inertial_config.C_imu_to_platform)
    assert np.allclose(
        DCM @ original_message.wrapped_message.meas_accel,
        rotated_imu_message.wrapped_message.meas_accel,
    )
    assert np.allclose(
        DCM @ original_message.wrapped_message.meas_gyro,
        rotated_imu_message.wrapped_message.meas_gyro,
    )


########### Time Adjuster Tests ##############


@pytest.fixture
def time_adjuster_preprocessor(
    preprocessor_plugin: StandardPreprocessorPlugin,
) -> Preprocessor:
    idx = preprocessor_plugin.preprocessor_identifiers.index('time_adjuster')
    preprocessor = preprocessor_plugin.new_preprocessor(idx, 'test')
    assert preprocessor is not None
    assert isinstance(preprocessor, TimeAdjusterPreprocessor)
    return preprocessor


def create_imu_message(time: int) -> Message:
    return Message(
        MeasurementImu(
            TypeHeader(0, 1, 2, 3),
            TypeTimestamp(time),
            MeasurementImuImuType.INTEGRATED,
            np.array([0.01, 0.02, 0.03]),
            np.array([0.04, 0.05, 0.06]),
            [],
        ),
        '/sensor/imu',
    )


def test_time_adjuster(time_adjuster_preprocessor: Preprocessor) -> None:
    first_message = create_imu_message(int(1e9))
    second_message = create_imu_message(int(1.01 * 1e9))
    bad_message = create_imu_message(int(1.5 * 1e9))
    low_dt_message = create_imu_message(int(1.025 * 1e9))
    within_tolerance_above_dt_message = create_imu_message(int(1.040015 * 1e9))
    within_tolerance_below_dt_message = create_imu_message(int(1.049978 * 1e9))
    last_message = create_imu_message(int(1.06 * 1e9))

    out_messages = time_adjuster_preprocessor.process_pntos_message(first_message)
    assert out_messages is not None
    assert len(out_messages) == 1
    out_msg = out_messages[0]
    assert isinstance(out_msg.wrapped_message, MeasurementImu)
    assert out_msg.wrapped_message.time_of_validity.elapsed_nsec == 1e9

    out_messages = time_adjuster_preprocessor.process_pntos_message(second_message)
    assert out_messages is not None
    assert len(out_messages) == 1
    out_msg = out_messages[0]
    assert isinstance(out_msg.wrapped_message, MeasurementImu)
    assert out_msg.wrapped_message.time_of_validity.elapsed_nsec == 1.01 * 1e9

    out_messages = time_adjuster_preprocessor.process_pntos_message(bad_message)
    assert out_messages is not None
    assert len(out_messages) == 1
    synth_message = out_messages[0]
    assert isinstance(synth_message.wrapped_message, MeasurementImu)
    assert synth_message.wrapped_message.time_of_validity.elapsed_nsec == 1.02 * 1e9

    out_messages = time_adjuster_preprocessor.process_pntos_message(low_dt_message)
    assert out_messages is not None
    assert len(out_messages) == 1
    synth_message = out_messages[0]
    assert isinstance(synth_message.wrapped_message, MeasurementImu)
    assert synth_message.wrapped_message.time_of_validity.elapsed_nsec == 1.03 * 1e9

    out_messages = time_adjuster_preprocessor.process_pntos_message(
        within_tolerance_above_dt_message
    )
    assert out_messages is not None
    assert len(out_messages) == 1
    out_msg = out_messages[0]
    assert isinstance(out_msg.wrapped_message, MeasurementImu)
    # account for floating point precision errors
    assert np.allclose(
        out_msg.wrapped_message.time_of_validity.elapsed_nsec, 1.040015 * 1e9
    )

    out_messages = time_adjuster_preprocessor.process_pntos_message(
        within_tolerance_below_dt_message
    )
    assert out_messages is not None
    assert len(out_messages) == 1
    out_msg = out_messages[0]
    assert isinstance(out_msg.wrapped_message, MeasurementImu)
    # account for floating point precision errors
    assert np.allclose(
        out_msg.wrapped_message.time_of_validity.elapsed_nsec, 1.049978 * 1e9
    )

    out_messages = time_adjuster_preprocessor.process_pntos_message(last_message)
    assert out_messages is not None
    assert len(out_messages) == 1
    out_msg = out_messages[0]
    assert isinstance(out_msg.wrapped_message, MeasurementImu)
    assert out_msg.wrapped_message.time_of_validity.elapsed_nsec == 1.06 * 1e9


########### Barometer to Altitude Converter Tests ##############


@pytest.fixture
def baro_message() -> Message:
    header = TypeHeader(4, 5, 6, 7)
    time = TypeTimestamp(0)
    baro = MeasurementBarometer(
        header,
        time,
        90000.0,
        10,
        MeasurementBarometerErrorModel.NONE,
        error_model_params=np.array([]),
        integrity=[],
    )

    return Message(baro, '/sensor/barometer')


@pytest.fixture
def baro_to_alt(
    preprocessor_plugin: StandardPreprocessorPlugin,
) -> Preprocessor:
    idx = preprocessor_plugin.preprocessor_identifiers.index('baro_converter')
    preprocessor = preprocessor_plugin.new_preprocessor(idx, 'baro_test')
    assert preprocessor is not None
    assert isinstance(preprocessor, BarometerToAltitudePreprocessor)
    return preprocessor


def test_bad_config_group(preprocessor_plugin: StandardPreprocessorPlugin) -> None:
    idx = preprocessor_plugin.preprocessor_identifiers.index('baro_converter')
    preprocessor = preprocessor_plugin.new_preprocessor(idx, 'wrong_group')
    assert preprocessor is None


def test_no_config_group(preprocessor_plugin: StandardPreprocessorPlugin) -> None:
    idx = preprocessor_plugin.preprocessor_identifiers.index('baro_converter')
    preprocessor = preprocessor_plugin.new_preprocessor(idx, None)
    assert preprocessor is None


def test_baro_conversion(baro_message: Message, baro_to_alt: Preprocessor) -> None:
    msg_list = baro_to_alt.process_pntos_message(baro_message)
    assert msg_list is not None
    out_msg = msg_list[0]
    assert isinstance(out_msg.wrapped_message, MeasurementAltitude)
    assert np.isclose(out_msg.wrapped_message.altitude, 988.50)
    expected_var = (988.50 / 90000) ** 2 * 10
    assert np.isclose(out_msg.wrapped_message.variance, expected_var)


def test_wrong_aspn_type(baro_to_alt: Preprocessor) -> None:
    imu_msg = create_imu_message(int(1e9))
    msg_list = baro_to_alt.process_pntos_message(imu_msg)
    assert msg_list is not None
    out_msg = msg_list[0]
    assert isinstance(out_msg.wrapped_message, MeasurementImu)
    assert imu_msg == out_msg
