import numpy as np
from aspn23 import (
    MeasurementPosition,
    MeasurementPositionVelocityAttitude as MeasurementPVA,
)
from numpy import float64
from numpy.typing import NDArray
from pntos.api import (
    EstimateWithCovariance,
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


class TutorialPinsonWithNedFogmPositionMeasurementProcessor(
    StandardMeasurementProcessor
):
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
    ) -> None:
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

    def receive_aux_data(self, aux: list[Message]) -> None:
        if not isinstance(aux[0].wrapped_message, MeasurementPVA):
            return
        pva = aux[0].wrapped_message
        self._inertial_pva = pva

    def generate_model(
        self, message: Message, x_and_p: EstimateWithCovariance
    ) -> StandardMeasurementModel | None:
        if (
            not isinstance(message.wrapped_message, MeasurementPosition)
            or self._inertial_pva is None
        ):
            return None

        pos = message.wrapped_message
        llh = np.array([pos.term1, pos.term2, pos.term3])
        inertial_llh = np.array(
            [
                self._inertial_pva.p1,
                self._inertial_pva.p2,
                self._inertial_pva.p3,
            ]
        )

        C_platform_to_nav = quat_to_dcm(self._inertial_pva.quaternion)  # type: ignore[arg-type]

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
            res: NDArray[float64] = (
                x[0:3, 0]
                + (np.eye(3) - skew(x[6:9, 0])) @ C_platform_to_nav @ self._l_ps_p
                - x[-3:, 0]
            ).reshape(3, 1)
            return res

        R = pos.covariance

        return StandardMeasurementModel(z, h, H, R)
