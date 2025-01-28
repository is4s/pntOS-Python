from math import cos, sin
from typing import cast

import numpy as np
from aspn23 import (
    MeasurementImu,
    MeasurementPosition,
    MeasurementPositionReferenceFrame,
    MeasurementPositionVelocityAttitude as MeasurementPVA,
    TypeTimestamp,
)
from numpy import float64
from numpy.typing import NDArray

from pntos.api.plugins.common import (
    EstimateWithCovariance,
    LoggingLevel,
    Mediator,
    Message,
)
from pntos.api.plugins.fusion import (
    StandardFusionEngine,
    StandardMeasurementProcessor,
    StandardStateBlock,
    VirtualStateBlock,
)
from pntos.api.plugins.fusion_strategy import (
    StandardDynamicsModel,
    StandardMeasurementModel,
)
from pntos.api.plugins.state_modeling import (
    StandardStateModelProvider,
    StateModelingPlugin,
    StateModelProviderType,
)
from pntos.cobra.utils import (
    OMEGA_E,
    EarthModel,
    ImuModel,
    calc_lat_factor,
    calc_lon_factor,
    ecef_to_llh,
    llh_to_cen,
    llh_to_ecef,
    quat_to_dcm,
    skew,
)


def extract_pos(pva: MeasurementPVA):
    return np.array([pva.p1, pva.p2, pva.p3])


def extract_vel(pva: MeasurementPVA):
    return np.array([pva.v1, pva.v2, pva.v3])


