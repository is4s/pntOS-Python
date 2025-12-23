import re
from collections.abc import Callable
from pathlib import Path
from site import getsitepackages
from subprocess import PIPE, Popen

import aspn2_translations
import aspn23
import aspn23_lcm
import datasources.lcm.messages.aspn as aspn2_lcm

from pntos.api import LoggingLevel, Mediator, Message
from pntos.cobra.config import AspnVersion

from .apps import kill, monitor_app_output, run_app, wait_until_file_stable

Aspn23LcmMeasurement = (
    aspn23_lcm.measurement_angular_velocity_1d
    | aspn23_lcm.measurement_angular_velocity
    | aspn23_lcm.measurement_accumulated_distance_traveled
    | aspn23_lcm.measurement_altitude
    | aspn23_lcm.measurement_attitude_2d
    | aspn23_lcm.measurement_attitude_3d
    | aspn23_lcm.measurement_barometer
    | aspn23_lcm.measurement_delta_position
    | aspn23_lcm.measurement_delta_range
    | aspn23_lcm.measurement_delta_range_to_point
    | aspn23_lcm.measurement_direction_2d_to_points
    | aspn23_lcm.measurement_direction_3d_to_points
    | aspn23_lcm.measurement_direction_of_motion_2d
    | aspn23_lcm.measurement_direction_of_motion_3d
    | aspn23_lcm.measurement_frequency_difference
    | aspn23_lcm.measurement_heading
    | aspn23_lcm.measurement_image
    | aspn23_lcm.measurement_IMU
    | aspn23_lcm.measurement_magnetic_field
    | aspn23_lcm.measurement_magnetic_field_magnitude
    | aspn23_lcm.measurement_position
    | aspn23_lcm.measurement_position_attitude
    | aspn23_lcm.measurement_position_velocity_attitude
    | aspn23_lcm.measurement_range_rate_to_point
    | aspn23_lcm.measurement_range_to_point
    | aspn23_lcm.measurement_satnav
    | aspn23_lcm.measurement_satnav_subframe
    | aspn23_lcm.measurement_satnav_with_sv_data
    | aspn23_lcm.measurement_specific_force_1d
    | aspn23_lcm.measurement_speed
    | aspn23_lcm.measurement_TDOA_1Tx_2Rx
    | aspn23_lcm.measurement_TDOA_2Tx_1Rx
    | aspn23_lcm.measurement_temperature
    | aspn23_lcm.measurement_time
    | aspn23_lcm.measurement_time_difference
    | aspn23_lcm.measurement_time_frequency_difference
    | aspn23_lcm.measurement_velocity
)

Aspn2LcmMeasurement = (
    aspn2_lcm.accumulateddistancetraveled
    | aspn2_lcm.altitude
    | aspn2_lcm.attitude1d
    | aspn2_lcm.attitude2d
    | aspn2_lcm.attitude3d
    | aspn2_lcm.barometricpressure
    | aspn2_lcm.bearingtoknownfeature
    | aspn2_lcm.bearingtounknownfeature
    | aspn2_lcm.correspondedopticalcamerafeatures
    | aspn2_lcm.deltaposition1d
    | aspn2_lcm.deltaposition2d
    | aspn2_lcm.deltaposition3d
    | aspn2_lcm.deltarange
    | aspn2_lcm.deltarangetoknownfeature
    | aspn2_lcm.deltarotation1d
    | aspn2_lcm.deltarotation2d
    | aspn2_lcm.deltarotation3d
    | aspn2_lcm.directionofmotion2d
    | aspn2_lcm.directionofmotion3d
    | aspn2_lcm.directiontoknownfeature2d
    | aspn2_lcm.directiontoknownfeature3d
    | aspn2_lcm.geodeticposition2d
    | aspn2_lcm.geodeticposition3d
    | aspn2_lcm.gnss
    | aspn2_lcm.gpsephemeris
    | aspn2_lcm.imu
    | aspn2_lcm.ins
    | aspn2_lcm.opticalcameraimage
    | aspn2_lcm.overhausermagnetometer
    | aspn2_lcm.positionattitude
    | aspn2_lcm.positionvelocity
    | aspn2_lcm.positionvelocityattitude
    | aspn2_lcm.rangeratetoknownfeature
    | aspn2_lcm.rangeratetounknownfeature
    | aspn2_lcm.rangetoknownfeature
    | aspn2_lcm.rangetounknownfeature
    | aspn2_lcm.speed
    | aspn2_lcm.tdoatoknownfeature
    | aspn2_lcm.tdoatounknownfeature
    | aspn2_lcm.temperature
    | aspn2_lcm.threeaxismagnetometer
    | aspn2_lcm.uncorrespondedopticalcamerafeatures
    | aspn2_lcm.velocity1d
    | aspn2_lcm.velocity2d
    | aspn2_lcm.velocity3d
)

