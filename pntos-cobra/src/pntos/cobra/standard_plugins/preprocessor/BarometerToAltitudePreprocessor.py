from analysis.lcm.conversions import pressure_to_alt
from aspn23 import (
    MeasurementAltitude,
    MeasurementAltitudeErrorModel,
    MeasurementAltitudeReference,
    MeasurementBarometer,
)
from pntos.api import (
    LoggingLevel,
    Mediator,
    Message,
    Preprocessor,
)


class BarometerToAltitudePreprocessor(Preprocessor):
    """
    A preprocessor that converts barometer measurements to altitude measurements.
    """

    _deg_k: float
    _channel: str
    _mediator: Mediator
    _alt_sigma: float | None

    def __init__(
        self, channel: str, mediator: Mediator, alt_sigma: float | None
    ) -> None:
        """
        Cobra Barometer to Altitude Preprocessor
        """
        self._deg_k = 288.15
        self._channel = channel
        self._mediator = mediator
        self._alt_sigma = alt_sigma

    def process_pntos_message(self, message: Message) -> list[Message]:
        if message.source_identifier == self._channel:
            msg = message.wrapped_message
            if isinstance(msg, MeasurementBarometer):
                altitude = pressure_to_alt(msg.pressure, self._deg_k)
                altitude_variance = (
                    self._alt_sigma**2
                    if self._alt_sigma is not None
                    else msg.variance * (altitude / msg.pressure) ** 2
                )
                return [
                    Message(
                        MeasurementAltitude(
                            msg.header,
                            msg.time_of_validity,
                            MeasurementAltitudeReference.MSL,
                            altitude,
                            altitude_variance,
                            MeasurementAltitudeErrorModel.NONE,
                            msg.error_model_params,
                            msg.integrity,
                        ),
                        message.source_identifier.replace('baro_pressure', 'altitude'),
                    )
                ]
            self._mediator.log_message(
                LoggingLevel.WARN,
                f'BarometerToAltitudePreprocessor expected barometer message, but got {type(message.wrapped_message)}. Cannot convert.',
            )
        return [message]
