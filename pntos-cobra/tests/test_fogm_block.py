import pytest
from aspn23 import (
    MeasurementPosition,
    MeasurementPositionErrorModel,
    MeasurementPositionReferenceFrame,
    TypeHeader,
    TypeTimestamp,
)
from numpy import allclose, array, deg2rad, diag, exp, eye, ones, zeros
from pntos.api import (
    EstimateWithCovariance,
    EstimateWithCovarianceType,
    Message,
    RegistryPlugin,
)
from pntos.cobra import SimpleRegistryPlugin
from pntos.cobra.config import BaseConfig
from pntos.cobra.internal import SimpleMediator
from pntos.cobra.state_modeling_simple_gps_ins.FogmBlock import (
    FogmBlock,
)

my_config: list[BaseConfig] = []


@pytest.fixture
def mediator() -> SimpleMediator:
    registry_plugin = SimpleRegistryPlugin('Simple registry', config=my_config)
    mediator = SimpleMediator(registry_plugin.identifier, RegistryPlugin)
    registry_plugin.init_plugin(mediator=mediator)
    registry = registry_plugin.new_registry()
    SimpleMediator.registry = registry
    SimpleMediator._controller_plugin = None
    return mediator


@pytest.fixture
def pos_meas() -> Message:
    return Message(
        MeasurementPosition(
            TypeHeader(0, 0, 0, 0),
            TypeTimestamp(1_000_000_000),
            MeasurementPositionReferenceFrame.GEODETIC,
            deg2rad(39.00001),
            deg2rad(-84.00001),
            1005,
            diag([25, 25, 100]),
            MeasurementPositionErrorModel.NONE,
            array([]),
            [],
        ),
        'pos_aux',
    )


def test_empty_init(mediator):
    with pytest.raises(RuntimeError) as excinfo:
        FogmBlock('bk', mediator, array([]), array([]))
    assert excinfo.type is RuntimeError


def test_single_init(mediator):
    blk = FogmBlock('bk', mediator, array([1.0]), array([2.0]))
    x_and_p = EstimateWithCovariance(
        EstimateWithCovarianceType.EWC_GENERIC, ones(1), eye(1)
    )
    dyn = blk.generate_dynamics(
        x_and_p, time_from=TypeTimestamp(0), time_to=TypeTimestamp(1e9)
    )
    assert dyn.Phi.shape == (1, 1)
    assert dyn.Qd.shape == (1, 1)


def test_double_flat_init(mediator):
    blk = FogmBlock('bk', mediator, array([1.0, 2.0]), array([3.0, 4.0]))
    x_and_p = EstimateWithCovariance(
        EstimateWithCovarianceType.EWC_GENERIC, ones(2), eye(2)
    )
    dyn = blk.generate_dynamics(
        x_and_p, time_from=TypeTimestamp(0), time_to=TypeTimestamp(1e9)
    )
    assert dyn.Phi.shape == (2, 2)
    assert dyn.Qd.shape == (2, 2)


def test_double_trans_init(mediator):
    blk = FogmBlock('bk', mediator, array([[1.0], [2.0]]), array([[3.0], [4.0]]))
    x_and_p = EstimateWithCovariance(
        EstimateWithCovarianceType.EWC_GENERIC, ones(2), eye(2)
    )
    dyn = blk.generate_dynamics(
        x_and_p, time_from=TypeTimestamp(0), time_to=TypeTimestamp(1e9)
    )
    assert dyn.Phi.shape == (2, 2)
    assert dyn.Qd.shape == (2, 2)


# Fail to create on all size mismatches
def test_bad_size1(mediator):
    with pytest.raises(RuntimeError) as excinfo:
        FogmBlock('bk', mediator, array([1.0]), array([[3.0], [4.0]]))
    assert excinfo.type is RuntimeError


def test_bad_size2(mediator):
    with pytest.raises(RuntimeError) as excinfo:
        FogmBlock('bk', mediator, array([1.0, 2.0, 3.0]), array([[3.0], [4.0]]))
    assert excinfo.type is RuntimeError


def test_bad_size3(mediator):
    with pytest.raises(RuntimeError) as excinfo:
        FogmBlock('bk', mediator, array([1.0, 2.0]), array([3.0]))
    assert excinfo.type is RuntimeError


def test_bad_size4(mediator):
    with pytest.raises(RuntimeError) as excinfo:
        FogmBlock('bk', mediator, array([1.0, 2.0]), array([3.0, 4.0, 5.0]))
    assert excinfo.type is RuntimeError


