from pathlib import Path
from site import getsitepackages

from aspn23 import (
    MeasurementImu,
    MeasurementImuImuType,
    MeasurementPosition,
    MeasurementPositionErrorModel,
    MeasurementPositionReferenceFrame,
    MeasurementPositionVelocityAttitude,
)
from aspn23_lcm import measurement_position_velocity_attitude
from lcm import EventLog
from navtk.navutils import (
    calculate_gravity_schwartz,
    dcm_to_rpy,
    east_to_delta_lon,
    north_to_delta_lat,
    quat_to_dcm,
)
from numpy import array, eye, float64, pi, sin, zeros
from numpy.typing import NDArray
from pntos import api
from pntos.api import (
    EstimateWithCovariance,
    EstimateWithCovarianceType,
    FusionPlugin,
    Message,
    StandardFusionEngine,
    StandardFusionStrategy,
)
from pntos.cobra import (
    EkfFusionStrategyPlugin,
    StandardFusionPlugin,
    StandardRegistryPlugin,
    StandardStateModelingPlugin,
)
from pntos.cobra.config import BaseConfig, FogmConfig, ImuConfig, SensorConfig
from pntos.cobra.internal import StandardMediator, StandardStateModelProvider
from pntos.cobra.utils import decode_aspn_lcm_msg, marshal_from_lcm


def gen_msg(
    pva: MeasurementPositionVelocityAttitude, la: NDArray[float64], lab: str = 'proc'
) -> Message:
    assert pva.quaternion is not None
    assert pva.p1 is not None
    assert pva.p2 is not None
    assert pva.p3 is not None
    cnb = quat_to_dcm(pva.quaternion)
    la_ned = cnb @ la
    dla = north_to_delta_lat(la_ned[0, 0], pva.p1, pva.p3)
    dlo = east_to_delta_lon(la_ned[1, 0], pva.p1, pva.p3)
    wrapped_message = MeasurementPosition(
        pva.header,
        pva.time_of_validity,
        reference_frame=MeasurementPositionReferenceFrame.GEODETIC,
        term1=pva.p1 + dla,
        term2=pva.p2 + dlo,
        term3=pva.p3 - la_ned[2, 0],
        covariance=pva.covariance[0:3, 0:3],
        error_model=MeasurementPositionErrorModel.NONE,
        error_model_params=array([0, 0]),
        integrity=[],
    )
    return Message(wrapped_message, lab)


def gen_force_rate(
    pva0: MeasurementPositionVelocityAttitude, pva1: MeasurementPositionVelocityAttitude
) -> MeasurementImu:
    # Coarse calculation of forces/rates needed for pinson propagation
    dt = (pva1.time_of_validity.elapsed_nsec - pva0.time_of_validity.elapsed_nsec) / 1e9
    assert pva0.quaternion is not None
    assert pva1.quaternion is not None
    assert pva0.v1 is not None
    assert pva1.v1 is not None
    assert pva0.v2 is not None
    assert pva1.v2 is not None
    assert pva0.v3 is not None
    assert pva1.v3 is not None
    assert pva1.p1 is not None
    assert pva1.p3 is not None
    cnb1 = quat_to_dcm(pva1.quaternion)
    cnb0 = quat_to_dcm(pva0.quaternion)
    wb1b0 = dcm_to_rpy(cnb1.T @ cnb0) / dt
    fned = array([pva1.v1 - pva0.v1, pva1.v2 - pva0.v2, pva1.v3 - pva0.v3]) / dt
    fned[2] += calculate_gravity_schwartz(sin(pva1.p1), pva1.p3)

    return MeasurementImu(
        pva1.header,
        pva1.time_of_validity,
        imu_type=MeasurementImuImuType.SAMPLED,
        meas_accel=fned,
        meas_gyro=wb1b0,
        integrity=[],
    )


