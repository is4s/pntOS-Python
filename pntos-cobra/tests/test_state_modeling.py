from copy import deepcopy

import numpy as np
import pytest
from aspn23 import (
    MeasurementAltitude,
    MeasurementAltitudeErrorModel,
    MeasurementAltitudeReference,
    MeasurementDirection3DToPoints,
    MeasurementImu,
    MeasurementImuImuType,
    MeasurementPosition,
    MeasurementPositionErrorModel,
    MeasurementPositionReferenceFrame,
    MeasurementPositionVelocityAttitude,
    MeasurementPositionVelocityAttitudeErrorModel,
    MeasurementPositionVelocityAttitudeReferenceFrame,
    MeasurementVelocity,
    MeasurementVelocityErrorModel,
    MeasurementVelocityReferenceFrame,
    TypeDirection3DToPoint,
    TypeDirection3DToPointErrorModel,
    TypeDirection3DToPointReferenceFrame,
    TypeHeader,
    TypeImageFeature,
    TypeRemotePoint,
    TypeRemotePointPositionReferenceFrame,
    TypeTimestamp,
)
from conftest import gxp
from navtk.navutils import (
    d_rpy_to_dcm_wrt_p,
    d_rpy_to_dcm_wrt_r,
    d_rpy_to_dcm_wrt_y,
    hae_to_msl,
    rpy_to_dcm,
)
from pntos.api import (
    EstimateWithCovariance,
    EstimateWithCovarianceType,
    GenXandP,
    Message,
    RegistryPlugin,
    StandardMeasurementProcessor,
    StandardStateBlock,
    StandardStateModelProvider,
    StateModelProviderType,
)
from pntos.cobra import (
    StandardGpsInsStateModelingPlugin,
    StandardRegistryPlugin,
)
from pntos.cobra.config import (
    BaseConfig,
    ImuConfig,
    PinsonStateBlockConfig,
    SensorConfig,
    SensorMeasurementProcessorConfig,
    StateExtractorConfig,
)
from pntos.cobra.internal import (
    AltitudeMeasurementProcessor,
    Direction3DToPointsMeasurementProcessor,
    Pinson15NedBlock,
    PinsonBodyVelocityMeasurementProcessor,
    PinsonErrorToStandard,
    PinsonPositionMeasurementProcessor,
    PinsonPosVelMeasurementProcessor,
    PinsonVelocityMeasurementProcessor,
    PinsonWithLeverArmPositionMeasurementProcessor,
    PinsonWithNedFogmPositionMeasurementProcessor,
    PositionMeasurementProcessor,
    StandardMediator,
    StateExtractor,
)
from pntos.cobra.utils.navigation import (
    OMEGA_E,
    delta_lat_to_north,
    delta_lon_to_east,
    east_to_delta_lon,
    meridian_radius,
    north_to_delta_lat,
    quat_to_dcm,
    skew,
    transverse_radius,
)

_lever_arm = (-2.0, 3.0, 5.0)
# _orientation = (0.707106781, 0.0, 0.707106781, 0.0)
_orientation = (1.0, 0.0, 0.0, 0.0)

