from aspn23 import (
    MeasurementImu,
)
from numpy import float64
from numpy.typing import NDArray
from pntos.api import (
    LoggingLevel,
    Mediator,
    Message,
    Preprocessor,
)


class ImuRotationPreprocessor(Preprocessor):
    _mediator: Mediator
    _imu_channel: str
    _C_imu_to_platform: NDArray[float64]

    def __init__(
        self,
        mediator: Mediator,
        imu_channel: str,
        C_imu_to_platform: NDArray[float64],
    ) -> None:
        self._mediator = mediator
        self._imu_channel = imu_channel
        self._C_imu_to_platform = C_imu_to_platform

    def process_pntos_message(self, message: Message) -> list[Message]:
        if message.source_identifier == self._imu_channel:
            if isinstance(message.wrapped_message, MeasurementImu):
                imu = message.wrapped_message
                imu.meas_accel = self._C_imu_to_platform @ imu.meas_accel
                imu.meas_gyro = self._C_imu_to_platform @ imu.meas_gyro
            else:
                self._mediator.log_message(
                    LoggingLevel.WARN,
                    f'ImuRotationPreprocessor expected IMU message, but got {type(message.wrapped_message)}. Cannot rotate.',
                )

        return [message]
