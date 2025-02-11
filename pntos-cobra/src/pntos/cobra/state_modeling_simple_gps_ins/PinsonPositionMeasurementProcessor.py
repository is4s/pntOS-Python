from typing import cast

import numpy as np
from aspn23 import (
    MeasurementPosition,
    MeasurementPositionReferenceFrame,
    MeasurementPositionVelocityAttitude as MeasurementPVA,
)
from numpy import float64
from numpy.typing import NDArray
from pntos.api.plugins.common import (
    EstimateWithCovariance,
    LoggingLevel,
    Mediator,
    Message,
)
from pntos.api.plugins.fusion import StandardMeasurementProcessor
from pntos.api.plugins.fusion_strategy import StandardMeasurementModel
from pntos.cobra.utils import (
    calc_lat_factor,
    calc_lon_factor,
    ecef_to_llh,
    llh_to_cen,
    llh_to_ecef,
    quat_to_dcm,
    skew,
)


class PinsonPositionMeasurementProcessor(StandardMeasurementProcessor):
    _mediator: Mediator
    _inertial_pva: MeasurementPVA | None
    _l_ps_p: NDArray[float64]

    def __init__(
        self,
        label: str,
        state_block_labels: list[str],
        mediator: Mediator,
        l_ps_p: NDArray[float64],
    ):
        self.label = label
        self.state_block_labels = state_block_labels
        self._mediator = mediator
        self._inertial_pva = None
        self._l_ps_p = l_ps_p

    def validate_aux_data(self, aux: list[Message]) -> bool:
        if not aux:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'PinsonPositionMeasurementProcessor expected aux data of type MeasurementPositionVelocityAttitude, but received empty list.',
            )
            return False

        if len(aux) > 1:
            self._mediator.log_message(
                LoggingLevel.WARN,
                f'PinsonPositionMeasurementProcessor expected a single MeasurementPositionVelocityAttitude aux message, but received {len(aux)} aux messages. Ignoring all except the first message.',
            )

        if not isinstance(aux[0].wrapped_message, MeasurementPVA):
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'PinsonPositionMeasurementProcessor expected aux data of type MeasurementPositionVelocityAttitude, but got message of type {type(aux[0].wrapped_message)}.',
            )
            return False

        pva = aux[0].wrapped_message

        if pva.quaternion is None:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'Pinson15NedBlock received PVA aux data with no quaternion at time {pva.time_of_validity.elapsed_nsec/1e9}s.',
            )

        return True

    def receive_aux_data(self, aux: list[Message]) -> None:
        if not self.validate_aux_data(aux):
            return

        self._inertial_pva = cast(MeasurementPVA, aux[0].wrapped_message)

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
        inertial_llh = np.array(
            [
                self._inertial_pva.p1,
                self._inertial_pva.p2,
                self._inertial_pva.p3,
            ]
        )

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
        H[:, :3] = np.eye(3)

        def h(x: NDArray[float64]) -> NDArray[float64]:
            return H @ x

        R = pos.covariance

        return StandardMeasurementModel(z, h, H, R)
