"""
An example LCM Transport Plugin for ASPN 2.X implemented in Python

The Transport LCM Plugin in this file can be substituted for the Viper
Transport LCM Plugin in the default plugins list.  However, it is not currently
a complete substitution.  Only geodetic 3D position, PVA, and IMU data sources
are supported in this example.

To see it in action, run
python sdk/python/example_plugin_transport_lcm_aspn_2/run_transport_lcm_plugin.py
from the pntOS project root folder.
"""


from pntos import (
    class_PntosTransportPlugin,
    PntosLoggingLevel,
    PntosMediator,
    PntosMessage,
)

from example_plugin_transport_lcm_aspn_2.LcmTransport import (
    LcmTransport,
    LcmLogger,
)
from example_plugin_transport_lcm_aspn_2.lcm_aspn2_handler import (
    lcm_transport_send_message,
    general_handler,
    listener_thread,
    send_thread,
)

from threading import Thread


@class_PntosTransportPlugin
class TransportLcmAspnV2Plugin:
    """
    An example LCM Transport Plugin for ASPN 2.X implemented in Python

    The Transport LCM Plugin in this file can be substituted for the Viper
    Transport LCM Plugin in the default plugins list.  However, it is not currently
    a complete substitution.  Only geodetic 3D position, PVA, and IMU data sources
    are supported in this example.

    To see it in action, run
    python sdk/python/example_plugin_transport_lcm_aspn_2/run_transport_lcm_plugin.py
    from the pntOS project root folder.
    """

    def __init__(self):
        self.mediator = None
        self.identifier = "python-transport-lcm2-plugin"

    def init_plugin(self, plugin_location, mediator: PntosMediator):
        """
        pntOS plugin initialization function

        This is called by the pntOS system before calling any other function.

        Implements C API PntosCommonPlugin.init_plugin.  See documentation in
        api/include/pntos/plugins/common.h for more information.
        """
        self.log_info(f"init_plugin for {self}")
        self.mediator = mediator
        self.lcm_transport = LcmTransport(mediator=mediator)

    def shutdown_plugin(self):
        """
        pntOS plugin shutdown function

        This is called by the pntOS system when it is done with the plugin.

        Implements C API PntosCommonPlugin.shutdown_plugin.  See documentation
        in api/include/pntos/plugins/common.h for more information.
        """
        self.log_info(f"shutdown_plugin for {self}")
        self.lcm_transport.destroy()

    def log_info(self, message: str):
        """
        Send informational log message to pntOS

        Use the mediator provided by init_plugin to send a log message to the
        pntOS system.  If unavailable, print directly to the console.
        """

        if self.mediator is not None:
            self.mediator.log_message(
                PntosLoggingLevel.PNTOS_LOG_LEVEL_INFO, message
            )
        else:
            print(f"INFO: {message}")

    def log_error(self, message: str):
        """
        Send error log message to pntOS

        Use the mediator provided by init_plugin to send a log message to the
        pntOS system.  If unavailable, print directly to the console.
        """

        if self.mediator is not None:
            self.mediator.log_message(
                PntosLoggingLevel.PNTOS_LOG_LEVEL_ERROR, message
            )
        else:
            print(f"ERROR: {message}")

    def start_listening(
        self, config_path="config/transport/is4s_transport_lcm"
    ):
        """
        Begin listening for lcm messages given input configuration
        """

        # Get configs fom Pntos Registry
        store = self.lcm_transport.pntos_mediator.registry.batch_start(
            config_path
        )

        # Get URL to listen on
        url = store.get_str("url") if store.has_key("url") else None
        if url is not None:
            self.log_info(f"LCM listening on: {url}")
        else:
            self.log_error(
                "Invalid URL string in lcm transport. Is there a valid config?"
            )
            return

        # Get log file to output to
        file = "lcm_data.log"
        if store.has_key("logfile") and store.get_str("logfile") != "none":
            file = store.get_str("logfile")

        # Get the channel to pass to lcm_subscribe
        channel = ".*"
        if store.has_key("record") and store.get_str("record") != "none":
            channel = store.get_str("record")

        file = (
            store.get_str("logfile")
            if store.has_key("logfile")
            else "lcm_data.log"
        )
        warn_q_len = (
            store.get_int("warn_send_queue_length")
            if store.has_key("warn_send_queue_length")
            else None
        )
        store.batch_end()

        self.lcm_transport.create(url)

        if self.lcm_transport.lcm is None:
            self.log_error("Failed to create lcm transport")
            return

        self.lcm_transport.warn_send_queue_length = warn_q_len
        self.lcm_transport.send_thread = Thread(
            target=send_thread, args=(self.lcm_transport,)
        )
        self.lcm_transport.send_thread.start()

        self.lcm_transport.listener = Thread(
            target=listener_thread, args=(self.lcm_transport,)
        )
        self.lcm_transport.listener.start()
        self.lcm_transport.subscription = self.lcm_transport.lcm.subscribe(
            "^((?!pntos).)*$", general_handler(self.lcm_transport)
        )

        self.lcm_transport.is_running = True

        self.lcm_transport.logger_process = LcmLogger(
            url=url, channel=channel, file=file
        )
        self.lcm_transport.logger_process.start()
        self.log_info("LCM transport started")

    def stop_listening(self):
        """
        Shut down all processes and threads spun up for LCM message passing
        """
        # Transport is marked as no longer running
        if self.lcm_transport.is_running:
            self.lcm_transport.is_running = False

        # Wait for listener thread to join.
        if self.lcm_transport.listener is not None:
            self.lcm_transport.listener.join()

        # Wait for logger thread to join.
        if self.lcm_transport.logger_process is not None:
            self.lcm_transport.logger_process._is_running = False

        # Unblock send thread with empty message and wait for join.
        if self.lcm_transport.send_thread is not None:
            self.lcm_transport.send_queue.put(None)
            self.lcm_transport.send_thread.join()

        if (
            self.lcm_transport.subscription is not None
            and self.lcm_transport.lcm is not None
        ):
            self.lcm_transport.lcm.unsubscribe(self.lcm_transport.subscription)

        self.log_info("LCM transport stopped")

    def broadcast_message(self, msg: PntosMessage, channel_name: str):
        """
        Send a message over LCM to a specific channel
        """
        lcm_transport_send_message(self.lcm_transport, msg, channel_name)
