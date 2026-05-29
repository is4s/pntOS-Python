import threading
import time
from queue import Queue
from threading import Thread

from lcm import LCM, LCMSubscription
from pntos.api import LoggingLevel, Mediator, Message, TransportPlugin
from pntos.cobra.config import LcmTransportConfig, config_from_registry
from pntos.cobra.utils import (
    UiSourceInterface,
    marshal_to_aspn23_lcm,
    process_lcm_message,
)


class LcmTransportPlugin(TransportPlugin):
    """A transport plugin which listens for LCM messages.

    Capable of marshalling ASPN23-LCM to ASPN23-Python."""

    identifier: str
    lcm: LCM | None
    mediator: Mediator
    subscription: LCMSubscription
    handler: Thread | None
    _sender: Thread | None
    _url: str
    _subscription_regex: str
    _shutdown_threads: threading.Event
    _channels: set[str]
    _output_queue: Queue[Message | None]
    _ui: UiSourceInterface

    def __init__(self, identifier: str) -> None:
        """
        ASPN-LCM Transport Plugin

        Args:
            identifier (str): The plugin identifier passed to the
                :meth:`pntos.api.CommonPlugin.identifier` field.
        """
        self.identifier = identifier
        self._shutdown_threads = threading.Event()
        self.lcm = None
        self.handler = None
        self._sender = None
        self._channels = set()
        self._output_queue = Queue()

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

        self._ui = UiSourceInterface(self.mediator.registry)

        config = config_from_registry(
            LcmTransportConfig, self.mediator, LcmTransportConfig.group
        )
        if config is None:
            self.mediator.log_message(
                LoggingLevel.ERROR,
                'Unable to retrieve config from registry.',
            )
            return

        self._url = config.url
        self._subscription_regex = config.subscribe_to

        self._sender = threading.Thread(target=self._send_thread)
        self._sender.start()

    def shutdown_plugin(self) -> None:
        """
        PntOS plugin shutdown function

        This is called by the pntOS system when it is done with the plugin.
        """
        self.stop_listening()
        self.mediator.log_message(
            LoggingLevel.INFO, f'Shutdown plugin for {self.identifier}.'
        )

    def _send_thread(self) -> None:
        while not self._shutdown_threads.is_set():
            message = self._output_queue.get()

            if message is None:
                break

            if self.lcm is None:
                self.mediator.log_message(
                    LoggingLevel.WARN,
                    'Lcm is not connected; dropping message set for broadcast.',
                )
                continue

            lcm_msg = marshal_to_aspn23_lcm(message.wrapped_message)
            if lcm_msg is None:
                self.mediator.log_message(
                    LoggingLevel.WARN,
                    f'Cannot marshal message on channel {message.source_identifier} '
                    + f'of type {type(message.wrapped_message)}. Ignoring message.',
                )
                continue

            try:
                self.lcm.publish(message.source_identifier, lcm_msg.encode())
            except OSError as e:
                self.mediator.log_message(
                    LoggingLevel.WARN,
                    f'Failed to publish message over lcm: {e}',
                )

    def _general_handler(self, channel: str, data: bytes) -> None:
        if self._ui.new_message(channel):
            process_lcm_message(self.mediator, channel, data, self._channels)

    def _handler_thread(self) -> None:
        """Call LCM.handle in a loop."""
        while not self._shutdown_threads.is_set():
            # Handle any messages that have come - restart every hundredth of a second
            if self.lcm is not None:
                self.lcm.handle_timeout(10)
            else:
                time.sleep(0.01)

    def start_listening(self) -> None:
        try:
            self.lcm = LCM(self._url)
        except RuntimeError as e:
            self.mediator.log_message(LoggingLevel.ERROR, f'Failed to start lcm: {e}')
            return
        self.subscription: LCMSubscription = self.lcm.subscribe(
            self._subscription_regex, self._general_handler
        )
        self.mediator.log_message(
            LoggingLevel.DEBUG,
            f'Subscribed to all channels matching the pattern: {self._subscription_regex}.',
        )

        self.handler = Thread(target=self._handler_thread, args=[])
        self.handler.start()
        self.mediator.log_message(LoggingLevel.INFO, 'LCM message handler is running.')

    def stop_listening(self) -> None:
        # This closes the handler thread
        self._shutdown_threads.set()
        self._output_queue.put(None)
        # Wait for other threads to terminate
        if self.handler:
            self.handler.join()
        if self._sender:
            self._sender.join()
        if self.lcm is not None:
            self.lcm.unsubscribe(self.subscription)

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
        # if we were to publish here, multiple threads could call into
        # lcm publish simultaneously, pushing interleaved and garbage
        # data to the socket
        #
        # to prevent this, an output queue is used, with a single
        # thread performing the publish operation
        message.source_identifier = channel_name
        self._output_queue.put(message)
