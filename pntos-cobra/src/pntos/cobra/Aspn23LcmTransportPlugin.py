from threading import Thread
from typing import Callable

from aspn23 import (
    MeasurementAltitude,
    MeasurementBarometer,
    MeasurementDeltaPosition,
    MeasurementHeading,
    MeasurementImu,
    MeasurementPosition,
    MeasurementPositionVelocityAttitude,
    MeasurementSatnav,
    MetadataGpsLnavEphemeris,
)
from aspn23_lcm import (
    lcm_to_measurement_altitude,
    lcm_to_measurement_barometer,
    lcm_to_measurement_delta_position,
    lcm_to_measurement_heading,
    lcm_to_measurement_IMU,
    lcm_to_measurement_position,
    lcm_to_measurement_position_velocity_attitude,
    lcm_to_measurement_satnav,
    lcm_to_metadata_GPS_Lnav_ephemeris,
    measurement_altitude as MeasurementAltitude_LCM,
    measurement_altitude_to_lcm,
    measurement_barometer as MeasurementBarometer_LCM,
    measurement_barometer_to_lcm,
    measurement_delta_position as MeasurementDeltaPosition_LCM,
    measurement_delta_position_to_lcm,
    measurement_heading as MeasurementHeading_LCM,
    measurement_heading_to_lcm,
    measurement_IMU as MeasurementImu_LCM,
    measurement_IMU_to_lcm,
    measurement_position as MeasurementPosition_LCM,
    measurement_position_to_lcm,
    measurement_position_velocity_attitude as MeasurementPositionVelocityAttitude_LCM,
    measurement_position_velocity_attitude_to_lcm,
    measurement_satnav as MeasurementSatnav_LCM,
    measurement_satnav_to_lcm,
    metadata_GPS_Lnav_ephemeris as MetadataGpsLnavEphemeris_LCM,
    metadata_GPS_Lnav_ephemeris_to_lcm,
)
from lcm import LCM, LCMSubscription

