import pytest
from numpy import (
    allclose,
    arange,
    array,
    copy,
    diagflat,
    eye,
    float64,
    zeros,
)
from numpy.typing import NDArray
from pntos.api import (
    RegistryPlugin,
    StandardDynamicsModel,
    StandardFusionStrategy,
    StandardMeasurementModel,
)
from pntos.cobra import StandardRegistryPlugin
from pntos.cobra.config import BaseConfig
from pntos.cobra.internal import StandardMediator
from pntos.cobra.standard_plugins.EkfFusionStrategyPlugin import (
    EkfFusionStrategy,
    EkfFusionStrategyPlugin,
)

my_config: list[BaseConfig] = []


@pytest.fixture
def mediator() -> StandardMediator:
    registry_plugin = StandardRegistryPlugin('Simple registry', config=my_config)
    mediator = StandardMediator(registry_plugin.identifier, RegistryPlugin)
    registry_plugin.init_plugin(mediator=mediator)
    registry = registry_plugin.new_registry()
    StandardMediator.registry = registry
    StandardMediator._controller_plugin = None
    return mediator


@pytest.fixture
def plugin(mediator: StandardMediator) -> EkfFusionStrategyPlugin:
    plg = EkfFusionStrategyPlugin('plg')
    plg.init_plugin(mediator=mediator)
    return plg


@pytest.fixture
def strat(plugin: EkfFusionStrategyPlugin) -> EkfFusionStrategy:
    strat = plugin.new_fusion_strategy(StandardFusionStrategy)
    assert isinstance(strat, EkfFusionStrategy)
    return strat


def pop_strat(st: EkfFusionStrategy, ns: int, v1: float64 | int) -> None:
    x = arange(v1, v1 + ns, 1.0).reshape((ns, 1))
    p = diagflat(pow(x, 2))
    st.add_states(x, p)


def test_get_strategy_fail(plugin: EkfFusionStrategyPlugin) -> None:
    st = plugin.new_fusion_strategy(StandardDynamicsModel)
    assert st is None


def test_shutdown(plugin: EkfFusionStrategyPlugin) -> None:
    plugin.shutdown_plugin()


def test_get_no_states(strat: EkfFusionStrategy) -> None:
    assert strat.num_states == 0
    assert strat.estimate is None
    assert strat.covariance is None


def test_add_one_state(strat: EkfFusionStrategy) -> None:
    pop_strat(strat, 1, 0)
    assert strat.num_states == 1
    assert strat.estimate is not None
    assert strat.covariance is not None
    assert allclose(strat.estimate, array([[0]]))
    assert allclose(strat.covariance, array([[0]]))


def test_add_two_state(strat: EkfFusionStrategy) -> None:
    pop_strat(strat, 2, 0)
    assert strat.num_states == 2
    assert strat.estimate is not None
    assert strat.covariance is not None
    assert allclose(strat.estimate, array([[0], [1]]))
    assert allclose(strat.covariance, array([[0, 0], [0, 1]]))


def test_add_states_twice(strat: EkfFusionStrategy) -> None:
    pop_strat(strat, 2, 0)
    pop_strat(strat, 1, 5)
    assert strat.num_states == 3
    assert strat.estimate is not None
    assert strat.covariance is not None
    assert allclose(strat.estimate, array([[0], [1], [5]]))
    assert allclose(strat.covariance, array([[0, 0, 0], [0, 1, 0], [0, 0, 25]]))


def test_add_then_remove_once(strat: EkfFusionStrategy) -> None:
    pop_strat(strat, 1, 0)
    assert strat.num_states == 1
    strat.remove_states(0, 1)
    assert strat.num_states == 0
    assert strat.estimate is None
    assert strat.covariance is None