Aspn23Measurement = (
    aspn23.MeasurementAngularVelocity1D
    | aspn23.MeasurementAngularVelocity
    | aspn23.MeasurementAccumulatedDistanceTraveled
    | aspn23.MeasurementAltitude
    | aspn23.MeasurementAttitude2D
    | aspn23.MeasurementAttitude3D
    | aspn23.MeasurementBarometer
    | aspn23.MeasurementDeltaPosition
    | aspn23.MeasurementDeltaRange
    | aspn23.MeasurementDeltaRangeToPoint
    | aspn23.MeasurementDirection2DToPoints
    | aspn23.MeasurementDirection3DToPoints
    | aspn23.MeasurementDirectionOfMotion2D
    | aspn23.MeasurementDirectionOfMotion3D
    | aspn23.MeasurementFrequencyDifference
    | aspn23.MeasurementHeading
    | aspn23.MeasurementImage
    | aspn23.MeasurementImu
    | aspn23.MeasurementMagneticField
    | aspn23.MeasurementMagneticFieldMagnitude
    | aspn23.MeasurementPosition
    | aspn23.MeasurementPositionAttitude
    | aspn23.MeasurementPositionVelocityAttitude
    | aspn23.MeasurementRangeRateToPoint
    | aspn23.MeasurementRangeToPoint
    | aspn23.MeasurementSatnav
    | aspn23.MeasurementSatnavSubframe
    | aspn23.MeasurementSatnavWithSvData
    | aspn23.MeasurementSpecificForce1D
    | aspn23.MeasurementSpeed
    | aspn23.MeasurementTdoa1Tx2Rx
    | aspn23.MeasurementTdoa2Tx1Rx
    | aspn23.MeasurementTemperature
    | aspn23.MeasurementTime
    | aspn23.MeasurementTimeDifference
    | aspn23.MeasurementTimeFrequencyDifference
    | aspn23.MeasurementVelocity
)

# It is possible aspn2 lcm->aspn23 conversions to return non-Measurement types to get around
# non-standard conversions, see for instance translate_from_aspn2_rangeratetoknownfeature_to_aspn23
Aspn23MeasurementExtended = (
    Aspn23Measurement
    | list[aspn23.MeasurementDeltaRangeToPoint]
    | aspn23.MetadataGpsLnavEphemeris
    | list[aspn23.MeasurementRangeRateToPoint]
    | list[aspn23.MeasurementRangeToPoint]
    | list[aspn23.MeasurementTdoa1Tx2Rx]
)

