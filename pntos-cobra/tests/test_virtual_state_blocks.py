import random

import pytest
from aspn23 import (
    MeasurementPositionVelocityAttitude as MeasurementPVA,
    MeasurementPositionVelocityAttitudeErrorModel,
    MeasurementPositionVelocityAttitudeReferenceFrame,
    TypeHeader,
    TypeTimestamp,
)
from navtk.filtering import (
    EstimateWithCovariance as NavtkEWC,
    NavSolution,
    PinsonErrorToStandard as NavtkPES,
)
from navtk.navutils import quat_to_dcm
from numpy import allclose, array, eye, fill_diagonal, float64, pi, zeros
from numpy.typing import NDArray
from pntos.api import (
    EstimateWithCovariance,
    EstimateWithCovarianceType,
    Mediator,
    Message,
    RegistryPlugin,
    VirtualStateBlock,
)
from pntos.cobra import StandardRegistryPlugin
from pntos.cobra.internal import (
    PinsonErrorToStandard,
    SimpleMediator,
    StateExtractor,
    VirtualStateBlockManager,
)
from pntos.cobra.utils import convert_timestamp_to_cpp

VSB_SOURCE = 'test_source'


#############################
### WRAPPED NAVTK CLASSES ###
class PinsonErrorToStandardWrapped(VirtualStateBlock):
    _mediator: Mediator
    _pva: MeasurementPVA | None
    _pes: NavtkPES
    source: str
    target: str

    def __init__(
        self,
        mediator: Mediator,
        source: str,
        target: str,
    ) -> None:
        self._mediator = mediator
        self.source = source
        self.target = target
        self._pes = NavtkPES(
            source,
            target,
            lambda time: NavSolution(
                array([self._pva.p1, self._pva.p2, self._pva.p3]),  # type: ignore[union-attr]
                array([self._pva.v1, self._pva.v2, self._pva.v3]),  # type: ignore[union-attr]
                quat_to_dcm(self._pva.quaternion).T,  # type: ignore
                time,
            ),
        )

    def receive_aux_data(self, aux: list[Message | None]) -> None:
        for msg in reversed(aux):
            if msg is not None and isinstance(msg.wrapped_message, MeasurementPVA):
                self._pva = msg.wrapped_message
                break

    def convert(
        self,
        estimate_with_covariance: EstimateWithCovariance,
        time: TypeTimestamp,
    ) -> EstimateWithCovariance:
        ewc = NavtkEWC(
            estimate_with_covariance.estimate, estimate_with_covariance.covariance
        )
        ewc = self._pes.convert(ewc, convert_timestamp_to_cpp(time))
        return EstimateWithCovariance(
            estimate_with_covariance.type, ewc.estimate, ewc.covariance
        )

    def convert_estimate(
        self, estimate: NDArray[float64], time: TypeTimestamp
    ) -> NDArray[float64]:
        return self._pes.convert_estimate(estimate, convert_timestamp_to_cpp(time))

    def jacobian(
        self, estimate: NDArray[float64], time: TypeTimestamp
    ) -> NDArray[float64]:
        return self._pes.jacobian(estimate, convert_timestamp_to_cpp(time))


#############################


@pytest.fixture
def mediator() -> SimpleMediator:
    registry_plugin = StandardRegistryPlugin('Standard registry')
    mediator = SimpleMediator(registry_plugin.identifier, RegistryPlugin)
    registry_plugin.init_plugin(mediator=mediator)
    registry = registry_plugin.new_registry()
    SimpleMediator.registry = registry
    SimpleMediator._controller_plugin = None
    return mediator


@pytest.fixture
def pva() -> Message:
    return Message(
        MeasurementPVA(
            header=TypeHeader(0, 0, 0, 0),
            time_of_validity=TypeTimestamp(0),
            reference_frame=MeasurementPositionVelocityAttitudeReferenceFrame.GEODETIC,
            p1=1,
            p2=1,
            p3=1,
            v1=0,
            v2=0,
            v3=0,
            quaternion=array((1, 0, 0, 0)),
            covariance=zeros([9, 9]),
            error_model=MeasurementPositionVelocityAttitudeErrorModel.NONE,
            error_model_params=array([], dtype=float64),
            integrity=[],
        ),
        source_identifier='test',
    )


@pytest.fixture
def est() -> NDArray[float64]:
    return array([0, 1, 2])


@pytest.fixture
def ewc(est: NDArray[float64]) -> EstimateWithCovariance:
    return EstimateWithCovariance(EstimateWithCovarianceType.EWC_GENERIC, est, eye(3))


def test_valid_state_extractor(mediator: SimpleMediator) -> None:
    vsb = StateExtractor(mediator, VSB_SOURCE, 'first_three_outta_five', 5, [0, 1, 2])
    ewc = EstimateWithCovariance(
        EstimateWithCovarianceType.EWC_GENERIC, array([0, 1, 2, 3, 4]), eye(5)
    )
    ewc_out = vsb.convert(ewc, TypeTimestamp(0))
    assert ewc_out.type == ewc.type
    assert len(ewc_out.estimate) == 3
    assert allclose(ewc_out.estimate[:3], ewc.estimate[:3])
    print(vsb._jac)
    print(ewc_out.covariance)
    assert allclose(ewc_out.covariance, eye(3))
    assert allclose(
        vsb.jacobian(ewc.estimate, TypeTimestamp(0)),
        array(([1, 0, 0, 0, 0], [0, 1, 0, 0, 0], [0, 0, 1, 0, 0])),
    )


