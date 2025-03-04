from typing import Callable

import aspn23
import aspn23_lcm
from aspn23_xtensor import TypeTimestamp

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

# dictionary mapping LCM message type to ASPN23 marshaling functions
marshaler_to_lcm: dict[type[Aspn23Measurement], Callable] = {
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
marshaler_from_lcm: dict[type[Aspn23LcmMeasurement], Callable] = {
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
}

# dictionary mapping LCM message fingerprint to message decode function
decoder: dict[bytes, Callable[[bytes], Aspn23LcmMeasurement]] = {}
for aspn23_type in marshaler_from_lcm:
    decoder[aspn23_type._get_packed_fingerprint()] = aspn23_type.decode


def decode_aspn_lcm_msg(data: bytes) -> Aspn23LcmMeasurement | None:
    fingerprint = data[:8]

    if fingerprint not in decoder:
        return None

    decode_func = decoder[fingerprint]
    return decode_func(data)


def marshal_from_lcm(msg: Aspn23LcmMeasurement) -> Aspn23Measurement | None:
    msg_type = type(msg)

    if msg_type not in marshaler_from_lcm:
        return None

    marshal_func = marshaler_from_lcm[msg_type]
    return marshal_func(msg)


def marshal_to_lcm(msg: aspn23.AspnBase) -> Aspn23LcmMeasurement | None:
    msg_type = type(msg)

    if msg_type not in marshaler_to_lcm:
        return None

    marshal_func = marshaler_to_lcm[msg_type]  # type: ignore[index]
    return marshal_func(msg)