# dictionary mapping ASPN23 message type to ASPN23 LCM marshaling functions
marshaler_to_aspn23_lcm: dict[
    type[Aspn23Measurement], Callable[..., Aspn23LcmMeasurement]
] = {
    aspn23.MeasurementAngularVelocity1D: aspn23_lcm.measurement_angular_velocity_1d_to_lcm,
    aspn23.MeasurementAngularVelocity: aspn23_lcm.measurement_angular_velocity_to_lcm,
    aspn23.MeasurementAccumulatedDistanceTraveled: aspn23_lcm.measurement_accumulated_distance_traveled_to_lcm,
    aspn23.MeasurementAltitude: aspn23_lcm.measurement_altitude_to_lcm,
    aspn23.MeasurementAttitude2D: aspn23_lcm.measurement_attitude_2d_to_lcm,
    aspn23.MeasurementAttitude3D: aspn23_lcm.measurement_attitude_3d_to_lcm,
    aspn23.MeasurementBarometer: aspn23_lcm.measurement_barometer_to_lcm,
    aspn23.MeasurementDeltaPosition: aspn23_lcm.measurement_delta_position_to_lcm,
    aspn23.MeasurementDeltaRange: aspn23_lcm.measurement_delta_range_to_lcm,
    aspn23.MeasurementDeltaRangeToPoint: aspn23_lcm.measurement_delta_range_to_point_to_lcm,
    aspn23.MeasurementDirection2DToPoints: aspn23_lcm.measurement_direction_2d_to_points_to_lcm,
    aspn23.MeasurementDirection3DToPoints: aspn23_lcm.measurement_direction_3d_to_points_to_lcm,
    aspn23.MeasurementDirectionOfMotion2D: aspn23_lcm.measurement_direction_of_motion_2d_to_lcm,
    aspn23.MeasurementDirectionOfMotion3D: aspn23_lcm.measurement_direction_of_motion_3d_to_lcm,
    aspn23.MeasurementFrequencyDifference: aspn23_lcm.measurement_frequency_difference_to_lcm,
    aspn23.MeasurementHeading: aspn23_lcm.measurement_heading_to_lcm,
    aspn23.MeasurementImage: aspn23_lcm.measurement_image_to_lcm,
    aspn23.MeasurementImu: aspn23_lcm.measurement_IMU_to_lcm,
    aspn23.MeasurementMagneticField: aspn23_lcm.measurement_magnetic_field_to_lcm,
    aspn23.MeasurementMagneticFieldMagnitude: aspn23_lcm.measurement_magnetic_field_magnitude_to_lcm,
    aspn23.MeasurementPosition: aspn23_lcm.measurement_position_to_lcm,
    aspn23.MeasurementPositionAttitude: aspn23_lcm.measurement_position_attitude_to_lcm,
    aspn23.MeasurementPositionVelocityAttitude: aspn23_lcm.measurement_position_velocity_attitude_to_lcm,
    aspn23.MeasurementRangeRateToPoint: aspn23_lcm.measurement_range_rate_to_point_to_lcm,
    aspn23.MeasurementRangeToPoint: aspn23_lcm.measurement_range_to_point_to_lcm,
    aspn23.MeasurementSatnav: aspn23_lcm.measurement_satnav_to_lcm,
    aspn23.MeasurementSatnavSubframe: aspn23_lcm.measurement_satnav_subframe_to_lcm,
    aspn23.MeasurementSatnavWithSvData: aspn23_lcm.measurement_satnav_with_sv_data_to_lcm,
    aspn23.MeasurementSpecificForce1D: aspn23_lcm.measurement_specific_force_1d_to_lcm,
    aspn23.MeasurementSpeed: aspn23_lcm.measurement_speed_to_lcm,
    aspn23.MeasurementTdoa1Tx2Rx: aspn23_lcm.measurement_TDOA_1Tx_2Rx_to_lcm,
    aspn23.MeasurementTdoa2Tx1Rx: aspn23_lcm.measurement_TDOA_2Tx_1Rx_to_lcm,
    aspn23.MeasurementTemperature: aspn23_lcm.measurement_temperature_to_lcm,
    aspn23.MeasurementTime: aspn23_lcm.measurement_time_to_lcm,
    aspn23.MeasurementTimeDifference: aspn23_lcm.measurement_time_difference_to_lcm,
    aspn23.MeasurementTimeFrequencyDifference: aspn23_lcm.measurement_time_frequency_difference_to_lcm,
    aspn23.MeasurementVelocity: aspn23_lcm.measurement_velocity_to_lcm,
}

