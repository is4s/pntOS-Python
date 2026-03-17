from threading import Thread
from time import sleep

import numpy as np
from aspn23 import (
    MeasurementPosition,
    MeasurementPositionErrorModel,
    MeasurementPositionReferenceFrame,
    TypeHeader,
    TypeTimestamp,
)
from pntos.api import Mediator, TransportPlugin
from pntos.api.plugins.common import LoggingLevel, Message


class DummyTransportPlugin(TransportPlugin):
    """
    A TransportPlugin with minimal capability. Not for use in production code.

    This transport simulates inbound data to Cobra by producing fake messages in a loop to pass out
    through :func:`~pntos.api.Mediator.process_pntos_message`. As there is no mechanism for actual
    publishing, outbound data sent through :func:`~pntos.api.TransportPlugin.broadcast_message` die
    here, eulogized by a logged message containing the channel it would have been published to.
    """

    identifier: str
    mediator: Mediator | None
    """ Mediator used to pass data around and log messages."""
    _thread: Thread
    """ Main listener thread that produces simulated data. """
    _listening: bool
    """ Flag that indicates if :attr:`_thread` should be active."""

    def __init__(self, identifier: str) -> None:
        self.identifier = identifier
        self.mediator = None
        self._thread = Thread(target=listen_for_messages, args=(self,))
        self._listening = False

    def init_plugin(
        self,
        plugin_resources_location: str | None = None,
        mediator: Mediator | None = None,
    ) -> None:
        self.mediator = mediator
        self._log(message='Initialized DummyTransport')

    def shutdown_plugin(self) -> None:
        self._log(message='Shutting down DummyTransport')
        self.stop_listening()
        if self._thread:
            self._thread.join()

    def start_listening(self) -> None:
        """
        Starts the thread that generates data and pushes into the :attr:`mediator`, simulating data
        arriving over the network or similar source.
        """
        self._listening = True
        self._log(message='DummyTransport listening')
        if not self._thread.is_alive():
            self._thread.start()

    def stop_listening(self) -> None:
        """
        Stops the data generation if it is active.
        """
        self._log(message='DummyTransport stopping')
        self._listening = False

    def broadcast_message(
        self, message: Message, channel_name: str | None = None
    ) -> None:
        self._log(message=f'DummyTransport broadcasting on {channel_name}')

    def _log(self, message: str, level: LoggingLevel = LoggingLevel.INFO) -> None:
        """
        Wrapper around :func:`~pntos.api.Mediator.log_message` that hard asserts that the mediator
        exists.

        Args:
            message: Message to log.
            level: Level to log message at.
        """
        assert self.mediator is not None
        self.mediator.log_message(message=message, level=level)


def listen_for_messages(my_plugin: DummyTransportPlugin) -> None:
    """
    Simulates receiving external messages and hands the simulated data off to be processed.
    """
    chan = 'channel_foo'
    header = TypeHeader(0, 0, 0, 0)
    time = TypeTimestamp(0)
    frame = MeasurementPositionReferenceFrame.GEODETIC
    error_model = MeasurementPositionErrorModel.NONE
    aspn_msg = MeasurementPosition(
        header,
        time,
        frame,
        None,
        None,
        None,
        np.empty(0),
        error_model,
        np.empty(0),
        [],
    )

    while my_plugin._listening:
        # Send a new ASPN message we've received to the system
        if my_plugin.mediator:
            my_plugin._log(f'DummyTransport publishing to {chan}')
            my_plugin.mediator.process_pntos_message(
                Message(aspn_msg, source_identifier=chan)
            )
        sleep(0.1)