class Pinson15NedBlock(StandardStateBlock):
    _mediator: Mediator
    _imu_model: ImuModel
    _old_pva_aux: MeasurementPVA | None
    _new_pva_aux: MeasurementPVA | None
    _force_and_rate_aux: MeasurementImu | None
    _pre_Q: NDArray

    def __init__(self, label: str, mediator: Mediator, imu_model: ImuModel):
        self.label = label
        self.num_states = 15
        self._mediator = mediator
        self._imu_model = imu_model
        self._pre_Q = np.diag(
            np.power(
                np.concatenate(
                    [
                        np.zeros(3),
                        imu_model.accel_random_walk_sigma,
                        imu_model.gyro_random_walk_sigma,
                        imu_model.accel_bias_sigma
                        * np.sqrt(2 / imu_model.accel_bias_tau),
                        imu_model.gyro_bias_sigma
                        * np.sqrt(2 / imu_model.gyro_bias_tau),
                    ]
                ),
                2,
            )
        )
        self._new_pva_aux = None
        self._old_pva_aux = None
        self._force_and_rate_aux = None

    def receive_aux_data(self, aux: list[Message]) -> None:
        for message in aux:
            if isinstance(message.wrapped_message, MeasurementPVA):
                self._old_pva_aux = self._new_pva_aux
                self._new_pva_aux = message.wrapped_message
            elif isinstance(message.wrapped_message, MeasurementImu):
                self._force_and_rate_aux = message.wrapped_message
            else:
                self._mediator.log_message(
                    LoggingLevel.ERROR,
                    f'Pinson15NedBlock expected aux data of type MeasurementPositionVelocityAttitude or MeasurementImu, but got message of type {type(message.wrapped_message)}.',
                )

    def generate_dynamics(
        self,
        x_and_p: EstimateWithCovariance,
        time_from: TypeTimestamp,
        time_to: TypeTimestamp,
    ) -> StandardDynamicsModel | None:
        if not self._new_pva_aux or not self._force_and_rate_aux:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'Pinson15NedBlock cannot propagate from time {time_from.elapsed_nsec / 1e9}s to {time_to.elapsed_nsec / 1e9}s as it has not received PVA and force aux data.',
            )
            return None

        dt = (time_to.elapsed_nsec - time_from.elapsed_nsec) / 1e9
        F = self.generate_f_pinson15()
        Q = self.generate_q_pinson15()

        # Second-order discretization
        Phi = 0.5 * dt * dt * np.linalg.matrix_power(F, 2) + (
            F * dt + np.eye(F.shape[1])
        )
        Q_prop = Phi @ Q @ Phi.T
        Qd = (Q_prop + Q) * (0.5 * dt)

        self.scale_phi(Phi)

        def g(x: NDArray):
            return Phi @ x

        return StandardDynamicsModel(g, Phi, Qd)

    def scale_phi(self, Phi):
        if self._old_pva_aux is not None:
            pos = extract_pos(self._old_pva_aux)
            lat_factor0 = calc_lat_factor(pos[0], pos[2])
            lon_factor0 = calc_lon_factor(pos[0], pos[2])

            new_pos = extract_pos(self._new_pva_aux)
            lat_factor1 = calc_lat_factor(new_pos[0], new_pos[2])
            lon_factor1 = calc_lon_factor(new_pos[0], new_pos[2])

            lat0Tolat1 = lat_factor1 / lat_factor0
            lon0Tolon1 = lon_factor1 / lon_factor0
            Phi[:, 0] *= lat0Tolat1
            Phi[:, 1] *= lon0Tolon1

    def generate_f_pinson15(self):
        pos = extract_pos(self._new_pva_aux)
        vel = extract_vel(self._new_pva_aux)
        force = self._force_and_rate_aux.meas_accel
        C_sensor_to_ned = quat_to_dcm(self._new_pva_aux.quaternion)

        earth = EarthModel(pos, vel)
        omega = OMEGA_E
        sinl = earth.sin_l
        cosl = earth.cos_l
        tanl = earth.tan_l
        vn, ve, vd = vel
        re = earth.r_e
        rn = earth.r_n
        scalem2r = np.array(
            [
                [1 / earth.lat_factor, 0, 0],
                [0, 1 / earth.lon_factor, 0],
                [0, 0, -1],
            ]
        )

        # Initialize F
        # Terms in T+W are by-product of relationship between NED vel and LLA
        # position errors which are are not applicable to NED positions; see
        # model derivation.
        F = np.zeros((self.num_states, self.num_states))

        # block1: deltatilt = block1 * dtilt
        block1 = np.array(
            [
                [0, -(omega * sinl + ve / re * tanl), vn / rn],
                [(omega * sinl + ve / re * tanl), 0, omega * cosl + ve / re],
                [-vn / rn, -omega * cosl - ve / re, 0],
            ]
        )

        # block2: deltatilt = block2 * dvel
        block2 = np.array([[0, 1 / re, 0], [-1 / rn, 0, 0], [0, -tanl / re, 0]])

        # block3: deltatilt = block3 * dpos
        block3 = (
            np.array(
                [
                    [-omega * sinl, 0, -ve / pow(re, 2)],
                    [0, 0, vn / pow(rn, 2)],
                    [
                        -omega * cosl - ve / (re * cosl * cosl),
                        0,
                        ve * tanl / pow(re, 2),
                    ],
                ]
            )
            @ scalem2r
        )

        # block4: deltavel = block4 * dtilt
        block4 = skew(force)

        # block5: deltavel = block5*dvel
        block5 = np.array(
            [
                [vd / rn, -2 * (omega * sinl + ve / re * tanl), vn / rn],
                [
                    2 * omega * sinl + ve / re * tanl,
                    1 / re * (vn * tanl + vd),
                    2 * omega * cosl + ve / re,
                ],
                [-2 * vn / rn, -2 * (omega * cosl + ve / re), 0],
            ]
        )

        # Try adding gravity effect based on lat/north error. Derived from the
        # 'Schwartz' gravity model
        a1 = 9.7803267715
        a2 = 0.0052790414
        a3 = 0.0000232718
        a4 = -3.0876910891e-6
        a5 = 4.3977311e-9
        a6 = 7.211e-13
        dgdlat = (
            2 * a1 * a2 * cos(2 * pos[0])
            + a1 * a3 * (12 * (1 - cos(4 * pos[0])) / 8 - pow(sin(pos[0]), 4))
            + 2 * a5 * (cos(2 * pos[0]) - cosl * sinl) * pos[2]
        )
        dgdalt = (a4 + a5 * pow(sinl, 2)) + a6 * 2 * pos[2]

        # block6: deltavel = block6 * dpos
        block6 = (
            np.array(
                [
                    [
                        -ve * (2 * omega * cosl + ve / (re * cosl * cosl)),
                        0,
                        ve * ve * tanl / pow(re, 2) - vn * vd / pow(rn, 2),
                    ],
                    [
                        (
                            2 * omega * (vn * cosl - vd * sinl)
                            + vn * ve / (re * cosl * cosl)
                        ),
                        0,
                        -ve / pow(re, 2) * (vn * tanl + vd),
                    ],
                    [
                        2 * omega * ve * sinl + dgdlat,
                        0,
                        vn * vn / pow(rn, 2) + ve * ve / pow(re, 2) + dgdalt,
                    ],
                ]
            )
            @ scalem2r
        )

        # block7: deltapos = block7 * dtilt (zeros/not applicable)

        # block8: deltapos = block8 * dvel
        # T+W matrix has non-unity terms that are canceled out by conversion of
        # the LLA position errors used in the book to the NED position errors
        # used in this model. See model derivation in function documentation
        # for more detail.
        block8 = np.eye(3)

        # block9: deltapos = block9 * dpos

        F[6:9, 6:9] = block1
        F[6:9, 3:6] = block2
        F[6:9, 0:3] = block3
        F[3:6, 6:9] = block4
        F[3:6, 3:6] = block5
        F[3:6, 0:3] = block6
        F[0:3, 3:6] = block8

        F[3:6, 9:12] = C_sensor_to_ned  # Add in accel bias to vdot
        F[6:9, 12:15] = -C_sensor_to_ned  # Add in gyro bias to tiltdot

        # Accelerometer FOGM bias and Gyro FOGM bias
        for ii in range(0, 3):
            F[ii + 9, ii + 9] = -1.0 / self._imu_model.accel_bias_tau[ii]
            F[ii + 12, ii + 12] = -1.0 / self._imu_model.gyro_bias_tau[ii]

        return F

    def generate_q_pinson15(self):
        Q = self._pre_Q
        C_sensor_to_ned = quat_to_dcm(self._new_pva_aux.quaternion)

        Q[3:6, 3:6] = C_sensor_to_ned @ Q[3:6, 3:6] @ C_sensor_to_ned.T
        Q[6:9, 6:9] = C_sensor_to_ned @ Q[6:9, 6:9] @ C_sensor_to_ned.T

        return Q