def test_add_then_remove_multi(strat: EkfFusionStrategy) -> None:
    pop_strat(strat, 2, 1)
    pop_strat(strat, 2, 4)
    assert strat.num_states == 4
    assert strat.estimate is not None
    assert strat.covariance is not None
    assert allclose(strat.estimate, array([[1], [2], [4], [5]]))
    assert allclose(
        strat.covariance,
        array([[1, 0, 0, 0], [0, 4, 0, 0], [0, 0, 16, 0], [0, 0, 0, 25]]),
    )
    strat.remove_states(1, 2)
    assert strat.num_states == 2
    assert strat.estimate is not None
    assert strat.covariance is not None
    assert allclose(strat.estimate, array([[1], [5]]))
    assert allclose(
        strat.covariance,
        array([[1, 0], [0, 25]]),
    )
    x = array([[9], [8], [7]])
    p = array([[1.1, 1.2, 1.3], [1.2, 3.3, 9.7], [1.3, 9.7, 2.2]])
    strat.add_states(x, p)
    assert strat.num_states == 5
    assert strat.estimate is not None
    assert strat.covariance is not None
    assert allclose(strat.estimate, array([[1], [5], [9], [8], [7]]))
    assert allclose(
        strat.covariance,
        array(
            [
                [1, 0, 0, 0, 0],
                [0, 25, 0, 0, 0],
                [0, 0, 1.1, 1.2, 1.3],
                [0, 0, 1.2, 3.3, 9.7],
                [0, 0, 1.3, 9.7, 2.2],
            ]
        ),
    )
    strat.remove_states(1, 3)
    assert strat.num_states == 2
    assert strat.estimate is not None
    assert strat.covariance is not None
    assert allclose(strat.estimate, array([[1], [7]]))
    assert allclose(
        strat.covariance,
        array([[1, 0], [0, 2.2]]),
    )


def test_add_states_mismatch_size(strat: EkfFusionStrategy) -> None:
    with pytest.raises(ValueError) as excinfo:
        strat.add_states(zeros((1, 1)), zeros((2, 2)))
    assert excinfo.type is ValueError
    with pytest.raises(ValueError) as excinfo:
        strat.add_states(zeros((1, 1)), zeros((2, 1)))
    assert excinfo.type is ValueError
    with pytest.raises(ValueError) as excinfo:
        strat.add_states(zeros((1, 1)), zeros((1, 2)))
    assert excinfo.type is ValueError


def test_add_states_wrong_dims(strat: EkfFusionStrategy) -> None:
    with pytest.raises(ValueError) as excinfo:
        strat.add_states(zeros(2), zeros((2, 2)))
    assert excinfo.type is ValueError


def test_add_states_w_initial_cross(strat: EkfFusionStrategy) -> None:
    # If there are no other initial states, there is nothing to form cross cov with
    with pytest.raises(ValueError) as excinfo:
        strat.add_states(zeros((1, 1)), zeros((1, 1)), zeros((1, 1)))
    assert excinfo.type is ValueError


def test_add_states_w_cross(strat: EkfFusionStrategy) -> None:
    pop_strat(strat, 2, 1)
    strat.add_states(array([[3.0]]), array([[9.0]]), array([[2.2], [3.3]]))
    assert strat.num_states == 3
    assert strat.estimate is not None
    assert strat.covariance is not None
    assert allclose(strat.estimate, array([[1.0], [2.0], [3.0]]))
    assert allclose(
        strat.covariance,
        array([[1, 0, 2.2], [0, 4.0, 3.3], [2.2, 3.3, 9.0]]),
    )


def test_add_states_w_cross_trans(strat: EkfFusionStrategy) -> None:
    pop_strat(strat, 2, 1)
    with pytest.raises(ValueError) as excinfo:
        strat.add_states(array([[3.0]]), array([[9.0]]), array([[2.2, 3.3]]))
    assert excinfo.type is ValueError


def test_add_states_w_cross_bad_shape(strat: EkfFusionStrategy) -> None:
    pop_strat(strat, 2, 1)
    with pytest.raises(ValueError) as excinfo:
        strat.add_states(array([[3.0]]), array([[9.0]]), array([[2.2], [3.3], [1.0]]))
    assert excinfo.type is ValueError
    with pytest.raises(ValueError) as excinfo:
        strat.add_states(array([[3.0]]), array([[9.0]]), array([[1.0]]))
    assert excinfo.type is ValueError


def test_remove_no_states(strat: EkfFusionStrategy) -> None:
    strat.remove_states(0, 0)
    strat.remove_states(0, 1)
    pop_strat(strat, 2, 1)
    strat.remove_states(0, 0)
    assert strat.num_states == 2
    assert strat.estimate is not None
    assert strat.covariance is not None
    assert allclose(strat.estimate, array([[1.0], [2.0]]))
    assert allclose(
        strat.covariance,
        array([[1, 0], [0, 4.0]]),
    )


def test_remove_bad_args(strat: EkfFusionStrategy) -> None:
    pop_strat(strat, 2, 1)
    strat.remove_states(0, -1)
    assert strat.num_states == 2
    assert strat.estimate is not None
    assert strat.covariance is not None
    assert allclose(strat.estimate, array([[1.0], [2.0]]))
    assert allclose(
        strat.covariance,
        array([[1, 0], [0, 4.0]]),
    )
    strat.remove_states(2, 1)
    assert strat.num_states == 2
    assert strat.estimate is not None
    assert strat.covariance is not None
    assert allclose(strat.estimate, array([[1.0], [2.0]]))
    assert allclose(
        strat.covariance,
        array([[1, 0], [0, 4.0]]),
    )
    strat.remove_states(0, 3)
    assert strat.num_states == 2
    assert strat.estimate is not None
    assert strat.covariance is not None
    assert allclose(strat.estimate, array([[1.0], [2.0]]))
    assert allclose(
        strat.covariance,
        array([[1, 0], [0, 4.0]]),
    )


