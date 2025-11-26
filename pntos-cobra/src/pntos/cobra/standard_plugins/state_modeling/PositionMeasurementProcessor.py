import numpy as np
from aspn23 import (
    MeasurementPosition,
    MeasurementPositionReferenceFrame,
)
from navtk.navutils import (
    d_rpy_to_dcm_wrt_p,
    d_rpy_to_dcm_wrt_r,
    d_rpy_to_dcm_wrt_y,
    east_to_delta_lon,
    north_to_delta_lat,
    rpy_to_dcm,
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


class PositionMeasurementProcessor(StandardMeasurementProcessor):
    """
    Generates a model that maps a position measurement to an inertial direct state block.

    See :meth:`generate_model` for a detailed description of the assumptions and capabilities of
    this processor.
    """

    _mediator: Mediator

    def __init__(
        self,
        label: str,
        state_block_labels: list[str],
        mediator: Mediator,
        l_ps_p: NDArray[float64],
    ) -> None:
        """
        A Geodetic 3D Position Measurement Processor.

        Args:
            label (str): Name of processor.
            state_block_labels (list[str]): The list of state blocks this measurement processor can update.
            mediator (Mediator): a Mediator instance.
        """
        if len(state_block_labels) != 2:  # noqa: PLR2004
            mediator.log_message(
                LoggingLevel.ERROR,
                f'PositionMeasurementProcessor expects two state block labels but received {len(state_block_labels)}.',
            )
        self.label = label
        self.state_block_labels = state_block_labels
        self._mediator = mediator
        self._l_ps_p = l_ps_p

    def receive_aux_data(self, aux: list[Message | None]) -> None:
        self._mediator.log_message(
            LoggingLevel.DEBUG,
            'PositionMeasurementProcessor does not require aux data.',
        )

    def generate_model(
        self, message: Message, x_and_p: EstimateWithCovariance
    ) -> StandardMeasurementModel | None:
        """
        Generates the model mapping state estimates to the provided measurement.

        Args:
            message (Message): Measurement to process. `message.wrapped_message` must be a
                MeasurementPosition using the GEODETIC reference frame.
            x_and_p: Current joint state estimate and covariance for both the PinsonErrorToStandard
                block and sensor measurement error blocks this processor is updating. LLA position in
                rad, rad, meters respectively are expected at indices [0:3] and RPY tilt in radians are
                expected at indices [6:9]. Sensor measurement error states in the NED frame are expected to
                be the last 3 states.
        Returns:
            StandardMeasurementModel if all restrictions on `message` and `x_and_p` are met and
            proper aux data is available, None otherwise.
        """
        if not isinstance(message.wrapped_message, MeasurementPosition):
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'PositionMeasurementProcessor expected message of type MeasurementPosition, but got message of type {type(message.wrapped_message)}. Cannot process message.',
            )
            return None

        pos = message.wrapped_message
        time = pos.time_of_validity

        if pos.reference_frame is not MeasurementPositionReferenceFrame.GEODETIC:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'PositionMeasurementProcessor expected MeasurementPosition with a reference frame of f{MeasurementPositionReferenceFrame.GEODETIC}, but got measurement at time {time.elapsed_nsec / 1e9:.9f}s with a reference frame of {pos.reference_frame}. Cannot process message.',
            )
            return None

        z = np.array([[pos.term1], [pos.term2], [pos.term3]], dtype=float64)

        if np.any(np.isnan(z)):
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'PositionMeasurementProcessor received a MeasurementPosition message at time {time.elapsed_nsec / 1e9:.9f}s with an invalid position. Cannot process message.',
            )
            return None

        def h(x: NDArray[float64]) -> NDArray[float64]:
            arm_ned = rpy_to_dcm(x[6:9, 0]) @ self._l_ps_p
            arm_llh = np.array(
                [
                    [north_to_delta_lat(arm_ned[0], z[0, 0], z[2, 0])],
                    [east_to_delta_lon(arm_ned[1], z[0, 0], z[2, 0])],
                    [-arm_ned[2]],
                ]
            )
            est_platform_pos = x[0:3]
            sensor_fogm_err = x[-3:]
            predicted_pos_meas: NDArray[float64] = (
                est_platform_pos + arm_llh - sensor_fogm_err
            )
            return predicted_pos_meas

        north_fac = north_to_delta_lat(1, z[0, 0], z[2, 0])
        east_fac = east_to_delta_lon(1, z[0, 0], z[2, 0])
        conversion = np.diag([north_fac, east_fac, -1.0])
        R = conversion @ pos.covariance @ conversion

        H = np.eye(3, x_and_p.estimate.shape[0])
        rpy = x_and_p.estimate[6:9, 0]
        H[:, 6] = conversion @ d_rpy_to_dcm_wrt_r(rpy) @ self._l_ps_p
        H[:, 7] = conversion @ d_rpy_to_dcm_wrt_p(rpy) @ self._l_ps_p
        H[:, 8] = conversion @ d_rpy_to_dcm_wrt_y(rpy) @ self._l_ps_p
        H[:, -3:] = -np.eye(3)

        return StandardMeasurementModel(z, h, H, R)