class PinsonPositionMeasurementProcessor(StandardMeasurementProcessor):
    _mediator: Mediator
    _inertial_pva: MeasurementPVA | None
    _l_ps_p: NDArray
    _C_platform_to_sensor: NDArray

    def __init__(
        self,
        label: str,
        state_block_labels: list[str],
        mediator: Mediator,
        l_ps_p: NDArray,
        C_platform_to_sensor: NDArray,
    ):
        self.label = label
        self.state_block_labels = state_block_labels
        self._mediator = mediator
        self._inertial_pva = None
        self._l_ps_p = l_ps_p
        self._C_platform_to_sensor = C_platform_to_sensor

    def receive_aux_data(self, aux: list[Message]) -> None:
        if not isinstance(aux[0].wrapped_message, MeasurementPVA):
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'PinsonPositionMeasurementProcessor expected aux data of type MeasurementPositionVelocityAttitude, but got message of type {type(aux[0].wrapped_message)}.',
            )
            return

        self._inertial_pva = aux[0].wrapped_message

    def generate_model(
        self, message: Message, x_and_p: EstimateWithCovariance
    ) -> StandardMeasurementModel | None:
        if not isinstance(message.wrapped_message, MeasurementPosition):
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'PinsonPositionMeasurementProcessor expected message of type MeasurementPosition, but got message of type {type(message.wrapped_message)}. Cannot process message.',
            )
            return None

        pos = message.wrapped_message
        time = pos.time_of_validity
        if self._inertial_pva is None:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'PinsonPositionMeasurementProcessor cannot process message at time {time.elapsed_nsec / 1e9}s as it has not received inertial PVA aux data.',
            )
            return None

        pva_aux_time = self._inertial_pva.time_of_validity
        if abs(pva_aux_time.elapsed_nsec - time.elapsed_nsec) > 1000:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'PinsonPositionMeasurementProcessor cannot process message at time {time.elapsed_nsec / 1e9}s as inertial PVA aux data is at a different time (t={pva_aux_time.elapsed_nsec / 1e9}s).',
            )
            return None

        if pos.reference_frame is not MeasurementPositionReferenceFrame.GEODETIC:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'PinsonPositionMeasurementProcessor expected MeasurementPosition with a reference from of GEODETIC, but got measurement at time {time.elapsed_nsec / 1e9}s with a reference frame of {pos.reference_frame}. Cannot process message.',
            )
            return None

        llh = np.array([pos.term1, pos.term2, pos.term3])
        inertial_llh = extract_pos(self._inertial_pva)

        # TODO: Can we assume inertial PVA already in platform frame?
        ecef_platform = llh_to_ecef(inertial_llh)
        C_nav_to_ecef = llh_to_cen(inertial_llh)

        assert self._inertial_pva.quaternion is not None
        uncorr_C_nav_to_platform = quat_to_dcm(self._inertial_pva.quaternion)
        # TODO: Do we need to correct inertial attitude before transforming to sensor frame?
        tilt_err = x_and_p.estimate[6:9]
        C_nav_to_platform = uncorr_C_nav_to_platform @ (np.eye(3) + skew(tilt_err))

        # Transform inertial position into sensor frame
        ecef_sensor = ecef_platform + C_nav_to_ecef @ (
            C_nav_to_platform.T @ self._l_ps_p
        )
        llh_sensor = ecef_to_llh(ecef_sensor)

        # TODO: use sensor pos for calculating lat factor, or corrected inertial pos instead?
        lat_factor = calc_lat_factor(llh[0], llh[2])
        lon_factor = calc_lon_factor(llh[0], llh[2])
        delta_pos = llh - llh_sensor
        z = np.array(
            [
                delta_pos[0] * lat_factor,
                delta_pos[1] * lon_factor,
                -delta_pos[2],
            ]
        )
        H = np.zeros((3, 15))
        H[:, :3] = np.eye(3)  # TODO

        def h(x: NDArray):
            return H @ x

        R = pos.covariance

        return StandardMeasurementModel(z, h, H, R)