my_config: list[BaseConfig] = [
    ImuConfig(
        group='/config/cobra/imu',
        # HG9900 model
        accel_bias_sigma=(25 * 9.81e-6, 25 * 9.81e-6, 25 * 9.81e-6),
        accel_bias_tau=(3600.0, 3600.0, 3600.0),
        accel_random_walk_sigma=(1e-12, 1e-12, 1e-12),
        gyro_bias_sigma=(
            0.003 * pi / 180 / 3600,
            0.003 * pi / 180 / 3600,
            0.003 * pi / 180 / 3600,
        ),
        gyro_bias_tau=(3600.0, 3600.0, 3600.0),
        gyro_random_walk_sigma=(
            0.002 * pi / 180 / 60,
            0.002 * pi / 180 / 60,
            0.002 * pi / 180 / 60,
        ),
    ),
    FogmConfig(group='/config/fogm1', sigma=(0.0, 0.0, 0.0), tau=(1000, 1000, 1000)),
    FogmConfig(group='/config/fogm2', sigma=(0.0, 0.0, 0.0), tau=(1e8, 1e8, 1e8)),
    SensorConfig(
        group='/config/cobra/sensor',
        lever_arm=(0.0, 0.0, 0.0),
        orientation=(1.0, 0.0, 0.0, 0.0),
        sensor_name='novatel',
    ),
]


def fusion(la_guess: NDArray[float64]) -> StandardFusionEngine:
    """
    Sets up a fusion engine ready to do lever arm estimation.

    Args:
    la_guess (NDArray[float64]): Platform-frame lever arm to assign to sensor config for this instance.
    Returns:
    A fusion engine with pinson and 2 fogm blocks, and the Pinson/LeverArm processor.
    """
    assert isinstance(my_config[-1], SensorConfig)
    my_config[-1].lever_arm = (la_guess[0, 0], la_guess[1, 0], la_guess[2, 0])
    registry_plugin = StandardRegistryPlugin('Standard registry', config=my_config)
    mediator = StandardMediator(
        attached_plugin_type=FusionPlugin, attached_plugin_identifier='Fusion Plugin'
    )
    registry_plugin.init_plugin(mediator=mediator)
    registry = registry_plugin.new_registry()
    StandardMediator.registry = registry
    fusion_plugin = StandardFusionPlugin(identifier='test_fusion_plugin')
    fusion_plugin.init_plugin('test', mediator=mediator)

    fusion_engine = fusion_plugin.new_fusion_engine(StandardFusionEngine)
    assert isinstance(fusion_engine, StandardFusionEngine)
    fusion_strategy_plugin = EkfFusionStrategyPlugin(identifier='test_strategy_plugin')
    fusion_strategy_plugin.init_plugin('test_strategy', mediator=mediator)
    fusion_strategy = fusion_strategy_plugin.new_fusion_strategy(StandardFusionStrategy)
    fusion_engine.strategy = fusion_strategy  # type: ignore[assignment]

    pos_model_plug = StandardStateModelingPlugin('pos_ins_state_modeling')
    pos_model_plug.init_plugin(mediator=mediator)
    mod_prov = pos_model_plug.new_state_model_provider(api.StandardStateModelProvider)
    assert isinstance(mod_prov, StandardStateModelProvider)
    pins = mod_prov.new_block(0, None, 'pinson', '/config/cobra/imu')
    sb1 = mod_prov.new_block(1, None, 'fogm1', '/config/fogm1')
    sb2 = mod_prov.new_block(1, None, 'fogm2', '/config/fogm2')
    assert pins is not None
    assert sb1 is not None
    assert sb2 is not None
    proc_index = mod_prov.processor_identifiers.index('pinson_with_lever_arm_position')
    mp = mod_prov.new_processor(
        proc_index, None, 'proc', ['pinson', 'fogm1', 'fogm2'], '/config/cobra/sensor'
    )
    assert mp is not None

    ewc = EstimateWithCovariance(
        EstimateWithCovarianceType.EWC_GENERIC,
        zeros((15, 1)),
        zeros((15, 15)),
    )
    fusion_engine.add_state_block(pins, ewc)

    ewc = EstimateWithCovariance(
        EstimateWithCovarianceType.EWC_GENERIC, zeros((3, 1)), eye(3) * 1.0
    )
    fusion_engine.add_state_block(sb1, ewc)

    ewc = EstimateWithCovariance(
        EstimateWithCovarianceType.EWC_GENERIC, zeros((3, 1)), eye(3) * 100.0
    )
    fusion_engine.add_state_block(sb2, ewc)
    fusion_engine.add_measurement_processor(mp)
    return fusion_engine