from pntos.api import LoggingLevel, Mediator, Message, TransportPlugin


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

    def general_handler(self) -> Callable[[str, bytes], None]:
        """
        Generic listener for lcm messages to marshal to the mediator for processing.

        NOTE: Current implementation only supports message types:
            MeasurementAltitude
            MeasurementBarometer
            MeasurementDeltaPosition
            MeasurementHeading
            MeasurementImu
            MeasurementPosition
            MeasurementPositionVelocityAttitude
            MeasurementSatnav
            MetadataGpsLnavEphemeris
        """

        def _general_handler(channel: str, data: bytes) -> None:
            # Do not process messages sent from pntos.
            if 'pntos' in channel:
                self.mediator.log_message(
                    LoggingLevel.INFO,
                    'pntOS channel message, not processing in ASPN handler.',
                )
                return

            hash = data[0:8]

            # Define types of Aspn message.
            aspn_msg: (
                None
                | MeasurementAltitude
                | MeasurementBarometer
                | MeasurementDeltaPosition
                | MeasurementHeading
                | MeasurementImu
                | MeasurementPosition
                | MeasurementPositionVelocityAttitude
                | MeasurementSatnav
                | MetadataGpsLnavEphemeris
            )

            # Process received message appropriately.
            if hash == MeasurementAltitude_LCM._get_packed_fingerprint():
                altitude = MeasurementAltitude_LCM()
                decoded = altitude.decode(data)
                aspn_msg = lcm_to_measurement_altitude(decoded)
            elif hash == MeasurementBarometer_LCM._get_packed_fingerprint():
                barometer = MeasurementBarometer_LCM()
                decoded = barometer.decode(data)
                aspn_msg = lcm_to_measurement_barometer(decoded)
            elif hash == MeasurementDeltaPosition_LCM._get_packed_fingerprint():
                delta_pos = MeasurementDeltaPosition_LCM()
                decoded = delta_pos.decode(data)
                aspn_msg = lcm_to_measurement_delta_position(decoded)
            elif hash == MeasurementHeading_LCM._get_packed_fingerprint():
                heading = MeasurementHeading_LCM()
                decoded = heading.decode(data)
                aspn_msg = lcm_to_measurement_heading(decoded)
            elif hash == MeasurementImu_LCM._get_packed_fingerprint():
                imu = MeasurementImu_LCM()
                decoded = imu.decode(data)
                aspn_msg = lcm_to_measurement_IMU(decoded)
            elif hash == MeasurementPosition_LCM._get_packed_fingerprint():
                position = MeasurementPosition_LCM()
                decoded = position.decode(data)
                aspn_msg = lcm_to_measurement_position(decoded)
            elif (
                hash
                == MeasurementPositionVelocityAttitude_LCM._get_packed_fingerprint()
            ):
                pva = MeasurementPositionVelocityAttitude_LCM()
                decoded = pva.decode(data)
                aspn_msg = lcm_to_measurement_position_velocity_attitude(decoded)
            elif hash == MeasurementSatnav_LCM._get_packed_fingerprint():
                satnav = MeasurementSatnav_LCM()
                decoded = satnav.decode(data)
                aspn_msg = lcm_to_measurement_satnav(decoded)
            elif hash == MetadataGpsLnavEphemeris_LCM._get_packed_fingerprint():
                gle = MetadataGpsLnavEphemeris_LCM()
                decoded = gle.decode(data)
                aspn_msg = lcm_to_metadata_GPS_Lnav_ephemeris(decoded)

            if aspn_msg:
                message = Message(aspn_msg, channel)
                self.broadcast_message(message, channel)

        return _general_handler

    def listener_thread(self) -> None:
        """Subscribe to specified channels (excluding any channels with "pntos")"""
        self.subscription = self.lcm.subscribe(
            '^((?!pntos).)*$', self.general_handler()
        )

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
        translated: (
            None
            | MeasurementAltitude_LCM
            | MeasurementBarometer_LCM
            | MeasurementDeltaPosition_LCM
            | MeasurementHeading_LCM
            | MeasurementImu_LCM
            | MeasurementPosition_LCM
            | MeasurementPositionVelocityAttitude_LCM
            | MeasurementSatnav_LCM
            | MetadataGpsLnavEphemeris_LCM
        )
        if isinstance(message.wrapped_message, MeasurementAltitude):
            translated = measurement_altitude_to_lcm(message.wrapped_message)
        elif isinstance(message.wrapped_message, MeasurementBarometer):
            translated = measurement_barometer_to_lcm(message.wrapped_message)
        elif isinstance(message.wrapped_message, MeasurementDeltaPosition):
            translated = measurement_delta_position_to_lcm(message.wrapped_message)
        elif isinstance(message.wrapped_message, MeasurementHeading):
            translated = measurement_heading_to_lcm(message.wrapped_message)
        elif isinstance(message.wrapped_message, MeasurementImu):
            translated = measurement_IMU_to_lcm(message.wrapped_message)
        elif isinstance(message.wrapped_message, MeasurementPosition):
            translated = measurement_position_to_lcm(message.wrapped_message)
        elif isinstance(message.wrapped_message, MeasurementPositionVelocityAttitude):
            translated = measurement_position_velocity_attitude_to_lcm(
                message.wrapped_message
            )
        elif isinstance(message.wrapped_message, MeasurementSatnav):
            translated = measurement_satnav_to_lcm(message.wrapped_message)
        elif isinstance(message.wrapped_message, MetadataGpsLnavEphemeris):
            translated = metadata_GPS_Lnav_ephemeris_to_lcm(message.wrapped_message)

        if translated is None:
            self.mediator.log_message(LoggingLevel.ERROR, 'Invalid LCM message')
        elif channel_name is None:
            self.mediator.log_message(
                LoggingLevel.WARN,
                'No channel name specified. This implementation requires a channel name.',
            )
        else:
            self.lcm.publish(channel_name, translated.encode())
