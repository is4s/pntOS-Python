import numpy as np
import pytest
from aspn23 import (
    MeasurementAltitude,
    MeasurementAltitudeErrorModel,
    MeasurementAltitudeReference,
    TypeHeader,
    TypeTimestamp,
)
from pntos.api import Message, Preprocessor, RegistryPlugin
from pntos.api.plugins.preprocessor import Preprocessor
from pntos.cobra import (
    SimplePreprocessorDownsamplerPlugin,
    SimpleRegistryPlugin,
)
from pntos.cobra.config import BaseConfig, DownsamplerConfig
from pntos.cobra.internal import SimpleMediator

config_list: list[BaseConfig] = [
    DownsamplerConfig(
        channels_to_downsample=['test1', 'test2', 'test3'],
        downsampling_factors=[2, 3, -1],
        group='test',
    ),
]


@pytest.fixture
def mediator() -> SimpleMediator:
    registry_plugin = SimpleRegistryPlugin('Simple registry', config=config_list)
    mediator = SimpleMediator(registry_plugin.identifier, RegistryPlugin)
    registry_plugin.init_plugin(mediator=mediator)
    registry = registry_plugin.new_registry()
    SimpleMediator.registry = registry
    return mediator


@pytest.fixture
def preprocessor_downsampler_plugin(
    mediator: SimpleMediator,
) -> SimplePreprocessorDownsamplerPlugin:
    ds_plugin = SimplePreprocessorDownsamplerPlugin('preprocessor_downsampler')
    ds_plugin.init_plugin(mediator=mediator)
    return ds_plugin


@pytest.fixture
def downsampler(
    preprocessor_downsampler_plugin: SimplePreprocessorDownsamplerPlugin,
) -> Preprocessor:
    ds = preprocessor_downsampler_plugin.new_preprocessor(0, 'test')
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


def assert_aspn_alt_equal(alt1: MeasurementAltitude, alt2: MeasurementAltitude):
    assert alt1.time_of_validity.elapsed_nsec == alt2.time_of_validity.elapsed_nsec
    assert alt1.altitude == alt2.altitude
    assert alt1.variance == alt2.variance


def test_plugin_constructor(
    preprocessor_downsampler_plugin: SimplePreprocessorDownsamplerPlugin,
) -> None:
    assert preprocessor_downsampler_plugin.identifier == 'preprocessor_downsampler'
    assert len(preprocessor_downsampler_plugin.preprocessor_identifiers) == 1


def test_invalid_mediator() -> None:
    ds_plugin = SimplePreprocessorDownsamplerPlugin('preprocessor_downsampler')
    ds_plugin.init_plugin()
    assert not ds_plugin.new_preprocessor(0, 'test')


def test_preprocessor_plugin_errors(
    preprocessor_downsampler_plugin: SimplePreprocessorDownsamplerPlugin,
) -> None:
    assert not preprocessor_downsampler_plugin.new_preprocessor(0)
    assert not preprocessor_downsampler_plugin.new_preprocessor(-1, 'test')
    assert not preprocessor_downsampler_plugin.new_preprocessor(2, 'test')


def test_invalid_config_group(
    preprocessor_downsampler_plugin: SimplePreprocessorDownsamplerPlugin,
) -> None:
    ds = preprocessor_downsampler_plugin.new_preprocessor(0, 'invalid')
    assert ds is not None
    t1 = create_aspn_altitude('test1')
    t1_alt_meas = t1.wrapped_message
    assert isinstance(t1_alt_meas, MeasurementAltitude)

    msg_list = ds.process_pntos_message(t1)
    assert len(msg_list) > 0
    # Both messages should come through because of invalid config
    assert isinstance(msg_list[0].wrapped_message, MeasurementAltitude)
    assert_aspn_alt_equal(t1_alt_meas, msg_list[0].wrapped_message)
    assert isinstance(msg_list[0].wrapped_message, MeasurementAltitude)
    assert_aspn_alt_equal(t1_alt_meas, msg_list[0].wrapped_message)


def test_bad_channel(
    preprocessor_downsampler_plugin: SimplePreprocessorDownsamplerPlugin,
) -> None:
    ds = preprocessor_downsampler_plugin.new_preprocessor(0, 'test')
    assert ds is not None
    bad = create_aspn_altitude('bad')
    bad_alt_meas = bad.wrapped_message
    assert isinstance(bad_alt_meas, MeasurementAltitude)

    # All messages should come through
    msg_list = ds.process_pntos_message(bad)
    assert len(msg_list) > 0
    assert isinstance(msg_list[0].wrapped_message, MeasurementAltitude)
    assert_aspn_alt_equal(bad_alt_meas, msg_list[0].wrapped_message)
    msg_list = ds.process_pntos_message(bad)
    assert isinstance(msg_list[0].wrapped_message, MeasurementAltitude)
    assert_aspn_alt_equal(bad_alt_meas, msg_list[0].wrapped_message)


def test_channel_one(
    downsampler: Preprocessor,
) -> None:
    t1 = create_aspn_altitude('test1')
    t1_alt_meas = t1.wrapped_message
    assert isinstance(t1_alt_meas, MeasurementAltitude)

    msg_list = downsampler.process_pntos_message(t1)
    assert len(msg_list) > 0
    assert isinstance(msg_list[0].wrapped_message, MeasurementAltitude)
    assert_aspn_alt_equal(t1_alt_meas, msg_list[0].wrapped_message)
    msg_list = downsampler.process_pntos_message(t1)
    assert len(msg_list) == 0
    msg_list = downsampler.process_pntos_message(t1)
    assert len(msg_list) > 0
    assert isinstance(msg_list[0].wrapped_message, MeasurementAltitude)
    assert_aspn_alt_equal(t1_alt_meas, msg_list[0].wrapped_message)
    msg_list = downsampler.process_pntos_message(t1)
    assert len(msg_list) == 0


def test_channel_two(
    downsampler: Preprocessor,
) -> None:
    t2 = create_aspn_altitude('test2')
    t2_alt_meas = t2.wrapped_message
    assert isinstance(t2_alt_meas, MeasurementAltitude)

    # 1 every 3 messages should come through
    msg_list = downsampler.process_pntos_message(t2)
    assert len(msg_list) > 0
    assert isinstance(msg_list[0].wrapped_message, MeasurementAltitude)
    assert_aspn_alt_equal(t2_alt_meas, msg_list[0].wrapped_message)
    msg_list = downsampler.process_pntos_message(t2)
    assert len(msg_list) == 0
    msg_list = downsampler.process_pntos_message(t2)
    assert len(msg_list) == 0
    msg_list = downsampler.process_pntos_message(t2)
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
    assert len(msg_list) > 0
    assert isinstance(msg_list[0].wrapped_message, MeasurementAltitude)
    assert_aspn_alt_equal(t3_alt_meas, msg_list[0].wrapped_message)
    msg_list = downsampler.process_pntos_message(t3)
    assert len(msg_list) > 0
    assert isinstance(msg_list[0].wrapped_message, MeasurementAltitude)
    assert_aspn_alt_equal(t3_alt_meas, msg_list[0].wrapped_message)
    msg_list = downsampler.process_pntos_message(t3)
    assert len(msg_list) > 0
    assert isinstance(msg_list[0].wrapped_message, MeasurementAltitude)
    assert_aspn_alt_equal(t3_alt_meas, msg_list[0].wrapped_message)
