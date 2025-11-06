import numpy as np
import pytest
from aspn23 import (
    TypeTimestamp,
)
from pntos.api import (
    EstimateWithCovariance,
    EstimateWithCovarianceType,
    RegistryPlugin,
)
from pntos.cobra import StandardRegistryPlugin
from pntos.cobra.config import (
    BaseConfig,
    ConstantStateBlockConfig,
    config_from_registry,
)
from pntos.cobra.internal import ConstantStateBlock, SimpleMediator

my_config: list[BaseConfig] = [
    ConstantStateBlockConfig(
        group='constant_block',
        identifier='constant',
        label='constant_block',
        estimate_with_covariance=EstimateWithCovariance(
            EstimateWithCovarianceType.EWC_GENERIC,
            estimate=np.array([100.0, 200.0, 300.0]).reshape((3, 1)),
            covariance=np.eye(3),
        ),
    ),
    ConstantStateBlockConfig(
        group='constant_block_with_noise',
        identifier='constant',
        label='constant_block_with_noise',
        estimate_with_covariance=EstimateWithCovariance(
            EstimateWithCovarianceType.EWC_GENERIC,
            estimate=np.array([100.0, 200.0, 300.0]).reshape((3, 1)),
            covariance=np.eye(3),
        ),
        Q=((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
    ),
]


@pytest.fixture
def mediator() -> SimpleMediator:
    registry_plugin = StandardRegistryPlugin('Standard registry', config=my_config)
    mediator = SimpleMediator(registry_plugin.identifier, RegistryPlugin)
    registry_plugin.init_plugin(mediator=mediator)
    registry = registry_plugin.new_registry()
    SimpleMediator.registry = registry
    SimpleMediator._controller_plugin = None
    return mediator


@pytest.fixture
def block(mediator: SimpleMediator) -> ConstantStateBlock:
    config = config_from_registry(ConstantStateBlockConfig, mediator, 'constant_block')
    assert config is not None
    assert config.estimate_with_covariance is not None

    return ConstantStateBlock(
        config.label, mediator, config.estimate_with_covariance.estimate.shape[0]
    )


@pytest.fixture
def block_with_noise(mediator: SimpleMediator) -> ConstantStateBlock:
    config = config_from_registry(
        ConstantStateBlockConfig, mediator, 'constant_block_with_noise'
    )
    assert config is not None
    assert config.estimate_with_covariance is not None

    return ConstantStateBlock(
        config.label,
        mediator,
        config.estimate_with_covariance.estimate.shape[0],
        np.array(config.Q),
    )


def test_constant_generate_dynamics(block: ConstantStateBlock) -> None:
    t1 = TypeTimestamp(0)
    t2 = TypeTimestamp(1_000_000_000)
    t3 = TypeTimestamp(101_000_000_000)

    expected_Phi = np.eye(3)
    expected_Qd = np.zeros((3, 3))

    dyn = block.generate_dynamics(None, t1, t2)  # type:ignore[arg-type]

    # propagating x shouldn't change x
    init_x = np.random.rand(3, 1)
    prop_x = dyn.g(init_x)
    assert np.all(prop_x == init_x)
    assert np.all(expected_Phi == dyn.Phi)
    assert np.all(expected_Qd == dyn.Qd)

    # propagating over longer interval should be the exact same as a shorter interval
    dyn2 = block.generate_dynamics(None, t2, t3)  # type:ignore[arg-type]
    assert np.all(dyn2.Phi == dyn.Phi)
    assert np.all(dyn2.Qd == dyn.Qd)
    prop_x2 = dyn2.g(prop_x)
    assert np.all(prop_x2 == prop_x)


def test_generate_dynamics_with_noise(block_with_noise: ConstantStateBlock) -> None:
    t1 = TypeTimestamp(0)
    t2 = TypeTimestamp(1_000_000_000)
    t3 = TypeTimestamp(101_000_000_000)

    expected_Phi = np.eye(3)
    expected_Qd = np.eye(3)

    dyn = block_with_noise.generate_dynamics(None, t1, t2)  # type:ignore[arg-type]

    # propagating x shouldn't change x
    init_x = np.random.rand(3, 1)
    prop_x = dyn.g(init_x)
    assert np.all(prop_x == init_x)
    assert np.all(expected_Phi == dyn.Phi)
    assert np.all(expected_Qd == dyn.Qd)

    # propagating over longer interval should be the exact same as a shorter interval
    expected_Qd *= 100
    dyn2 = block_with_noise.generate_dynamics(None, t2, t3)  # type:ignore[arg-type]
    assert np.all(dyn2.Phi == dyn.Phi)
    assert np.all(dyn2.Qd == expected_Qd)
    prop_x2 = dyn2.g(prop_x)
    assert np.all(prop_x2 == prop_x)


def test_various_sizes(mediator: SimpleMediator) -> None:
    t1 = TypeTimestamp(0)
    t2 = TypeTimestamp(1_000_000_000)
    for num_states in range(1, 101, 10):
        block = ConstantStateBlock('block', mediator, num_states)

        init_x = np.random.rand(num_states, 1)
        dyn = block.generate_dynamics(None, t1, t2)  # type:ignore[arg-type]
        assert np.all(dyn.Phi == dyn.Phi)
        assert np.all(dyn.Qd == dyn.Qd)
        prop_x = dyn.g(init_x)
        assert np.all(prop_x == init_x)
