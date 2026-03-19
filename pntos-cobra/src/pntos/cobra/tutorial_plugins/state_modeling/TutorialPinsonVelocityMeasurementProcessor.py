import numpy as np
from aspn23 import MeasurementPositionVelocityAttitude, MeasurementVelocity
from numpy import float64
from numpy.typing import NDArray
from pntos.api import (
    GenXandP,
    Mediator,
    Message,
    StandardMeasurementModel,
    StandardMeasurementProcessor,
)


class TutorialPinsonVelocityMeasurementProcessor(StandardMeasurementProcessor):
    """
    Generates a model that maps a velocity measurement to an inertial error state block.
    """

    _mediator: Mediator
    _inertial_pva: MeasurementPositionVelocityAttitude | None

    def __init__(
        self, label: str, state_block_labels: list[str], mediator: Mediator
    ) -> None:
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

    def receive_aux_data(self, aux: list[Message | None]) -> None:
        if aux[0] is None or not isinstance(
            aux[0].wrapped_message, MeasurementPositionVelocityAttitude
        ):
            return
        pva = aux[0].wrapped_message
        self._inertial_pva = pva

    def generate_model(
        self, message: Message, gen_x_and_p_func: GenXandP
    ) -> StandardMeasurementModel | None:
        if (
            not isinstance(message.wrapped_message, MeasurementVelocity)
            or self._inertial_pva is None
        ):
            return None

        vel = message.wrapped_message

        meas_vel = np.array([vel.x, vel.y, vel.z])
        inertial_vel = np.array(
            [self._inertial_pva.v1, self._inertial_pva.v2, self._inertial_pva.v3]
        )

        # z = measured NED inertial velocity error
        z = np.reshape(meas_vel - inertial_vel, (3, 1))
        H = np.zeros((3, 15))
        H[:, 3:6] = np.eye(3)

        def h(x: NDArray[float64]) -> NDArray[float64]:
            return H @ x

        R = vel.covariance

        return StandardMeasurementModel(z, h, H, R)