my_config: list[BaseConfig] = [
    PinsonStateBlockConfig(
        group='config/pinson_block',
        label='pinson15',
        imu_model=ImuConfig(
            group='config/pinson_block',
            # HG9900 model
            accel_bias_sigma=(25 * 9.81e-6, 25 * 9.81e-6, 25 * 9.81e-6),
            accel_bias_tau=(3600.0, 3600.0, 3600.0),
            accel_random_walk_sigma=(1e-12, 1e-12, 1e-12),
            gyro_bias_sigma=(
                0.003 * np.pi / 180 / 3600,
                0.003 * np.pi / 180 / 3600,
                0.003 * np.pi / 180 / 3600,
            ),
            gyro_bias_tau=(3600.0, 3600.0, 3600.0),
            gyro_random_walk_sigma=(
                0.002 * np.pi / 180 / 60,
                0.002 * np.pi / 180 / 60,
                0.002 * np.pi / 180 / 60,
            ),
        ),
    ),
    SensorMeasurementProcessorConfig(
        group='config/test',
        identifier='NA',
        label='NA',
        channel='NA',
        state_block_labels=('NA',),
        sensor_config=SensorConfig(
            group='config/gp3d_state_modeling',
            lever_arm=_lever_arm,
            orientation=(1.0, 0.0, 0.0, 0.0),
            sensor_name='NA',
        ),
    ),
    StateExtractorConfig(
        group='config/extractor',
        source='some_real_block',
        target='extractor',
        incoming_state_size=3,
        indices_to_extract=(0, 1),
    ),
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
def state_modeling_plugin(
    mediator: StandardMediator,
) -> StandardGpsInsStateModelingPlugin:
    sm_plugin = StandardGpsInsStateModelingPlugin('gps_ins_state_modeling')
    sm_plugin.init_plugin(mediator=mediator)
    return sm_plugin


@pytest.fixture
def state_model_provider(
    state_modeling_plugin: StandardGpsInsStateModelingPlugin,
) -> StateModelProviderType | None:
    return state_modeling_plugin.new_state_model_provider(StandardStateModelProvider)


@pytest.fixture
def pinson_block(
    state_model_provider: StateModelProviderType,
) -> StandardStateBlock | None:
    out = state_model_provider.new_block(0, None, 'pinson15', 'config/pinson_block')
    if isinstance(out, StandardStateBlock):
        return out
    return None


@pytest.fixture
def position_mp(
    state_model_provider: StateModelProviderType,
) -> StandardMeasurementProcessor:
    out = state_model_provider.new_processor(
        0, None, 'position', ['pinson'], 'config/test'
    )
    assert isinstance(out, StandardMeasurementProcessor)
    return out


@pytest.fixture
def position_mp2(
    state_model_provider: StateModelProviderType,
) -> StandardMeasurementProcessor:
    out = state_model_provider.new_processor(
        2, None, 'position', ['pinson', 'fogm'], 'config/test'
    )
    assert isinstance(out, StandardMeasurementProcessor)
    return out


@pytest.fixture
def position_mp3(
    state_model_provider: StateModelProviderType,
) -> StandardMeasurementProcessor:
    out = state_model_provider.new_processor(
        4, None, 'position', ['pinson', 'fogm', 'fogm2'], 'config/test'
    )
    assert isinstance(out, StandardMeasurementProcessor)
    return out


@pytest.fixture
def direct_pos(
    state_model_provider: StateModelProviderType,
) -> StandardMeasurementProcessor:
    out = state_model_provider.new_processor(
        7, None, 'position', ['pinson', 'fogm'], 'config/test'
    )
    assert isinstance(out, StandardMeasurementProcessor)
    assert isinstance(out, PositionMeasurementProcessor)
    return out


all_pos_proc_type = list[
    tuple[
        PinsonPositionMeasurementProcessor
        | PinsonWithNedFogmPositionMeasurementProcessor
        | PinsonWithLeverArmPositionMeasurementProcessor,
        int,
        int,
        int,
    ]
]


@pytest.fixture
def all_pos_processors(
    position_mp: PinsonPositionMeasurementProcessor,
    position_mp2: PinsonWithNedFogmPositionMeasurementProcessor,
    position_mp3: PinsonWithLeverArmPositionMeasurementProcessor,
) -> all_pos_proc_type:
    # Second arg is num expected states, third is expected number of state block labels, 4th is index to create
    return [(position_mp, 15, 1, 0), (position_mp2, 18, 2, 2), (position_mp3, 21, 3, 4)]


@pytest.fixture
def gen_x_and_p_all_pos(all_pos_processors: all_pos_proc_type) -> GenXandP:
    def _test_gen_x_and_p(sb_labels: list[str]) -> EstimateWithCovariance | None:
        out: EstimateWithCovariance | None = None
        for m in all_pos_processors:
            if not set(m[0].state_block_labels).difference(sb_labels):
                out = gxp(m[1])
        return out

    return _test_gen_x_and_p


@pytest.fixture
def velocity_mp(
    state_model_provider: StateModelProviderType,
) -> StandardMeasurementProcessor | None:
    out = state_model_provider.new_processor(
        1, None, 'velocity', ['pinson'], 'config/test'
    )
    if isinstance(out, StandardMeasurementProcessor):
        return out
    return None


@pytest.fixture
def altitude_mp(
    state_model_provider: StateModelProviderType,
) -> StandardMeasurementProcessor:
    out = state_model_provider.new_processor(
        3, None, 'altitude', ['pinson', 'fogm'], '/config/cobra/sensor'
    )
    assert isinstance(out, StandardMeasurementProcessor)
    assert isinstance(out, AltitudeMeasurementProcessor)

    return out


@pytest.fixture
def body_velocity_mp(
    state_model_provider: StateModelProviderType,
) -> StandardMeasurementProcessor:
    out = state_model_provider.new_processor(
        5, None, 'body_velocity', ['pinson'], 'config/test'
    )
    assert isinstance(out, StandardMeasurementProcessor)
    assert isinstance(out, PinsonBodyVelocityMeasurementProcessor)

    return out


@pytest.fixture
def posvel_mp(
    state_model_provider: StateModelProviderType,
) -> StandardMeasurementProcessor:
    out = state_model_provider.new_processor(
        6, None, 'posvel', ['pinson'], 'config/test'
    )
    assert isinstance(out, StandardMeasurementProcessor)
    assert isinstance(out, PinsonPosVelMeasurementProcessor)

    return out


@pytest.fixture
def direction3D_to_points_mp(
    state_model_provider: StateModelProviderType,
) -> StandardMeasurementProcessor:
    out = state_model_provider.new_processor(
        8, None, 'direction3D_to_points', ['pinson'], 'config/test'
    )
    assert isinstance(out, StandardMeasurementProcessor)
    assert isinstance(out, Direction3DToPointsMeasurementProcessor)

    return out


@pytest.fixture
def pva_aux_data() -> Message:
    return Message(
        MeasurementPositionVelocityAttitude(
            TypeHeader(0, 0, 0, 0),
            TypeTimestamp(1_000_000_000),
            MeasurementPositionVelocityAttitudeReferenceFrame.GEODETIC,
            np.deg2rad(39),
            np.deg2rad(-84),
            1000,
            2,
            3,
            4,
            np.array([1, 0, 0, 0]),
            np.zeros((9, 9)),
            MeasurementPositionVelocityAttitudeErrorModel.NONE,
            np.array([]),
            [],
        ),
        'pva_aux',
    )


@pytest.fixture
def zero_pva_aux_data(dummy_pva: MeasurementPositionVelocityAttitude) -> Message:
    return Message(dummy_pva, 'pva_aux')


@pytest.fixture
def pos_meas() -> Message:
    return Message(
        MeasurementPosition(
            TypeHeader(0, 0, 0, 0),
            TypeTimestamp(1_000_000_000),
            MeasurementPositionReferenceFrame.GEODETIC,
            np.deg2rad(39.00001),
            np.deg2rad(-84.00001),
            1005,
            np.diag([25, 25, 100]),
            MeasurementPositionErrorModel.NONE,
            np.array([]),
            [],
        ),
        'gps_position',
    )


@pytest.fixture
def vel_meas() -> Message:
    return Message(
        MeasurementVelocity(
            TypeHeader(0, 0, 0, 0),
            TypeTimestamp(1_000_000_000),
            MeasurementVelocityReferenceFrame.NED,
            2.2,
            3.3,
            4.4,
            np.diag([1, 4, 0.5]),
            MeasurementVelocityErrorModel.NONE,
            np.array([]),
            [],
        ),
        'gps_velocity',
    )


@pytest.fixture
def posvel_meas() -> Message:
    return Message(
        MeasurementPositionVelocityAttitude(
            TypeHeader(0, 0, 0, 0),
            TypeTimestamp(1_000_000_000),
            MeasurementPositionVelocityAttitudeReferenceFrame.GEODETIC,
            np.deg2rad(39.00001),
            np.deg2rad(-84.00001),
            1005,
            2.2,
            3.3,
            4.4,
            None,
            np.diag([25, 25, 100, 1, 4, 0.5]),
            MeasurementPositionVelocityAttitudeErrorModel.NONE,
            np.array([]),
            [],
        ),
        'gps_posvel',
    )


@pytest.fixture
def bodyvel_meas() -> Message:
    return Message(
        MeasurementVelocity(
            TypeHeader(0, 0, 0, 0),
            TypeTimestamp(1_000_000_000),
            MeasurementVelocityReferenceFrame.SENSOR,
            4.4,
            3.3,
            2.2,
            np.diag([0.5, 0.5, 0.5]),
            MeasurementVelocityErrorModel.NONE,
            np.array([]),
            [],
        ),
        'body_velocity',
    )


@pytest.fixture
def alt_meas() -> Message:
    return Message(
        MeasurementAltitude(
            TypeHeader(0, 0, 0, 0),
            TypeTimestamp(1_000_000_000),
            MeasurementAltitudeReference.HAE,
            1005,
            100,
            MeasurementAltitudeErrorModel.NONE,
            np.array([]),
            [],
        ),
        'alt',
    )


@pytest.fixture
def direction3D_to_points_meas() -> Message:
    return Message(
        MeasurementDirection3DToPoints(
            TypeHeader(0, 0, 0, 0),
            TypeTimestamp(1_000_000_000),
            [
                TypeDirection3DToPoint(
                    TypeRemotePoint(
                        3,
                        0,
                        TypeRemotePointPositionReferenceFrame.GEODETIC,
                        0.693950,
                        -1.468400,
                        0.0,
                        np.array(
                            [
                                [1.0, 0.0, 0.0],
                                [0.0, 1.0, 0.0],
                                [0.0, 0.0, 1.0],
                            ]
                        ),
                    ),
                    TypeDirection3DToPointReferenceFrame.SINE_SPACE,
                    np.array([0.5, 0.4]),
                    np.diag([0.0001, 0.0001]),
                    False,
                    TypeImageFeature(1.0, 1.0, 1.0, 1, 1, np.array([1])),
                    TypeDirection3DToPointErrorModel.NONE,
                    np.array([]),
                    [],
                )
            ],
        ),
        'direction3D_to_points',
    )


@pytest.fixture
def force_and_rate_aux_data() -> Message:
    return Message(
        MeasurementImu(
            TypeHeader(0, 0, 0, 0),
            TypeTimestamp(1_000_000_000),
            MeasurementImuImuType.INTEGRATED,
            np.array([0, 0, -9.8]),
            np.zeros(3),
            [],
        ),
        'force_and_rate_aux',
    )


def test_invalid_fusion_type(
    state_modeling_plugin: StandardGpsInsStateModelingPlugin,
) -> None:
    invalid_sm_provider = state_modeling_plugin.new_state_model_provider(
        EstimateWithCovarianceType
    )
    assert invalid_sm_provider is None


def test_enough_labels(
    state_modeling_plugin: StandardGpsInsStateModelingPlugin,
) -> None:
    model_provider = state_modeling_plugin.new_state_model_provider(
        StandardStateModelProvider
    )
    assert isinstance(model_provider, StandardStateModelProvider)
    proc_ids = model_provider.processor_identifiers
    assert proc_ids is not None
    mod_plus = model_provider.new_processor(len(proc_ids), None, 'l', ['s'], '')
    assert mod_plus is None


def test_invalid_index(state_model_provider: StateModelProviderType) -> None:
    good_sb = state_model_provider.new_block(0, None, 'label', 'config/pinson_block')
    assert good_sb is not None

    block_ids = state_model_provider.block_identifiers
    assert block_ids is not None
    invalid_sb = state_model_provider.new_block(
        len(block_ids) + 1,
        None,
        'label',
        'config/pinson_block',
    )
    assert invalid_sb is None

    proc_ids = state_model_provider.processor_identifiers
    assert proc_ids is not None
    invalid_mp = state_model_provider.new_processor(
        len(proc_ids) + 1,
        None,
        'label',
        ['state_block_labels'],
        'config/test',
    )
    assert invalid_mp is None

    vblock_ids = state_model_provider.virtual_block_identifiers
    if vblock_ids is not None:
        invalid_vsb = state_model_provider.new_virtual_block(
            len(vblock_ids) + 1,
            'source',
            'target',
            'config/vsb',
        )
        assert invalid_vsb is None


def test_wrong_number_blocks(
    state_model_provider: StateModelProviderType,
    pva_aux_data: Message,
    pos_meas: Message,
    all_pos_processors: all_pos_proc_type,
    gen_x_and_p_all_pos: GenXandP,
) -> None:
    inertial_pva = pva_aux_data.wrapped_message
    assert isinstance(inertial_pva, MeasurementPositionVelocityAttitude)
    pos = pos_meas.wrapped_message
    assert isinstance(pos, MeasurementPosition)
    labs = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']

    for m in all_pos_processors:
        invalid_mp = state_model_provider.new_processor(
            m[3], None, 'label', [], 'config/test'
        )
        assert invalid_mp is not None
        assert isinstance(invalid_mp, type(m[0]))
        invalid_mp.receive_aux_data([pva_aux_data])
        mod = invalid_mp.generate_model(pos_meas, gen_x_and_p_all_pos)
        assert mod is None

        invalid_mp = state_model_provider.new_processor(
            m[3], None, 'label', labs[: (m[2] + 1)], 'config/test'
        )
        assert invalid_mp is not None
        assert isinstance(invalid_mp, type(m[0]))
        invalid_mp.receive_aux_data([pva_aux_data])
        mod = invalid_mp.generate_model(pos_meas, gen_x_and_p_all_pos)
        assert mod is None


def test_vsb_instantiation(
    state_model_provider: StateModelProviderType,
) -> None:
    pes = state_model_provider.new_virtual_block(
        0, 'some_real_block', 'to_direct', None
    )
    assert isinstance(pes, PinsonErrorToStandard)

    se = state_model_provider.new_virtual_block(
        1, 'some_real_block', 'extractor', 'config/extractor'
    )
    assert isinstance(se, StateExtractor)

    no_se = state_model_provider.new_virtual_block(
        1, 'some_real_block', 'extractor', 'config/bad'
    )
    assert no_se is None

    no_se = state_model_provider.new_virtual_block(
        1, 'some_real_block', 'extractor', None
    )
    assert no_se is None


def test_bad_meas_inputs(
    all_pos_processors: all_pos_proc_type,
    state_model_provider: StateModelProviderType,
    pva_aux_data: Message,
    pos_meas: Message,
    gen_x_and_p_all_pos: GenXandP,
) -> None:
    inertial_pva = pva_aux_data.wrapped_message
    assert isinstance(inertial_pva, MeasurementPositionVelocityAttitude)
    pos = pos_meas.wrapped_message
    assert isinstance(pos, MeasurementPosition)

    mp = state_model_provider.new_processor(0, None, 'l', ['p'], 'config/test')
    assert isinstance(mp, PinsonPositionMeasurementProcessor)
    mp2 = state_model_provider.new_processor(2, None, 'l', ['p', 'f'], 'config/test')
    assert isinstance(mp2, PinsonWithNedFogmPositionMeasurementProcessor)
    pv2 = deepcopy(pva_aux_data)
    assert isinstance(pv2.wrapped_message, MeasurementPositionVelocityAttitude)
    pv2.wrapped_message.quaternion = None
    for m in all_pos_processors:
        m[0].receive_aux_data([pva_aux_data])
        mod = m[0].generate_model(pos_meas, gen_x_and_p_all_pos)
        assert mod is not None
        pos.reference_frame = MeasurementPositionReferenceFrame.ECI
        mod = m[0].generate_model(pos_meas, gen_x_and_p_all_pos)
        assert mod is None
        pos.reference_frame = MeasurementPositionReferenceFrame.GEODETIC
        mod = m[0].generate_model(pos_meas, gen_x_and_p_all_pos)
        assert mod is not None
        m[0].receive_aux_data([pv2])
        mod = m[0].generate_model(pos_meas, gen_x_and_p_all_pos)
        assert mod is not None


def test_invalid_aux_block(pinson_block: Pinson15NedBlock) -> None:
    bad_aux = Message(TypeHeader(0, 0, 0, 0), 'bad_aux')
    pinson_block.receive_aux_data([bad_aux])
    assert pinson_block._new_pva_aux is None
    assert pinson_block._force_and_rate_aux is None


def test_invalid_aux_proc(
    all_pos_processors: all_pos_proc_type,
) -> None:
    bad_aux = Message(TypeHeader(0, 0, 0, 0), 'bad_aux')
    for proc in all_pos_processors:
        proc[0].receive_aux_data([bad_aux])
        assert proc[0]._inertial_pva is None
        proc[0].receive_aux_data([])
        assert proc[0]._inertial_pva is None


def test_no_aux_block(
    pinson_block: Pinson15NedBlock, gen_x_and_p_all_pos: GenXandP
) -> None:
    dm = pinson_block.generate_dynamics(
        gen_x_and_p_all_pos, TypeTimestamp(0), TypeTimestamp(1)
    )
    assert dm is None


def test_no_aux_data_proc(
    all_pos_processors: all_pos_proc_type,
    pos_meas: Message,
    gen_x_and_p_all_pos: GenXandP,
) -> None:
    for m in all_pos_processors:
        mm = m[0].generate_model(pos_meas, gen_x_and_p_all_pos)
        assert mm is None


def test_stale_aux_data(
    all_pos_processors: all_pos_proc_type,
    pva_aux_data: Message,
    pos_meas: Message,
    gen_x_and_p_all_pos: GenXandP,
) -> None:
    inertial_pva = pva_aux_data.wrapped_message
    assert isinstance(inertial_pva, MeasurementPositionVelocityAttitude)
    assert isinstance(pos_meas.wrapped_message, MeasurementPosition)
    pos_time = pos_meas.wrapped_message.time_of_validity
    # Set aux data ToV to be 1 second older than pos meas ToV
    inertial_pva.time_of_validity.elapsed_nsec = pos_time.elapsed_nsec - 1_000_000_000
    for m in all_pos_processors:
        m[0].receive_aux_data([pva_aux_data])
        assert m[0]._inertial_pva is not None
        mm = m[0].generate_model(pos_meas, gen_x_and_p_all_pos)
        assert mm is None


def test_stale_aux_data2(
    all_pos_processors: all_pos_proc_type,
    pva_aux_data: Message,
    pos_meas: Message,
    gen_x_and_p_all_pos: GenXandP,
) -> None:
    assert isinstance(pos_meas.wrapped_message, MeasurementPosition)
    for m in all_pos_processors:
        m[0].receive_aux_data([pva_aux_data])
        assert m[0]._inertial_pva is not None
        pos_meas.wrapped_message.time_of_validity.elapsed_nsec += 1_000_000_000
        mm = m[0].generate_model(pos_meas, gen_x_and_p_all_pos)
        assert mm is None


def test_invalid_measurement(
    all_pos_processors: all_pos_proc_type, gen_x_and_p_all_pos: GenXandP
) -> None:
    msg = Message(TypeHeader(0, 0, 0, 0), 'bad_meas')
    for m in all_pos_processors:
        mm = m[0].generate_model(msg, gen_x_and_p_all_pos)
        assert mm is None


def test_generate_model_direct_pos(
    direct_pos: PositionMeasurementProcessor, pos_meas: Message
) -> None:
    x_and_p = EstimateWithCovariance(
        EstimateWithCovarianceType.EWC_GENERIC, np.zeros((18, 1)), np.eye(18)
    )

    def _test_gen_x_and_p(sb_labels: list[str]) -> EstimateWithCovariance | None:
        return x_and_p

    pos = pos_meas.wrapped_message
    assert isinstance(pos, MeasurementPosition)
    assert pos.term1 is not None
    assert pos.term2 is not None
    assert pos.term3 is not None
    mm = direct_pos.generate_model(pos_meas, _test_gen_x_and_p)
    assert mm is not None

    conv = np.diag(
        [
            north_to_delta_lat(1, pos.term1, pos.term3),
            east_to_delta_lon(1, pos.term1, pos.term3),
            -1.0,
        ]
    )

    rpy = np.zeros((3,))
    exp_H = np.eye(3, 18)
    exp_H[:, 6] = conv @ d_rpy_to_dcm_wrt_r(rpy) @ _lever_arm
    exp_H[:, 7] = conv @ d_rpy_to_dcm_wrt_p(rpy) @ _lever_arm
    exp_H[:, 8] = conv @ d_rpy_to_dcm_wrt_y(rpy) @ _lever_arm
    exp_H[:, -3:] = -np.eye(3)
    exp_R = conv @ pos.covariance @ conv
    exp_z = np.array([[pos.term1], [pos.term2], [pos.term3]])
    arm_ned = rpy_to_dcm(np.zeros((3,))) @ _lever_arm
    exp_conv_meas = np.array(
        [
            [north_to_delta_lat(arm_ned[0], pos.term1, pos.term3)],
            [east_to_delta_lon(arm_ned[1], pos.term1, pos.term3)],
            [-arm_ned[2]],
        ]
    )
    assert np.allclose(mm.H, exp_H)
    assert np.allclose(mm.R, exp_R)
    assert np.allclose(mm.h(x_and_p.estimate), exp_conv_meas)
    assert np.allclose(mm.z, exp_z)


def test_generate_model_gps_all(
    all_pos_processors: all_pos_proc_type,
    pva_aux_data: Message,
    pos_meas: Message,
    gen_x_and_p_all_pos: GenXandP,
) -> None:
    inertial_pva = pva_aux_data.wrapped_message
    assert isinstance(inertial_pva, MeasurementPositionVelocityAttitude)
    pos = pos_meas.wrapped_message
    assert isinstance(pos, MeasurementPosition)
    for m in all_pos_processors:
        m[0].receive_aux_data([pva_aux_data])
        assert m[0]._inertial_pva is not None
        x_and_p = gxp(m[1])
        mm = m[0].generate_model(pos_meas, gen_x_and_p_all_pos)
        assert mm is not None
        exp_H = np.zeros((3, m[1]))
        exp_H[:, :3] = np.eye(3)
        assert inertial_pva.quaternion is not None
        la_as_array = np.array([_lever_arm[0], _lever_arm[1], _lever_arm[2]])
        C = quat_to_dcm(inertial_pva.quaternion)
        c_cor = (np.eye(3) - skew(x_and_p.estimate[6:9, 0])) @ C
        exp_H[:, 6:9] = skew(C @ la_as_array)
        exp_pred = x_and_p.estimate[0:3, 0] + c_cor @ la_as_array
        if isinstance(m[0], PinsonWithNedFogmPositionMeasurementProcessor):
            exp_H[:, -3:] = -np.eye(3)
            exp_pred -= x_and_p.estimate[-3:, 0]
        if isinstance(m[0], PinsonWithLeverArmPositionMeasurementProcessor):
            exp_H[:, -6:-3] = -np.eye(3)
            exp_H[:, -3:] = c_cor
            exp_H[:, 6:9] += skew(C @ x_and_p.estimate[-3:, 0])
            exp_pred -= x_and_p.estimate[-6:-3, 0]
            exp_pred += c_cor @ x_and_p.estimate[-3:, 0]

        exp_R = pos.covariance
        meas_llh = np.array([pos.term1, pos.term2, pos.term3])
        inertial_llh = np.array([inertial_pva.p1, inertial_pva.p2, inertial_pva.p3])
        delta_pos = meas_llh - inertial_llh
        lat_factor = delta_lat_to_north(1, meas_llh[0], meas_llh[2])
        lon_factor = delta_lon_to_east(1, meas_llh[0], meas_llh[2])
        exp_z = np.array(
            [[delta_pos[0] * lat_factor], [delta_pos[1] * lon_factor], [-delta_pos[2]]]
        )
        assert np.array_equal(mm.H, exp_H)
        assert np.array_equal(mm.R, exp_R)
        pre = mm.h(x_and_p.estimate).flatten()
        assert np.allclose(pre, exp_pred)
        assert np.allclose(mm.z, exp_z)


def test_generate_model_vel(
    velocity_mp: PinsonVelocityMeasurementProcessor,
    pva_aux_data: Message,
    vel_meas: Message,
) -> None:
    inertial_pva = pva_aux_data.wrapped_message
    assert isinstance(inertial_pva, MeasurementPositionVelocityAttitude)
    vel = vel_meas.wrapped_message
    assert isinstance(vel, MeasurementVelocity)
    velocity_mp.receive_aux_data([pva_aux_data])
    assert velocity_mp._inertial_pva is not None
    x_and_p = EstimateWithCovariance(
        EstimateWithCovarianceType.EWC_GENERIC, np.zeros(15), np.eye(15)
    )

    def _test_gen_x_and_p(sb_labels: list[str]) -> EstimateWithCovariance | None:
        return x_and_p

    mm = velocity_mp.generate_model(vel_meas, _test_gen_x_and_p)
    assert mm is not None
    exp_H = np.zeros((3, 15))
    exp_H[:, 3:6] = np.eye(3)
    exp_R = vel.covariance
    meas_vel = np.array([vel.x, vel.y, vel.z])
    inertial_vel = np.array([inertial_pva.v1, inertial_pva.v2, inertial_pva.v3])
    delta_vel = meas_vel - inertial_vel
    exp_z = delta_vel[:, np.newaxis]
    assert np.array_equal(mm.H, exp_H)
    assert np.array_equal(mm.R, exp_R)
    assert np.array_equal(mm.h(x_and_p.estimate), np.zeros(3))
    assert np.allclose(mm.z, exp_z)


def test_generate_model_posvel(
    posvel_mp: PinsonPosVelMeasurementProcessor,
    pva_aux_data: Message,
    posvel_meas: Message,
) -> None:
    inertial_pva = pva_aux_data.wrapped_message
    assert isinstance(inertial_pva, MeasurementPositionVelocityAttitude)
    assert inertial_pva.quaternion is not None
    posvel = posvel_meas.wrapped_message
    assert isinstance(posvel, MeasurementPositionVelocityAttitude)
    posvel_mp.receive_aux_data([pva_aux_data])
    assert posvel_mp._inertial_pva is not None
    x_and_p = EstimateWithCovariance(
        EstimateWithCovarianceType.EWC_GENERIC,
        np.array([0.1, 0.1, 0.1, 0, 0, 0, 0.1, 0.1, 0.1, 0, 0, 0, 0, 0, 0]).reshape(
            (15, 1)
        ),
        np.eye(15),
    )

    def _test_gen_x_and_p(sb_labels: list[str]) -> EstimateWithCovariance | None:
        return x_and_p

    mm = posvel_mp.generate_model(posvel_meas, _test_gen_x_and_p)
    assert mm is not None

    exp_H = np.zeros((6, 15))
    exp_H[:3, :3] = np.eye(3)
    la_as_array = np.array([_lever_arm[0], _lever_arm[1], _lever_arm[2]])
    C = quat_to_dcm(inertial_pva.quaternion)
    c_cor = (np.eye(3) - skew(x_and_p.estimate[6:9, 0])) @ C
    exp_H[:3, 6:9] = skew(C @ la_as_array)
    exp_H[3:, 3:6] = np.eye(3)

    exp_R = posvel.covariance

    meas_pos = np.array([posvel.p1, posvel.p2, posvel.p3])
    meas_vel = np.array([posvel.v1, posvel.v2, posvel.v3])
    inertial_pos = np.array([inertial_pva.p1, inertial_pva.p2, inertial_pva.p3])
    inertial_vel = np.array([inertial_pva.v1, inertial_pva.v2, inertial_pva.v3])
    delta_pos = meas_pos - inertial_pos
    lat_factor = delta_lat_to_north(1, meas_pos[0], meas_pos[2])
    lon_factor = delta_lon_to_east(1, meas_pos[0], meas_pos[2])
    delta_pos[0] *= lat_factor
    delta_pos[1] *= lon_factor
    delta_pos[2] *= -1
    delta_vel = meas_vel - inertial_vel
    exp_z = np.concatenate((delta_pos, delta_vel))

    exp_pred_pos = x_and_p.estimate[0:3, 0] + c_cor @ la_as_array
    exp_pred_vel = np.zeros(3)
    exp_pred = np.concatenate((exp_pred_pos, exp_pred_vel))

    assert np.array_equal(mm.H, exp_H)
    assert np.array_equal(mm.R, exp_R)
    assert np.array_equal(mm.h(x_and_p.estimate).flatten(), exp_pred)
    assert np.allclose(mm.z.flatten(), exp_z)


def test_generate_model_bodyvel(
    body_velocity_mp: PinsonBodyVelocityMeasurementProcessor,
    pva_aux_data: Message,
    force_and_rate_aux_data: Message,
    bodyvel_meas: Message,
) -> None:
    inertial_pva = pva_aux_data.wrapped_message
    assert isinstance(inertial_pva, MeasurementPositionVelocityAttitude)
    force_and_rate = force_and_rate_aux_data.wrapped_message
    assert isinstance(force_and_rate, MeasurementImu)
    bodyvel = bodyvel_meas.wrapped_message
    assert isinstance(bodyvel, MeasurementVelocity)
    body_velocity_mp.receive_aux_data([pva_aux_data, force_and_rate_aux_data])
    assert body_velocity_mp._inertial_pva is not None
    assert body_velocity_mp._force_and_rate_aux is not None

    x_and_p = EstimateWithCovariance(
        EstimateWithCovarianceType.EWC_GENERIC, np.zeros((15, 1)), np.eye(15)
    )

    def _test_gen_x_and_p(sb_labels: list[str]) -> EstimateWithCovariance | None:
        return x_and_p

    mm = body_velocity_mp.generate_model(bodyvel_meas, _test_gen_x_and_p)
    assert mm is not None
    x = x_and_p.estimate
    inertial_vel = np.array([inertial_pva.v1, inertial_pva.v2, inertial_pva.v3])
    C_sensor_to_platform = np.eye(3)
    C_platform_to_sensor = C_sensor_to_platform.T
    assert inertial_pva.quaternion is not None
    uncorr_C_ned_to_imu = quat_to_dcm(inertial_pva.quaternion).T
    att_error = x[6:9, 0]
    corr_C_ned_to_imu = uncorr_C_ned_to_imu @ (np.eye(3) + skew(att_error))
    C_ned_to_sensor = C_platform_to_sensor @ corr_C_ned_to_imu
    uncorr_C_ned_to_sensor = C_platform_to_sensor @ uncorr_C_ned_to_imu
    inertial_vel_error = x[3:6, 0]
    corr_inertial_vel_ned = inertial_vel + inertial_vel_error
    C_ned_to_sensor_der = -uncorr_C_ned_to_sensor @ skew(corr_inertial_vel_ned)
    exp_z = np.array([[bodyvel.x], [bodyvel.y], [bodyvel.z]])
    exp_H = np.zeros((3, 15))
    exp_H[:, 3:6] = C_ned_to_sensor
    exp_H[:, 6:9] = C_ned_to_sensor_der

    rotation_rate = force_and_rate.meas_gyro
    assert inertial_pva is not None and inertial_pva.p1 is not None
    alt = inertial_pva.p3 - x[2, 0]
    lat = inertial_pva.p1 + north_to_delta_lat(x[0, 0], inertial_pva.p1, alt)
    gyro_bias = x[12:15, 0]
    rn = meridian_radius(lat)
    re = transverse_radius(lat)
    w_en_n = np.array(
        [
            corr_inertial_vel_ned[1] / (re + alt),
            -corr_inertial_vel_ned[0] / (rn + alt),
            -corr_inertial_vel_ned[1] * np.tan(lat) / (re + alt),
        ]
    )
    w_ie_n = np.array(
        [
            OMEGA_E * np.cos(lat),
            0.0,
            -OMEGA_E * np.sin(lat),
        ]
    )
    # Remove remaining biases (additive error states), earth and transport rates
    rotation_rate = rotation_rate + gyro_bias - corr_C_ned_to_imu @ (w_ie_n - w_en_n)
    la_as_array = np.array([_lever_arm[0], _lever_arm[1], _lever_arm[2]])
    tan_vel_imu = np.cross(rotation_rate, la_as_array)
    tan_vel_sensor = C_platform_to_sensor @ tan_vel_imu
    inertial_vel_sensor = C_ned_to_sensor @ corr_inertial_vel_ned
    exp_pred = inertial_vel_sensor + tan_vel_sensor
    exp_R = bodyvel.covariance
    assert np.allclose(mm.H, exp_H)
    assert np.array_equal(mm.R, exp_R)
    pred = mm.h(x_and_p.estimate).flatten()
    assert np.allclose(pred, exp_pred)
    assert np.array_equal(mm.z, exp_z)


def test_generate_model_alt(
    altitude_mp: AltitudeMeasurementProcessor,
    pva_aux_data: Message,
    alt_meas: Message,
) -> None:
    inertial_pva = pva_aux_data.wrapped_message
    assert isinstance(inertial_pva, MeasurementPositionVelocityAttitude)
    assert inertial_pva.p3 is not None
    alt = alt_meas.wrapped_message
    assert isinstance(alt, MeasurementAltitude)

    altitude_mp.receive_aux_data([pva_aux_data])
    assert altitude_mp._inertial_solution_time_nsec is not None

    x_and_p = EstimateWithCovariance(
        EstimateWithCovarianceType.EWC_GENERIC, np.zeros((16, 1)), np.eye(16)
    )

    def _test_gen_x_and_p(sb_labels: list[str]) -> EstimateWithCovariance | None:
        return x_and_p

    mm = altitude_mp.generate_model(alt_meas, _test_gen_x_and_p)

    assert mm is not None
    exp_H = np.zeros((1, 16))
    exp_H[0, 2] = -1
    exp_H[0, 15] = 1
    exp_R = np.array([[alt.variance]])
    exp_z = alt.altitude - inertial_pva.p3
    assert np.array_equal(mm.H, exp_H)
    assert np.array_equal(mm.R, exp_R)
    assert np.array_equal(mm.h(x_and_p.estimate).flatten(), np.zeros(1))
    assert np.allclose(mm.z, exp_z)


def test_generate_model_alt_msl(
    altitude_mp: AltitudeMeasurementProcessor,
    pva_aux_data: Message,
    alt_meas: Message,
) -> None:
    inertial_pva = pva_aux_data.wrapped_message
    assert isinstance(inertial_pva, MeasurementPositionVelocityAttitude)
    assert inertial_pva.p1 is not None
    assert inertial_pva.p2 is not None
    assert inertial_pva.p3 is not None
    alt = alt_meas.wrapped_message
    assert isinstance(alt, MeasurementAltitude)
    altitude_mp.receive_aux_data([pva_aux_data])
    assert altitude_mp._inertial_solution_time_nsec is not None

    # Convert alt from HAE to MSL
    hae_alt = alt.altitude
    msl_alt = hae_to_msl(hae_alt, inertial_pva.p1, inertial_pva.p2)[1]
    assert msl_alt != hae_alt
    alt.altitude = msl_alt

    x_and_p = EstimateWithCovariance(
        EstimateWithCovarianceType.EWC_GENERIC, np.zeros((16, 1)), np.eye(16)
    )

    def _test_gen_x_and_p(sb_labels: list[str]) -> EstimateWithCovariance | None:
        return x_and_p

    alt.reference = MeasurementAltitudeReference.MSL
    mm = altitude_mp.generate_model(alt_meas, _test_gen_x_and_p)

    assert mm is not None
    exp_H = np.zeros((1, 16))
    exp_H[0, 2] = -1
    exp_H[0, 15] = 1
    exp_R = np.array([[alt.variance]])
    exp_z = hae_alt - inertial_pva.p3
    assert np.array_equal(mm.H, exp_H)
    assert np.array_equal(mm.R, exp_R)
    assert np.array_equal(mm.h(x_and_p.estimate).flatten(), np.zeros(1))
    assert np.allclose(mm.z, exp_z)


def test_generate_model_pos_alt(
    altitude_mp: AltitudeMeasurementProcessor,
    pva_aux_data: Message,
    pos_meas: Message,
) -> None:
    inertial_pva = pva_aux_data.wrapped_message
    assert isinstance(inertial_pva, MeasurementPositionVelocityAttitude)
    assert inertial_pva.p3 is not None
    pos = pos_meas.wrapped_message
    assert isinstance(pos, MeasurementPosition)
    assert pos.term3 is not None

    altitude_mp.receive_aux_data([pva_aux_data])
    assert altitude_mp._inertial_solution_time_nsec is not None

    x_and_p = EstimateWithCovariance(
        EstimateWithCovarianceType.EWC_GENERIC, np.zeros((16, 1)), np.eye(16)
    )

    def _test_gen_x_and_p(sb_labels: list[str]) -> EstimateWithCovariance | None:
        return x_and_p

    mm = altitude_mp.generate_model(pos_meas, _test_gen_x_and_p)

    assert mm is not None
    exp_H = np.zeros((1, 16))
    exp_H[0, 2] = -1
    exp_H[0, 15] = 1
    exp_R = np.array([[pos.covariance[2, 2]]])
    exp_z = pos.term3 - inertial_pva.p3
    assert np.array_equal(mm.H, exp_H)
    assert np.array_equal(mm.R, exp_R)
    assert np.array_equal(mm.h(x_and_p.estimate).flatten(), np.zeros(1))
    assert np.allclose(mm.z, exp_z)


def test_generate_model_direction3D_to_points(
    direction3D_to_points_mp: Direction3DToPointsMeasurementProcessor,
    pva_aux_data: Message,
    direction3D_to_points_meas: Message,
) -> None:
    inertial_pva = pva_aux_data.wrapped_message
    assert isinstance(inertial_pva, MeasurementPositionVelocityAttitude)
    assert inertial_pva.p1 is not None
    assert inertial_pva.p2 is not None
    assert inertial_pva.p3 is not None
    direction3D_to_points = direction3D_to_points_meas.wrapped_message
    assert isinstance(direction3D_to_points, MeasurementDirection3DToPoints)
    assert direction3D_to_points.obs[0].obs[0] is not None
    assert direction3D_to_points.obs[0].obs[1] is not None

    direction3D_to_points_mp.receive_aux_data([pva_aux_data])
    x_and_p = EstimateWithCovariance(
        EstimateWithCovarianceType.EWC_GENERIC, np.zeros((16, 1)), np.eye(16)
    )

    def _test_gen_x_and_p(sb_labels: list[str]) -> EstimateWithCovariance | None:
        return x_and_p

    mm = direction3D_to_points_mp.generate_model(
        direction3D_to_points_meas, _test_gen_x_and_p
    )

    assert mm is not None
    inertial_llh = np.array([inertial_pva.p1, inertial_pva.p2, inertial_pva.p3])
    assert inertial_pva.quaternion is not None
    C_nav_to_platform = quat_to_dcm(inertial_pva.quaternion).T
    C_platform_to_sensor = quat_to_dcm(np.array(_orientation))
    C_nav_to_sensor = C_platform_to_sensor @ C_nav_to_platform
    la_as_array = np.array([_lever_arm[0], _lever_arm[1], _lever_arm[2]]).reshape(3, 1)
    feature_llh = np.array(
        [
            direction3D_to_points.obs[0].remote_point.position1,
            direction3D_to_points.obs[0].remote_point.position2,
            direction3D_to_points.obs[0].remote_point.position3,
        ]
    )
    delta_pos_ned = np.array(
        [
            delta_lat_to_north(
                feature_llh[0] - inertial_llh[0], inertial_llh[0], inertial_llh[2]
            ),
            delta_lon_to_east(
                feature_llh[1] - inertial_llh[1], inertial_llh[0], inertial_llh[2]
            ),
            inertial_llh[2] - feature_llh[2],
        ]
    ).reshape(3, 1)
    delta_pos_sensor = (
        C_nav_to_sensor @ delta_pos_ned - C_platform_to_sensor @ la_as_array
    )
    u_nom = delta_pos_sensor / np.linalg.norm(delta_pos_sensor)
    sy_m, sz_m = direction3D_to_points.obs[0].obs
    exp_z = np.array([[sy_m - u_nom[1, 0]], [sz_m - u_nom[2, 0]]])
    exp_H = np.zeros((2, 16))
    exp_H[:, 0:3] = (
        ((np.eye(3) - np.outer(u_nom, u_nom)) / np.linalg.norm(delta_pos_sensor))[
            1:3, :
        ]
    ) @ (-C_nav_to_sensor)  # Position error
    exp_H[:, 6:9] = (
        ((np.eye(3) - np.outer(u_nom, u_nom)) / np.linalg.norm(delta_pos_sensor))[
            1:3, :
        ]
    ) @ (C_nav_to_sensor @ -skew(delta_pos_ned.flatten()))  # Tilt error
    x = x_and_p.estimate
    dpos_ned = x[0:3, 0].reshape(3, 1)
    dtheta_ned = x[6:9, 0].reshape(3, 1)
    # Predict perturbed unit vector
    delta_pos_sensor_p = (
        C_nav_to_sensor
        @ ((np.eye(3) + skew(dtheta_ned.flatten())) @ (delta_pos_ned - dpos_ned))
        - C_platform_to_sensor @ la_as_array
    )
    u_p = delta_pos_sensor_p / np.linalg.norm(delta_pos_sensor_p)
    # Predict nominal unit vector (no error)
    delta_pos_sensor_n = (
        C_nav_to_sensor @ delta_pos_ned - C_platform_to_sensor @ la_as_array
    )
    u_n = delta_pos_sensor_n / np.linalg.norm(delta_pos_sensor_n)
    exp_pred = u_p[1:3] - u_n[1:3]
    exp_R = direction3D_to_points.obs[0].covariance
    assert np.array_equal(mm.H, exp_H)
    assert np.array_equal(mm.R, exp_R)
    assert np.array_equal(mm.h(x_and_p.estimate).flatten(), exp_pred.flatten())
    assert np.allclose(mm.z, exp_z)


def test_generate_dynamics(
    pinson_block: Pinson15NedBlock,
    zero_pva_aux_data: Message,
    force_and_rate_aux_data: Message,
) -> None:
    # fmt: off
    expected_Phi = np.array(
        [
            [1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 4.9, 0.0, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0,1.0,0.0,0.0,1.0,0.00007292115147,-4.90,0.0,0.0,0.0,0.50,0.0,0.0,0.0,0.0],
            [0.00000000814951,0.0,1.00000154384554,0.0,-0.00007292115147,1.0,0.0,0.0,0.0,0.0,0.0,0.50,0.0,0.0,0.0],
            [0.0,0.0,0.0,0.99999922657297,0.0,0.0,0.0,9.80,0.00035731364219,0.99986111111111,0.0,0.0,0.0,-4.90,0.0],
            [1.1885438536036494e-12,0.0,0.00000000022516,0.0,0.9999992211156,0.00014584230293,-9.80,0.0,0.0,0.0,0.99986111111111,0.00007292115147,4.90,0.0,0.0],
            [0.00000001629903,0.0,0.00000308769109,0.00000000814951,-0.00014584230293,1.00000153321056,0.00071462728438,0.0,0.0,0.0,-0.00007292115147,0.99986111111111,0.0,0.0,0.0],
            [0.0,0.0,0.0,0.0,0.00000015678559,1.1432986068972804e-11,0.99999923175059,0.0,0.0,0.0,0.0000000783928,0.0,-0.99986111111111,0.0,0.0],
            [-4.196626355780571e-16,0.0,0.0,-0.00000015784225,0.0,0.0,0.0,0.99999922391423,0.00007292115147,-0.00000007892113,0.0,0.0,0.0,-0.99986111111111,-0.00003646057573],
            [-1.151003864133914e-11,0.0,0.0,0.0,0.0,0.0,0.0,-0.00007292115147,0.99999999734125,0.0,0.0,0.0,0.0,0.00003646057573,-0.99986111111111],
            [0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.99972226080247,0.0,0.0,0.0,0.0,0.0],
            [0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.99972226080247,0.0,0.0,0.0,0.0],
            [0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.99972226080247,0.0,0.0,0.0],
            [0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.99972226080247,0.0,0.0],
            [0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.99972226080247,0.0],
            [0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.99972226080247],
        ]
    )

    expected_Qd = np.array(
        [
            [8.24017197865543e-12,0.0,0.0,1.6479183703404108e-11,0.0,4.074756876753095e-33,0.0,8.292350065673561e-13,-6.046886652110622e-17,8.351507939480248e-12,0.0,0.0,0.0,0.0,0.0],
            [0.0,8.240171978655426e-12,0.0,0.0,1.6479183703404105e-11,-1.2017656579392867e-15,-8.292350174791127e-13,0.0,0.0,0.0,8.351507939480247e-12,0.0,0.0,0.0,0.0],
            [0.0,0.0,4.176914062500499e-12,0.0,6.091707660324459e-16,8.352667871094247e-12,0.0,0.0,0.0,0.0,0.0,8.351507939480248e-12,0.0,0.0,0.0],
            [1.6479183703404108e-11,0.0,0.0,3.2956048653748266e-11,0.0,4.074753725226001e-33,0.0,1.6584703056165926e-12,-6.046887717994475e-17,1.6700696015643975e-11,0.0,0.0,0.0,-2.8784930485841387e-19,0.0],
            [0.0,1.6479183703404108e-11,6.091707660324459e-16,0.0,3.295604872098478e-11,-1.1851897838136817e-15,-1.6584703230294208e-12,0.0,0.0,0.0,1.6700696015643975e-11,1.2180031508653846e-15,2.8784930485841387e-19,0.0,0.0],
            [4.074756876753095e-33,-1.2017656579392869e-15,8.352667871094247e-12,4.0747537252260006e-33,-1.185189783813682e-15,1.6703015731937017e-11,1.2093754462266956e-16,-6.431687948141506e-40,0.0,0.0,-1.2180031508653846e-15,1.6700696015643975e-11,0.0,0.0,0.0],
            [0.0,-8.292350174791127e-13,0.0,0.0,-1.6584703230294206e-12,1.2093754462266956e-16,3.3846359848335194e-13,0.0,0.0,0.0,1.3093961354985395e-18,0.0,-5.873659709965196e-20,0.0,0.0],
            [8.29235006567356e-13,0.0,0.0,1.6584703056165924e-12,0.0,-6.431687948141506e-40,0.0,3.3846359673092043e-13,9.544541964032542e-24,-1.3182208064880816e-18,0.0,0.0,0.0,-5.873659709965196e-20,-2.1418676284950054e-24],
            [-6.046886652110622e-17,0.0,0.0,-6.046887717994475e-17,0.0,0.0,0.0,9.544541964032542e-24,3.384638585077646e-13,0.0,0.0,0.0,0.0,2.1418676284950054e-24,-5.873659709965196e-20],
            [8.351507939480248e-12,0.0,0.0,1.6700696015643975e-11,0.0,0.0,0.0,-1.3182208064880814e-18,0.0,3.340603304673392e-11,0.0,0.0,0.0,0.0,0.0],
            [0.0,8.351507939480247e-12,0.0,0.0,1.6700696015643975e-11,-1.2180031508653845e-15,1.3093961354985395e-18,0.0,0.0,0.0,3.340603304673392e-11,0.0,0.0,0.0,0.0],
            [0.0,0.0,8.351507939480248e-12,0.0,1.2180031508653845e-15,1.6700696015643975e-11,0.0,0.0,0.0,0.0,0.0,3.340603304673392e-11,0.0,0.0,0.0],
            [0.0,0.0,0.0,0.0,2.8784930485841387e-19,0.0,-5.873659709965196e-20,0.0,0.0,0.0,0.0,0.0,1.17489516719882e-19,0.0,0.0],
            [0.0,0.0,0.0,-2.8784930485841387e-19,0.0,0.0,0.0,-5.873659709965196e-20,2.1418676284950054e-24,0.0,0.0,0.0,0.0,1.17489516719882e-19,0.0],
            [0.0,0.0,0.0,0.0,0.0,0.0,0.0,-2.1418676284950054e-24,-5.873659709965196e-20,0.0,0.0,0.0,0.0,0.0,1.17489516719882e-19],
        ]
    )
    # fmt: on

    pinson_block.receive_aux_data([zero_pva_aux_data, force_and_rate_aux_data])
    assert isinstance(
        zero_pva_aux_data.wrapped_message, MeasurementPositionVelocityAttitude
    )
    time_from: TypeTimestamp = zero_pva_aux_data.wrapped_message.time_of_validity
    time_to = TypeTimestamp(time_from.elapsed_nsec + 1_000_000_000)
    x_and_p = EstimateWithCovariance(
        EstimateWithCovarianceType.EWC_GENERIC, np.zeros(15), np.eye(15)
    )

    def _test_gen_x_and_p(sb_labels: list[str]) -> EstimateWithCovariance | None:
        return x_and_p

    dyn = pinson_block.generate_dynamics(_test_gen_x_and_p, time_from, time_to)
    assert dyn is not None

    absolute_tolerance = 1e-20
    relative_tolerance = 1e-5
    assert np.allclose(expected_Phi, dyn.Phi, relative_tolerance, absolute_tolerance)
    assert np.allclose(expected_Qd, dyn.Qd, relative_tolerance, absolute_tolerance)


def test_copy_block(pinson_block: Pinson15NedBlock) -> None:
    # copy pinson block and compare with new block
    new_pinson_block = deepcopy(pinson_block)
    assert (
        new_pinson_block._imu_model.accel_bias_sigma
        == pinson_block._imu_model.accel_bias_sigma
    )
    # modify new block and re-compare with original block
    new_pinson_block._imu_model.accel_bias_sigma = (1.0, 2.0, 3.0)
    assert (
        new_pinson_block._imu_model.accel_bias_sigma
        != pinson_block._imu_model.accel_bias_sigma
    )


def test_copy_proc(
    all_pos_processors: all_pos_proc_type,
    pva_aux_data: Message,
) -> None:
    for m in all_pos_processors:
        # pass PVA aux data to position MP
        assert m[0]._inertial_pva is None
        m[0].receive_aux_data([pva_aux_data])
        assert m[0]._inertial_pva is not None

        # copy MP and compare with new MP
        new_position_mp = deepcopy(m[0])  # type: ignore[unreachable]
        assert new_position_mp._inertial_pva is not None
        assert new_position_mp._inertial_pva.p1 == m[0]._inertial_pva.p1
        # modify new MP and re-compare with original MP
        new_position_mp._inertial_pva.p1 = 3
        assert new_position_mp._inertial_pva.p1 != m[0]._inertial_pva.p1