def test_add_remove_states_w_cross(strat: EkfFusionStrategy) -> None:
    pop_strat(strat, 2, 1)
    strat.add_states(array([[3.0]]), array([[9.0]]), array([[2.2], [3.3]]))
    assert strat.num_states == 3
    assert strat.estimate is not None
    assert strat.covariance is not None
    assert allclose(strat.estimate, array([[1.0], [2.0], [3.0]]))
    assert allclose(
        strat.covariance,
        array([[1, 0, 2.2], [0, 4.0, 3.3], [2.2, 3.3, 9.0]]),
    )
    strat.remove_states(1, 1)
    assert strat.num_states == 2
    assert strat.estimate is not None
    assert strat.covariance is not None
    assert allclose(strat.estimate, array([[1.0], [3.0]]))
    assert allclose(
        strat.covariance,
        array([[1, 2.2], [2.2, 9.0]]),
    )
    strat.remove_states(0, 1)
    assert strat.num_states == 1
    assert strat.estimate is not None
    assert strat.covariance is not None
    assert allclose(strat.estimate, array([[3.0]]))
    assert allclose(
        strat.covariance,
        array([[9.0]]),
    )


def test_set_estimate_slice_full(strat: EkfFusionStrategy) -> None:
    pop_strat(strat, 5, 0)
    a = array([[9.0], [3.0], [4.0], [1.0], [-2.0]])
    strat.set_estimate_slice(a, 0)
    assert strat.num_states == 5
    assert strat.estimate is not None
    assert allclose(strat.estimate, a)


def test_set_estimate_slice_part(strat: EkfFusionStrategy) -> None:
    pop_strat(strat, 5, 0)
    a = array([[9.0], [3.0], [4.0], [1.0], [-2.0]])
    strat.set_estimate_slice(a[1:, :], 1)
    assert strat.num_states == 5
    assert strat.estimate is not None
    assert allclose(strat.estimate, array([[0.0], [3.0], [4.0], [1.0], [-2.0]]))
    strat.set_estimate_slice(a[3:, :], 0)
    assert strat.num_states == 5
    assert strat.estimate is not None
    assert allclose(strat.estimate, array([[1.0], [-2.0], [4.0], [1.0], [-2.0]]))
    strat.set_estimate_slice(a[3, :], 2)
    assert strat.num_states == 5
    assert strat.estimate is not None
    assert allclose(strat.estimate, array([[1.0], [-2.0], [1.0], [1.0], [-2.0]]))


def test_set_estimate_slice_bad_size(strat: EkfFusionStrategy) -> None:
    pop_strat(strat, 5, 0)
    with pytest.raises(ValueError) as excinfo:
        strat.set_estimate_slice(zeros((17, 1)), 1)
    assert excinfo.type is ValueError
    with pytest.raises(ValueError) as excinfo:
        strat.set_estimate_slice(zeros((1, 17)), 1)
    assert excinfo.type is ValueError


def test_set_estimate_slice_bad_shape(strat: EkfFusionStrategy) -> None:
    pop_strat(strat, 5, 0)
    a = array([9.0, 3.0, 4.0, 1.0, -2.0])
    with pytest.raises(ValueError) as excinfo:
        strat.set_estimate_slice(a, 0)
    assert excinfo.type is ValueError


def test_set_estimate_slice_oob(strat: EkfFusionStrategy) -> None:
    pop_strat(strat, 5, 0)
    a = array([[9.0], [3.0], [4.0], [1.0], [-2.0]])
    with pytest.raises(ValueError) as excinfo:
        strat.set_estimate_slice(a, 5)
    assert excinfo.type is ValueError


def test_set_estimate_slice_wrap(strat: EkfFusionStrategy) -> None:
    pop_strat(strat, 5, 0)
    a = array([[9.0], [3.0], [4.0], [1.0], [-2.0]])
    with pytest.raises(ValueError) as excinfo:
        strat.set_estimate_slice(a, 3)
    assert excinfo.type is ValueError


