import aspn23_xtensor
import numpy as np
from aspn23 import (
    AspnBase,
    MeasurementImu,
    MeasurementImuImuType,
    MeasurementPosition,
    MeasurementPositionReferenceFrame,
    MeasurementPositionVelocityAttitude,
    MeasurementPositionVelocityAttitudeErrorModel,
    MeasurementPositionVelocityAttitudeReferenceFrame,
    TypeHeader,
    TypeTimestamp,
)
from numpy.typing import NDArray


def convert_header_to_cpp(
    header: TypeHeader, message_type: aspn23_xtensor.AspnMessageType
) -> aspn23_xtensor.TypeHeader:
    """
    Convert from ASPN-Python header to ASPN-C++ header.

    Args:
        header (TypeHeader): The measurement header to convert.
        message_type (aspn23_xtensor.AspnMessageType): The type of measurement from which the ASPN measurement originates.

    Returns:
        aspn23_xtensor.TypeHeader
    """
    return aspn23_xtensor.TypeHeader(
        message_type,
        header.vendor_id,
        header.device_id,
        header.context_id,
        header.sequence_id,
    )


def convert_timestamp_to_cpp(timestamp: TypeTimestamp) -> aspn23_xtensor.TypeTimestamp:
    """
    Convert from ASPN-Python timestamp to ASPN-C++ timestamp.

    Args:
        timestamp (TypeTimestamp): The timestamp to convert.

    Returns:
        aspn23_xtensor.TypeTimestamp
    """
    return aspn23_xtensor.TypeTimestamp(timestamp.elapsed_nsec)


def convert_timestamp_from_cpp(
    timestamp: aspn23_xtensor.TypeTimestamp,
) -> TypeTimestamp:
    """
    Convert from ASPN-C++ timestamp to ASPN-Python timestamp.

    Args:
        timestamp (aspn23_xtensor.TypeTimestamp): The timestamp to convert.

    Returns:
        TypeTimestamp
    """
    return TypeTimestamp(timestamp.get_elapsed_nsec())


def convert_pva_to_cpp(
    pva: MeasurementPositionVelocityAttitude,
) -> aspn23_xtensor.MeasurementPositionVelocityAttitude:
    """
    Convert from ASPN-Python PVA measurement to ASPN-C++ PVA measurement.

    Args:
        pva (MeasurementPositionVelocityAttitude): The pva to convert.

    Returns:
        aspn23_xtensor.MeasurementPositionVelocityAttitude
    """
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
    covariance: NDArray[np.float64] | None = None,
) -> MeasurementPositionVelocityAttitude:
    """
    Convert from ASPN-C++ PVA measurement to ASPN-Python PVA measurement. If ``covariance`` is ``None``,
    this function will use the covariance stored in the ``pva`` parameter.

    Args:
        pva (aspn23_xtensor.MeasurementPositionVelocityAttitude): The pva to convert.
        covariance (NDArray | None): The covariance to associate with the pva measurement.

    Returns:
        MeasurementPositionVelocityAttitude
    """
    header = TypeHeader(
        pva.get_vendor_id(),
        pva.get_device_id(),
        pva.get_context_id(),
        pva.get_sequence_id(),
    )
    time = TypeTimestamp(pva.get_time_of_validity().get_elapsed_nsec())
    if covariance is None:
        covariance = pva.get_covariance()
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
        covariance,
        MeasurementPositionVelocityAttitudeErrorModel.NONE,
        np.array([]),
        [],
    )


def convert_header_from_cpp(header: aspn23_xtensor.TypeHeader) -> TypeHeader:
    """
    Convert from ASPN-C++ header to ASPN-Python header.

    Args:
        header (aspn23_xtensor.TypeHeader): The header to convert.

    Returns:
        TypeHeader
    """
    return TypeHeader(
        header.get_vendor_id(),
        header.get_device_id(),
        header.get_context_id(),
        header.get_sequence_id(),
    )


def convert_imu_type_from_cpp(
    imu_type: aspn23_xtensor.AspnMeasurementImuImuType,
) -> MeasurementImuImuType:
    """
    Convert from ASPN-C++ IMU type to ASPN-Python IMU type. If the type cannot be matched, this function will default and
    return ``MeasurementImuImuType.INTEGRATED``.

    Args:
        imu_type (aspn23_xtensor.AspnMeasurementImuImuType): The IMU type to convert.

    Returns:
        MeasurementImuImuType
    """
    match imu_type:
        case aspn23_xtensor.AspnMeasurementImuImuType.ASPN_MEASUREMENT_IMU_IMU_TYPE_INTEGRATED:
            return MeasurementImuImuType.INTEGRATED
        case aspn23_xtensor.AspnMeasurementImuImuType.ASPN_MEASUREMENT_IMU_IMU_TYPE_SAMPLED:
            return MeasurementImuImuType.SAMPLED
    return MeasurementImuImuType.INTEGRATED