def test_invalid_state_extractors(mediator: SimpleMediator) -> None:
    failed_to_catch = False
    try:
        vsb = StateExtractor(mediator, VSB_SOURCE, 'bad_state_size', 0, [1, 2, 3])
        failed_to_catch = True
    except RuntimeError:
        pass
    try:
        vsb = StateExtractor(mediator, VSB_SOURCE, 'bad_indices_length', 3, [])
        failed_to_catch = True
    except RuntimeError:
        pass
    try:
        vsb = StateExtractor(mediator, VSB_SOURCE, 'bad_index', 3, [1, 3])
        failed_to_catch = True
    except RuntimeError:
        pass
    try:
        vsb = StateExtractor(mediator, VSB_SOURCE, 'duplicate_index', 3, [0, 0])
        failed_to_catch = True
    except RuntimeError:
        pass
    try:
        vsb = StateExtractor(mediator, VSB_SOURCE, 'bad_est', 3, [0, 1])
        vsb.convert_estimate(array([1, 2, 3, 4]), TypeTimestamp(0))
        failed_to_catch = True
    except RuntimeError:
        pass
    try:
        vsb = StateExtractor(mediator, VSB_SOURCE, 'bad_ewc_dim', 3, [0, 1])
        vsb.convert(
            EstimateWithCovariance(
                EstimateWithCovarianceType.EWC_GENERIC,
                array([0, 1, 2]),
                array([1, 1, 1]),
            ),
            TypeTimestamp(0),
        )
        failed_to_catch = True
    except RuntimeError:
        pass
    assert not failed_to_catch


def test_pinson_error_to_standard(mediator: SimpleMediator) -> None:
    pes = PinsonErrorToStandard(mediator, VSB_SOURCE, 'pinson_direct')
    pesw = PinsonErrorToStandardWrapped(mediator, VSB_SOURCE, 'pinson_direct_wrapped')
    for i in range(1000):
        time = TypeTimestamp(i * 1000)
        pva = Message(
            MeasurementPVA(
                header=TypeHeader(0, 0, 0, 0),
                time_of_validity=time,
                reference_frame=MeasurementPositionVelocityAttitudeReferenceFrame.GEODETIC,
                p1=i * (pi / 180) % pi,
                p2=i * (pi / 180) % (pi / 2),
                p3=i,
                v1=i + 1,
                v2=i + 2,
                v3=i + 3,
                quaternion=array((1, 0, 0, 0)),
                covariance=zeros([9, 9]),
                error_model=MeasurementPositionVelocityAttitudeErrorModel.NONE,
                error_model_params=array([], dtype=float64),
                integrity=[],
            ),
            source_identifier='test',
        )
        pes.receive_aux_data([pva])
        est_in = array(
            (i, i + 1, i + 2, i + 3, i + 4, i + 5, i * 1e-6, i * 1.1e-6, i * 1.2e-6)
        )
        cov = eye(9)
        fill_diagonal(
            cov,
            [
                i,
                i + 0.001,
                i + 0.002,
                i + 0.003,
                i + 0.004,
                i + 0.005,
                i + 0.007,
                i + 0.008,
                i + 0.009,
            ],
        )
        ewc = EstimateWithCovariance(
            EstimateWithCovarianceType.EWC_GENERIC, est_in, cov
        )
        ewc1 = pes.convert(ewc, time)
        jac1 = pes.jacobian(est_in, time)

        pesw.receive_aux_data([pva])
        ewc2 = pesw.convert(ewc, time)
        jac2 = pesw.jacobian(est_in, time)
        assert allclose(ewc1.estimate, ewc2.estimate, equal_nan=True)
        assert allclose(ewc1.covariance, ewc2.covariance, equal_nan=True)
        assert allclose(jac1, jac2, equal_nan=True)


def test_invalid_pinson_error_to_standard(
    mediator: SimpleMediator, pva: Message
) -> None:
    failed_to_catch = False
    pes = PinsonErrorToStandard(mediator, VSB_SOURCE, 'pinson_direct')
    arr = array([1, 1, 1, 0, 0, 0, 0, 0, 0])
    assert isinstance(pva.wrapped_message, MeasurementPVA)
    # no pva
    try:
        pes.convert_estimate(arr, TypeTimestamp(0))
        failed_to_catch = True
    except RuntimeError:
        pass
    try:
        pes.jacobian(arr, TypeTimestamp(0))
        failed_to_catch = True
    except RuntimeError:
        pass
    # bad time
    pes.receive_aux_data([pva])
    try:
        pes.convert_estimate(arr, TypeTimestamp(1))
        failed_to_catch = True
    except RuntimeError:
        pass
    try:
        pes.jacobian(arr, TypeTimestamp(1))
        failed_to_catch = True
    except RuntimeError:
        pass
    # bad quat
    pva.wrapped_message.quaternion = None
    pva.wrapped_message.time_of_validity = TypeTimestamp(1)
    pes.receive_aux_data([pva])
    try:
        pes.convert_estimate(arr, TypeTimestamp(1))
        failed_to_catch = True
    except RuntimeError:
        pass
    try:
        pes.jacobian(arr, TypeTimestamp(1))
        failed_to_catch = True
    except RuntimeError:
        pass
    # bad pos
    pva.wrapped_message.quaternion = array([1, 0, 0, 0])
    pva.wrapped_message.p1 = None
    pes.receive_aux_data([pva])
    try:
        pes.convert_estimate(arr, TypeTimestamp(1))
        failed_to_catch = True
    except RuntimeError:
        pass
    try:
        pes.jacobian(arr, TypeTimestamp(1))
        failed_to_catch = True
    except RuntimeError:
        pass
    assert not failed_to_catch


