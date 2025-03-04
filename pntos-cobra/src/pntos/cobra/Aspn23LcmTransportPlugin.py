from threading import Thread
from typing import Callable

from lcm import LCM, LCMSubscription

from pntos.api import LoggingLevel, Mediator, Message, TransportPlugin
from pntos.cobra.utils import decode_aspn_lcm_msg, marshal_from_lcm, marshal_to_lcm


class Aspn23LcmTransportPlugin(TransportPlugin):
    """An example LCM Transport Plugin for ASPN23 implemented in Python"""

    identifier: str
    lcm: LCM
    listener: Thread
    mediator: Mediator
    subscription: LCMSubscription

    def __init__(self, identifier: str):
        self.identifier = identifier

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
        """
        Generic listener for lcm messages to marshal to the mediator for processing.
        """
        # Do not process messages sent from pntos.
        if 'pntos' in channel:
            self.mediator.log_message(
                LoggingLevel.INFO,
                'pntOS channel message, not processing in ASPN handler.',
            )
            return

        lcm_aspn_msg = decode_aspn_lcm_msg(data)
        if lcm_aspn_msg is None:
            self.mediator.log_message(
                LoggingLevel.WARN,
                f'Cannot decode message on channel {channel}. Ignoring message.',
            )
            return
        aspn_msg = marshal_from_lcm(lcm_aspn_msg)
        if aspn_msg is None:
            self.mediator.log_message(
                LoggingLevel.WARN,
                f'Cannot marshal message on channel {channel} of type {type(aspn_msg)}. Ignoring message.',
            )
            return
        message = Message(aspn_msg, channel)
        self.mediator.process_pntos_message(message)

    def listener_thread(self) -> None:
        """Subscribe to specified channels (excluding any channels with "pntos")"""
        self.subscription = self.lcm.subscribe('^((?!pntos).)*$', self._general_handler)

    def start_listening(self) -> None:
        """Begin listening for lcm messages given input configuration"""
        self.lcm = LCM()
        self.listener = Thread(target=self.listener_thread, args=[])
        self.listener.start()

    def stop_listening(self) -> None:
        """Shut down all processes and threads spun up for LCM message passing"""
        if self.listener.is_alive():
            self.listener.join()

        if self.subscription is not None and self.lcm is not None:
            self.lcm.unsubscribe(self.subscription)

        self.mediator.log_message(LoggingLevel.INFO, 'LCM transport stopped.')

    def broadcast_message(
        self, message: Message, channel_name: str | None = None
    ) -> None:
        """Send a message over LCM to a specific channel"""
        lcm_msg = marshal_to_lcm(message.wrapped_message)

        if lcm_msg is None:
            self.mediator.log_message(
                LoggingLevel.ERROR,
                f'Cannot marshal message on channel {channel_name} of type {type(message.wrapped_message)}. Ignoring message.',
            )
        elif channel_name is None:
            self.mediator.log_message(
                LoggingLevel.WARN,
                'No channel name specified. This implementation requires a channel name.',
            )
        else:
            self.lcm.publish(channel_name, lcm_msg.encode())
