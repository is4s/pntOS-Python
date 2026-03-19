from math import cos, sin

import numpy as np
from aspn23 import (
    MeasurementImu,
    MeasurementPositionVelocityAttitude as MeasurementPVA,
    TypeTimestamp,
)
from numpy import float64
from numpy.typing import NDArray
from pntos.api import (
    GenXandP,
    LoggingLevel,
    Mediator,
    Message,
    StandardDynamicsModel,
    StandardStateBlock,
)
from pntos.cobra.config import ImuConfig
from pntos.cobra.utils import (
    OMEGA_E,
    EarthModel,
    delta_lat_to_north,
    delta_lon_to_east,
    quat_to_dcm,
    skew,
)


def extract_pos(pva: MeasurementPVA) -> NDArray[float64]:
    """Extract position from an ASPN23 PVA

    Args:
        pva (MeasurementPVA): The PVA.

    Returns:
        NDArray[float64]: The position as a 3-element array.
    """
    return np.array([pva.p1, pva.p2, pva.p3])


def extract_vel(pva: MeasurementPVA) -> NDArray[float64]:
    """Extract velocity from an ASPN23 PVA

    Args:
        pva (MeasurementPVA): The PVA.

    Returns:
        NDArray[float64]: The velocity as a 3-element array.
    """
    return np.array([pva.v1, pva.v2, pva.v3])


