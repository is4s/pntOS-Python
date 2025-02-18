import aspn23_xtensor
import numpy as np
from aspn23 import (
    MeasurementImu,
    MeasurementImuImuType,
    MeasurementPositionVelocityAttitude,
    MeasurementPositionVelocityAttitudeErrorModel,
    MeasurementPositionVelocityAttitudeReferenceFrame,
    TypeHeader,
    TypeTimestamp,
)


def convert_header_to_cpp(
    header: TypeHeader, message_type: aspn23_xtensor.AspnMessageType
) -> aspn23_xtensor.TypeHeader:
    return aspn23_xtensor.TypeHeader(
        message_type,
        header.vendor_id,
        header.device_id,
        header.context_id,
        header.sequence_id,
    )


def convert_timestamp_to_cpp(timestamp: TypeTimestamp) -> aspn23_xtensor.TypeTimestamp:
    return aspn23_xtensor.TypeTimestamp(timestamp.elapsed_nsec)


def convert_timestamp_from_cpp(
    timestamp: aspn23_xtensor.TypeTimestamp,
) -> TypeTimestamp:
    return TypeTimestamp(timestamp.get_elapsed_nsec())


def convert_pva_to_cpp(
    pva: MeasurementPositionVelocityAttitude,
) -> aspn23_xtensor.MeasurementPositionVelocityAttitude:
    header = aspn23_xtensor.TypeHeader(
        aspn23_xtensor.AspnMessageType.ASPN_MEASUREMENT_POSITION_VELOCITY_ATTITUDE,
        pva.header.vendor_id,
        pva.header.device_id,
        pva.header.context_id,
        pva.header.sequence_id,
    )
    time = aspn23_xtensor.TypeTimestamp(pva.time_of_validity.elapsed_nsec)
    p1 = pva.p1 if pva.p1 is not None else float('nan')
    p2 = pva.p2 if pva.p2 is not None else float('nan')
    p3 = pva.p3 if pva.p3 is not None else float('nan')
    v1 = pva.v1 if pva.v1 is not None else float('nan')
    v2 = pva.v2 if pva.v2 is not None else float('nan')
    v3 = pva.v3 if pva.v3 is not None else float('nan')
    quaternion = pva.quaternion if pva.quaternion is not None else np.array([])
    return aspn23_xtensor.MeasurementPositionVelocityAttitude(
        header,
        time,
        aspn23_xtensor.AspnMeasurementPositionVelocityAttitudeReferenceFrame.ASPN_MEASUREMENT_POSITION_VELOCITY_ATTITUDE_REFERENCE_FRAME_GEODETIC,
        p1,
        p2,
        p3,
        v1,
        v2,
        v3,
        quaternion,
        pva.covariance,
        aspn23_xtensor.AspnMeasurementPositionVelocityAttitudeErrorModel.ASPN_MEASUREMENT_POSITION_VELOCITY_ATTITUDE_ERROR_MODEL_NONE,
        np.array([]),
        [],
    )


def convert_pva_from_cpp(
    pva: aspn23_xtensor.MeasurementPositionVelocityAttitude,
) -> MeasurementPositionVelocityAttitude:
    header = TypeHeader(
        pva.get_vendor_id(),
        pva.get_device_id(),
        pva.get_context_id(),
        pva.get_sequence_id(),
    )
    time = TypeTimestamp(pva.get_time_of_validity().get_elapsed_nsec())
    return MeasurementPositionVelocityAttitude(
        header,
        time,
        MeasurementPositionVelocityAttitudeReferenceFrame.GEODETIC,
        pva.get_p1(),
        pva.get_p2(),
        pva.get_p3(),
        pva.get_v1(),
        pva.get_v2(),
        pva.get_v3(),
        pva.get_quaternion(),
        pva.get_covariance(),
        MeasurementPositionVelocityAttitudeErrorModel.NONE,
        np.array([]),
        [],
    )


def convert_header_from_cpp(header: aspn23_xtensor.TypeHeader) -> TypeHeader:
    return TypeHeader(
        header.get_vendor_id(),
        header.get_device_id(),
        header.get_context_id(),
        header.get_sequence_id(),
    )


def convert_imu_type_from_cpp(
    imu_type: aspn23_xtensor.AspnMeasurementImuImuType,
) -> MeasurementImuImuType:
    match imu_type:
        case aspn23_xtensor.AspnMeasurementImuImuType.ASPN_MEASUREMENT_IMU_IMU_TYPE_INTEGRATED:
            return MeasurementImuImuType.INTEGRATED
        case aspn23_xtensor.AspnMeasurementImuImuType.ASPN_MEASUREMENT_IMU_IMU_TYPE_SAMPLED:
            return MeasurementImuImuType.SAMPLED
    return MeasurementImuImuType.INTEGRATED


def convert_imu_from_cpp(imu: aspn23_xtensor.MeasurementImu) -> MeasurementImu:
    header = convert_header_from_cpp(imu.get_header())
    time = convert_timestamp_from_cpp(imu.get_time_of_validity())
    imu_type = convert_imu_type_from_cpp(imu.get_imu_type())
    return MeasurementImu(
        header, time, imu_type, imu.get_meas_accel(), imu.get_meas_gyro(), []
    )


def convert_imu_type_to_cpp(
    imu_type: MeasurementImuImuType,
) -> aspn23_xtensor.AspnMeasurementImuImuType:
    match imu_type:
        case MeasurementImuImuType.INTEGRATED:
            return aspn23_xtensor.AspnMeasurementImuImuType.ASPN_MEASUREMENT_IMU_IMU_TYPE_INTEGRATED
        case MeasurementImuImuType.SAMPLED:
            return aspn23_xtensor.AspnMeasurementImuImuType.ASPN_MEASUREMENT_IMU_IMU_TYPE_SAMPLED


def convert_imu_to_cpp(imu: MeasurementImu) -> aspn23_xtensor.MeasurementImu:
    header = convert_header_to_cpp(
        imu.header, aspn23_xtensor.AspnMessageType.ASPN_MEASUREMENT_IMU
    )
    time = convert_timestamp_to_cpp(imu.time_of_validity)
    imu_type = convert_imu_type_to_cpp(imu.imu_type)
    return aspn23_xtensor.MeasurementImu(
        header, time, imu_type, imu.meas_accel, imu.meas_gyro, []
    )