def open_log() -> EventLog:
    """Log opening code yoinked from the postprocessing folder"""
    log_filename = None
    for site in getsitepackages():
        candidate = Path(f'{site}/pntos_python_datasets/cobra_gps_ins_example_data.log')
        if candidate.exists():
            log_filename = candidate.as_posix()
            break
    if log_filename is None:
        raise Exception('Could not find log file.')
    log = EventLog(log_filename)
    assert log is not None
    return log


def estimate_arm(
    la_true: NDArray[float64], la_guess: NDArray[float64], acceptable_error: float = 0.1
) -> None:
    """
    Run a filter that ingests position measurements and estimates lever arm offsets.

    Uses cobra_gps_ins_example_data.log, harvests /sensor/ins-d/pva channel data which is used
    as the 'nominal'. The position from this channel is modified with a lever arm and used to
    form an update, and the final lever arm estimated value is tested for accuracy.

    Args:
        la_true (NDArray[float64]): Actual 3 element lever arm from body to sensor in body frame.
        la_guess (NDArray[float64]): Initial lever arm estimate, provided to processor through config.
        acceptable_error (float): Maximum allowable value of error between la_true and the final
        combination of la_guess and the estimated lever arm states.
    """
    fus = fusion(la_guess)
    assert isinstance(fus, StandardFusionEngine)

    log = open_log()

    chan = '/sensor/ins-d/pva'
    # Skip this many measurements before updating
    proc_every = 100
    num = 0
    last_pva: MeasurementPositionVelocityAttitude | None = None
    # mypy complains about no __iter__
    for e in log:  # type: ignore[attr-defined]
        if chan == e.channel:
            num += 1
            if num >= proc_every:
                num = 0
                # Decode base message
                m1 = decode_aspn_lcm_msg(e.data)
                assert isinstance(m1, measurement_position_velocity_attitude)
                base = marshal_from_lcm(m1)
                assert isinstance(base, MeasurementPositionVelocityAttitude)
                # Have to wait for pva span so we can calc force/rate from pvas
                if last_pva is not None:
                    pva_aux_msg = Message(base, 'pva_aux')
                    imu_aux_msg = Message(gen_force_rate(last_pva, base), 'imu_aux')
                    fus.give_state_block_aux_data('pinson', [pva_aux_msg, imu_aux_msg])
                    fus.give_measurement_processor_aux_data('proc', [pva_aux_msg])
                    msg = gen_msg(base, la_true)
                    fus.update('proc', msg)
                else:
                    # Init filter time
                    fus.time = base.time_of_validity
                last_pva = base
    est = fus.get_state_block_estimate('fogm2')
    assert est is not None
    abs_err = abs(la_true - (est + la_guess))
    assert all(abs_err < acceptable_error)


if __name__ == '__main__':
    # Large lever arm, no initial condition
    estimate_arm(array([[5.0], [10.0], [99.0]]), array([[0.0], [0.0], [0.0]]))
    # Typical lever arm, no initial condition
    estimate_arm(array([[-1.0], [2.0], [-3.0]]), array([[0.0], [0.0], [0.0]]))
    # No lever arm, no initial condition
    estimate_arm(array([[0.0], [0.0], [0.0]]), array([[0.0], [0.0], [0.0]]))
    # Typical lever arm, perfectly known initial condition
    estimate_arm(array([[-1.0], [2.0], [-3.0]]), array([[-1.0], [2.0], [-3.0]]))
    # Typical lever arm, initial guess with some error
    estimate_arm(array([[-1.0], [2.0], [-3.0]]), array([[-0.6], [-1.0], [-2.0]]))
