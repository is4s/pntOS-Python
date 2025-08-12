import numpy as np
from aspn23 import (
    MeasurementAltitude,
    MeasurementAltitudeReference,
    MeasurementPosition,
    MeasurementPositionVelocityAttitude,
    MeasurementPositionVelocityAttitudeReferenceFrame,
)
from navtk.navutils import msl_to_hae
from numpy import float64
from numpy.typing import NDArray
from pntos.api import (
    EstimateWithCovariance,
    LoggingLevel,
    Mediator,
    Message,
    StandardMeasurementModel,
    StandardMeasurementProcessor,
)


class AltitudeMeasurementProcessor(StandardMeasurementProcessor):
    """
    Generates a model that maps an altitude measurement to a Pinson15 inertial error
    state block and a 1-state altitude FOGM bias block.

    This measurement processor handles all of the following ASPN message types:
     - MeasurementAltitude
     - MeasurementPosition
     - MeasurementPositionVelocityAttitude
    """

    _mediator: Mediator
    _inertial_solution_time_nsec: int | None
    _inertial_pos: NDArray[float64]

    def __init__(
        self,
        label: str,
        state_block_labels: list[str],
        mediator: Mediator,
    ):
        """
        An Altitude Measurement Processor.

        Args:
            label (str): Name of processor.
            state_block_labels (list[str]): A 2-element list of labels of state blocks this
                processor can update. The first entry should refer to a Pinson-style
                state block of at least size 3, with NED position errors in meters as
                the first three states. The second entry should refer to a 1-state FOGM
                state block estimating time-correlated altitude bias.
            mediator (Mediator): A :class:`pntos.api.Mediator` instance.
        """
        self.label = label
        self.state_block_labels = state_block_labels
        self._mediator = mediator
        self._inertial_solution_time_nsec = None
        self._inertial_pos = np.zeros(3)

    def receive_aux_data(self, aux: list[Message]) -> None:
        # Receive and store estimated inertial solution
        if not aux:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'AltitudeMeasurementProcessor expected aux data of type MeasurementPositionVelocityAttitude, but received empty list.',
            )
            return

        if len(aux) > 1:
            self._mediator.log_message(
                LoggingLevel.WARN,
                f'AltitudeMeasurementProcessor expected a single MeasurementPositionVelocityAttitude aux message, but received {len(aux)} aux messages. Ignoring all except the first message.',
            )

        if not isinstance(aux[0].wrapped_message, MeasurementPositionVelocityAttitude):
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'AltitudeMeasurementProcessor expected aux data of type MeasurementPositionVelocityAttitude, but got message of type {type(aux[0].wrapped_message)}.',
            )
            return

        pva = aux[0].wrapped_message

        if pva.p1 is None or pva.p2 is None or pva.p3 is None:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'AltitudeMeasurementProcessor received PVA aux data with no position at time {pva.time_of_validity.elapsed_nsec / 1e9:.9f}s.',
            )
            return

        if (
            pva.reference_frame
            is not MeasurementPositionVelocityAttitudeReferenceFrame.GEODETIC
        ):
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'AltitudeMeasurementProcessor received PVA aux data with reference frame of {pva.reference_frame}. Expected {MeasurementPositionVelocityAttitudeReferenceFrame.GEODETIC}.',
            )
            return

        self._inertial_solution_time_nsec = pva.time_of_validity.elapsed_nsec
        self._inertial_pos[0] = pva.p1
        self._inertial_pos[1] = pva.p2
        self._inertial_pos[2] = pva.p3

    def generate_model(
        self, message: Message, x_and_p: EstimateWithCovariance
    ) -> StandardMeasurementModel | None:
        meas = message.wrapped_message
        alt = None
        variance = None
        time = None

        if self._inertial_solution_time_nsec is None:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'AltitudeMeasurementProcessor cannot process message as it has not received inertial PVA aux data.',
            )
            return None

        # Extract altitude measurement
        if isinstance(meas, MeasurementAltitude):
            time = meas.time_of_validity
            alt = meas.altitude
            variance = meas.variance
            # Convert altitude from MSL to HAE if necessary
            if meas.reference is MeasurementAltitudeReference.MSL:
                alt = msl_to_hae(alt, self._inertial_pos[0], self._inertial_pos[1])[1]
        elif isinstance(meas, MeasurementPosition):
            time = meas.time_of_validity
            alt = meas.term3
            variance = meas.covariance[2, 2]
        elif isinstance(meas, MeasurementPositionVelocityAttitude):
            time = meas.time_of_validity
            alt = meas.p3
            variance = meas.covariance[2, 2]
        else:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'AltitudeMeasurementProcessor expected message of type MeasurementAltitude, MeasurementPosition, or MeasurementPositionVelocityAttitude, but got message of type {type(meas)}. Cannot process message.',
            )
            return None

        if alt is None:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'AltitudeMeasurementProcessor got message without a valid altitude at time {time.elapsed_nsec / 1e9:.9f}s. Cannot process message.',
            )
            return None

        if abs(self._inertial_solution_time_nsec - time.elapsed_nsec) > 1000:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'AltitudeMeasurementProcessor cannot process message at time {time.elapsed_nsec / 1e9:.9f}s as inertial PVA aux data is at a different time (t={self._inertial_solution_time_nsec / 1e9:.9f}s).',
            )
            return None

        inertial_alt = self._inertial_pos[2]

        num_states = x_and_p.estimate.size
        # z = measured inertial altitude error
        z = np.array([[alt - inertial_alt]])
        H = np.zeros((1, num_states))
        H[0, 2] = 1
        H[0, 15] = 1

        def h(x: NDArray[float64]) -> NDArray[float64]:
            return H @ x

        R = np.array([[variance]])

        return StandardMeasurementModel(z, h, H, R)