class SimpleGpsInsStateModelProvider(StandardStateModelProvider):
    _mediator: Mediator

    def __init__(self, mediator: Mediator):
        self._mediator = mediator
        self.processor_identifiers = ['pinson_position']
        self.block_identifiers = ['pinson15']
        self.virtual_block_identifiers = []

    def new_processor(
        self,
        processor_index: int,
        engine: StandardFusionEngine | None,
        label: str,
        state_block_labels: list[str],
        config_group: str,
    ) -> PinsonPositionMeasurementProcessor | None:
        if processor_index == 0:
            batch = self._mediator.registry.batch_start(config_group)
            l_ps_p = batch.get_value('lever_arm', np.ndarray)
            l_ps_p = cast(NDArray, l_ps_p)
            C_platform_to_sensor = batch.get_value('orientation', np.ndarray)
            C_platform_to_sensor = cast(NDArray, C_platform_to_sensor)
            return PinsonPositionMeasurementProcessor(
                label,
                state_block_labels,
                self._mediator,
                l_ps_p,
                C_platform_to_sensor,
            )

        self._mediator.log_message(
            LoggingLevel.ERROR,
            f'Invalid processor index of {processor_index}. SimpleGpsInsStateModelProvider provides {len(self.processor_identifiers)} processors.',
        )
        return None

    def new_block(
        self,
        block_index: int,
        engine: StandardFusionEngine | None,
        label: str,
        config_group: str,
    ) -> Pinson15NedBlock | None:
        if block_index == 0:
            batch = self._mediator.registry.batch_start(config_group)
            accel_bias_sigma = batch.get_value('accel_bias_sigma', np.ndarray)
            accel_bias_tau = batch.get_value('accel_bias_tau', np.ndarray)
            accel_rw_sigma = batch.get_value('accel_rw_sigma', np.ndarray)
            gyro_bias_sigma = batch.get_value('gyro_bias_sigma', np.ndarray)
            gyro_bias_tau = batch.get_value('gyro_bias_tau', np.ndarray)
            gyro_rw_sigma = batch.get_value('gyro_rw_sigma', np.ndarray)
            batch.batch_end()

            return Pinson15NedBlock(
                label,
                self._mediator,
                ImuModel(
                    # TODO: would be nice to not have to cast
                    cast(NDArray, accel_bias_sigma),
                    cast(NDArray, accel_bias_tau),
                    cast(NDArray, accel_rw_sigma),
                    cast(NDArray, gyro_bias_sigma),
                    cast(NDArray, gyro_bias_tau),
                    cast(NDArray, gyro_rw_sigma),
                ),
            )

        self._mediator.log_message(
            LoggingLevel.ERROR,
            f'Invalid block index of {block_index}. SimpleGpsInsStateModelProvider provides {len(self.block_identifiers)} state blocks.',
        )
        return None

    def new_virtual_block(
        self,
        virtual_block_index: int,
        source_label: str,
        target_label: str,
        config_group: str,
    ) -> VirtualStateBlock | None:
        self._mediator.log_message(
            LoggingLevel.ERROR,
            f'Invalid virtual block index of {virtual_block_index}. SimpleGpsInsStateModelProvider provides {len(self.virtual_block_identifiers)} virtual state blocks.',
        )
        return None


class SimpleGpsInsStateModelingPlugin(StateModelingPlugin):
    _mediator: Mediator

    def __init__(self, identifier: str):
        self.identifier = identifier

    def init_plugin(
        self,
        plugin_resources_location: str | None = None,
        mediator: Mediator | None = None,
    ) -> None:
        assert mediator is not None
        self._mediator = mediator

    def shutdown_plugin(self) -> None:
        pass

    def new_state_model_provider(
        self, type: type[StateModelProviderType]
    ) -> StateModelProviderType | None:
        if not self.is_fusion_type_supported(type):
            return None

        return SimpleGpsInsStateModelProvider(self._mediator)

    def is_fusion_type_supported(self, type: StateModelProviderType) -> bool:
        return type == StandardStateModelProvider
