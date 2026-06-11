import numpy as np
import pytest
from aspn23 import (
    MeasurementAltitude,
    MeasurementAltitudeErrorModel,
    MeasurementAltitudeReference,
    MeasurementVelocity,
    TypeHeader,
    TypeTimestamp,
)
from pntos.api import Message, RegistryPlugin
from pntos.cobra import StandardRegistryPlugin
from pntos.cobra.config import BaseConfig
from pntos.cobra.internal import StandardMediator
from pntos.extras import AdvancedPreprocessorPlugin
from pntos.extras.config import ZeroVelocity2dGeneratorConfig
from pntos.extras.internal import ZeroVelocity2dGenerator

########## Config setup ###############
LATERAL_VEL_SIGMA = 0.5
VERTICAL_VEL_SIGMA = 1.0
zerovel2d_generator_config1 = ZeroVelocity2dGeneratorConfig(
    group='config/zerovel2d_generator_with_any_channel',
    lateral_vel_sigma=LATERAL_VEL_SIGMA,
    vertical_vel_sigma=VERTICAL_VEL_SIGMA,
    output_channel='/generated/zero/velocity2d',
)
zerovel2d_generator_config2 = ZeroVelocity2dGeneratorConfig(
    group='config/zerovel2d_generator_with_desired_channel',
    channels=('/sensor/foo',),
    lateral_vel_sigma=LATERAL_VEL_SIGMA,
    vertical_vel_sigma=VERTICAL_VEL_SIGMA,
    output_channel='/generated/zero/velocity2d',
)
zerovel2d_generator_config3 = ZeroVelocity2dGeneratorConfig(
    group='config/zerovel2d_generator_with_dt_trigger',
    channels=('/sensor/foo',),
    trigger_dt_sec=1.0,
    lateral_vel_sigma=LATERAL_VEL_SIGMA,
    vertical_vel_sigma=VERTICAL_VEL_SIGMA,
    output_channel='/generated/zero/velocity2d',
)

config_list: list[BaseConfig] = [
    zerovel2d_generator_config1,
    zerovel2d_generator_config2,
    zerovel2d_generator_config3,
]


########## Utility functions ###############
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


########## Preprocessor Plugin Tests ###############


@pytest.fixture
def mediator() -> StandardMediator:
    registry_plugin = StandardRegistryPlugin('Standard registry', config=config_list)
    mediator = StandardMediator(registry_plugin.identifier, RegistryPlugin)
    registry_plugin.init_plugin(mediator=mediator)
    registry = registry_plugin.new_registry()
    StandardMediator.registry = registry
    return mediator


@pytest.fixture
def preprocessor_plugin(
    mediator: StandardMediator,
) -> AdvancedPreprocessorPlugin:
    ds_plugin = AdvancedPreprocessorPlugin('preprocessor_plugin')
    ds_plugin.init_plugin(mediator=mediator)
    return ds_plugin


def test_plugin_constructor(
    preprocessor_plugin: AdvancedPreprocessorPlugin,
) -> None:
    assert preprocessor_plugin.identifier == 'preprocessor_plugin'
    assert len(preprocessor_plugin.preprocessor_identifiers) == 1


def test_invalid_mediator() -> None:
    ds_plugin = AdvancedPreprocessorPlugin('preprocessor_plugin')
    ds_plugin.init_plugin()
    assert not ds_plugin.new_preprocessor(0, 'test')


def test_invalid_index(
    preprocessor_plugin: AdvancedPreprocessorPlugin,
) -> None:
    assert preprocessor_plugin.new_preprocessor(-1, 'test') is None
    assert (
        preprocessor_plugin.new_preprocessor(
            len(preprocessor_plugin.preprocessor_identifiers), 'test'
        )
        is None
    )


################## Shared Preprocessor Tests #################


@pytest.mark.parametrize(
    'preprocessor_id',
    ['zero_velocity2d_generator'],
)
def test_bad_config_group(
    preprocessor_plugin: AdvancedPreprocessorPlugin, preprocessor_id: str
) -> None:
    idx = preprocessor_plugin.preprocessor_identifiers.index(preprocessor_id)
    preprocessor = preprocessor_plugin.new_preprocessor(idx, 'wrong_group')
    assert preprocessor is None


@pytest.mark.parametrize(
    'preprocessor_id',
    argvalues=['zero_velocity2d_generator'],
)
def test_no_config_group(
    preprocessor_plugin: AdvancedPreprocessorPlugin, preprocessor_id: str
) -> None:
    idx = preprocessor_plugin.preprocessor_identifiers.index(preprocessor_id)
    preprocessor = preprocessor_plugin.new_preprocessor(idx, None)
    assert preprocessor is None


########### ZeroVelocity2dGenerator Preprocessor Tests ##############


