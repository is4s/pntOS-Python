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


class PinsonPositionMeasurementProcessor(StandardMeasurementProcessor):
    """
    Generates a model that maps a position measurement to an inertial error state block.

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
        A Pinson Position Measurement Processor

        Args:
            label (str): Name of processor.
            state_block_labels (list[str]): A 1-element list of labels of state blocks this
                processor can update. The single entry should refer to a Pinson-style
                state block of at least size 9, with NED position errors in meters as
                the first three states and NED tilt errors, in radians, as states 6:9.
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
                f'PinsonPositionMeasurementProcessor requires {self._num_required_blocks} state blocks, got {state_block_labels}.',
            )

    def receive_aux_data(self, aux: list[Message | None]) -> None:
        if not aux or aux[0] is None:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                'PinsonPositionMeasurementProcessor expected aux data of type MeasurementPositionVelocityAttitude, but received empty list.',
            )
            return

        if len(aux) > 1:
            self._mediator.log_message(
                LoggingLevel.DEBUG,
                f'PinsonPositionMeasurementProcessor expected a single MeasurementPositionVelocityAttitude aux message, but received {len(aux)} aux messages. Ignoring all except the first message.',
            )

        if not isinstance(aux[0].wrapped_message, MeasurementPVA):
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'PinsonPositionMeasurementProcessor expected aux data of type MeasurementPositionVelocityAttitude, but got message of type {type(aux[0].wrapped_message)}.',
            )
            return

        pva = aux[0].wrapped_message

        if pva.quaternion is None:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'PinsonPositionMeasurementProcessor received PVA aux data with no quaternion at time {pva.time_of_validity.elapsed_nsec / 1e9:.9f}s.',
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
                MeasurementPosition using the GEODETIC reference frame.
            x_and_p: Current state estimate and covariance for the pinson-style block this processor
                is updating. NED position errors in meters are expected in at indices [0:3] and
                NED tilt errors in radians at indices [6:9].
        Returns:
            StandardMeasurementModel if all restrictions on `message` and `x_and_p` are met and
            proper aux data is available, None otherwise.

        **Model Description and Derivation**

        Measurements accepted by this this processor are modeled as

        :math:`P_s^g = P_p^g + C^g_p l_{p \\Rightarrow s}^p + \\eta(0, \\sigma_z)`

        where

        :math:`P_s^g` is the measured position vector of the :math:`s` sensor frame origin in some global Cartesian frame :math:`g`.

        :math:`P_p^g` is the true position of the :math:`p` platform frame origin in the :math:`g` frame.

        :math:`C^g_p` is the true rotation from the :math:`p` frame to the :math:`g` frame.

        :math:`l_{p \\Rightarrow s}^p` is the lever arm, a vector from the :math:`p` frame origin to the
        :math:`s` frame origin, expressed in the :math:`p` frame.

        :math:`\\eta(0, \\sigma_z)` is 0-mean Gaussian white noise.

        In other words, the measurement is modeled as perfect aside from white noise, offset from the
        platform frame by a known lever arm.

        The measurement is used to update the estimates of the error in the nominal trajectory of the
        platform frame, provided through a `MeasurementPositionVelocityAttitude` (PVA) via the
        :meth:`receive_aux_data` function. This PVA provides the following values of interest:

        :math:`\\hat{P_p^g}`: The estimated position of the platform frame origin in the :math:`g` frame.

        :math:`\\hat{C^{ned}_p}`: The estimated orientation of the platform frame with respect to the `NED` frame.

        We wish to use this measurement to update estimates of the following states contained in the
        'Pinson' state block:

        :math:`\\delta P_p^{ned}`: the estimate of the error in the current nominal position of the
        platform frame, expressed in the North-East-Down (NED) frame. The relationship between the true
        position, the nominal position, and the error state estimates is :math:`P = \\hat{P} + \\delta P`

        :math:`\\delta \\psi^{ned}`: The NED frame tilt error estimates. The relationship between the true
        and estimated rotations is :math:`C^{ned}_p = C^{ned}_{\\hat{ned}}C^{\\hat{ned}}_p \\approx [I - \\delta \\psi^{ned} \\times ]C^{\\hat{ned}}_p`
        (where :math:`\\times` is the skew/cross operator).

        The measurement vector provided to the filter :math:`z` is the difference between the
        measurement and the nominal platform frame position (white noise terms dropped, and :math:`ned` frame used as `g` frame):

        :math:`z = P_s^{ned}  - \\hat{P^{ned}_p}`

        The measurement model :math:`h(x)` is found by expanding :math:`z` in terms of the states :math:`x` (i.e. :math:`\\delta P_p^{ned}` and :math:`\\delta \\psi^{ned}`):

        :math:`P_s^{ned}  - \\hat{P^{ned}_p} = P_p^{ned} + C^{ned}_p l_{p \\Rightarrow s}^p  - \\hat{P}_p^{ned}`

        :math:`= \\hat{P_p^{ned}} + \\delta P_p^{ned} + C^{ned}_p l_{p \\Rightarrow s}^p - \\hat{P}_p^{ned}`

        :math:`= \\delta P_p^{ned} + C^{ned}_p l_{p \\Rightarrow s}^p`

        :math:`h(x) \\approx \\delta P_p^{ned} + [I - \\delta \\psi^{ned} \\times ]C^{\\hat{ned}}_p l_{p \\Rightarrow s}^p`

        Finally, to generate the measurement Jacobian :math:`H` we take derivatives of :math:`h(x)`:

        :math:`\\frac{\\delta h(x)}{d \\delta P_p^{ned}} = I`

        :math:`\\frac{\\delta h(x)}{d \\delta \\psi^{ned}} = C^{\\hat{ned}}_p l_{p \\Rightarrow s}^p \\times`
        """
        if len(self.state_block_labels) != self._num_required_blocks:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                'PinsonPositionMeasurementProcessor has wrong number of state blocks. Cannot generate model.',
            )
            return None

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
                f'PinsonPositionMeasurementProcessor cannot process message at time {time.elapsed_nsec / 1e9:.9f}s as it has not received inertial PVA aux data.',
            )
            return None

        pva_aux_time = self._inertial_pva.time_of_validity
        if pva_aux_time.elapsed_nsec != time.elapsed_nsec:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'PinsonPositionMeasurementProcessor cannot process message at time {time.elapsed_nsec / 1e9:.9f}s as inertial PVA aux data is at a different time (t={pva_aux_time.elapsed_nsec / 1e9:.9f}s).',
            )
            return None

        if pos.reference_frame is not MeasurementPositionReferenceFrame.GEODETIC:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'PinsonPositionMeasurementProcessor expected MeasurementPosition with a reference frame of f{MeasurementPositionReferenceFrame.GEODETIC}, but got measurement at time {time.elapsed_nsec / 1e9:.9f}s with a reference frame of {pos.reference_frame}. Cannot process message.',
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
        H[:, 6:9] = skew(C_platform_to_nav @ self._l_ps_p)

        def h(x: NDArray[float64]) -> NDArray[float64]:
            return (
                x[0:3, 0]
                + (np.eye(3) - skew(x[6:9, 0])) @ C_platform_to_nav @ self._l_ps_p
            ).reshape(3, 1)

        R = pos.covariance

        return StandardMeasurementModel(z, h, H, R)
