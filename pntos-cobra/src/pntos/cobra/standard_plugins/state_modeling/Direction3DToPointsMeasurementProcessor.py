import numpy as np
import scipy.linalg
from aspn23 import (
    MeasurementDirection3DToPoints as MeasurementD2P3,
    MeasurementPositionVelocityAttitude as MeasurementPVA,
    TypeDirection3DToPointReferenceFrame,
)
from numpy import float64
from numpy.typing import NDArray
from pntos.api import (
    GenXandP,
    LoggingLevel,
    Mediator,
    Message,
    StandardMeasurementModel,
    StandardMeasurementProcessor,
)
from pntos.cobra.utils import (
    delta_lat_to_north,
    delta_lon_to_east,
    quat_to_dcm,
    skew,
)


class Direction3DToPointsMeasurementProcessor(StandardMeasurementProcessor):
    """
    Generates a model that maps a Direction3DToPoints measurement to an inertial error state block.

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
        orientation: NDArray[float64],
    ) -> None:
        """
        A Direction3DToPoints Measurement Processor

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
            orientation (NDArray[float64]): A 4 element quaternion array representing the sensor frame angle offset from the platform frame.
        """
        self.label = label
        self.state_block_labels = state_block_labels
        self._mediator = mediator
        self._inertial_pva = None
        self._l_ps_p = l_ps_p
        self._orientation = orientation
        self._num_required_blocks = 1
        if len(state_block_labels) != self._num_required_blocks:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'Direction3DToPointsMeasurementProcessor requires {self._num_required_blocks} state blocks, got {state_block_labels}.',
            )

    def receive_aux_data(self, aux: list[Message | None]) -> None:
        if not aux or aux[0] is None:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                'Direction3DToPointsMeasurementProcessor expected aux data of type MeasurementPositionVelocityAttitude, but received empty list.',
            )
            return

        if len(aux) > 1:
            self._mediator.log_message(
                LoggingLevel.WARN,
                f'Direction3DToPointsMeasurementProcessor expected a single MeasurementPositionVelocityAttitude aux message, but received {len(aux)} aux messages. Ignoring all except the first message.',
            )

        if not isinstance(aux[0].wrapped_message, MeasurementPVA):
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'Direction3DToPointsMeasurementProcessor expected aux data of type MeasurementPositionVelocityAttitude, but got message of type {type(aux[0].wrapped_message)}.',
            )
            return

        pva = aux[0].wrapped_message

        if pva.quaternion is None:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'Direction3DToPointsMeasurementProcessor received PVA aux data with no quaternion at time {pva.time_of_validity.elapsed_nsec / 1e9:.9f}s.',
            )
            return

        self._inertial_pva = pva

    def generate_model(
        self, message: Message, gen_x_and_p_func: GenXandP
    ) -> StandardMeasurementModel | None:
        """
        Generates the model mapping state estimates to the provided measurement.

        Args:
            message (Message): Measurement to process. `message.wrapped_message` must be a
                MeasurementDirection3DToPoints using the SINE_SPACE reference frame.
            gen_x_and_p_func (GenXandP): Callback to get the state estimate and covariance for
                the pinson-style block this processor is updating. NED position errors
                in meters are expected in at indices [0:3] and NED tilt errors in
                radians at indices [6:9].
        Returns:
            StandardMeasurementModel if all restrictions on `message` and `gen_x_and_p_func` are met and
            proper aux data is available, None otherwise.

        **Model Description and Derivation**

        Measurements accepted by this processor are modeled as

        :math:`U_{s \\Rightarrow f}^s = \\frac{C_p^s C_g^p (P_f^g - (P_p^g + C_p^g l_{p \\Rightarrow s}^p))}{|| C_p^s C_g^p (P_f^g - (P_p^g + C_p^g l_{p \\Rightarrow s}^p)) ||} + \\eta(0,\\sigma_z)`

        .. _note-label:

        .. note:: The Direction3DToPointsMeasurement for this processor is a sine-space measurement type, meaning the received measurements are 2-element arrays represented by the y and z components of the unit vector above.

        where

        :math:`U_{s \\Rightarrow f}^s` is the measured unit vector describing the direction to the position of some feature :math:`P_f^g` along the vector from :math:`s` sensor to :math:`f` feature.

        :math:`C_p^s` is the true rotation from the :math:`p` platform frame to the :math:`s` sensor frame.

        :math:`C_g^p` is the true rotation from some global Cartesian frame :math:`g` to the :math:`p` platform frame.

        :math:`P_f^g` is the true position of the :math:`f` feature in the :math:`g` frame.

        :math:`P_p^g` is the true position of the :math:`p` platform frame origin in the :math:`g` frame.

        :math:`C_p^g` is the true rotation from the :math:`p` platform frame to the :math:`g` frame.

        :math:`l_{p \\Rightarrow s}^p` is the lever arm, a vector from the :math:`p` frame origin to the :math:`s` frame origin, expressed in the :math:`p` frame.

        :math:`\\eta(0, \\sigma_z)` is 0-mean Gaussian white noise.

        :math:`||` is the magnitude of the vector inside these symbols.

        In other words, the measurement is modeled as perfect aside from white noise, offset from the
        platform frame by a known lever arm.

        The measurement is used to update the estimates of the error in the nominal trajectory of the
        platform frame, provided through a `MeasurementPositionVelocityAttitude` (PVA) via the
        :meth:`receive_aux_data` function. This PVA provides the following values of interest:

        :math:`\\hat{P}_p^g`: The estimated position of the platform frame origin in the g frame.

        :math:`\\hat{C}^{ned}_p`: The estimated orientation of the platform frame with respect to the North-East-Down (NED) frame.

        We wish to use this measurement to update estimates of the following states contained in the
        'Pinson' state block:

        :math:`\\delta P_p^{ned}`: The estimate of the error in the current nominal position of the
        platform frame, expressed in the NED frame. The relationship between the true
        position, the nominal position, and the error state estimates is :math:`P = \\hat{P} + \\delta P`

        :math:`\\delta \\psi^{ned}`: The NED frame tilt error estimates. The relationship between the true
        and estimated rotations is :math:`C^{ned}_p = C^{ned}_{\\hat{ned}}C^{\\hat{ned}}_p \\approx [I - \\delta \\psi^{ned} \\times ]C^{\\hat{ned}}_p`
        (where :math:`\\times` is the skew/cross operator).

        The measurement vector provided to the filter :math:`z` is the difference between the
        measurement and the predicted unit vector to the feature using nominal platform position and orientation (white noise terms dropped, and :math:`ned` frame used as `g` frame):

        :math:`z = U_{s \\Rightarrow f}^s  - \\hat{U}_{s \\Rightarrow f}^s`

        The measurement model :math:`h(x)` is found by expanding :math:`z` in terms of the states :math:`x` (i.e. :math:`\\delta P_p^{ned}` and :math:`\\delta \\psi^{ned}`):

        :math:`z = U_{s \\Rightarrow f}^s  - \\hat{U}_{s \\Rightarrow f}^s = \\frac{\\vec{v}_{s \\Rightarrow f}^s}{||\\vec{v}_{s \\Rightarrow f}^s||} - \\frac{\\hat{\\vec{v}}_{s \\Rightarrow f}^s}{||\\hat{\\vec{v}}_{s \\Rightarrow f}^s||}`

        where we can expand the true numerator :math:`\\vec{v}_{s \\Rightarrow f}^s` using the error state definitions above:

        :math:`\\vec{v}_{s \\Rightarrow f}^s = C_p^s C_{ned}^p (P_f^{ned} - (P_p^{ned} + C_p^{ned} l_{p \\Rightarrow s}^p))`

        :math:`= C_p^s \\hat{C}_{ned}^p [I + \\delta\\psi^{ned} \\times](P_f^{ned} - ((\\hat{P}_p^{ned} + \\delta P_p^{ned}) + [I - \\delta\\psi^{ned} \\times] \\hat{C}_p^{ned} l_{p \\Rightarrow s}^p)`

        After expanding the solution above, the higher-order error products (:math:`2^{nd}` order or higher) can be dropped, giving us the following :

        :math:`= C_p^s \\hat{C}_{ned}^p (P_f^{ned} - \\hat{P}_p^{ned} - \\hat{C}_p^{ned} l_{p \\Rightarrow s}^p) + C_p^s \\hat{C}_{ned}^p [\\delta\\psi^{ned} \\times] (P_f^{ned} - \\hat{P}_p^{ned} - \\hat{C}_p^{ned} l_{p \\Rightarrow s}^p) - C_p^s \\hat{C}_{ned}^p \\delta P_p^{ned} + C_p^s \\hat{C}_{ned}^p [\\delta\\psi^{ned} \\times]\\hat{C}_p^{ned} l_{p \\Rightarrow s}^p`

        :math:`= C_p^s \\hat{C}_{ned}^p (P_f^{ned} - \\hat{P}_p^{ned} - \\hat{C}_p^{ned} l_{p \\Rightarrow s}^p) - C_p^s \\hat{C}_{ned}^p [(P_f^{ned} - \\hat{P}_p^{ned}) \\times] \\delta\\psi - C_p^s \\hat{C}_{ned}^p \\delta P_p^{ned}`

        :math:`= \\hat{\\vec{v}}_{s \\Rightarrow f}^s - C_p^s \\hat{C}_{ned}^p [(P_f^{ned} - \\hat{P}_p^{ned}) \\times] \\delta\\psi - C_p^s \\hat{C}_{ned}^p \\delta P_p^{ned}`

        The numerator estimate :math:`\\hat{\\vec{v}}_{s \\Rightarrow f}^s` can now be subtracted to satisfy the :math:`\\delta \\vec{v}_{s \\Rightarrow f}^s = \\vec{v}_{s \\Rightarrow f}^s - \\hat{\\vec{v}}_{s \\Rightarrow f}^s` definition:

        :math:`\\delta \\vec{v}_{s \\Rightarrow f}^s = -C_p^s \\hat{C}_{ned}^p [(P_f^{ned} - \\hat{P}_p^{ned}) \\times] \\delta\\psi - C_p^s \\hat{C}_{ned}^p \\delta P_p^{ned}`

        Using the identity :math:`\\delta U \\approx A \\delta v` where :math:`A = \\frac{I - \\hat{U} \\hat{U}^T}{||\\hat{v}||}` (bottom 2x3 is used for this processor by dropping the first row, see :ref:`Note <note-label>` above), the measurement model :math:`h(x)` for the whole unit vector can be found:

        :math:`h(x) \\approx A (-C_p^s \\hat{C}_{ned}^p [(P_f^{ned} - \\hat{P}_p^{ned}) \\times] \\delta\\psi) - A (C_p^s \\hat{C}_{ned}^p \\delta P_p^{ned})`

        where :math:`h(x)` is a 2x1 array, matching the size of the measurements.

        Finally, to generate the measurement Jacobian :math:`H` we take derivatives of :math:`h(x)`:

        :math:`\\frac{\\delta h(x)}{d \\delta P_p^{ned}} = -A C_p^s \\hat{C}_{ned}^p`

        :math:`\\frac{\\delta h(x)}{d \\delta \\psi^{ned}} = -A C_p^s \\hat{C}_{ned}^p [(P_f^{ned} - \\hat{P}_p^{ned}) \\times]`
        """
        if len(self.state_block_labels) != self._num_required_blocks:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                'Direction3DToPointsMeasurementProcessor has wrong number of state blocks. Cannot generate model.',
            )
            return None

        if not isinstance(message.wrapped_message, MeasurementD2P3):
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'Direction3DToPointsMeasurementProcessor expected message of type MeasurementDirection3DToPoints, but got message of type {type(message.wrapped_message)}. Cannot process message.',
            )
            return None

        dir2known = message.wrapped_message
        time = dir2known.time_of_validity
        if self._inertial_pva is None:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'Direction3DToPointsMeasurementProcessor cannot process message at time {time.elapsed_nsec / 1e9:.9f}s as it has not received inertial PVA aux data.',
            )
            return None

        pva_aux_time = self._inertial_pva.time_of_validity
        if pva_aux_time.elapsed_nsec != time.elapsed_nsec:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'Direction3DToPointsMeasurementProcessor cannot process message at time {time.elapsed_nsec / 1e9:.9f}s as inertial PVA aux data is at a different time (t={pva_aux_time.elapsed_nsec / 1e9:.9f}s).',
            )
            return None

        if (
            dir2known.obs[0].reference_frame
            is not TypeDirection3DToPointReferenceFrame.SINE_SPACE
        ):
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'Direction3DToPointsMeasurementProcessor expected MeasurementDirection3DToPoints with a reference frame of f{TypeDirection3DToPointReferenceFrame.SINE_SPACE}, but got measurement at time {time.elapsed_nsec / 1e9:.9f}s with a reference frame of {dir2known.obs[0].reference_frame}. Cannot process message.',
            )
            return None

        # Unit Vector method

        # Define current filter position estimate
        inertial_llh = np.array(
            [
                self._inertial_pva.p1,
                self._inertial_pva.p2,
                self._inertial_pva.p3,
            ]
        )

        # Define frame transformations
        assert self._inertial_pva.quaternion is not None
        C_nav_to_platform = quat_to_dcm(self._inertial_pva.quaternion).T
        C_platform_to_sensor = quat_to_dcm(self._orientation)
        C_nav_to_sensor = C_platform_to_sensor @ C_nav_to_platform

        l_s = self._l_ps_p.reshape(3, 1)  # Lever arm in body frame

        ewc = gen_x_and_p_func(self.state_block_labels)
        if ewc is None:
            return None

        N = len(dir2known.obs)  # number of observations
        num_states = ewc.estimate.shape[0]
        H = np.zeros((N, 2, num_states))

        # Nx3 array of locations of each feature
        feature_llh = np.array(
            [
                [
                    obs.remote_point.position1,
                    obs.remote_point.position2,
                    obs.remote_point.position3,
                ]
                for obs in dir2known.obs
            ]
        )
        # Nx2 array of direction observations to each feature
        direction_obs = np.array([obs.obs for obs in dir2known.obs])

        # Convert LLA difference to NED meters
        delta_pos = feature_llh - inertial_llh
        delta_pos[:, 0] = delta_lat_to_north(
            delta_pos[:, 0], inertial_llh[0], inertial_llh[2]
        )
        delta_pos[:, 1] = delta_lon_to_east(
            delta_pos[:, 1], inertial_llh[0], inertial_llh[2]
        )
        delta_pos[:, 2] = -delta_pos[:, 2]

        # Map to sensor frame
        delta_pos_sensor = (delta_pos @ C_nav_to_sensor.T)[:, :, None] - (
            C_platform_to_sensor @ l_s
        )[None, :]
        delta_pos_norm = np.linalg.norm(delta_pos_sensor, axis=1)[:, None, :]
        u_nom: NDArray[float64] = delta_pos_sensor / delta_pos_norm

        # Measured least squares residual (Sine-Space Y, Z only)
        z = (direction_obs[:, :, None] - u_nom[:, 1:3]).reshape((N * 2, 1))

        # N x 3 x 3 array of unit vector outer products
        uuT = u_nom @ u_nom.transpose((0, 2, 1))
        I3x3 = np.eye(3)
        temp = ((I3x3 - uuT) / delta_pos_norm)[:, 1:3]
        H[:, :, :3] = temp @ -C_nav_to_sensor  # Position error
        H[:, :, 6:9] = temp @ (C_nav_to_sensor @ -skew(delta_pos))  # Tilt error

        # Covariance
        R = np.array([obs.covariance for obs in dir2known.obs])  # Nx2x2
        # Add feature uncertainty if available
        feat_cov = np.array(
            [
                obs.remote_point.position_covariance
                if obs.remote_point.position_covariance.size
                else np.zeros((2, 2))
                for obs in dir2known.obs
            ]
        )
        H_slice = H[:, :, :3]
        R += H_slice @ feat_cov @ H_slice.transpose((0, 2, 1))

        # Measurement Function
        def h(x: NDArray[np.float64]) -> NDArray[np.float64]:
            dpos_ned = x[0:3, 0].reshape(3, 1)
            dtheta_ned = x[6:9, 0].reshape(3, 1)

            out: NDArray[np.float64] = (
                -temp @ C_nav_to_sensor @ dpos_ned[None, :, :]
                - temp @ C_nav_to_sensor @ skew(delta_pos) @ dtheta_ned[None, :, :]
            )

            return out.reshape(-1, 1)

        # stacked R matrices along the block diagonal to keep them independent (e.g. noise for feature A is independent of noise for feature B)
        return StandardMeasurementModel(
            z, h, H.reshape(-1, num_states), scipy.linalg.block_diag(*R)
        )