def convert_imu_from_cpp(imu: aspn23_xtensor.MeasurementImu) -> MeasurementImu:
    """
    Convert from ASPN-C++ IMU measurement to ASPN-Python IMU measurement.

    Args:
        imu (aspn23_xtensor.MeasurementImu): The IMU measurement to convert.

    Returns:
        aspn23.MeausurementImu
    """
    header = convert_header_from_cpp(imu.get_header())
    time = convert_timestamp_from_cpp(imu.get_time_of_validity())
    imu_type = convert_imu_type_from_cpp(imu.get_imu_type())
    return MeasurementImu(
        header, time, imu_type, imu.get_meas_accel(), imu.get_meas_gyro(), []
    )


def convert_imu_type_to_cpp(
    imu_type: MeasurementImuImuType,
) -> aspn23_xtensor.AspnMeasurementImuImuType:
    """
    Convert from ASPN-Python IMU type to ASPN-C++ IMU type.

    Args:
        imu_type (MeasurementImuImuType): The IMU type to convert.

    Returns:
        aspn23_xtensor.AspnMeasurementImuImuType
    """
    match imu_type:
        case MeasurementImuImuType.INTEGRATED:
            return aspn23_xtensor.AspnMeasurementImuImuType.ASPN_MEASUREMENT_IMU_IMU_TYPE_INTEGRATED
        case MeasurementImuImuType.SAMPLED:
            return aspn23_xtensor.AspnMeasurementImuImuType.ASPN_MEASUREMENT_IMU_IMU_TYPE_SAMPLED


def convert_imu_to_cpp(imu: MeasurementImu) -> aspn23_xtensor.MeasurementImu:
    """
    Convert from ASPN-Python IMU measurement to ASPN-C++ IMU measurement.

    Args:
        imu (MeasurementImu): The IMU measurement to convert.

    Returns:
        aspn23_xtensor.MeasurementImu
    """
    header = convert_header_to_cpp(
        imu.header, aspn23_xtensor.AspnMessageType.ASPN_MEASUREMENT_IMU
    )
    time = convert_timestamp_to_cpp(imu.time_of_validity)
    imu_type = convert_imu_type_to_cpp(imu.imu_type)
    return aspn23_xtensor.MeasurementImu(
        header, time, imu_type, imu.meas_accel, imu.meas_gyro, []
    )


def convert_reference_frame_to_cpp(
    frame: MeasurementPositionReferenceFrame,
) -> aspn23_xtensor.AspnMeasurementPositionReferenceFrame:
    """
    Convert from ASPN-Python position reference frame to ASPN-C++ position reference frame.

    Args:
        frame (aspn23.MeasurementPositionReferenceFrame): The position reference frame to convert.

    Returns:
        aspn23_xtensor.AspnMeasurementPositionReferenceFrame
    """
    match frame:
        case MeasurementPositionReferenceFrame.ECI:
            return aspn23_xtensor.AspnMeasurementPositionReferenceFrame.ASPN_MEASUREMENT_POSITION_REFERENCE_FRAME_ECI
        case MeasurementPositionReferenceFrame.GEODETIC:
            return aspn23_xtensor.AspnMeasurementPositionReferenceFrame.ASPN_MEASUREMENT_POSITION_REFERENCE_FRAME_GEODETIC


def convert_position_to_cpp(
    position: MeasurementPosition,
) -> aspn23_xtensor.MeasurementPosition:
    """
    Convert from ASPN-Python position measurement to ASPN-C++ position measurement.

    Args:
        position (aspn23.MeasurementPosition): The position measurement to convert.

    Returns:
        aspn23_xtensor.MeasurementPosition
    """
    header = convert_header_to_cpp(
        position.header, aspn23_xtensor.AspnMessageType.ASPN_MEASUREMENT_POSITION
    )
    time = convert_timestamp_to_cpp(position.time_of_validity)
    frame = convert_reference_frame_to_cpp(position.reference_frame)
    latitude = position.term1 if position.term1 is not None else float('nan')
    longitude = position.term2 if position.term2 is not None else float('nan')
    altitude = position.term3 if position.term3 is not None else float('nan')
    return aspn23_xtensor.MeasurementPosition(
        header,
        time,
        frame,
        latitude,
        longitude,
        altitude,
        position.covariance,
        aspn23_xtensor.AspnMeasurementPositionErrorModel.ASPN_MEASUREMENT_POSITION_ERROR_MODEL_NONE,
        np.array([]),
        [],
    )


def convert_message(message: AspnBase) -> aspn23_xtensor.TypeHeader | None:
    """
    Convert from ASPN-Python message to ASPN-C++ message. Currently only supports ``MeasurementImu`` and ``aspn23.MeasurementPosition`` messages.

    Args:
        message (AspnBase): The message to convert.

    Returns:
        aspn23_xtensor.TypeHeader | None
    """
    if isinstance(message, MeasurementImu):
        return convert_imu_to_cpp(message)
    if isinstance(message, MeasurementPosition):
        return convert_position_to_cpp(message)
    # Support more types as-needed.
    return None
