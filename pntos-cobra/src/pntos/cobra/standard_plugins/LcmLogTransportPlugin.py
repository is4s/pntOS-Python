import threading
from threading import Thread
from time import time

from lcm import LCM, Event, EventLog
from pntos.api import LoggingLevel, Mediator, Message, TransportPlugin
from pntos.cobra.config import LcmLogTransportConfig, config_from_registry
from pntos.cobra.utils import (
    create_lcm_message,
    process_lcm_message,
)
from tqdm import tqdm


class LcmLogTransportPlugin(TransportPlugin):
    """A transport plugin which process LCM messages from a log.

    Capable of marshalling both ASPN2-LCM and ASPN23-LCM to ASPN23-Python."""

    identifier: str
    mediator: Mediator
    _log_reader_thread: Thread | None
    _shutdown_threads: threading.Event
    _lcm: LCM
    _channels: set[str]

    def __init__(self, identifier: str) -> None:
        """
        LCM Log Transport Plugin

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
        if mediator is not None:
            self.mediator = mediator

        config_group = 'config/lcm_log_transport'
        config = config_from_registry(
            LcmLogTransportConfig, self.mediator, config_group
        )
        if config is None:
            self.mediator.log_message(
                LoggingLevel.ERROR,
                'Unable to retrieve config from registry.',
            )
            return

        self._output_version = config.output_version
        self._input_log = EventLog(config.input_file)
        if config.output_file == config.input_file:
            self.mediator.log_message(
                LoggingLevel.ERROR,
                f'Output file of {config.output_file} cannot be the same as input file.',
            )
            return
        self._output_log = EventLog(config.output_file, 'w', overwrite=True)

    def shutdown_plugin(self) -> None:
        """
        PntOS plugin shutdown function

        This is called by the pntOS system when it is done with the plugin.
        """
        self.stop_listening()
        self.mediator.log_message(
            LoggingLevel.INFO, f'Shutdown plugin for {self.identifier}.'
        )

    def read_log(self) -> None:
        """Process messages from LCM log"""
        log_size = self._input_log.size()
        progressbar = tqdm(total=log_size)
        fpos = self._input_log.tell()

        # Read until end of log or until pntOS is shut down
        msg: Event | None = self._input_log.read_next_event()
        while msg is not None and not self._shutdown_threads.is_set():
            # update progressbar
            new_fpos = self._input_log.tell()
            progressbar.update(new_fpos - fpos)
            fpos = new_fpos

            # process message
            process_lcm_message(self.mediator, msg.channel, msg.data, self._channels)

            # write input messages to output log so that they can be analyzed along with
            # any messages that are output via broadcast_message
            time_microsec = int(time() * 1e6)
            self._output_log.write_event(time_microsec, msg.channel, msg.data)

            msg = self._input_log.read_next_event()

        progressbar.close()
        self._input_log.close()
        self._output_log.close()

        if msg is None:
            # Reached end of log and pntOS has not been shut down yet
            self.mediator.log_message(
                LoggingLevel.INFO,
                'Done processing LCM log. Press Ctrl + C to shut down pntOS.',
            )

    def start_listening(self) -> None:
        self._log_reader_thread = Thread(target=self.read_log, args=[])
        self._log_reader_thread.start()
        self.mediator.log_message(LoggingLevel.INFO, 'LCM log reader is running.')

    def stop_listening(self) -> None:
        self._shutdown_threads.set()

    def broadcast_message(
        self, message: Message, channel_name: str | None = None
    ) -> None:
        """Record LCM message to output file"""
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

        time_microsec = int(time() * 1e6)
        self._output_log.write_event(time_microsec, channel_name, lcm_msg.encode())
