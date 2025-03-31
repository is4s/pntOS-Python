import threading
from threading import Thread

from aspn23 import TypeTimestamp
from lcm import LCM, LCMSubscription

from pntos.api import LoggingLevel, Mediator, Message, TransportPlugin
from pntos.cobra.utils import decode_aspn_lcm_msg, marshal_from_lcm, marshal_to_lcm

LCM_URL = 'tcpq://localhost:7700'


class Aspn23LcmTransportPlugin(TransportPlugin):
    """An example LCM Transport Plugin for ASPN23 implemented in Python"""

    identifier: str
    lcm: LCM
    mediator: Mediator
    subscription: LCMSubscription
    last_solution_time: TypeTimestamp | None
    last_message_time: TypeTimestamp | None
    handler: Thread | None
    _shutdown_threads: threading.Event

    def __init__(self, identifier: str):
        self.identifier = identifier
        self.last_solution_time = None
        self._shutdown_threads = threading.Event()
        self.last_message_time = None
        self.handler = None

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
        self.last_message_time = aspn_msg.time_of_validity
        message = Message(aspn_msg, channel)
        self.mediator.process_pntos_message(message)

    def handler_thread(self) -> None:
        """Call LCM.handle in a loop, and request a solution approx. every second."""
        while not self._shutdown_threads.is_set():
            # Handle any messages that have come - restart every hundredth of a second
            self.lcm.handle_timeout(10)

            # Need to make sure the orchestration has received some messages before we
            # start requesting solutions.
            if self.last_message_time is None:
                continue

            if self.last_solution_time is None:
                self.last_solution_time = self.last_message_time
                continue

            # Print the current solution every second in message time
            if (
                self.last_message_time.elapsed_nsec
                - self.last_solution_time.elapsed_nsec
                > 1_000_000_000
            ):
                solution = self.mediator.request_solutions([self.last_message_time])
                if len(solution) > 0:
                    self.mediator.log_message(
                        LoggingLevel.INFO, f'Got a solution! {solution}'
                    )
                    self.mediator.broadcast_aspn_message(
                        solution[0],
                        transport=self.identifier,
                        destination_identifier='/solution/cobra/pva',
                    )
                else:
                    self.mediator.log_message(
                        LoggingLevel.WARN,
                        'Could not receive solution from orchestration.',
                    )
                self.last_solution_time = self.last_message_time

    def start_listening(self) -> None:
        """Begin listening for lcm messages given input configuration"""
        self.lcm = LCM(LCM_URL)
        self.subscription: LCMSubscription = self.lcm.subscribe(
            '^((?!cobra).)*$', self._general_handler
        )
        self.mediator.log_message(LoggingLevel.DEBUG, 'LCM tcpq connected.')
        self.mediator.log_message(
            LoggingLevel.DEBUG, 'Subscribed to all available channels.'
        )

        self.handler = Thread(target=self.handler_thread, args=[])
        self.handler.start()
        self.mediator.log_message(LoggingLevel.INFO, 'LCM message handler is running.')

    def stop_listening(self) -> None:
        """Shut down all processes and threads spun up for LCM message passing"""
        self.lcm.unsubscribe(self.subscription)

        # This closes the handler thread
        self._shutdown_threads.set()

        self.mediator.log_message(LoggingLevel.INFO, 'LCM transport stopped.')

    def broadcast_message(
        self, message: Message, channel_name: str | None = None
    ) -> None:
        """Send a message over LCM to a specific channel"""
        lcm_msg = marshal_to_lcm(message.wrapped_message)
        # TODO: remove this hack once firehose#50 is resolved
        lcm_msg.num_meas = 9  # type: ignore[union-attr]

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
