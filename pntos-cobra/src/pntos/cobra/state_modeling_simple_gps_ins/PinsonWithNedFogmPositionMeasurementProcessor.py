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
    delta_lat_to_north,
    delta_lon_to_east,
    quat_to_dcm,
    skew,
)


class PinsonWithNedFogmPositionMeasurementProcessor(StandardMeasurementProcessor):
    """
    Generates a model that maps a position measurement to an inertial error state
    block and a position measurement error block.
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
    ):
        """
        Args:
            label (str): Name of processor.
            state_block_labels (list[str]): A 2-length list of labels of state blocks this
            processor can update. The first entry should refer to a Pinson-style
            state block of at least size 9, with NED position errors in meters as
            the first three states and NED tilt errors, in radians, as states 6:9.
            The second state block entry should refer to a 3-element FOGM
            state block that models the position sensor errors in the NED frame.
            mediator (Mediator): a Mediator instance
            l_ps_p (NDArray[float64]): A 3-element array representing the lever arm from the
            platform frame origin to the position sensor origin, in the platform frame, in
            units of meters.
        """
        self.label = label
        self.state_block_labels = state_block_labels
        self._mediator = mediator
        self._inertial_pva = None
        self._l_ps_p = l_ps_p
        self._num_required_blocks = 2
        if len(state_block_labels) != self._num_required_blocks:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                'PinsonWithNedFogmPositionMeasurementProcessor requires {} state blocks, got {}.'.format(
                    self._num_required_blocks, state_block_labels
                ),
            )

    def receive_aux_data(self, aux: list[Message]) -> None:
        if not aux:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'PinsonWithNedFogmPositionMeasurementProcessor expected aux data of type\
                MeasurementPositionVelocityAttitude, but received empty list.',
            )
            return

        if len(aux) > 1:
            self._mediator.log_message(
                LoggingLevel.WARN,
                f'PinsonWithNedFogmPositionMeasurementProcessor expected a single \
                MeasurementPositionVelocityAttitude aux message, but received\
                {len(aux)} aux messages. Ignoring all except the first message.',
            )

        if not isinstance(aux[0].wrapped_message, MeasurementPVA):
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'PinsonWithNedFogmPositionMeasurementProcessor expected aux data of type\
                MeasurementPositionVelocityAttitude, but got message of\
                type {type(aux[0].wrapped_message)}.',
            )
            return

        pva = aux[0].wrapped_message

        if pva.quaternion is None:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'PinsonWithNedFogmPositionMeasurementProcessor received PVA aux data with no quaternion\
                at time {pva.time_of_validity.elapsed_nsec / 1e9}s.',
            )
            return

        self._inertial_pva = pva

    def generate_model(
        self, message: Message, x_and_p: EstimateWithCovariance
    ) -> StandardMeasurementModel | None:
        if len(self.state_block_labels) != self._num_required_blocks:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'PinsonWithNedFogmPositionMeasurementProcessor has wrong number of state blocks. Cannot generate model.',
            )
            return None

        if not isinstance(message.wrapped_message, MeasurementPosition):
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'PinsonWithNedFogmPositionMeasurementProcessorexpected message of type\
                MeasurementPosition, but got message of type \
                {type(message.wrapped_message)}. Cannot process message.',
            )
            return None

        pos = message.wrapped_message
        time = pos.time_of_validity
        if self._inertial_pva is None:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'PinsonWithNedFogmPositionMeasurementProcessor cannot process message at time\
                {time.elapsed_nsec / 1e9}s as it has not received inertial PVA aux data.',
            )
            return None

        pva_aux_time = self._inertial_pva.time_of_validity
        if abs(pva_aux_time.elapsed_nsec - time.elapsed_nsec) > 1000:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'PinsonWithNedFogmPositionMeasurementProcessor cannot process message at time\
                {time.elapsed_nsec / 1e9}s as inertial PVA aux data is at a\
                different time (t={pva_aux_time.elapsed_nsec / 1e9}s).',
            )
            return None

        if pos.reference_frame is not MeasurementPositionReferenceFrame.GEODETIC:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'PinsonWithNedFogmPositionMeasurementProcessor expected MeasurementPosition\
                with a reference from of GEODETIC, but got measurement at\
                time {time.elapsed_nsec / 1e9}s with a reference frame of\
                {pos.reference_frame}.Cannot process message.',
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

        # Already validated presence of quaternion when aux data was received. This
        # assertion is just to satisfy mypy.
        assert self._inertial_pva.quaternion is not None
        C_platform_to_nav = quat_to_dcm(self._inertial_pva.quaternion)

        z = llh - inertial_llh
        z[0] = delta_lat_to_north(z[0], llh[0], llh[2])
        z[1] = delta_lon_to_east(z[1], llh[0], llh[2])
        z[2] = -z[2]
        z = z.reshape(3, 1)

        H = np.zeros((3, x_and_p.estimate.shape[0]))
        H[:, 0:3] = np.eye(3)
        H[:, 6:9] = C_platform_to_nav @ self._l_ps_p
        H[:, -3:] = -np.eye(3)

        def h(x: NDArray[float64]) -> NDArray[float64]:
            return (
                x[0:3, 0]
                + (np.eye(3) - skew(x[6:9, 0])) @ C_platform_to_nav @ self._l_ps_p
                - x[-3:, 0]
            ).reshape(3, 1)

        R = pos.covariance

        return StandardMeasurementModel(z, h, H, R)
