from aspn23 import (
    AspnBase,
    MeasurementImu,
    MeasurementPositionVelocityAttitude,
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
from pntos.cobra.utils import (
    convert_imu_from_cpp,
    convert_imu_to_cpp,
    convert_pva_from_cpp,
    convert_pva_to_cpp,
    convert_timestamp_from_cpp,
    convert_timestamp_to_cpp,
)


class StandardInertial(StandardInertialMechanization):
    """
    An inertial object which mechanizes IMU data to generate a series of inertial solutions.
    """

    inertial: BufferedImu
    mediator: Mediator
    identifier: str = 'Cobra standard inertial'

    def __init__(
        self, config_group: str, mediator: Mediator, solution: Message
    ) -> None:
        """
        An Inertial Mechanization Object

        Args:
            config_group (str): An :class:`pntos.cobra.config.InertialConfig` config group.
            mediator (Mediator): A :class:`pntos.api.Mediator` instance.
            solution (Message): An initial PVA message required for inertial mechanization.
        """
        self.mediator = mediator
        if not isinstance(
            solution.wrapped_message, MeasurementPositionVelocityAttitude
        ):
            self.mediator.log_message(
                LoggingLevel.ERROR,
                'Message must be of type MeasurementPositionVelocityAttitude.',
            )
            return

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
        p_cpp = self.inertial.calc_pva(convert_timestamp_to_cpp(time))
        if p_cpp:
            return Message(
                convert_pva_from_cpp(p_cpp),
                self.identifier,
            )
        return None

    def request_solutions(
        self, times: list[TypeTimestamp], solution_type: InertialSolutionRangeType
    ) -> list[Message | None] | None:
        if len(times) == 0:
            return None
        solutions: list[Message | None] = []
        first_time = convert_timestamp_to_cpp(times[0])
        for time in times:
            cpp_time = convert_timestamp_to_cpp(time)
            if solution_type == InertialSolutionRangeType.INERTIAL_BEST_KNOWN_SOLUTION:
                pva = self.inertial.calc_pva(cpp_time)
            elif (
                solution_type
                == InertialSolutionRangeType.INERTIAL_NO_UPDATES_WITHIN_RANGE
            ):
                pva = self.inertial.calc_pva_no_reset_since(cpp_time, first_time)
            solutions.append(Message(convert_pva_from_cpp(pva), self.identifier))
        return solutions

    def is_time_in_range(self, time: TypeTimestamp) -> bool:
        return self.inertial.in_range(convert_timestamp_to_cpp(time))

    def request_earliest_time(self) -> TypeTimestamp:
        return convert_timestamp_from_cpp(self.inertial.time_span()[0])

    def request_latest_time(self) -> TypeTimestamp:
        return convert_timestamp_from_cpp(self.inertial.time_span()[1])

    def request_process_pntos_message_types(self) -> list[type[AspnBase]]:
        return [MeasurementImu]

    def process_pntos_message(self, message: Message) -> None:
        if isinstance(message.wrapped_message, MeasurementImu):
            imu_cpp = convert_imu_to_cpp(message.wrapped_message)
            self.inertial.add_data(imu_cpp)
        else:
            self.mediator.log_message(
                LoggingLevel.WARN,
                'Invalid message type received; ignoring it. See '
                'request_process_pntos_message_types() for valid message types.',
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
        if forces_and_rates_cpp is None:
            self.mediator.log_message(  # type: ignore[unreachable] # navtk stubs are incorrect as calc_force_and_rate may return None
                LoggingLevel.WARN,
                f'Requested average force and rate spanning time [{time1.elapsed_nsec / 1e9}, {time2.elapsed_nsec / 1e9}], but inertial only spans [{self.request_earliest_time().elapsed_nsec / 1e9}, {self.request_latest_time().elapsed_nsec / 1e9}]',
            )
            return None
        forces_and_rates = convert_imu_from_cpp(forces_and_rates_cpp)
        return InertialForcesRates(forces_and_rates, InertialFrame.INERTIAL_FRAME_NED)

    def request_reset_message_types(self) -> list[type[AspnBase]] | None:
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


class StandardInertialPlugin(InertialPlugin):
    """
    An inertial plugin that generates instances of the :class:`internal.StandardInertial` class.
    """

    mediator: Mediator | None

    def __init__(self, identifier: str) -> None:
        """
        An Inertial Plugin

        Args:
            identifier (str): The plugin identifier passed to the
                :meth:`pntos.api.CommonPlugin.identifier` field.
        """
        self.identifier = identifier

    def init_plugin(
        self,
        plugin_resources_location: str | None = None,
        mediator: Mediator | None = None,
    ) -> None:
        if mediator is not None:
            self.mediator = mediator
        else:
            self.mediator = None
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
        if self.mediator is None:
            print(
                'Error: mediator is None. '
                + 'StandardInertialPlugin.init_plugin '
                + 'must be called and passed a valid mediator '
                + 'before new_preprocessor.'
            )
            return None
        if config_group is None:
            self.mediator.log_message(
                LoggingLevel.ERROR,
                'config_group is a required parameter for this plugin and cannot be None.',
            )
            return None
        if self.is_inertial_type_supported(inertial_type):
            return StandardInertial(config_group, self.mediator, solution)
        self.mediator.log_message(LoggingLevel.ERROR, 'Unsupported type requested.')
        return None
