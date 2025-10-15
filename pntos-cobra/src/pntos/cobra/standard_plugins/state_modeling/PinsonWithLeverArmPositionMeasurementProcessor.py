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


class PinsonWithLeverArmPositionMeasurementProcessor(StandardMeasurementProcessor):
    """
    Maps a position measurement to an inertial error state block, a lever arm offset block, and a
    sensor error block.

    See :meth:`generate_model` for a detailed description of the assumptions and capabilities of
    this processor.
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
        Args:
            label (str): Name of processor.
            state_block_labels (list[str]): A 3-length list of labels of state blocks this
                processor can update. The first entry should refer to a Pinson-style
                state block of at least size 9, with NED position errors in meters as
                the first three states and NED tilt errors, in radians, as states ``6:9``.
                The second state block entry should refer to a 3-element
                state block that models the position sensor errors in the NED frame.
                The third state block entry should refer to a 3-element state block
                that models the additional platform to position sensor lever arm in the body frame,
                in meters. The complete lever arm estimate is composed of the sum of these last 3
                states and ``l_ps_p``.
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
        self._num_required_blocks = 3
        if len(state_block_labels) != self._num_required_blocks:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                'PinsonWithLeverArmPositionMeasurementProcessor requires {} state blocks, got {}.'.format(
                    self._num_required_blocks, state_block_labels
                ),
            )

    def receive_aux_data(self, aux: list[Message]) -> None:
        """
        Receive aux data.

        This function is used to provide additional data required by :meth:`generate_model` beyond
        what is provided by the measurement and state estimate and covariance. This processor requires
        aux data that represents the nominal position, velocity and attitude of the platform at the
        time of measuremet update. The inertial error block referenced in :meth:`generate_model`
        represents the estimated errors in this nominal PVA.

        Args:
            aux (list[Message]): Aux data to process. Expected to be length 1 and contain a
                ``MeasurementPositionVelocityAttitude`` with a valid quaternion.
        """
        if not aux:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'PinsonWithLeverArmPositionMeasurementProcessor expected aux data of type \
                MeasurementPositionVelocityAttitude, but received empty list.',
            )
            return

        if len(aux) > 1:
            self._mediator.log_message(
                LoggingLevel.DEBUG,
                f'PinsonWithLeverArmPositionMeasurementProcessor expected a single \
                MeasurementPositionVelocityAttitude aux message, but received\
                {len(aux)} aux messages. Ignoring all except the first message.',
            )

        if not isinstance(aux[0].wrapped_message, MeasurementPVA):
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'PinsonWithLeverArmPositionMeasurementProcessor expected aux data of type\
                MeasurementPositionVelocityAttitude, but got message of\
                type {type(aux[0].wrapped_message)}.',
            )
            return

        pva = aux[0].wrapped_message

        if pva.quaternion is None:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'PinsonWithLeverArmPositionMeasurementProcessor received PVA aux data with no \
                    quaternion at time {pva.time_of_validity.elapsed_nsec / 1e9:.9f}s.',
            )
            return

        self._inertial_pva = pva

    def generate_model(
        self, message: Message, x_and_p: EstimateWithCovariance
    ) -> StandardMeasurementModel | None:
        """
        Generates a StandardMeasurementModel relating a position measurement to the states
        described in :meth:`__init__`.

        Args:
            message (Message): Measurement used to update. The ``wrapped_message`` member must
                be of type ``aspn23.MeasurementPosition``.
            x_and_p (EstimateWithCovariance): The estimate and covariance of the states referenced
                by this model. The layout of the states should follow the description in :meth:`__init__`.

        Returns:
            Model relating measurement to states. Will return ``None`` if
            a) ``state_block_labels`` is incorrectly configured
            b) ``message`` is an unsupported type
            c) a ``MeasurementPositionVelocityAttitude`` with the estimated PVA at the current
            measurement time has not been received via :meth:`receive_aux_data`.


        **Model Description and Derivation**

        This processor uses a model very similar to that used described in
        :meth:`pntos.cobra.internal.PinsonWithNedFogmPositionMeasurementProcessor.generate_model`.
        The primary difference is that instead of assuming the lever arm between the platform
        frame and the sensor frame is perfectly known, the model incorporates 3 additional states
        to account for the possible deviation between the assumed lever arm provided to
        :meth:`__init__` and the *actual* lever arm.

        The model for the measurement is the same as that of :class:`pntos.cobra.internal.PinsonWithNedFogmPositionMeasurementProcessor`:

        :math:`P_s^g = P_p^g + C^g_p l_{p \\Rightarrow s}^p - \\delta z^{g} + \\eta(0, \\sigma_z)`

        but now we can rewrite the true lever arm :math:`l_{p \\Rightarrow s}^p` in terms of the
        estimated lever arm :math:`\\hat{l}_{p \\Rightarrow s}^p` plus deviation :math:`\\delta l_{p \\Rightarrow s}^p`:

        :math:`P_s^g = P_p^g + C^g_p(\\hat{l}_{p \\Rightarrow s}^p + \\delta l_{p \\Rightarrow s}^p) - \\delta z^{g} + \\eta(0, \\sigma_z)`.

        Following the procedure outlined in the documentation for the other position processors we form the filter update vector by differencing
        the measurement and the estimated platform position:

        :math:`z = P_s^{ned}  - \\hat{P^{ned}_p}`

        :math:`= P_p^{ned} + C^{ned}_p l_{p \\Rightarrow s}^p - \\delta z_{ned} - \\hat{P}_p^{ned}`

        :math:`= \\hat{P_p^{ned}} + \\delta P_p^{ned} + C^{ned}_p l_{p \\Rightarrow s}^p - \\delta z^{ned} - \\hat{P}_p^{ned}`

        :math:`= \\delta P_p^{ned} + C^{ned}_p l_{p \\Rightarrow s}^p - \\delta z^{ned}`

        The measurement prediction function is found by expanding this in terms of state estimates and nominal values:

        :math:`h(x) \\approx \\delta P_p^{ned} + [I - \\delta \\psi^{ned} \\times ]C^{\\hat{ned}}_p (\\hat{l}_{p \\Rightarrow s}^p + \\delta l_{p \\Rightarrow s}^p) - \\delta z^{ned}`

        Taking the derivative with respect to the states we get the Jacobian elements:

        :math:`\\frac{\\delta h(x)}{d \\delta P_p^{ned}} = I`

        :math:`\\frac{\\delta h(x)}{d \\delta \\psi^{ned}} = C^{\\hat{ned}}_p(\\hat{l}_{p \\Rightarrow s}^p + \\delta l_{p \\Rightarrow s}^p)\\times`

        :math:`\\frac{\\delta h(x)}{d \\delta l_{p \\Rightarrow s}^p} = [I - \\delta \\psi^{ned} \\times ]C^{\\hat{ned}}_p`

        :math:`\\frac{\\delta h(x)}{d \\delta z^{ned}} = -I`

        """
        if len(self.state_block_labels) != self._num_required_blocks:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                'PinsonWithLeverArmPositionMeasurementProcessor has wrong number of state blocks \
                 Cannot generate model.',
            )
            return None

        if not isinstance(message.wrapped_message, MeasurementPosition):
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'PinsonWithLeverArmPositionMeasurementProcessor expected message of type \
                MeasurementPosition, but got message of type \
                {type(message.wrapped_message)}. Cannot process message.',
            )
            return None

        pos = message.wrapped_message
        time = pos.time_of_validity
        if self._inertial_pva is None:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'PinsonWithLeverArmPositionMeasurementProcessor cannot process message at time \
                {time.elapsed_nsec / 1e9:.9f}s as it has not received inertial PVA aux data.',
            )
            return None

        pva_aux_time = self._inertial_pva.time_of_validity
        if abs(pva_aux_time.elapsed_nsec - time.elapsed_nsec) > 1000:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'PinsonWithLeverArmPositionMeasurementProcessor cannot process message at time \
                {time.elapsed_nsec / 1e9:.9f}s as inertial PVA aux data is at a\
                different time (t={pva_aux_time.elapsed_nsec / 1e9:.9f}s).',
            )
            return None

        if pos.reference_frame is not MeasurementPositionReferenceFrame.GEODETIC:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'PinsonWithLeverArmPositionMeasurementProcessor expected MeasurementPosition \
                with a reference frame of GEODETIC, but got measurement at \
                time {time.elapsed_nsec / 1e9:.9f}s with a reference frame of \
                {pos.reference_frame}. Cannot process message.',
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
        H[:, 6:9] = skew(C_platform_to_nav @ (self._l_ps_p + x_and_p.estimate[-3:, 0]))
        H[:, -3:] = (np.eye(3) - skew(x_and_p.estimate[6:9, 0])) @ C_platform_to_nav
        H[:, -6:-3] = -np.eye(3)

        def h(x: NDArray[float64]) -> NDArray[float64]:
            res: NDArray[float64] = (
                x[0:3, 0]
                + (np.eye(3) - skew(x[6:9, 0]))
                @ C_platform_to_nav
                @ (self._l_ps_p + x[-3:, 0])
                - x[-6:-3, 0]
            ).reshape(3, 1)
            return res

        R = pos.covariance

        return StandardMeasurementModel(z, h, H, R)
