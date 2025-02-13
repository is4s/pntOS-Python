from typing import List

import aspn23_xtensor
import numpy as np
from aspn23 import (
    AspnBase,
    MeasurementImu,
    MeasurementImuImuType,
    MeasurementPositionVelocityAttitude,
    MeasurementPositionVelocityAttitudeErrorModel,
    MeasurementPositionVelocityAttitudeReferenceFrame,
    TypeHeader,
    TypeTimestamp,
)
from navtk.inertial import BufferedImu, ImuErrors

from pntos.api import (
    InertialForcesRates,
    InertialFrame,
    InertialPlugin,
    InertialSolutionRangeType,
    InertialType,
    LoggingLevel,
    Mediator,
    Message,
    StandardInertialErrors,
    StandardInertialMechanization,
)

# from .config.utils import config_from_registry
from pntos.cobra.config import InertialConfig, config_from_registry


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


class SimpleInertial(StandardInertialMechanization):
    inertial: BufferedImu
    mediator: Mediator
    identifier: str = 'Cobra simple inertial'

    def __init__(self, config_group: str, mediator: Mediator, solution: Message):
        if not isinstance(
            solution.wrapped_message, MeasurementPositionVelocityAttitude
        ):
            self.mediator.log_message(
                LoggingLevel.ERROR,
                'Message must be of type MeasurementPositionVelocityAttitude.',
            )
            return
        self.mediator = mediator

        config = config_from_registry(InertialConfig, mediator, config_group)
        if config is None:
            self.mediator.log_message(
                LoggingLevel.ERROR,
                'Unable to retrieve config from registry.',
            )
            return

        self.inertial = BufferedImu(
            convert_pva_to_cpp(solution.wrapped_message),
            expected_dt=config.expected_dt,
            buffer_length=config.inertial_buffer_length,
        )

    def request_solution_message_type(self) -> type[AspnBase]:
        return MeasurementPositionVelocityAttitude

    def request_current_solution(self) -> Message:
        return Message(
            convert_pva_from_cpp(
                self.inertial.calc_pva(
                    convert_timestamp_to_cpp(self.request_latest_time())
                )
            ),
            self.identifier,
        )

    def request_solution(self, time: TypeTimestamp) -> Message | None:
        return Message(
            convert_pva_from_cpp(
                self.inertial.calc_pva(convert_timestamp_to_cpp(time))
            ),
            self.identifier,
        )

    def request_solutions(
        self, times: List[TypeTimestamp], type: InertialSolutionRangeType
    ) -> List[Message] | None:
        if len(times) == 0:
            return None
        solutions = []
        first_time = convert_timestamp_to_cpp(times[0])
        for time in times:
            cpp_time = convert_timestamp_to_cpp(time)
            if type == InertialSolutionRangeType.INERTIAL_BEST_KNOWN_SOLUTION:
                pva = self.inertial.calc_pva(cpp_time)
            elif type == InertialSolutionRangeType.INERTIAL_NO_UPDATES_WITHIN_RANGE:
                pva = self.inertial.calc_pva_no_reset_since(cpp_time, first_time)
            solutions.append(Message(convert_pva_from_cpp(pva), self.identifier))
        return solutions

    def is_time_in_range(self, time: TypeTimestamp) -> bool:
        return self.inertial.in_range(convert_timestamp_to_cpp(time))

    def request_earliest_time(self) -> TypeTimestamp:
        return convert_timestamp_from_cpp(self.inertial.time_span()[0])

    def request_latest_time(self) -> TypeTimestamp:
        return convert_timestamp_from_cpp(self.inertial.time_span()[1])

    def request_process_pntos_message_types(self) -> List[type[AspnBase]]:
        return [MeasurementImu]

    def process_pntos_message(self, message: Message) -> None:
        if isinstance(message.wrapped_message, MeasurementImu):
            imu_cpp = convert_imu_to_cpp(message.wrapped_message)
            self.inertial.add_data(imu_cpp)
        else:
            self.mediator.log_message(
                LoggingLevel.ERROR,
                'Message must be of type MeasurementImu.',
            )

    def request_forces_and_rates(
        self, time: TypeTimestamp
    ) -> InertialForcesRates | None:
        time_cpp = convert_timestamp_to_cpp(time)
        forces_and_rates_cpp = self.inertial.calc_force_and_rate(time_cpp)
        forces_and_rates = convert_imu_from_cpp(forces_and_rates_cpp)
        return InertialForcesRates(forces_and_rates, InertialFrame.INERTIAL_FRAME_NED)

    def request_average_forces_and_rates(
        self, time1: TypeTimestamp, time2: TypeTimestamp
    ) -> InertialForcesRates | None:
        time1_cpp = convert_timestamp_to_cpp(time1)
        time2_cpp = convert_timestamp_to_cpp(time2)
        forces_and_rates_cpp = self.inertial.calc_force_and_rate(time1_cpp, time2_cpp)
        forces_and_rates = convert_imu_from_cpp(forces_and_rates_cpp)
        return InertialForcesRates(forces_and_rates, InertialFrame.INERTIAL_FRAME_NED)

    def request_reset_message_types(self) -> List[type[AspnBase]] | None:
        return [MeasurementPositionVelocityAttitude]

    def reset_solution(self, message: Message) -> None:
        if isinstance(message.wrapped_message, MeasurementPositionVelocityAttitude):
            pva = convert_pva_to_cpp(message.wrapped_message)
            self.inertial.reset(pva)
        else:
            self.mediator.log_message(
                LoggingLevel.ERROR,
                'Message must be of type MeasurementPositionVelocityAttitude.',
            )

    def correct_sensor_errors(
        self, time: TypeTimestamp, errors: StandardInertialErrors
    ) -> None:
        errors_cpp = ImuErrors(
            errors.accel_biases,
            errors.gyro_biases,
            errors.accel_scale_factors,
            errors.gyro_scale_factors,
            convert_timestamp_to_cpp(time),
        )
        self.inertial.reset(imu_errs=errors_cpp)

    def request_sensor_errors(
        self, time: TypeTimestamp
    ) -> StandardInertialErrors | None:
        errors_cpp = self.inertial.get_imu_errors(convert_timestamp_to_cpp(time))
        return StandardInertialErrors(
            errors_cpp.accel_biases,
            errors_cpp.gyro_biases,
            errors_cpp.accel_scale_factors,
            errors_cpp.gyro_scale_factors,
        )


class SimpleInertialPlugin(InertialPlugin):
    mediator: Mediator

    def __init__(self, identifier: str):
        self.identifier = identifier

    def init_plugin(
        self,
        plugin_resources_location: str | None = None,
        mediator: Mediator | None = None,
    ) -> None:
        if mediator is not None:
            self.mediator = mediator
        else:
            print('Error: mediator cannot be None.')

    def shutdown_plugin(self) -> None:
        pass

    def is_inertial_type_supported(self, inertial_type: type[InertialType]) -> bool:
        return issubclass(inertial_type, StandardInertialMechanization)

    def new_inertial(
        self,
        inertial_type: type[InertialType],
        solution: Message,
        config_group: str | None = None,
    ) -> InertialType | None:
        if config_group is None:
            self.mediator.log_message(
                LoggingLevel.ERROR,
                'config_group is a required parameter for this plugin and cannot be None.',
            )
            return None
        if self.is_inertial_type_supported(inertial_type):
            return SimpleInertial(config_group, self.mediator, solution)
        else:
            self.mediator.log_message(LoggingLevel.ERROR, 'Unsupported type requested.')
            return None
