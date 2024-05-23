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

from multiprocessing import Process
from typing import Optional, Protocol

from aspn23_lcm import MeasurementPositionVelocityAttitude
from aspn23.lcm_translations import (
    lcm_to_measurement_position_velocity_attitude
)
from aspn23.lcm_translations import (
    measurement_position_velocity_attitude_to_lcm
)
from aspn23.measurement_position_velocity_attitude import (
    MeasurementPositionVelocityAttitude as MeasurementPVA,
)

from pntos.api.plugins.common import (
    CommonPlugin, Mediator, Message, LoggingLevel
)



from lcm import LCM, LCMSubscription

WARN = LoggingLevel.PNTOS_LOG_LEVEL_WARN
INFO = LoggingLevel.PNTOS_LOG_LEVEL_INFO
ERROR = LoggingLevel.PNTOS_LOG_LEVEL_ERROR
DEBUG = LoggingLevel.PNTOS_LOG_LEVEL_DEBUG


class TransportPlugin(CommonPlugin, Protocol):
    """
    An example LCM Transport Plugin for ASPN23 implemented in Python
    """

    identifier: str
    url: str
    lcm: LCM
    listener: Process
    mediator: Mediator
    subscription: LCMSubscription

    def __init__(self, url, handler: callable):
        self.identifier = "python-transport-aspn23-plugin"
        self.url = url

    def init_plugin(self, mediator:Mediator):
        """
        pntOS plugin initialization function

        This is called by the pntOS system before calling any other function.
        """
        self.mediator = mediator

    def shutdown_plugin(self):
        """
        pntOS plugin shutdown function

        This is called by the pntOS system when it is done with the plugin.
        """
        if self.listener is not None:
            self.listener.join()
        if self.subscription is not None and self.lcm is not None:
            self.lcm.unsubscribe(self.subscription)
        self.__init__(self.url, mediator=None)
        self.mediator.log_message(INFO, "shutdown_plugin for "+self.identifier)

    def general_handler(self):
        """
        Generic listener for lcm messages to marshal to the mediator for 
        processing.

        NOTE: Current implementation only supports input from the following 
        sensors:
            Position-velocity-attitude
        """

        def _general_handler(channel: str, data: bytes):
            # Do not process messages sent from pntos.
            if "pntos" in channel:
                self.mediator.log_message(
                    INFO, 
                    "pntos channel message, not processing in aspn handler"
                )
                return
            decoded = MeasurementPositionVelocityAttitude.decode(data)
            translated = lcm_to_measurement_position_velocity_attitude(decoded)
            self.broadcast_message(translated)

        return _general_handler

    def listener_thread(self, lcm: LCM):
        self.subscription = lcm.subscribe(
            "^((?!pntos).)*$", 
            self.general_handler()
        )

    def start_listening(self) -> None:
        """
        Begin listening for lcm messages given input configuration
        """

        # Get the channel to pass to lcm_subscribe
        channel = ".*"  # Currently subscribe all, will come from registry

        self.lcm = LCM(self.url)

        if self.lcm is None:
            self.mediator.log_message(ERROR, "Failed to create lcm transport")
            return

        # Start new listener thread
        self.listener = Process(target=self.listener_thread, args=[self.lcm])

        self.listener.start()

        self.mediator.log_message(INFO, "LCM transport started")

    def stop_listening(self) -> None:
        """
        Shut down all processes and threads spun up for LCM message passing
        """

        if self.listener.is_alive():
            self.listener.join()

        if self.lcm.subscription is not None and self.lcm is not None:
            self.lcm.unsubscribe(self.subscription)

        self.mediator.log_message(INFO, "LCM transport stopped")

    def broadcast_message(self, message: Message, channel_name: Optional[str]):
        """
        Send a message over LCM to a specific channel
        """

        if isinstance(message.wrapped_message, MeasurementPVA):
            translated = measurement_position_velocity_attitude_to_lcm(
                message.wrapped_message
            )
            self.lcm.publish(channel_name, translated.encode())
        else:
            self.mediator.log_message(WARN, "Invalid LCM message")