# tau must be positive
def test_neg_tau(mediator):
    with pytest.raises(RuntimeError) as excinfo:
        FogmBlock('bk', mediator, array([1.0, 2.0]), array([-3.0, 4.0]))
    assert excinfo.type is RuntimeError


def test_neg_tau2(mediator):
    with pytest.raises(RuntimeError) as excinfo:
        FogmBlock('bk', mediator, array([1.0, 2.0]), array([-3.0, -4.0]))
    assert excinfo.type is RuntimeError


def test_0_tau(mediator):
    with pytest.raises(RuntimeError) as excinfo:
        FogmBlock('bk', mediator, array([1.0, 2.0]), array([0, 4.0]))
    assert excinfo.type is RuntimeError


def test_0_tau2(mediator):
    with pytest.raises(RuntimeError) as excinfo:
        FogmBlock('bk', mediator, array([1.0, 2.0]), array([0, 0]))
    assert excinfo.type is RuntimeError


# Negative sigmas weird, but they get squared anyway, just log warning
def test_neg_sig(mediator):
    FogmBlock('bk', mediator, array([-1.0, 2.0]), array([3.0, 4.0]))


def test_neg_sig2(mediator):
    blk = FogmBlock('bk', mediator, array([-1.0, -2.0]), array([3.0, 4.0]))


# Aux data does nothing in this class
def test_empty_aux(mediator):
    blk = FogmBlock('bk', mediator, array([1.0]), array([3.0]))
    blk.receive_aux_data([])


def test_some_aux(mediator, pos_meas):
    blk = FogmBlock('bk', mediator, array([1.0]), array([3.0]))
    blk.receive_aux_data([Message(pos_meas, 'garbage')])


# An actual model
def test_gen_dyn(mediator):
    blk = FogmBlock('bk', mediator, array([3.0]), array([1.0]))
    x_and_p = EstimateWithCovariance(
        EstimateWithCovarianceType.EWC_GENERIC, zeros(1), eye(1)
    )
    dyn = blk.generate_dynamics(
        x_and_p, time_from=TypeTimestamp(0), time_to=TypeTimestamp(1e9)
    )
    res = dyn.g(array([1.0]))
    assert res.shape == (1,)
    assert res[0] == pytest.approx(0.36787944)


# Should be a no-op
def test_gen_dyn_eq(mediator):
    blk = FogmBlock('bk', mediator, array([3.0]), array([1.0]))
    x_and_p = EstimateWithCovariance(
        EstimateWithCovarianceType.EWC_GENERIC, array([3.0]), eye(1) * 9.0
    )
    dyn = blk.generate_dynamics(
        x_and_p, time_from=TypeTimestamp(1e9), time_to=TypeTimestamp(1e9)
    )
    res = dyn.g(x_and_p.estimate)
    assert res[0] == pytest.approx(x_and_p.estimate)
    assert dyn.Phi.shape == (1, 1)
    assert dyn.Qd.shape == (1, 1)
    assert dyn.Qd[0, 0] == pytest.approx(0.0)


# A negative dt likely incorrect but maybe allowable depending on context? No err here.
def test_gen_dyn_neg(mediator):
    blk = FogmBlock('bk', mediator, array([1.0]), array([3.0]))
    x_and_p = EstimateWithCovariance(
        EstimateWithCovarianceType.EWC_GENERIC, zeros(1), eye(1)
    )
    dyn = blk.generate_dynamics(
        x_and_p, time_from=TypeTimestamp(1e9), time_to=TypeTimestamp(0)
    )
    dyn.g(x_and_p.estimate)


def test_gen_dyn_multi(mediator):
    sigmas = array([1.0, 1.0, 1.0])
    taus = array([1.0, 1.0, 1.0])
    blk = FogmBlock('bk', mediator, sigmas, taus)
    x_and_p = EstimateWithCovariance(
        EstimateWithCovarianceType.EWC_GENERIC, array([0.5, 1.5, -2.5]), eye(3) * 3.0
    )
    dyn = blk.generate_dynamics(
        x_and_p, time_from=TypeTimestamp(0), time_to=TypeTimestamp(1e9)
    )
    res = dyn.g(x_and_p.estimate)
    assert res.shape == (3,)
    assert allclose(res, x_and_p.estimate * exp(-1 / taus))
    assert dyn.Phi.shape == (3, 3)
    assert dyn.Qd.shape == (3, 3)
    assert allclose(dyn.Phi @ x_and_p.estimate, res)
    q_exp = diag(2.0 * pow(sigmas, 2.0) / taus)
    alt = (q_exp + dyn.Phi @ q_exp @ dyn.Phi.T) * 0.5
    assert allclose(dyn.Qd, alt)
