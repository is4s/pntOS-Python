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


# from pntos import (
#     class_PntosTransportPlugin,
#     PntosLoggingLevel,
#     PntosMediator,\
#     PntosMessage,
# )

# from example_plugin_transport_lcm_aspn_2.LcmTransport import (
#     LcmTransport,
#     LcmLogger,
# )
# from example_plugin_transport_lcm_aspn_2.lcm_aspn2_handler import (
#     lcm_transport_send_message,
#     general_handler,
#     listener_thread,
#     send_thread,
# )

# from threading import Thread

from multiprocessing import Process
from typing import Optional, Protocol

import aspn23.lcm_translations
import aspn23.measurement_position_velocity_attitude
from pntos.api.plugins.common import CommonPlugin, Mediator, Message, LoggingLevel
from aspn23.measurement_position_velocity_attitude \
    import MeasurementPositionVelocityAttitude as MeasurementPVA
from aspn23_lcm import MeasurementPositionVelocityAttitude as lcm_PVA
from aspn23.lcm_translations \
    import lcm_to_measurement_position_velocity_attitude as lcm_to_aspn23_PVA

from lcm import LCM, LCMSubscription

WARN = LoggingLevel.PNTOS_LOG_LEVEL_WARN
INFO = LoggingLevel.PNTOS_LOG_LEVEL_INFO
ERROR = LoggingLevel.PNTOS_LOG_LEVEL_ERROR
DEBUG = LoggingLevel.PNTOS_LOG_LEVEL_DEBUG

class TransportPlugin(CommonPlugin, Protocol):
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
    identifier:str
    url:str
    lcm:LCM
    listener:Process
    mediator:Mediator
    subscription:LCMSubscription


    def __init__(self, url, handler:callable):
        self.identifier = "python-transport-lcm2-plugin"
        self.url = url

    def init_plugin(self, mediator):
        """
        pntOS plugin initialization function

        This is called by the pntOS system before calling any other function.

        Implements C API PntosCommonPlugin.init_plugin.  See documentation in
        api/include/pntos/plugins/common.h for more information.
        """
        self.mediator = mediator
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
            decoded = lcm_PVA.decode(data)
            translated = lcm_to_aspn23_PVA(translated)
            self.broadcast_message(translated)

        return _general_handler

    
    def listener_thread(self, lcm:LCM):
        self.subscription = lcm.subscribe("^((?!pntos).)*$", 
                                          self.general_handler()
        )
    
    

    def start_listening(self) -> None:
        # old: config_path="config/transport/is4s_transport_lcm"
        """
        Begin listening for lcm messages given input configuration
        """

        # Get the channel to pass to lcm_subscribe
        channel = ".*" # Currently subscribe all, will come from registry

        self.lcm = LCM(self.url)

        if self.lcm is None:
            self.mediator.log_message(ERROR, "Failed to create lcm transport")
            return

        # Start new listener thread
        self.listener = Process(
            target=self.listener_thread, args=[self.lcm]
        )

        self.listener.start()
        
        self.mediator.log_message(INFO,"LCM transport started")

    def stop_listening(self) -> None:
        """
        Shut down all processes and threads spun up for LCM message passing
        """

        if self.listener.is_alive():
            self.listener.join()

        if (self.lcm.subscription is not None
            and self.lcm is not None
        ):
            self.lcm.unsubscribe(self.lcm.subscription)

        self.mediator.log_message(INFO, "LCM transport stopped")

    def broadcast_message(self, message: Message, channel_name: Optional[str]):
        """
        Send a message over LCM to a specific channel
        """
        
        if isinstance(message.wrapped_message, MeasurementPVA):
            translated = \
                aspn23.lcm_translations.measurement_position_attitude_to_lcm(
                    message.wrapped_message)
            self.lcm.publish(channel_name, translated.encode())
        else:
            self.mediator.log_message(WARN, "Invalid LCM message")