def _contains_zerovel2d_message(messages: list[Message]) -> bool:
    """Check that messages array contains a generated zerovel2d message"""

    if len(messages) != 2:
        return False

    alt = messages[0].wrapped_message
    if not isinstance(alt, MeasurementAltitude):
        return False

    zerovel2d = messages[1].wrapped_message
    if not isinstance(zerovel2d, MeasurementVelocity):
        return False

    if zerovel2d.x is not None or zerovel2d.y != 0.0 or zerovel2d.z != 0.0:
        return False

    expected_cov = np.diag(np.square([LATERAL_VEL_SIGMA, VERTICAL_VEL_SIGMA]))
    return bool(np.all(zerovel2d.covariance == expected_cov))


@pytest.fixture
def zero_velocity2d_generator1(
    preprocessor_plugin: AdvancedPreprocessorPlugin,
) -> ZeroVelocity2dGenerator:
    idx = preprocessor_plugin.preprocessor_identifiers.index(
        ZeroVelocity2dGeneratorConfig.identifier
    )
    preprocessor = preprocessor_plugin.new_preprocessor(
        idx, zerovel2d_generator_config1.group
    )
    assert preprocessor is not None
    assert isinstance(preprocessor, ZeroVelocity2dGenerator)
    return preprocessor


@pytest.fixture
def zero_velocity2d_generator2(
    preprocessor_plugin: AdvancedPreprocessorPlugin,
) -> ZeroVelocity2dGenerator:
    idx = preprocessor_plugin.preprocessor_identifiers.index(
        ZeroVelocity2dGeneratorConfig.identifier
    )
    preprocessor = preprocessor_plugin.new_preprocessor(
        idx, zerovel2d_generator_config2.group
    )
    assert preprocessor is not None
    assert isinstance(preprocessor, ZeroVelocity2dGenerator)
    return preprocessor


@pytest.fixture
def zero_velocity2d_generator3(
    preprocessor_plugin: AdvancedPreprocessorPlugin,
) -> ZeroVelocity2dGenerator:
    idx = preprocessor_plugin.preprocessor_identifiers.index(
        ZeroVelocity2dGeneratorConfig.identifier
    )
    preprocessor = preprocessor_plugin.new_preprocessor(
        idx, zerovel2d_generator_config3.group
    )
    assert preprocessor is not None
    assert isinstance(preprocessor, ZeroVelocity2dGenerator)
    return preprocessor


def test_generator_with_any_channel(
    zero_velocity2d_generator1: ZeroVelocity2dGenerator,
) -> None:
    assert zerovel2d_generator_config1.channels is None

    # zerovel2d message generated from any channel
    msg = create_aspn_altitude('foo')
    out_msgs = zero_velocity2d_generator1.process_pntos_message(msg)
    assert _contains_zerovel2d_message(out_msgs)

    msg.source_identifier = 'bar'
    out_msgs = zero_velocity2d_generator1.process_pntos_message(msg)
    assert _contains_zerovel2d_message(out_msgs)


def test_generator_with_desired_channel(
    zero_velocity2d_generator2: ZeroVelocity2dGenerator,
) -> None:
    assert zerovel2d_generator_config2.channels is not None

    # no message generated from undesired channel
    msg = create_aspn_altitude('irrelevant' + zerovel2d_generator_config2.channels[0])
    out_msgs = zero_velocity2d_generator2.process_pntos_message(msg)
    assert not _contains_zerovel2d_message(out_msgs)

    # zerovel2d message generated from desired channel
    msg.source_identifier = zerovel2d_generator_config2.channels[0]
    out_msgs = zero_velocity2d_generator2.process_pntos_message(msg)
    assert _contains_zerovel2d_message(out_msgs)


def test_generator_with_dt_trigger(
    zero_velocity2d_generator3: ZeroVelocity2dGenerator,
) -> None:
    # no message generated from undesired channel
    assert zerovel2d_generator_config3.channels is not None
    msg = create_aspn_altitude('irrelevant' + zerovel2d_generator_config3.channels[0])
    assert isinstance(msg.wrapped_message, MeasurementAltitude)
    out_msgs = zero_velocity2d_generator3.process_pntos_message(msg)
    assert not _contains_zerovel2d_message(out_msgs)

    # zerovel2d message generated from first message received on desired channel
    msg.source_identifier = zerovel2d_generator_config3.channels[0]
    out_msgs = zero_velocity2d_generator3.process_pntos_message(msg)
    assert _contains_zerovel2d_message(out_msgs)

    # no message generated after 0.5 * trigger_dt has elapsed since last message
    trigger_dt = zerovel2d_generator_config3.trigger_dt_sec
    assert trigger_dt is not None
    trigger_dt_ns = int(trigger_dt * 1e9)
    msg.wrapped_message.time_of_validity.elapsed_nsec += trigger_dt_ns // 2
    out_msgs = zero_velocity2d_generator3.process_pntos_message(msg)
    assert not _contains_zerovel2d_message(out_msgs)

    # zerovel2d message generated after an additional 0.5 * trigger_dt has elapsed
    msg.wrapped_message.time_of_validity.elapsed_nsec += trigger_dt_ns // 2
    out_msgs = zero_velocity2d_generator3.process_pntos_message(msg)
    assert _contains_zerovel2d_message(out_msgs)