# dictionary mapping ASPN23 message type to ASPN2 LCM marshaling functions
marshaler_to_aspn2_lcm: dict[
    type[Aspn23Measurement], Callable[..., Aspn2LcmMeasurement]
] = {
    aspn23.MeasurementImu: aspn2_translations.translate_from_aspn23_imu_to_aspn2,
    aspn23.MeasurementPosition: aspn2_translations.translate_from_aspn23_position_to_aspn2_geodeticposition3d,
    aspn23.MeasurementPositionVelocityAttitude: aspn2_translations.translate_from_aspn23_positionvelocityattitude_to_aspn2,
}

# dictionary mapping ASPN LCM message type to ASPN23 marshaling functions
marshaler_from_lcm: dict[
    type[Aspn23LcmMeasurement] | type[Aspn2LcmMeasurement],
    Callable[..., Aspn23MeasurementExtended],
] = {
    # aspn23_lcm to aspn23
    aspn23_lcm.measurement_angular_velocity_1d: aspn23_lcm.lcm_to_measurement_angular_velocity_1d,
    aspn23_lcm.measurement_angular_velocity: aspn23_lcm.lcm_to_measurement_angular_velocity,
    aspn23_lcm.measurement_accumulated_distance_traveled: aspn23_lcm.lcm_to_measurement_accumulated_distance_traveled,
    aspn23_lcm.measurement_altitude: aspn23_lcm.lcm_to_measurement_altitude,
    aspn23_lcm.measurement_attitude_2d: aspn23_lcm.lcm_to_measurement_attitude_2d,
    aspn23_lcm.measurement_attitude_3d: aspn23_lcm.lcm_to_measurement_attitude_3d,
    aspn23_lcm.measurement_barometer: aspn23_lcm.lcm_to_measurement_barometer,
    aspn23_lcm.measurement_delta_position: aspn23_lcm.lcm_to_measurement_delta_position,
    aspn23_lcm.measurement_delta_range: aspn23_lcm.lcm_to_measurement_delta_range,
    aspn23_lcm.measurement_delta_range_to_point: aspn23_lcm.lcm_to_measurement_delta_range_to_point,
    aspn23_lcm.measurement_direction_2d_to_points: aspn23_lcm.lcm_to_measurement_direction_2d_to_points,
    aspn23_lcm.measurement_direction_3d_to_points: aspn23_lcm.lcm_to_measurement_direction_3d_to_points,
    aspn23_lcm.measurement_direction_of_motion_2d: aspn23_lcm.lcm_to_measurement_direction_of_motion_2d,
    aspn23_lcm.measurement_direction_of_motion_3d: aspn23_lcm.lcm_to_measurement_direction_of_motion_3d,
    aspn23_lcm.measurement_frequency_difference: aspn23_lcm.lcm_to_measurement_frequency_difference,
    aspn23_lcm.measurement_heading: aspn23_lcm.lcm_to_measurement_heading,
    aspn23_lcm.measurement_image: aspn23_lcm.lcm_to_measurement_image,
    aspn23_lcm.measurement_IMU: aspn23_lcm.lcm_to_measurement_IMU,
    aspn23_lcm.measurement_magnetic_field: aspn23_lcm.lcm_to_measurement_magnetic_field,
    aspn23_lcm.measurement_magnetic_field_magnitude: aspn23_lcm.lcm_to_measurement_magnetic_field_magnitude,
    aspn23_lcm.measurement_position: aspn23_lcm.lcm_to_measurement_position,
    aspn23_lcm.measurement_position_attitude: aspn23_lcm.lcm_to_measurement_position_attitude,
    aspn23_lcm.measurement_position_velocity_attitude: aspn23_lcm.lcm_to_measurement_position_velocity_attitude,
    aspn23_lcm.measurement_range_rate_to_point: aspn23_lcm.lcm_to_measurement_range_rate_to_point,
    aspn23_lcm.measurement_range_to_point: aspn23_lcm.lcm_to_measurement_range_to_point,
    aspn23_lcm.measurement_satnav: aspn23_lcm.lcm_to_measurement_satnav,
    aspn23_lcm.measurement_satnav_subframe: aspn23_lcm.lcm_to_measurement_satnav_subframe,
    aspn23_lcm.measurement_satnav_with_sv_data: aspn23_lcm.lcm_to_measurement_satnav_with_sv_data,
    aspn23_lcm.measurement_specific_force_1d: aspn23_lcm.lcm_to_measurement_specific_force_1d,
    aspn23_lcm.measurement_speed: aspn23_lcm.lcm_to_measurement_speed,
    aspn23_lcm.measurement_TDOA_1Tx_2Rx: aspn23_lcm.lcm_to_measurement_TDOA_1Tx_2Rx,
    aspn23_lcm.measurement_TDOA_2Tx_1Rx: aspn23_lcm.lcm_to_measurement_TDOA_2Tx_1Rx,
    aspn23_lcm.measurement_temperature: aspn23_lcm.lcm_to_measurement_temperature,
    aspn23_lcm.measurement_time: aspn23_lcm.lcm_to_measurement_time,
    aspn23_lcm.measurement_time_difference: aspn23_lcm.lcm_to_measurement_time_difference,
    aspn23_lcm.measurement_time_frequency_difference: aspn23_lcm.lcm_to_measurement_time_frequency_difference,
    aspn23_lcm.measurement_velocity: aspn23_lcm.lcm_to_measurement_velocity,
    # aspn2_lcm to aspn23
    aspn2_lcm.accumulateddistancetraveled: aspn2_translations.translate_from_aspn2_accumulateddistancetraveled_to_aspn23,
    aspn2_lcm.altitude: aspn2_translations.translate_from_aspn2_altitude_to_aspn23,
    aspn2_lcm.attitude1d: aspn2_translations.translate_from_aspn2_attitude1d_to_aspn23,
    aspn2_lcm.attitude2d: aspn2_translations.translate_from_aspn2_attitude2d_to_aspn23,
    aspn2_lcm.attitude3d: aspn2_translations.translate_from_aspn2_attitude3d_to_aspn23,
    aspn2_lcm.barometricpressure: aspn2_translations.translate_from_aspn2_barometricpressure_to_aspn23,
    aspn2_lcm.bearingtoknownfeature: aspn2_translations.translate_from_aspn2_bearingtoknownfeature_to_aspn23,
    aspn2_lcm.bearingtounknownfeature: aspn2_translations.translate_from_aspn2_bearingtounknownfeature_to_aspn23,
    aspn2_lcm.correspondedopticalcamerafeatures: aspn2_translations.translate_from_aspn2_correspondedopticalcamerafeatures_to_aspn23,
    aspn2_lcm.deltaposition1d: aspn2_translations.translate_from_aspn2_deltaposition1d_to_aspn23,
    aspn2_lcm.deltaposition2d: aspn2_translations.translate_from_aspn2_deltaposition2d_to_aspn23,
    aspn2_lcm.deltaposition3d: aspn2_translations.translate_from_aspn2_deltaposition3d_to_aspn23,
    aspn2_lcm.deltarange: aspn2_translations.translate_from_aspn2_deltarange_to_aspn23,
    aspn2_lcm.deltarangetoknownfeature: aspn2_translations.translate_from_aspn2_deltarangetoknownfeature_to_aspn23,
    aspn2_lcm.deltarotation1d: aspn2_translations.translate_from_aspn2_deltarotation1d_to_aspn23,
    aspn2_lcm.deltarotation2d: aspn2_translations.translate_from_aspn2_deltarotation2d_to_aspn23,
    aspn2_lcm.deltarotation3d: aspn2_translations.translate_from_aspn2_deltarotation3d_to_aspn23,
    aspn2_lcm.directionofmotion2d: aspn2_translations.translate_from_aspn2_directionofmotion2d_to_aspn23,
    aspn2_lcm.directionofmotion3d: aspn2_translations.translate_from_aspn2_directionofmotion3d_to_aspn23,
    aspn2_lcm.directiontoknownfeature2d: aspn2_translations.translate_from_aspn2_directiontoknownfeature2d_to_aspn23,
    aspn2_lcm.directiontoknownfeature3d: aspn2_translations.translate_from_aspn2_directiontoknownfeature3d_to_aspn23,
    aspn2_lcm.geodeticposition2d: aspn2_translations.translate_from_aspn2_geodeticposition2d_to_aspn23,
    aspn2_lcm.geodeticposition3d: aspn2_translations.translate_from_aspn2_geodeticposition3d_to_aspn23,
    aspn2_lcm.gnss: aspn2_translations.translate_from_aspn2_satnav_to_aspn23,
    aspn2_lcm.gpsephemeris: aspn2_translations.translate_from_aspn2_gpsephemeris_to_aspn23,
    aspn2_lcm.imu: aspn2_translations.translate_from_aspn2_imu_to_aspn23,
    aspn2_lcm.ins: aspn2_translations.translate_from_aspn2_ins_to_aspn23_imu,
    aspn2_lcm.opticalcameraimage: aspn2_translations.translate_from_aspn2_opticalcameraimage_to_aspn23,
    aspn2_lcm.overhausermagnetometer: aspn2_translations.translate_from_aspn2_overhausermagnetometer_to_aspn23,
    aspn2_lcm.positionattitude: aspn2_translations.translate_from_aspn2_positionattitude_to_aspn23,
    aspn2_lcm.positionvelocity: aspn2_translations.translate_from_aspn2_positionvelocity_to_aspn23,
    aspn2_lcm.positionvelocityattitude: aspn2_translations.translate_from_aspn2_positionvelocityattitude_to_aspn23,
    aspn2_lcm.rangeratetoknownfeature: aspn2_translations.translate_from_aspn2_rangeratetoknownfeature_to_aspn23,
    aspn2_lcm.rangeratetounknownfeature: aspn2_translations.translate_from_aspn2_rangeratetounknownfeature_to_aspn23,
    aspn2_lcm.rangetoknownfeature: aspn2_translations.translate_from_aspn2_rangetoknownfeature_to_aspn23,
    aspn2_lcm.rangetounknownfeature: aspn2_translations.translate_from_aspn2_rangetounknownfeature_to_aspn23,
    aspn2_lcm.speed: aspn2_translations.translate_from_aspn2_speed_to_aspn23,
    aspn2_lcm.tdoatoknownfeature: aspn2_translations.translate_from_aspn2_tdoatoknownfeature_to_aspn23,
    aspn2_lcm.tdoatounknownfeature: aspn2_translations.translate_from_aspn2_tdoatounknownfeature_to_aspn23,
    aspn2_lcm.temperature: aspn2_translations.translate_from_aspn2_temperature_to_aspn23,
    aspn2_lcm.threeaxismagnetometer: aspn2_translations.translate_from_aspn2_threeaxismagnetometer_to_aspn23,
    aspn2_lcm.uncorrespondedopticalcamerafeatures: aspn2_translations.translate_from_aspn2_uncorrespondedopticalcamerafeatures_to_aspn23,
    aspn2_lcm.velocity1d: aspn2_translations.translate_from_aspn2_velocity1d_to_aspn23,
    aspn2_lcm.velocity2d: aspn2_translations.translate_from_aspn2_velocity2d_to_aspn23,
    aspn2_lcm.velocity3d: aspn2_translations.translate_from_aspn2_velocity3d_to_aspn23,
}

