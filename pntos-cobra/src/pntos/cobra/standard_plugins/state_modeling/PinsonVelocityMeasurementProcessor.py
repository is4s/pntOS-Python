import numpy as np
from aspn23 import (
    MeasurementPositionVelocityAttitude,
    MeasurementVelocity,
    MeasurementVelocityReferenceFrame,
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


class PinsonVelocityMeasurementProcessor(StandardMeasurementProcessor):
    """
    Generates a model that maps a velocity measurement to an inertial error state block.
    """

    _mediator: Mediator
    _inertial_pva: MeasurementPositionVelocityAttitude | None

    def __init__(
        self,
        label: str,
        state_block_labels: list[str],
        mediator: Mediator,
    ):
        """
        A Pinson Velocity Measurement Processor

        Args:
            label (str): Name of processor.
            state_block_labels (list[str]): A 1-element list of labels of state blocks this
                processor can update. The single entry should refer to a Pinson-style
                state block of at least size 9, with NED position errors in meters as
                the first three states and NED tilt errors, in radians, as states 6:9.
            mediator (Mediator): A :class:`pntos.api.Mediator` instance.
        """
        self.label = label
        self.state_block_labels = state_block_labels
        self._mediator = mediator
        self._inertial_pva = None

    def receive_aux_data(self, aux: list[Message]) -> None:
        if not aux:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'PinsonVelocityMeasurementProcessor expected aux data of type MeasurementPositionVelocityAttitude, but received empty list.',
            )
            return

        if len(aux) > 1:
            self._mediator.log_message(
                LoggingLevel.DEBUG,
                f'PinsonVelocityMeasurementProcessor expected a single MeasurementPositionVelocityAttitude aux message, but received {len(aux)} aux messages. Ignoring all except the first message.',
            )

        if not isinstance(aux[0].wrapped_message, MeasurementPositionVelocityAttitude):
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'PinsonVelocityMeasurementProcessor expected aux data of type MeasurementPositionVelocityAttitude, but got message of type {type(aux[0].wrapped_message)}.',
            )
            return

        pva = aux[0].wrapped_message

        if pva.quaternion is None:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'PinsonVelocityMeasurementProcessor received PVA aux data with no quaternion at time {pva.time_of_validity.elapsed_nsec / 1e9:.9f}s.',
            )
            return

        self._inertial_pva = pva

    def generate_model(
        self, message: Message, x_and_p: EstimateWithCovariance
    ) -> StandardMeasurementModel | None:
        if not isinstance(message.wrapped_message, MeasurementVelocity):
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'PinsonVelocityMeasurementProcessor expected message of type MeasurementVelocity, but got message of type {type(message.wrapped_message)}. Cannot process message.',
            )
            return None

        vel = message.wrapped_message
        time = vel.time_of_validity
        if self._inertial_pva is None:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'PinsonVelocityMeasurementProcessor cannot process message at time {time.elapsed_nsec / 1e9:.9f}s as it has not received inertial PVA aux data.',
            )
            return None

        pva_aux_time = self._inertial_pva.time_of_validity
        if abs(pva_aux_time.elapsed_nsec - time.elapsed_nsec) > 1000:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'PinsonVelocityMeasurementProcessor cannot process message at time {time.elapsed_nsec / 1e9:.9f}s as inertial PVA aux data is at a different time (t={pva_aux_time.elapsed_nsec / 1e9:.9f}s).',
            )
            return None

        if vel.reference_frame is not MeasurementVelocityReferenceFrame.NED:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'PinsonVelocityMeasurementProcessor expected MeasurementVelocity with a reference frame of {MeasurementVelocityReferenceFrame.NED}, but got measurement at time {time.elapsed_nsec / 1e9:.9f}s with a reference frame of {vel.reference_frame}. Cannot process message.',
            )
            return None

        meas_vel = np.array([vel.x, vel.y, vel.z])
        inertial_vel = np.array(
            [
                self._inertial_pva.v1,
                self._inertial_pva.v2,
                self._inertial_pva.v3,
            ]
        )

        # z = measured NED inertial velocity error
        z = np.reshape(meas_vel - inertial_vel, (3, 1))
        H = np.zeros((3, 15))
        H[:, 3:6] = np.eye(3)

        def h(x: NDArray[float64]) -> NDArray[float64]:
            return H @ x

        R = vel.covariance

        return StandardMeasurementModel(z, h, H, R)