class Pinson15NedBlock(StandardStateBlock):
    """A 15-state representation of the error model of an inertial navigation system in NED frame.

    This block is based upon the model provided in the Titterton and Weston 2nd edition textbook (pg. 345). The
    15-state model is created by combining the original 9x9 state block with the 6x6 G*u block
    that relates the gyro biases and accelerometer biases to the tilt and velocity error states,
    respectively. Additional changes include the conversion to North, East and Down position
    errors in meters as opposed to the latitude (radians), longitude (radians) and altitude
    (meters) error states in the book model. Note that the error states are additive, meaning in
    general you add the error state to the uncorrected value to get the corrected value. Tilt
    states require special handling; see below.

    Tilt errors: The North, East and Down tilt errors are 3 small angle corrections that when
    represented in skew-symmetric form and subtracted from an identity matrix may be interpreted as
    a DCM that rotates a vector from an estimated navigation frame to the 'true' navigation frame,
    to the extent that the error states are correct. A positive tilt error results in a negative
    right-handed rotation about the axis to which it is attached. For example, if the sensor frame
    is aligned with the local vertical with 90 degree heading (sensor x axis is aligned with East
    axis), and the down tilt value is 1 degree, the corrected heading will be approximately 89
    degrees.

    The AspnBaseVector provided to this class should come from the inertial for which it is
    providing error estimates. Accel and gyro bias states are generally in the inertial sensor frame,
    but more precisely, they are in the frame that is related to the navigation frame by the
    NavSolution::rot_mat provided in AspnBaseVector. This means that if the inertial
    is mechanizing in the inertial sensor frame, then NavSolution::rot_mat should contain
    `C_nav_to_sensor`, or the nav-to-sensor DCM, and the biases will be in the sensor frame. If the
    inertial is mechanizing in the platform frame (which is very common), then
    NavSolution::rot_mat should be `C_nav_to_platform`, the nav-to-platform DCM. The biases will be
    with respect to that frame.

    Note that these definitions only hold when using the 'additive error state' formulation
    (true = estimated + error), the current assumption in all off-the-shelf measurement processors.
    The opposite formulation will flip the sign on estimated values.

    Order and description of states:
        0 - North position error (m).
        1 - East position error (m).
        2 - Down position error (m).
        3 - North velocity error (m/s).
        4 - East velocity error (m/s).
        5 - Down velocity error (m/s).
        6 - North tilt error (rad).
        7 - East tilt error (rad).
        8 - Down tilt error (rad).
        9 - Accel x-axis bias error (m/s^2) (See note on frame above).
        10 - Accel y-axis bias error (m/s^2).
        11 - Accel z-axis bias error (m/s^2).
        12 - Gyro x-axis bias error (rad/s).
        13 - Gyro y-axis bias error (rad/s).
        14 - Gyro z-axis bias error (rad/s).
    """

    _mediator: Mediator
    _imu_model: ImuConfig
    _old_pva_aux: MeasurementPVA | None
    _new_pva_aux: MeasurementPVA | None
    _force_and_rate_aux: MeasurementImu | None
    _pre_Q: NDArray[float64]

    def __init__(self, label: str, mediator: Mediator, imu_model: ImuConfig) -> None:
        """
        A Pinson15 NED Standard State Block

        Args:
            label (str): An identifier for this state block object.
            mediator (Mediator): A :class:`pntos.api.Mediator` instance.
            imu_model (ImuConfig): The :class:`pntos.cobra.config.ImuConfig` to use in FOGM bias estimation.
        """
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
                        * np.sqrt(np.divide(2, imu_model.accel_bias_tau)),
                        imu_model.gyro_bias_sigma
                        * np.sqrt(np.divide(2, imu_model.gyro_bias_tau)),
                    ]
                ),
                2,
            )
        )
        self._new_pva_aux = None
        self._old_pva_aux = None
        self._force_and_rate_aux = None

    def receive_aux_data(self, aux: list[Message | None]) -> None:
        """Receive inertial PVA and forces as aux data.

        Args:
            aux (list[Message | None]): List of messages. Assumed to contain inertial solution in a PVA message and forces in an IMU message.
        """
        for message in aux:
            if message is None:
                continue

            if isinstance(message.wrapped_message, MeasurementPVA):
                pva = message.wrapped_message
                if pva.quaternion is None:
                    self._mediator.log_message(
                        LoggingLevel.WARN,
                        f'Pinson15NedBlock received PVA aux data with no quaternion at time {pva.time_of_validity.elapsed_nsec / 1e9:.9f}s. Ignoring.',
                    )
                    continue
                self._old_pva_aux = self._new_pva_aux
                self._new_pva_aux = pva
            elif isinstance(message.wrapped_message, MeasurementImu):
                self._force_and_rate_aux = message.wrapped_message
            else:
                self._mediator.log_message(
                    LoggingLevel.ERROR,
                    f'Pinson15NedBlock expected aux data of type MeasurementPositionVelocityAttitude or MeasurementImu, but got message of type {type(message.wrapped_message)}.',
                )

    def generate_dynamics(
        self,
        gen_x_and_p_func: GenXandP,
        time_from: TypeTimestamp,
        time_to: TypeTimestamp,
    ) -> StandardDynamicsModel | None:
        if not self._new_pva_aux or not self._force_and_rate_aux:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'Pinson15NedBlock cannot propagate from time {time_from.elapsed_nsec / 1e9:.9f}s to {time_to.elapsed_nsec / 1e9:.9f}s as it has not received PVA and force aux data.',
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

        def g(x: NDArray[float64]) -> NDArray[float64]:
            return Phi @ x

        return StandardDynamicsModel(g, Phi, Qd)

    def scale_phi(self, Phi: NDArray[float64]) -> None:
        """Scale first 15 elements of first 2 columns of `phi` such to account for change in rad to meter scale factors over propagation time.

        Args:
            Phi (NDArray[float64]): Matrix obtained by discretizing the propagation Jacobian. This matrix will be modified to account for the rad to meter scaling.
        """
        if self._old_pva_aux is not None and self._new_pva_aux is not None:
            pos = extract_pos(self._old_pva_aux)
            lat_factor0 = delta_lat_to_north(1, pos[0], pos[2])
            lon_factor0 = delta_lon_to_east(1, pos[0], pos[2])

            new_pos = extract_pos(self._new_pva_aux)
            lat_factor1 = delta_lat_to_north(1, new_pos[0], new_pos[2])
            lon_factor1 = delta_lon_to_east(1, new_pos[0], new_pos[2])

            lat0_to_lat1 = lat_factor1 / lat_factor0
            lon0_to_lon1 = lon_factor1 / lon_factor0
            Phi[:, 0] *= lat0_to_lat1
            Phi[:, 1] *= lon0_to_lon1

    def generate_f_pinson15(self) -> NDArray[float64]:
        """Generates the continuous time propagation matrix F.

        F is the Jacobian of the differential equations governing inertial error growth.
        This is based upon the model given in Titterton and Weston, 2nd edition.

        Returns:
            NDArray[float64]: The F Matrix.
        """
        # Already validated aux data at top of generate_model. These assertions are just
        # to satisfy mypy.
        assert self._new_pva_aux is not None
        assert self._new_pva_aux.quaternion is not None
        assert self._force_and_rate_aux is not None

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
        for ii in range(3):
            F[ii + 9, ii + 9] = -1.0 / self._imu_model.accel_bias_tau[ii]
            F[ii + 12, ii + 12] = -1.0 / self._imu_model.gyro_bias_tau[ii]

        return F

    def generate_q_pinson15(self) -> NDArray[float64]:
        """Generates the continuous time process noise covariance matrix Q.

        Returns:
            NDArray[float64]: The Q Matrix.
        """
        # Already validated PVA aux at top of generate_model. These assertions are just
        # to satisfy mypy.
        assert self._new_pva_aux is not None
        assert self._new_pva_aux.quaternion is not None
        Q = self._pre_Q
        C_sensor_to_ned = quat_to_dcm(self._new_pva_aux.quaternion)

        Q[3:6, 3:6] = C_sensor_to_ned @ Q[3:6, 3:6] @ C_sensor_to_ned.T
        Q[6:9, 6:9] = C_sensor_to_ned @ Q[6:9, 6:9] @ C_sensor_to_ned.T

        return Q