# dictionary mapping LCM message fingerprint to message decode function
decoder: dict[bytes, Callable[[bytes], Aspn23LcmMeasurement | Aspn2LcmMeasurement]] = {}
for aspn_type in marshaler_from_lcm:
    decoder[aspn_type._get_packed_fingerprint()] = aspn_type.decode  # type: ignore[assignment]


def decode_aspn_lcm_msg(
    data: bytes,
) -> Aspn23LcmMeasurement | Aspn2LcmMeasurement | None:
    """
    Decodes a set of bytes into an ASPN-LCM message. Uses the first 8 bytes to determine the type of message,
    if the type cannot be determined this function will return ``None``.

    Args:
        data (bytes): The set of bytes to decode.

    Returns:
        Aspn23LcmMeasurement | None
    """
    fingerprint = data[:8]

    if fingerprint not in decoder:
        return None

    decode_func = decoder[fingerprint]
    return decode_func(data)


def marshal_from_lcm(
    msg: Aspn23LcmMeasurement | Aspn2LcmMeasurement,
) -> Aspn23MeasurementExtended | None:
    """
    Converts from ASPN-LCM message to ASPN23 message. If the input message cannot be converted,
    this function will return ``None``.

    Args:
        msg (``Aspn23LcmMeasurement``): The message to convert.

    Returns:
        Aspn23Measurement | None
    """
    msg_type = type(msg)

    if msg_type not in marshaler_from_lcm:
        return None

    marshal_func = marshaler_from_lcm[msg_type]
    return marshal_func(msg)


