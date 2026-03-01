import threading
from threading import Thread
from time import time

from lcm import LCM, Event, EventLog
from pntos.api import LoggingLevel, Mediator, Message, TransportPlugin
from pntos.cobra.config import LcmLogTransportConfig, config_from_registry
from pntos.cobra.utils import (
    marshal_to_aspn23_lcm,
    process_lcm_message,
)
from tqdm import tqdm


class TutorialLcmTransportPlugin(TransportPlugin):
    """A tutorial transport plugin which process LCM messages from a log.

    Capable of marshalling ASPN23-LCM to ASPN23-Python."""

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
        self._channels = set()

    def init_plugin(
        self,
        plugin_resources_location: str | None = None,
        mediator: Mediator | None = None,
    ) -> None:
        if mediator is not None:
            self.mediator = mediator

        config = config_from_registry(
            LcmLogTransportConfig, self.mediator, LcmLogTransportConfig.group
        )

        self._input_log = EventLog(config.input_file)
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

    def start_listening(self) -> None:
        """Process messages from LCM log"""
        log_size = self._input_log.size()
        progressbar = tqdm(total=log_size, unit='B', unit_scale=True)
        fpos = self._input_log.tell()

        # Read and process all messages in log
        msg: Event
        for msg in self._input_log:
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

        progressbar.close()
        self._input_log.close()
        self._output_log.close()

        self.mediator.log_message(
            LoggingLevel.INFO,
            'Done processing LCM log. Press Ctrl + C to shut down pntOS.',
        )

    def stop_listening(self) -> None:
        # Nothing to do upon shutdown, transport already processed all messages
        pass

    def broadcast_message(
        self, message: Message, channel_name: str | None = None
    ) -> None:
        """Record LCM message to output file"""
        lcm_msg = marshal_to_aspn23_lcm(message.wrapped_message)

        time_microsec = int(time() * 1e6)
        self._output_log.write_event(time_microsec, channel_name, lcm_msg.encode())


# mypy: disable-error-code="union-attr,attr-defined,arg-type"
