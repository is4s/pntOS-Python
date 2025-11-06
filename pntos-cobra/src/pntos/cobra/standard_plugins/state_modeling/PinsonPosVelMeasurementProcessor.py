import numpy as np
from aspn23 import (
    MeasurementPositionVelocityAttitude as MeasurementPVA,
    MeasurementPositionVelocityAttitudeReferenceFrame as MeasurementPVAReferenceFrame,
)
from numpy import float64
from numpy.typing import NDArray
from pntos.api.plugins.common import (
    EstimateWithCovariance,
    LoggingLevel,
    Mediator,
    Message,
)
from pntos.api.plugins.state_modeling import (
    StandardMeasurementModel,
    StandardMeasurementProcessor,
)
from pntos.cobra.utils import (
    delta_lat_to_north,
    delta_lon_to_east,
    quat_to_dcm,
    skew,
)


class PinsonPosVelMeasurementProcessor(StandardMeasurementProcessor):
    """
    Generates a model that maps PVA measurements to an inertial error state block.

    NOTE: Only the position and velocity fields of the PVA measurement are used,
    attitude is ignored.

    See :meth:`generate_model` for a detailed description of the assumptions and
    capabilities of this processor.
    """

    _mediator: Mediator
    _inertial_pva: MeasurementPVA | None
    _l_ps_p: NDArray[float64]
    _num_required_blocks: int

    def __init__(
        self,
        label: str,
        state_block_labels: list[str],
        mediator: Mediator,
        l_ps_p: NDArray[float64],
    ) -> None:
        """
        A Pinson Position and Velocity Measurement Processor

        Args:
            label (str): Name of processor.
            state_block_labels (list[str]): A 1-element list of labels of state blocks this
                processor can update. The single entry should refer to a Pinson-style
                state block of at least size 9, with NED position errors in meters as
                the first three states, NED velocity errors as states 3:6, and NED tilt
                errors, in radians, as states 6:9.
            mediator (Mediator): a Mediator instance.
            l_ps_p (NDArray[float64]): A 3-element array representing the lever arm from the
                platform frame origin to the position sensor origin, in the platform frame, in
                units of meters.
        """
        self.label = label
        self.state_block_labels = state_block_labels
        self._mediator = mediator
        self._inertial_pva = None
        self._l_ps_p = l_ps_p
        self._num_required_blocks = 1
        if len(state_block_labels) != self._num_required_blocks:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'PinsonPosVelMeasurementProcessor requires {self._num_required_blocks} state blocks, got {state_block_labels}.',
            )

    def receive_aux_data(self, aux: list[Message | None]) -> None:
        if not aux or aux[0] is None:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                'PinsonPosVelMeasurementProcessor expected aux data of type MeasurementPositionVelocityAttitude, but received empty list.',
            )
            return

        if len(aux) > 1:
            self._mediator.log_message(
                LoggingLevel.DEBUG,
                f'PinsonPosVelMeasurementProcessor expected a single MeasurementPositionVelocityAttitude aux message, but received {len(aux)} aux messages. Ignoring all except the first message.',
            )

        if not isinstance(aux[0].wrapped_message, MeasurementPVA):
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'PinsonPosVelMeasurementProcessor expected aux data of type MeasurementPositionVelocityAttitude, but got message of type {type(aux[0].wrapped_message)}.',
            )
            return

        pva = aux[0].wrapped_message

        if pva.quaternion is None:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'PinsonPosVelMeasurementProcessor received PVA aux data with no quaternion at time {pva.time_of_validity.elapsed_nsec / 1e9:.9f}s.',
            )
            return

        self._inertial_pva = pva

    def generate_model(
        self, message: Message, x_and_p: EstimateWithCovariance
    ) -> StandardMeasurementModel | None:
        """
        Generates the model mapping state estimates to the provided measurement.

        Args:
            message (Message): Measurement to process. `message.wrapped_message` must be a
                MeasurementPositionVelocityAttitude using the GEODETIC reference frame.
            x_and_p: Current state estimate and covariance for the pinson-style block this processor
                is updating. NED position errors in meters are expected in at indices [0:3], NED
                velocity errors at indices [3:6], and NED tilt errors in radians at indices [6:9].
        Returns:
            StandardMeasurementModel if all restrictions on `message` and `x_and_p` are met and
            proper aux data is available, None otherwise.

        **Model Description and Derivation**

        This measurement processes combined position and velocity measurements as a PVA measurement.
        The model for the position measurement is identical to that of `PinsonPositionMeasurementProcessor`,
        and the model for the velocity measurement is identical to that of `PinsonVelocityMeasurementProcessor`.
        """
        if len(self.state_block_labels) != self._num_required_blocks:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                'PinsonPosVelMeasurementProcessor has wrong number of state blocks. Cannot generate model.',
            )
            return None

        if not isinstance(message.wrapped_message, MeasurementPVA):
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'PinsonPosVelMeasurementProcessor expected message of type MeasurementPositionVelocityAttitude, but got message of type {type(message.wrapped_message)}. Cannot process message.',
            )
            return None

        pva = message.wrapped_message
        time = pva.time_of_validity
        if self._inertial_pva is None:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'PinsonPosVelMeasurementProcessor cannot process message at time {time.elapsed_nsec / 1e9:.9f}s as it has not received inertial PVA aux data.',
            )
            return None

        pva_aux_time = self._inertial_pva.time_of_validity
        if pva_aux_time.elapsed_nsec != time.elapsed_nsec:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'PinsonPosVelMeasurementProcessor cannot process message at time {time.elapsed_nsec / 1e9:.9f}s as inertial PVA aux data is at a different time (t={pva_aux_time.elapsed_nsec / 1e9:.9f}s).',
            )
            return None

        if pva.reference_frame is not MeasurementPVAReferenceFrame.GEODETIC:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'PinsonPosVelMeasurementProcessor expected MeasurementPositionVelocityAttitude with a reference frame of f{MeasurementPVAReferenceFrame.GEODETIC}, but got measurement at time {time.elapsed_nsec / 1e9:.9f}s with a reference frame of {pva.reference_frame}. Cannot process message.',
            )
            return None

        posvel = np.array([pva.p1, pva.p2, pva.p3, pva.v1, pva.v2, pva.v3])
        inertial_posvel = np.array(
            [
                self._inertial_pva.p1,
                self._inertial_pva.p2,
                self._inertial_pva.p3,
                self._inertial_pva.v1,
                self._inertial_pva.v2,
                self._inertial_pva.v3,
            ]
        )

        if None in posvel:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f"""PinsonPosVelMeasurementProcessor cannot process message at time
                {time.elapsed_nsec / 1e9:.9f}s as the measurement is missing fields`.
                \nMeasurement: {posvel}
                """,
            )
            return None
        if None in inertial_posvel:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                rf"""PinsonPosVelMeasurementProcessor cannot process message at time
                {time.elapsed_nsec / 1e9:.9f}s as the inertial PVA is missing fields`.
                \Inertial PVA: {inertial_posvel}
                """,
            )
            return None

        # Already validated presence of quaternion when aux data was received. This
        # assertion is just to satisfy mypy.
        assert self._inertial_pva.quaternion is not None
        C_platform_to_nav = quat_to_dcm(self._inertial_pva.quaternion)

        z = posvel - inertial_posvel
        z[0] = delta_lat_to_north(z[0], posvel[0], posvel[2])
        z[1] = delta_lon_to_east(z[1], posvel[0], posvel[2])
        z[2] = -z[2]
        z = z.reshape(6, 1)

        H = np.zeros((6, x_and_p.estimate.shape[0]))
        H[:3, :3] = np.eye(3)
        H[:3, 6:9] = skew(C_platform_to_nav @ self._l_ps_p)
        H[3:, 3:6] = np.eye(3)

        def h(x: NDArray[float64]) -> NDArray[float64]:
            pred_pos_err = (
                x[:3, 0]
                + (np.eye(3) - skew(x[6:9, 0])) @ C_platform_to_nav @ self._l_ps_p
            ).reshape(3, 1)
            pred_vel_err = x[3:6]
            return np.vstack((pred_pos_err, pred_vel_err))

        # Attitude may be present in PVA meas, but we dont need attitude covariance
        R = pva.covariance if pva.quaternion is None else pva.covariance[:6, :6]

        return StandardMeasurementModel(z, h, H, R)