def test_set_cov_slice_full(strat: EkfFusionStrategy) -> None:
    pop_strat(strat, 3, 0)
    p = array([[1.1, 1.2, 1.3], [1.2, 3.3, 9.7], [1.3, 9.7, 2.2]])
    strat.set_covariance_slice(p, 0, 0)
    assert strat.covariance is not None
    assert allclose(strat.covariance, p)


def test_set_cov_slice_part_diag(strat: EkfFusionStrategy) -> None:
    pop_strat(strat, 3, 0)
    p = array([[1.1, 1.2], [1.2, 3.3]])
    strat.set_covariance_slice(p, 1, 1)
    assert strat.covariance is not None
    assert allclose(
        strat.covariance, array([[0, 0, 0], [0.0, 1.1, 1.2], [0.0, 1.2, 3.3]])
    )
    strat.set_covariance_slice(p, 0, 0)
    assert strat.covariance is not None
    assert allclose(
        strat.covariance, array([[1.1, 1.2, 0], [1.2, 3.3, 1.2], [0.0, 1.2, 3.3]])
    )


def test_set_cov_slice_part_off_diag(strat: EkfFusionStrategy) -> None:
    pop_strat(strat, 3, 0)
    p = array([[1.1, 1.2], [1.2, 3.3]])
    strat.set_covariance_slice(p, 0, 1)
    assert strat.covariance is not None
    assert allclose(
        strat.covariance,
        array([[0.0, 1.1, 1.2], [0.0, 1.2, 3.3], [0.0, 0.0, 4.0]]),
    )
    strat.set_covariance_slice(p, 1, 0)
    assert strat.covariance is not None
    assert allclose(
        strat.covariance,
        array([[0.0, 1.1, 1.2], [1.1, 1.2, 3.3], [1.2, 3.3, 4.0]]),
    )


def test_set_cov_slice_bad_size(strat: EkfFusionStrategy) -> None:
    pop_strat(strat, 2, 0)
    p = array([[1.1, 1.2], [1.2, 3.3]])
    with pytest.raises(ValueError) as excinfo:
        strat.set_covariance_slice(p, 0, 1)
    assert excinfo.type is ValueError
    with pytest.raises(ValueError) as excinfo:
        strat.set_covariance_slice(p, 1, 0)
    assert excinfo.type is ValueError
    with pytest.raises(ValueError) as excinfo:
        strat.set_covariance_slice(p, 1, 1)
    assert excinfo.type is ValueError


def test_set_cov_slice_bad_shape(strat: EkfFusionStrategy) -> None:
    pop_strat(strat, 2, 0)
    p = array([[1.1, 1.2, 2.2], [1.2, 3.3, 1.1]])
    with pytest.raises(ValueError) as excinfo:
        strat.set_covariance_slice(p, 0, 0)
    assert excinfo.type is ValueError
    with pytest.raises(ValueError) as excinfo:
        strat.set_covariance_slice(p.T, 0, 0)
    assert excinfo.type is ValueError


def test_prop_bad_model_g(strat: EkfFusionStrategy) -> None:
    def g_bad(x: NDArray[float64]) -> NDArray[float64]:
        return x[1:]

    pop_strat(strat, 2, 0)
    with pytest.raises(ValueError) as excinfo:
        strat.propagate(StandardDynamicsModel(g_bad, eye(2), zeros((2, 2))))
    assert excinfo.type is ValueError


