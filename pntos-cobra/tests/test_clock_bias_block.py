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
    ClockBiasStateBlockConfig,
    config_from_registry,
)
from pntos.cobra.internal import ClockBiasStateBlock, StandardMediator

my_config: list[BaseConfig] = [
    ClockBiasStateBlockConfig(
        group='clock_bias_block',
        identifier='clock_bias',
        label='clock_bias',
        estimate_with_covariance=EstimateWithCovariance(
            EstimateWithCovarianceType.EWC_GENERIC,
            estimate=np.zeros(3),
            covariance=np.eye(3),
        ),
        h_0=2e-20,
        h_neg2=4e-29,
    )
]


@pytest.fixture
def mediator() -> StandardMediator:
    registry_plugin = StandardRegistryPlugin('Standard registry', config=my_config)
    mediator = StandardMediator(registry_plugin.identifier, RegistryPlugin)
    registry_plugin.init_plugin(mediator=mediator)
    registry = registry_plugin.new_registry()
    StandardMediator.registry = registry
    StandardMediator._controller_plugin = None
    return mediator


@pytest.fixture
def block(mediator: StandardMediator) -> ClockBiasStateBlock:
    config = config_from_registry(
        ClockBiasStateBlockConfig, mediator, 'clock_bias_block'
    )
    assert config is not None

    return ClockBiasStateBlock(
        config.label, mediator, config.h_0, config.h_neg2, config.q3
    )


def test_generate_dynamics_2state(block: ClockBiasStateBlock) -> None:
    t_start = TypeTimestamp(376_000_000)
    t_stop = TypeTimestamp(1_242_300_000)
    dt = (t_stop.elapsed_nsec - t_start.elapsed_nsec) * 1e-9
    dt2 = dt * dt
    pi_sq = np.pi * np.pi
    index_one = 0.5 * block._h_0 * dt + (2.0 / 3) * pi_sq * block._h_neg2 * dt * dt2
    diagonal = pi_sq * block._h_neg2 * dt2
    index_four = 2 * pi_sq * block._h_neg2 * dt

    expected_Phi = np.array([[1, dt], [0, 1]])
    expected_Qd = np.array([[index_one, diagonal], [diagonal, index_four]])

    dyn = block.generate_dynamics(None, t_start, t_stop)  # type:ignore[arg-type]

    init_x = np.array([0.0, 1.0])
    prop_x = dyn.g(init_x)
    assert np.allclose(prop_x, init_x + np.array([1.0 * dt, 0.0]))

    assert np.allclose(expected_Phi, dyn.Phi, 1e-25, 0.0)
    assert np.allclose(expected_Qd, dyn.Qd, 1e-25, 0.0)


def test_generate_dynamics_3state(block: ClockBiasStateBlock) -> None:
    block.num_states = 3
    block._q3 = 0.0

    t_start = TypeTimestamp(376_000_000)
    t_stop = TypeTimestamp(1_242_300_000)
    dt = (t_stop.elapsed_nsec - t_start.elapsed_nsec) * 1e-9
    dt2 = dt * dt
    pi_sq = np.pi * np.pi
    ct = pi_sq * block._h_neg2 * dt2
    third_state = np.array(
        [
            [
                (1.0 / 20) * block._q3 * dt2 * dt2 * dt,
                (1.0 / 8) * block._q3 * dt2 * dt2,
                (1.0 / 6) * block._q3 * dt2 * dt,
            ],
            [
                (1.0 / 8) * block._q3 * dt2 * dt2,
                (1.0 / 3) * block._q3 * dt * dt2,
                (1.0 / 2) * block._q3 * dt2,
            ],
            [
                (1.0 / 6) * block._q3 * dt2 * dt,
                (1.0 / 2) * block._q3 * dt2,
                block._q3 * dt,
            ],
        ]
    )

    expected_Phi = np.array(
        [
            [1.0, dt, 0.5 * dt2],
            [0, 1.0, dt],
            [0, 0, 1.0],
        ]
    )
    expected_Qd = (
        np.array(
            [
                [
                    0.5 * block._h_0 * dt
                    + (2.0 / 3) * pi_sq * block._h_neg2 * dt * dt2,
                    ct,
                    0,
                ],
                [ct, 2 * pi_sq * block._h_neg2 * dt, 0],
                [0, 0, 0],
            ]
        )
        + third_state
    )

    dyn = block.generate_dynamics(None, t_start, t_stop)  # type:ignore[arg-type]

    init_x = np.array([0.0, 1.0, 0.1])
    prop_x = dyn.g(init_x)
    assert np.allclose(
        prop_x, init_x + np.array([1.0 * dt + 0.1 * 0.5 * dt2, 0.1 * dt, 0.0])
    )

    assert np.allclose(expected_Phi, dyn.Phi, 1e-25, 0.0)
    assert np.allclose(expected_Qd, dyn.Qd, 1e-25, 0.0)
