from threading import Thread
from typing import Optional, Protocol

from aspn23 import (
    MeasurementPositionVelocityAttitude,
    lcm_to_measurement_position_velocity_attitude,
    measurement_position_velocity_attitude_to_lcm,
)
from aspn23_lcm import (
    measurement_position_velocity_attitude as MeasurementPositionVelocityAttitude_LCM,
)
from lcm import LCM, LCMSubscription

from pntos.api import CommonPlugin, LoggingLevel, Mediator, Message


class Aspn23LcmTransportPlugin(CommonPlugin, Protocol):
    """An example LCM Transport Plugin for ASPN23 implemented in Python"""

    identifier: str
    lcm: LCM
    listener: Thread
    mediator: Mediator
    subscription: LCMSubscription

    def __init__(self, mediator: Mediator):
        self.identifier = "python-transport-lcm23-plugin"
        self.mediator = mediator

    def init_plugin(
        self, plugin_resources_location: Optional[str], mediator: Mediator | None
    ):
        """
        PntOS plugin initialization function

        This is called by the pntOS system before calling any other function.
        """
        if mediator is not None:
            self.mediator = mediator

    def shutdown_plugin(self):
        """
        PntOS plugin shutdown function

        This is called by the pntOS system when it is done with the plugin.
        """
        if self.listener is not None:
            self.listener.join()
        if self.subscription is not None and self.lcm is not None:
            self.lcm.unsubscribe(self.subscription)
        self.__init__(self.url, mediator=None)
        self.mediator.log_message(
            LoggingLevel.INFO, "shutdown_plugin for " + self.identifier
        )

    def general_handler(self):
        """
        Generic listener for lcm messages to marshal to the mediator for processing.

        NOTE: Current implementation only supports input from the following
        sensors:
            Position-velocity-attitude
        """

        def _general_handler(channel: str, data: bytes):
            # Do not process messages sent from pntos.
            if "pntos" in channel:
                self.mediator.log_message(
                    LoggingLevel.INFO,
                    "pntos channel message, not processing in aspn handler",
                )
                return
            decoded = MeasurementPositionVelocityAttitude_LCM.decode(data)
            translated = lcm_to_measurement_position_velocity_attitude(decoded)
            message = Message(translated, channel)
            self.broadcast_message(message, None)

        return _general_handler

    def listener_thread(self, lcm: LCM):
        self.subscription = lcm.subscribe("^((?!pntos).)*$", self.general_handler())

    def start_listening(self) -> None:
        """Begin listening for lcm messages given input configuration"""
        self.lcm = LCM()

        if self.lcm is None:
            self.mediator.log_message(
                LoggingLevel.ERROR, "Failed to create lcm transport"
            )
            return

        self.listener = Thread(target=self.listener_thread, args=[])
        self.listener.start()

    def stop_listening(self) -> None:
        """Shut down all processes and threads spun up for LCM message passing"""
        if self.listener.is_alive():
            self.listener.join()

        if self.subscription is not None and self.lcm is not None:
            self.lcm.unsubscribe(self.subscription)

        self.mediator.log_message(LoggingLevel.INFO, "LCM transport stopped")

    def broadcast_message(self, message: Message, channel_name: Optional[str]):
        """Send a message over LCM to a specific channel"""
        if isinstance(message.wrapped_message, MeasurementPositionVelocityAttitude):
            translated = measurement_position_velocity_attitude_to_lcm(
                message.wrapped_message
            )
            channel = (
                channel_name if channel_name is not None else message.source_identifier
            )
            self.lcm.publish(channel, translated.encode())
        else:
            print("Invalid LCM message")