def test_prop_bad_model_phi_qd(strat: EkfFusionStrategy) -> None:
    def g_good(x: NDArray[float64]) -> NDArray[float64]:
        return x

    pop_strat(strat, 2, 0)
    with pytest.raises(ValueError) as excinfo:
        strat.propagate(StandardDynamicsModel(g_good, eye(1), zeros((2, 2))))
    assert excinfo.type is ValueError
    with pytest.raises(ValueError) as excinfo:
        strat.propagate(StandardDynamicsModel(g_good, eye(3), zeros((2, 2))))
    assert excinfo.type is ValueError
    with pytest.raises(ValueError) as excinfo:
        strat.propagate(StandardDynamicsModel(g_good, zeros((2, 1)), zeros((2, 2))))
    assert excinfo.type is ValueError
    with pytest.raises(ValueError) as excinfo:
        strat.propagate(StandardDynamicsModel(g_good, zeros((1, 2)), zeros((2, 2))))
    assert excinfo.type is ValueError
    with pytest.raises(ValueError) as excinfo:
        strat.propagate(StandardDynamicsModel(g_good, zeros((2, 3)), zeros((2, 2))))
    assert excinfo.type is ValueError
    with pytest.raises(ValueError) as excinfo:
        strat.propagate(StandardDynamicsModel(g_good, zeros((3, 2)), zeros((2, 2))))
    assert excinfo.type is ValueError
    with pytest.raises(ValueError) as excinfo:
        strat.propagate(StandardDynamicsModel(g_good, zeros(2), zeros((2, 2))))
    assert excinfo.type is ValueError

    with pytest.raises(ValueError) as excinfo:
        strat.propagate(StandardDynamicsModel(g_good, eye(2), zeros((1, 1))))
    assert excinfo.type is ValueError
    with pytest.raises(ValueError) as excinfo:
        strat.propagate(StandardDynamicsModel(g_good, eye(2), zeros((3, 3))))
    assert excinfo.type is ValueError
    with pytest.raises(ValueError) as excinfo:
        strat.propagate(StandardDynamicsModel(g_good, eye(2), zeros((2, 3))))
    assert excinfo.type is ValueError
    with pytest.raises(ValueError) as excinfo:
        strat.propagate(StandardDynamicsModel(g_good, eye(2), zeros((3, 2))))
    assert excinfo.type is ValueError
    with pytest.raises(ValueError) as excinfo:
        strat.propagate(StandardDynamicsModel(g_good, eye(2), zeros((2, 1))))
    assert excinfo.type is ValueError
    with pytest.raises(ValueError) as excinfo:
        strat.propagate(StandardDynamicsModel(g_good, eye(2), zeros((1, 2))))
    assert excinfo.type is ValueError
    with pytest.raises(ValueError) as excinfo:
        strat.propagate(StandardDynamicsModel(g_good, eye(2), zeros(2)))
    assert excinfo.type is ValueError


def test_update_bad_model_h(strat: EkfFusionStrategy) -> None:
    def h_bad(x: NDArray[float64]) -> NDArray[float64]:
        return array([[0.0], [0.0]])

    def h_bad2(x: NDArray[float64]) -> NDArray[float64]:
        return array([0.0, 0.0])

    pop_strat(strat, 3, 0)
    with pytest.raises(ValueError) as excinfo:
        strat.update(
            StandardMeasurementModel(zeros((1, 1)), h_bad, zeros((1, 3)), eye(1))
        )
    assert excinfo.type is ValueError
    with pytest.raises(ValueError) as excinfo:
        strat.update(
            StandardMeasurementModel(zeros((3, 1)), h_bad, zeros((3, 3)), eye(3))
        )
    assert excinfo.type is ValueError
    with pytest.raises(ValueError) as excinfo:
        strat.update(
            StandardMeasurementModel(zeros((1, 1)), h_bad2, zeros((1, 3)), eye(1))
        )
    assert excinfo.type is ValueError
    with pytest.raises(ValueError) as excinfo:
        strat.update(
            StandardMeasurementModel(zeros((2, 1)), h_bad2, zeros((2, 2)), eye(2, 2))
        )
    assert excinfo.type is ValueError


def test_propagate(strat: EkfFusionStrategy) -> None:
    def g(x: NDArray[float64]) -> NDArray[float64]:
        out = copy(x)
        out[0, 0] += x[1, 0]
        out[1, 0] *= 2
        return out

    pop_strat(strat, 2, 0)
    phi = array([[1, 1], [0, 2]])
    qd = array([[0.1, 0.2], [0.2, 3.0]])
    strat.propagate(StandardDynamicsModel(g, phi, qd))
    assert strat.estimate is not None
    assert strat.covariance is not None
    assert allclose(strat.estimate, array([[1], [2]]))
    assert allclose(strat.covariance, array([[1.1, 2.2], [2.2, 7]]))


def test_sym(strat: EkfFusionStrategy) -> None:
    def g(x: NDArray[float64]) -> NDArray[float64]:
        return x

    x = array([[2.0], [4.4]])
    p = array([[1.0, 2.3], [1.7, 4.0]])
    strat.add_states(x, p)
    strat.propagate(StandardDynamicsModel(g, eye(2), zeros((2, 2))))
    assert strat.estimate is not None
    assert strat.covariance is not None
    assert allclose(strat.estimate, x)
    assert allclose(strat.covariance, array([[1.0, 2.0], [2.0, 4.0]]))


def test_update(strat: EkfFusionStrategy) -> None:
    def h(x: NDArray[float64]) -> NDArray[float64]:
        return x

    pop_strat(strat, 1, 1)
    z = array([[2]])
    R = array([[3]])
    H = array([[1]])
    strat.update(StandardMeasurementModel(z, h, H, R))
    assert strat.estimate is not None
    assert strat.covariance is not None
    assert allclose(strat.estimate, array([[1.25]]))
    assert allclose(strat.covariance, array([[0.75]]))