def test_valid_vsb_manager_ops(
    mediator: SimpleMediator, est: NDArray[float64], ewc: EstimateWithCovariance
) -> None:
    vsbm = VirtualStateBlockManager(mediator)
    vsbs = []
    targets = []
    prevTarg = VSB_SOURCE
    max_val = 25
    targ_index = max_val - 1
    for i in range(max_val):
        newTarg = f't{i}'
        vsbs.append(StateExtractor(mediator, prevTarg, newTarg, 3, [0, 1, 2]))
        targets.append(newTarg)
        prevTarg = newTarg
    for vsb in random.sample(vsbs, max_val):
        vsbm.add_virtual_state_block(vsb)

    ewc_out = vsbm.convert(ewc, targets[0], targets[targ_index], TypeTimestamp(0))
    assert ewc_out is not None
    assert allclose(ewc.estimate, ewc_out.estimate)
    assert allclose(ewc.covariance, ewc_out.covariance)

    est_out = vsbm.convert_estimate(
        array(est), targets[0], targets[targ_index], TypeTimestamp(0)
    )
    assert est_out is not None
    assert allclose(est, est_out)

    jac_out = vsbm.jacobian(est, targets[0], targets[targ_index], TypeTimestamp(0))
    assert jac_out is not None
    assert allclose(jac_out, eye(3))

    start = vsbm.get_start_block_label(targets[targ_index])
    assert start[1] == VSB_SOURCE
    # test caching
    start = vsbm.get_start_block_label(targets[targ_index])
    assert start[1] == VSB_SOURCE

    new_se = StateExtractor(mediator, 'new_source', 't25', 3, [0, 1, 2])
    targets.append(new_se.target)
    vsbm.add_virtual_state_block(new_se)
    out_target = vsbm.get_virtual_state_block_labels()
    assert out_target is not None
    assert len(set(out_target) - set(targets)) == 0

    vsbm.remove_virtual_state_block(targets[targ_index])


def test_give_aux_data(mediator: SimpleMediator, pva: Message) -> None:
    vsbm = VirtualStateBlockManager(mediator)
    vsb = PinsonErrorToStandard(mediator, VSB_SOURCE, 'give_data')
    vsbm.add_virtual_state_block(vsb)
    aux: list[Message | None] = [pva]
    vsbm.give_virtual_state_block_aux_data('give_data', aux)
    node = vsbm._node_map['give_data']
    assert node.block._pva.p1 == pva.wrapped_message.p1  # type: ignore


def test_invalid_vsb_manager_ops(
    mediator: SimpleMediator, est: NDArray[float64], ewc: EstimateWithCovariance
) -> None:
    # vsb target and source cannot match
    vsbm = VirtualStateBlockManager(mediator)
    vsb = StateExtractor(mediator, VSB_SOURCE, VSB_SOURCE, 3, [0, 1, 2])
    labels = vsbm.get_virtual_state_block_labels()
    assert labels is None
    vsbm.add_virtual_state_block(vsb)
    assert vsb.target not in vsbm._node_map

    # assert only nodes are the VSB_SOURCE and 'duplicate' VSB
    vsb = StateExtractor(mediator, VSB_SOURCE, 'duplicate', 3, [0, 1, 2])
    vsbm.add_virtual_state_block(vsb)
    vsbm.add_virtual_state_block(vsb)
    assert len(vsbm._node_map.keys()) == 2

    time = TypeTimestamp(0)
    ewc_out = vsbm.convert(ewc, VSB_SOURCE, 'bad_targ', time)
    assert ewc_out is None

    est_out = vsbm.convert_estimate(est, VSB_SOURCE, 'bad_targ', time)
    assert est_out is None

    jac_out = vsbm.jacobian(est, VSB_SOURCE, 'bad_targ', time)
    assert jac_out is None

    pair = vsbm.get_start_block_label('bad_targ')
    assert pair[0] is False

    vsbm.give_virtual_state_block_aux_data('bad_targ', [])

    vsbm.remove_virtual_state_block('bad_targ')
    assert len(vsbm._node_map.keys()) == 2

    ewc_out = vsbm.convert(ewc, 'bad_source', 'duplicate', time)
    assert ewc_out is None