def marshal_to_aspn23_lcm(msg: aspn23.AspnBase) -> Aspn23LcmMeasurement | None:
    """
    Convert from ASPN23 message to ASPN23-LCM message. If the input message cannot be converted,
    this function will return ``None``.

    Args:
        msg (AspnBase): The message to convert.

    Returns:
        Aspn23LcmMeasurement | None
    """
    msg_type = type(msg)

    if msg_type not in marshaler_to_aspn23_lcm:
        return None

    marshal_func = marshaler_to_aspn23_lcm[msg_type]  # type: ignore[index]
    return marshal_func(msg)


def marshal_to_aspn2_lcm(msg: aspn23.AspnBase) -> Aspn2LcmMeasurement | None:
    """
    Convert from ASPN23 message to ASPN2-LCM message. If the input message cannot be converted,
    this function will return ``None``.

    Args:
        msg (AspnBase): The message to convert.

    Returns:
        Aspn2LcmMeasurement | None
    """
    msg_type = type(msg)

    if msg_type not in marshaler_to_aspn2_lcm:
        return None

    marshal_func = marshaler_to_aspn2_lcm[msg_type]  # type: ignore[index]
    try:
        return marshal_func(msg)
    except KeyError as e:
        print(e)
        return None


def process_lcm_message(
    mediator: Mediator, channel: str, data: bytes, channels: set[str]
) -> None:
    """
    Marshal LCM message to ASPN-Python and send to the mediator for processing.

    Args:
        mediator (Mediator): Mediator instance used for logging and processing message.
        channel (str): The channel name the data originates from.
        data (bytes): A message represented in binary.
        channels (set[str]): Set of channels found so far.
    """
    # Do not process messages sent from pntos.
    if 'pntos' in channel:
        mediator.log_message(
            LoggingLevel.DEBUG,
            'pntOS channel message, not processing in ASPN handler.',
        )
        return

    lcm_aspn_msg = decode_aspn_lcm_msg(data)
    if lcm_aspn_msg is None:
        mediator.log_message(
            LoggingLevel.WARN,
            f'Cannot decode message on channel {channel}. Ignoring message.',
        )
        return
    aspn_msg = marshal_from_lcm(lcm_aspn_msg)
    if aspn_msg is None:
        mediator.log_message(
            LoggingLevel.WARN,
            f'Cannot marshal message on channel {channel} of type {type(aspn_msg)}. Ignoring message.',
        )
        return
    if channel not in channels:
        # It is possible for conversions to return a list of Measurements to cover the case
        # where ASPN23 dropped support for multiple obs in 1 message
        ts = (
            aspn_msg[0].time_of_validity.elapsed_nsec / 1e9
            if isinstance(aspn_msg, list)
            else aspn_msg.time_of_validity.elapsed_nsec / 1e9
        )
        mediator.log_message(
            LoggingLevel.INFO,
            f'Found new channel {channel}\t with a timestamp of {ts:.9f}s',
        )
        channels.add(channel)
    if isinstance(aspn_msg, list):
        for am in aspn_msg:
            message = Message(am, channel)
            mediator.process_pntos_message(message)
    else:
        message = Message(aspn_msg, channel)
        mediator.process_pntos_message(message)


