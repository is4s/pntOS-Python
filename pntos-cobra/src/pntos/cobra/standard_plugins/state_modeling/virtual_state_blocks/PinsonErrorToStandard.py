from aspn23 import (
    MeasurementPositionVelocityAttitude as MeasurementPVA,
    MeasurementPositionVelocityAttitudeReferenceFrame,
    TypeTimestamp,
)
from navtk.navutils import (
    d_dcm_to_rpy,
    d_ortho_dcm_wrt_tilt,
    dcm_to_rpy,
    delta_lat_to_north,
    delta_lon_to_east,
    east_to_delta_lon,
    north_to_delta_lat,
    ortho_dcm,
    quat_to_dcm,
    skew,
)
from numpy import array, concatenate, dot, eye, float64, zeros
from numpy.typing import NDArray
from pntos.api import (
    EstimateWithCovariance,
    EstimateWithCovarianceType,
    LoggingLevel,
    Mediator,
    Message,
    VirtualStateBlock,
)
from pntos.cobra.utils import extract_pos_and_vel

POS_START = 0
POS_END = 3
VEL_START = 3
VEL_END = 6
ATT_START = 6
ATT_END = 9


class PinsonErrorToStandard(VirtualStateBlock):
    """
    A VirtualStateBlock that maps Pinson-style error states into a 'Standard' (or direct) whole-valued
    representation by combining the error states with the uncorrected reference PVA.

    Output Transformation States in Order:
        0 - Latitude        (rad)
        1 - Longitude       (rad)
        2 - Altitude HAE    (m)
        3 - North Velocity  (m/s)
        4 - East Velocity   (m/s)
        5 - Down Velocity   (m/s)
        6 - Roll            (rad)
        7 - Pitch           (rad)
        8 - Yaw             (rad)

    Additional trailing states are retained and unmodified.
    See Pinson15NedBlock.py for a description of input states.
    """

    _mediator: Mediator
    _pva: MeasurementPVA | None
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
        self._pva = None
        self._eye3 = eye(3)
        self._dx = array(((0, 0, 0), (0, 0, -1), (0, 1, 0)))
        self._dy = array(((0, 0, 1), (0, 0, 0), (-1, 0, 0)))
        self._dz = array(((0, -1, 0), (1, 0, 0), (0, 0, 0)))

    def receive_aux_data(self, aux: list[Message | None]) -> None:
        for msg in reversed(aux):
            if (
                msg is not None
                and isinstance(msg.wrapped_message, MeasurementPVA)
                and msg.wrapped_message.reference_frame
                == MeasurementPositionVelocityAttitudeReferenceFrame.GEODETIC
            ):
                self._pva = msg.wrapped_message
                break

    def convert(
        self,
        estimate_with_covariance: EstimateWithCovariance,
        time: TypeTimestamp,
    ) -> EstimateWithCovariance:
        state = self.convert_estimate(estimate_with_covariance.estimate, time)
        jac = self.jacobian(estimate_with_covariance.estimate, time)
        cov = dot(dot(jac, estimate_with_covariance.covariance), jac.T)
        return EstimateWithCovariance(
            EstimateWithCovarianceType.EWC_GENERIC, state, cov
        )

    def convert_estimate(
        self, estimate: NDArray[float64], time: TypeTimestamp
    ) -> NDArray[float64]:
        if self._pva is None:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                'No PVA aux data has been provided to PinsonErrorToStandard. Cannot convert estimate.',
            )
            raise RuntimeError
        if self._pva.quaternion is None:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                'An invalid quaternion was provided to PinsonErrorToStandard. Cannot convert estimate.',
            )
            raise RuntimeError
        if self._pva.time_of_validity.elapsed_nsec != time.elapsed_nsec:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'Requested time {time.elapsed_nsec} does not match the latest PVA solution at time {self._pva.time_of_validity.elapsed_nsec}. Cannot convert estimate.',
            )
            raise RuntimeError
        pos_n_vel = extract_pos_and_vel(self._pva)
        if pos_n_vel is None:
            self._mediator.log_message(
                LoggingLevel.ERROR, 'Invalid PVA aux data. Cannot convert estimate.'
            )
            raise RuntimeError
        pos, vel = pos_n_vel[0], pos_n_vel[1]
        delta_lat = north_to_delta_lat(estimate[POS_START, 0], pos[0], pos[2])
        delta_lon = east_to_delta_lon(estimate[POS_START + 1, 0], pos[0], pos[2])
        delta_alt = -estimate[POS_START + 2, 0]
        corr_llh = array(
            [
                delta_lat + pos[0],
                delta_lon + pos[1],
                delta_alt + pos[2],
            ]
        )
        corr_vel_ned = array(
            [
                vel[0] + estimate[VEL_START, 0],
                vel[1] + estimate[VEL_START + 1, 0],
                vel[2] + estimate[VEL_START + 2, 0],
            ]
        )

        pva_dcm = quat_to_dcm(self._pva.quaternion).T
        corr_rpy = dcm_to_rpy(
            ortho_dcm(dot(pva_dcm, self._eye3 + skew(estimate[ATT_START:ATT_END, 0])).T)
        )
        out: NDArray[float64] = concatenate(
            (corr_llh, corr_vel_ned, corr_rpy, estimate[ATT_END:, 0])
        ).reshape(-1, 1)
        return out

    def jacobian(
        self, estimate: NDArray[float64], time: TypeTimestamp
    ) -> NDArray[float64]:
        if self._pva is None:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                'No PVA aux data has been provided to PinsonErrorToStandard. Cannot create jacobian.',
            )
            raise RuntimeError
        if self._pva.quaternion is None:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                'An invalid quaternion was provided to PinsonErrorToStandard. Cannot create jacobian.',
            )
            raise RuntimeError
        if self._pva.time_of_validity.elapsed_nsec != time.elapsed_nsec:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'Requested time {time.elapsed_nsec} does not match the latest PVA solution at time {self._pva.time_of_validity.elapsed_nsec}. Cannot create jacobian.',
            )
            raise RuntimeError
        pos_n_vel = extract_pos_and_vel(self._pva)
        if pos_n_vel is None:
            self._mediator.log_message(
                LoggingLevel.ERROR, 'Invalid PVA aux data. Cannot create jacobian.'
            )
            raise RuntimeError
        pos = pos_n_vel[0]

        m2r = array(
            (
                (1.0 / delta_lat_to_north(1, pos[0], pos[2]), 0, 0),
                (0, 1.0 / delta_lon_to_east(1, pos[0], pos[2]), 0),
                (0, 0, -1),
            )
        )
        jac = eye(len(estimate))
        jac[POS_START:POS_END, POS_START:POS_END] = m2r
        pva_dcm = quat_to_dcm(self._pva.quaternion).T

        ddx = d_ortho_dcm_wrt_tilt(pva_dcm, estimate[ATT_START:ATT_END, 0], self._dx)
        ddy = d_ortho_dcm_wrt_tilt(pva_dcm, estimate[ATT_START:ATT_END, 0], self._dy)
        ddz = d_ortho_dcm_wrt_tilt(pva_dcm, estimate[ATT_START:ATT_END, 0], self._dz)
        corr_C_ned_to_s = ortho_dcm(
            dot(pva_dcm, self._eye3 + skew(estimate[ATT_START:ATT_END, 0]))
        )
        z3 = zeros((3, 3))

        jac[ATT_START:ATT_END, ATT_START:ATT_END] = d_dcm_to_rpy(
            self._eye3, z3, z3, z3, corr_C_ned_to_s, ddx, ddy, ddz
        )

        return jac
