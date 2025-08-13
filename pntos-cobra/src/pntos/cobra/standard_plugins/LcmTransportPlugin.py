import threading
from threading import Thread

from lcm import LCM, LCMSubscription
from pntos.api import LoggingLevel, Mediator, Message, TransportPlugin
from pntos.cobra.config import AspnVersion, LcmTransportConfig, config_from_registry
from pntos.cobra.utils import (
    decode_aspn_lcm_msg,
    marshal_from_lcm,
    marshal_to_aspn2_lcm,
    marshal_to_aspn23_lcm,
)
from pntos.cobra.utils.lcm import Aspn2LcmMeasurement, Aspn23LcmMeasurement

LCM_URL = 'tcpq://localhost:7700'


def process_lcm_message(
    mediator: Mediator, channel: str, data: bytes, channels: set[str]
) -> None:
    """
    Marshal LCM message to ASPN-Python and send to the mediator for processing.

    Args:
        mediator (Mediator): Mediator instance used for logging and processing message.
        channel (str): The channel name the data originates from.
        data (bytes): A message represented in binary.
        channels (set[str]): Set of channels found so far.
    """
    # Do not process messages sent from pntos.
    if 'pntos' in channel:
        mediator.log_message(
            LoggingLevel.DEBUG,
            'pntOS channel message, not processing in ASPN handler.',
        )
        return

    lcm_aspn_msg = decode_aspn_lcm_msg(data)
    if lcm_aspn_msg is None:
        mediator.log_message(
            LoggingLevel.WARN,
            f'Cannot decode message on channel {channel}. Ignoring message.',
        )
        return
    aspn_msg = marshal_from_lcm(lcm_aspn_msg)
    if aspn_msg is None:
        mediator.log_message(
            LoggingLevel.WARN,
            f'Cannot marshal message on channel {channel} of type {type(aspn_msg)}. Ignoring message.',
        )
        return
    if channel not in channels:
        mediator.log_message(
            LoggingLevel.INFO,
            f'Found new channel {channel}\t with a timestamp of {aspn_msg.time_of_validity.elapsed_nsec / 1e9}s',
        )
        channels.add(channel)
    message = Message(aspn_msg, channel)
    mediator.process_pntos_message(message)


def create_lcm_message(
    message: Message,
    output_version: AspnVersion,
):
    lcm_msg: Aspn2LcmMeasurement | Aspn23LcmMeasurement | None = None
    if output_version == AspnVersion.V2:
        lcm_msg = marshal_to_aspn2_lcm(message.wrapped_message)
    else:
        lcm_msg = marshal_to_aspn23_lcm(message.wrapped_message)

    return lcm_msg


class LcmTransportPlugin(TransportPlugin):
    """A transport plugin which listens for LCM messages.

    Capable of marshalling both ASPN2-LCM and ASPN23-LCM to ASPN23-Python."""

    identifier: str
    lcm: LCM
    mediator: Mediator
    subscription: LCMSubscription
    handler: Thread | None
    _shutdown_threads: threading.Event
    _channels: set[str]

    def __init__(self, identifier: str):
        """
        ASPN-LCM Transport Plugin

        Args:
            identifier (str): The plugin identifier passed to the
                :meth:`pntos.api.CommonPlugin.identifier` field.
        """
        self.identifier = identifier
        self._shutdown_threads = threading.Event()
        self.handler = None
        self._channels = set()

    def init_plugin(
        self,
        plugin_resources_location: str | None = None,
        mediator: Mediator | None = None,
    ) -> None:
        """
        PntOS plugin initialization function

        This is called by the pntOS system before calling any other function.
        """
        if mediator is not None:
            self.mediator = mediator

        config_group = 'config/lcm_transport'
        config = config_from_registry(LcmTransportConfig, self.mediator, config_group)
        if config is None:
            self.mediator.log_message(
                LoggingLevel.ERROR,
                'Unable to retrieve config from registry.',
            )
            return

        self._output_version = config.output_version

    def shutdown_plugin(self) -> None:
        """
        PntOS plugin shutdown function

        This is called by the pntOS system when it is done with the plugin.
        """
        self.stop_listening()
        self.mediator.log_message(
            LoggingLevel.INFO, f'Shutdown plugin for {self.identifier}.'
        )

    def _general_handler(self, channel: str, data: bytes) -> None:
        process_lcm_message(self.mediator, channel, data, self._channels)

    def _handler_thread(self) -> None:
        """Call LCM.handle in a loop."""
        while not self._shutdown_threads.is_set():
            # Handle any messages that have come - restart every hundredth of a second
            self.lcm.handle_timeout(10)

    def start_listening(self) -> None:
        self.lcm = LCM(LCM_URL)
        self.subscription: LCMSubscription = self.lcm.subscribe(
            '^((?!pntos).)*$', self._general_handler
        )
        self.mediator.log_message(LoggingLevel.DEBUG, 'LCM tcpq connected.')
        self.mediator.log_message(
            LoggingLevel.DEBUG, 'Subscribed to all available channels.'
        )

        self.handler = Thread(target=self._handler_thread, args=[])
        self.handler.start()
        self.mediator.log_message(LoggingLevel.INFO, 'LCM message handler is running.')

    def stop_listening(self) -> None:
        self.lcm.unsubscribe(self.subscription)

        # This closes the handler thread
        self._shutdown_threads.set()

        self.mediator.log_message(LoggingLevel.INFO, 'LCM transport stopped.')

    def broadcast_message(
        self, message: Message, channel_name: str | None = None
    ) -> None:
        """Send a message over LCM to a specific channel"""
        if channel_name is None:
            self.mediator.log_message(
                LoggingLevel.WARN,
                'No channel name specified. This implementation requires a channel name.',
            )
            return

        lcm_msg = create_lcm_message(message, self._output_version)
        if lcm_msg is None:
            self.mediator.log_message(
                LoggingLevel.WARN,
                f'Cannot marshal message on channel {channel_name} of type {type(message.wrapped_message)}. Ignoring message.',
            )
            return

        self.lcm.publish(channel_name, lcm_msg.data.encode())