def create_lcm_message(
    message: Message,
    output_version: AspnVersion,
) -> Aspn2LcmMeasurement | Aspn23LcmMeasurement | None:
    lcm_msg: Aspn2LcmMeasurement | Aspn23LcmMeasurement | None = None
    if output_version == AspnVersion.V2:
        lcm_msg = marshal_to_aspn2_lcm(message.wrapped_message)
    else:
        lcm_msg = marshal_to_aspn23_lcm(message.wrapped_message)

    return lcm_msg


def run_tcp_relay() -> Popen[str]:  # pragma: no cover
    sitepackages_dir = Path(getsitepackages()[0])
    process = Popen(
        [
            'java',
            '-classpath',
            sitepackages_dir / 'share' / 'java' / 'lcm.jar',
            'lcm.lcm.TCPService',
        ],
        text=True,
        stdout=PIPE,
        start_new_session=True,
    )
    # wait until we start seeing output from relay
    process.stdout.readline()  # type: ignore[union-attr]
    return process


def run_lcm_logger(output_file: Path) -> Popen[bytes]:  # pragma: no cover
    # Remove any pre-existing output
    if output_file.exists():
        output_file.unlink()
    return Popen(
        ['lcm-logger', '--lcm-url=tcpq://', '-q', output_file.as_posix()],
        start_new_session=True,
    )


