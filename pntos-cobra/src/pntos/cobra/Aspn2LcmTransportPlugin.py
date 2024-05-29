from threading import Thread
from typing import Optional, Protocol

from aspn23.measurement_position_velocity_attitude import (
    MeasurementPositionVelocityAttitude as MeasurementPVA,
)
from datasources.lcm.messages.aspn.positionvelocityattitude import (
    positionvelocityattitude,
)
from datasources.lcm.messages.aspn.types.geodeticposition3d_type import (
    geodeticposition3d_type,
)
from datasources.lcm.messages.aspn.types.header import header
from datasources.lcm.messages.aspn.types.timestamp import timestamp
from lcm import LCM, LCMSubscription

from pntos.api import CommonPlugin, LoggingLevel, Mediator, Message


class Aspn2LcmTransportPlugin(CommonPlugin, Protocol):
    identifier: str
    lcm: LCM
    listener: Thread
    mediator: Mediator
    subscription: LCMSubscription

    def __init__(self, mediator: Mediator):
        self.identifier = "python-transport-lcm2-plugin"
        self.mediator = mediator

    def init_plugin(self):
        """
        pntOS plugin initialization function

        This is called by the pntOS system before calling any other function.

        Implements C API PntosCommonPlugin.init_plugin.  See documentation in
        api/include/pntos/plugins/common.h for more information.
        """
        pass

    def shutdown_plugin(self):
        """
        pntOS plugin shutdown function

        This is called by the pntOS system when it is done with the plugin.

        Implements C API PntosCommonPlugin.shutdown_plugin.  See documentation
        in api/include/pntos/plugins/common.h for more information.
        """
        pass

    def general_handler(self):
        """
        Generic listener for lcm messages to marshal to the mediator for processing.

        NOTE: Current implementation only supports input from the following sensors:
            Inertial measurement unit (IMU)
            Geodetic position
            Position-velocity-attitude
        """

        def _general_handler(channel: str, data: bytes):
            # Do not process messages sent from pntos.
            if "pntos" in channel:
                print("pntos channel message, not processing in aspn handler")
                return

            untrans = positionvelocityattitude.decode(data)
            trans = MeasurementPVA()
            trans.p1 = untrans.position[0]
            trans.p2 = untrans.position[1]
            trans.p3 = untrans.position[2]
            trans.v1 = untrans.velocity[0]
            trans.v2 = untrans.velocity[1]
            trans.v3 = untrans.velocity[2]
            trans.quaternion = untrans.attitude
            msg = Message()
            msg.wrapped_message = trans

            self.broadcast_message(trans)

        return _general_handler

    def listener_thread(self):
        self.lcm.subscribe("^((?!pntos).)*$", self.general_handler())

    def start_listening(self) -> None:
        # old: config_path="config/transport/is4s_transport_lcm"
        """
        Begin listening for lcm messages given input configuration
        """

        self.lcm = LCM()

        if self.lcm is None:
            print("Failed to create lcm transport")
            return

        self.listener = Thread(target=self.listener_thread, args=[])
        self.listener.start()

    def stop_listening(self) -> None:
        """
        Shut down all processes and threads spun up for LCM message passing
        """
        if self.listener.is_alive():
            self.listener.join()

        if self.lcm.subscription is not None and self.lcm is not None:
            self.lcm.unsubscribe(self.subscription)

        self.mediator.log_message(LoggingLevel.INFO, "LCM transport stopped")

    def broadcast_message(self, message: Message, channel_name: Optional[str]):
        """
        Send a message over LCM to a specific channel
        """

        if isinstance(message.wrapped_message, MeasurementPVA):
            translated = positionvelocityattitude()
            head = header()
            ts = timestamp()
            head.seq_num = 0
            ts = timestamp()
            head.timestamp_arrival = ts
            head.timestamp_valid = ts
            translated.header = head
            translated.attitude = message.wrapped_message.quaternion
            geo = geodeticposition3d_type()
            geo.latitude = message.wrapped_message.p1
            geo.longitude = message.wrapped_message.p2
            geo.altitude = message.wrapped_message.p3
            translated.position = geo
            translated.velocity = [
                message.wrapped_message.v1,
                message.wrapped_message.v2,
                message.wrapped_message.v3,
            ]
            self.lcm.publish(channel_name, translated.encode())
        else:
            print("Invalid LCM message")
