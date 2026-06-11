from copy import deepcopy

import numpy as np
from aspn23 import (
    MeasurementVelocity,
    MeasurementVelocityErrorModel,
    MeasurementVelocityReferenceFrame,
    TypeHeader,
    TypeTimestamp,
)
from pntos.api import (
    Mediator,
    Message,
    Preprocessor,
)
from typing_extensions import override


class ZeroVelocity2dGenerator(Preprocessor):
    """
    A preprocessor that generates 2-D zero-velocity measurements.

    These measurements are based on the assumption that a ground vehicle does not slide
    laterally or lift vertically off the ground.
    """

    _mediator: Mediator
    _channels: tuple[str, ...] | None
    _trigger_dt_nsec: int
    _output_channel: str

    def __init__(
        self,
        mediator: Mediator,
        channels: tuple[str, ...] | None,
        dt: float,
        lat_sigma: float,
        vert_sigma: float,
        output_channel: str,
    ) -> None:
        """Cobra 2d zero-velocity generator Preprocessor."""
        self._mediator = mediator

        self._channels = channels
        self._trigger_dt_nsec = int(dt * 1e9)

        self._output_channel = output_channel

        self._meas = MeasurementVelocity(
            TypeHeader(0, 0, 0, 0),
            TypeTimestamp(0),
            MeasurementVelocityReferenceFrame.SENSOR,
            None,
            0.0,
            0.0,
            np.diag(np.square([lat_sigma, vert_sigma])),
            MeasurementVelocityErrorModel.NONE,
            np.array([]),
            [],
        )
        self._last_meas_time_ns: int | None = None

    @override
    def process_pntos_message(self, message: Message) -> list[Message]:
        channel = message.source_identifier
        if self._channels and channel not in self._channels:
            # Don't use current channel to generate zero-velocity measurement
            return [message]

        cur_time_ns = message.wrapped_message.time_of_validity.elapsed_nsec  # ty: ignore[unresolved-attribute]

        if (
            self._last_meas_time_ns is not None
            and (cur_time_ns - self._last_meas_time_ns) < self._trigger_dt_nsec
        ):
            # Not triggered yet by time elapsed since last velocity output
            return [message]

        # Output zero-velocity message
        self._meas.time_of_validity.elapsed_nsec = cur_time_ns
        velocity_msg = Message(deepcopy(self._meas), self._output_channel)
        self._last_meas_time_ns = cur_time_ns

        return [message, velocity_msg]