def run_lcm_logplayer(logfile: Path) -> Popen[bytes]:  # pragma: no cover
    return Popen(
        ['lcm-logplayer', '--lcm-url=tcpq://', '--speed=1000', logfile.as_posix()],
        start_new_session=True,
    )


def run_pntos_with_log_transport(
    app: Path,
    args: list[str] | None = None,
    validate: bool = False,
) -> None:  # pragma: no cover
    """Spin up app, process log, then shut down.

    Args:
        app (pathlib.Path): Path to app to run.
        args (list[str] | None): Optional command-line arguments to pass to app (e.g. output log).
        validate (bool): Whether to validate the app's output, ensuring there are no
            warnings or errors. Defaults to False.
    """
    # initialize process variables to avoid possibly unbound errors
    app_process = None

    try:
        app_process = run_app(app, args, validate=validate)

        # Wait until pntOS is done processing the LCM log
        done_msg = 'Done processing LCM log. Press Ctrl + C to shut down pntOS.'
        assert app_process.stdout is not None
        monitor_app_output(app_process.stdout, validate=validate, wait_for_msg=done_msg)

        # Continue to forward app output to stdout
        monitor_app_output(app_process.stdout, separate_thread=True)

    finally:
        if app_process is not None:
            kill(app_process)


def run_pntos_with_network_transport(
    app: Path,
    input_log: Path,
    output_log: Path,
    args: list[str] | None = None,
    validate: bool = False,
) -> None:  # pragma: no cover
    """Spin up app and network tools necessary to run it, process log, then shut down.

    Args:
        app (pathlib.Path): Path to app to run.
        input_log (pathlib.Path): LCM log containing the measurements to be processed.
        output_log (pathlib.Path): LCM log to which output should be recorded.
        args (list[str] | None): Optional command-line arguments to pass to app.
        validate (bool): Whether to validate the app's output, ensuring there are no
            warnings or errors. Defaults to False.
    """

    # initialize process variables to avoid possibly unbound errors
    relay_process = None
    logger_process = None
    logplayer_process = None
    app_process = None

    try:
        relay_process = run_tcp_relay()
        logger_process = run_lcm_logger(output_log)
        app_process = run_app(app, args, monitor=True, validate=validate)

        # wait for cobra to connect to TCP relay
        for line in relay_process.stdout:  # type: ignore[union-attr]
            # wait for at least 2 clients to be connected (cobra and LCM logger)
            if re.search(r'[2-9] clients', line):
                break

        # play log. note that logplayer process automatically terminates at end of log
        logplayer_process = run_lcm_logplayer(input_log)

        # Wait until data is no longer being recorded to output log
        wait_until_file_stable(output_log, stable_secs=5)

    finally:
        if app_process is not None:
            kill(app_process)
        if logger_process is not None:
            kill(logger_process)
        if logplayer_process is not None:
            kill(logplayer_process)
        if relay_process is not None:
            kill(relay_process)
