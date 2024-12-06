"""Python API of pntOS."""

from dataclasses import dataclass
from enum import Enum
from typing import List, Protocol

from aspn23 import AspnBase, MeasurementImu, TypeTimestamp
from numpy.typing import NDArray

from .common import CommonPlugin, Message


class InertialFrame(Enum):
    """
    An enumeration that specifies frame.

    Caution:
        **Unstable**: This feature is unstable and is not yet considered part of the stable pntOS
        API. Usage of this feature is highly discouraged in non-experimental code, and its
        definition may change at any time.
    """

    INERTIAL_FRAME_NED = 0
    """
    Force vectors in this frame are north-east-down in m/s^2.

	Rotation rate vectors in this frame are of an inertial sensor with respect to inertial frame,
	in the inertial sensor frame (rad/s). Sometimes represented as w_s_is (or w_b_ib if the body
	frame is aligned with the inertial sensor frame.
    """


@dataclass
class InertialForcesRates:
    """
    A struct containing specific forces and rotation rates from the inertial.

    Caution:
        **Unstable**: This feature is unstable and is not yet considered part of the stable pntOS
        API. Usage of this feature is highly discouraged in non-experimental code, and its
        definition may change at any time.

    Attributes:
        forces_and_rates (MeasurementImu): An ASPN IMU message which has been repurposed to hold 
            specific forces (the meas_accel field) and rotation rates (the meas_gyro field) in a 
            different frame (see #frame).
        frame (InertialFrame): Specifies the frame of the above forces and rates.
    """

    forces_and_rates: MeasurementImu
    frame: InertialFrame


@dataclass
class StandardInertialErrors:
    """
    A structure representing the biases on a set of 3-axis gyros and 3-axis accelerometers.

    Caution:
        **Unstable**: This feature is unstable and is not yet considered part of the stable pntOS
        API. Usage of this feature is highly discouraged in non-experimental code, and its
        definition may change at any time.

    Attributes:
        accel_biases (NDArray): A 1D vector of length 3 containing biases for a 3-axis accelerometer
            in the sensor's (X-Y-Z) frame, expressed in m/s^2.
        gyro_biases (NDArray): A 1D vector of length 3 containing biases for a 3-axis gyro in the
            sensor's (X-Y-Z) frame, expressed in rad/s.
        accel_scale_factors (NDArray): A 1D vector of length 3 containing scale factor errors for a
            3-axis accelerometer in the sensor's (X-Y-Z) frame, unitless.
        gyro_scale_factors (NDArray): A 1D vector of length 3 containing scale factor errors for a
            3-axis gyroscope in the sensor's (X-Y-Z) frame, unitless.
    """

    accel_biases: NDArray
    gyro_biases: NDArray
    accel_scale_factors: NDArray
    gyro_scale_factors: NDArray


class InertialSolutionRangeType(Enum):
    """
    Solution type to request from an inertial.

    An enumeration that allows the user to decide if the solution they request is the best available
    solution or one that has no discontinuities in it due to resets.

    Caution:
        **Unstable**: This feature is unstable and is not yet considered part of the stable pntOS
        API. Usage of this feature is highly discouraged in non-experimental code, and its
        definition may change at any time.
    """

    INERTIAL_BEST_KNOWN_SOLUTION = 0
    INERTIAL_NO_UPDATES_WITHIN_RANGE = 1


class CommonInertial(Protocol):
    """
    A common base type for an inertial.

    A user may use the CommonInertial.mechanization_type field to discover what type of
    inertial this type actually is and then downcast to the appropriate inertial class. For example,
    if CommonInertial.mechanization_type is `STANDARD_INERTIAL_MECHANIZATION`, then this
    instance is actually a StandardInertialMechanization.

    Caution:
        **Unstable**: This feature is unstable and is not yet considered part of the stable pntOS
        API. Usage of this feature is highly discouraged in non-experimental code, and its
        definition may change at any time.
    """

    def request_solution_message_type(self) -> type[AspnBase]:
        """
        Get the solution type.

        Return the message type that will be returned by request_current_solution, request_solution,
        and request_solutions.
        """
        pass

    def request_current_solution(self) -> Message:
        """Return the current inertial solution."""
        pass

    def request_solution(self, time: TypeTimestamp) -> Message | None:
        """
        Request solution at a specific time.

        @param time The time at which the returned solution should be valid.

        @return The solution computed by this inertial at `time` if `time` is in the valid range,
        None otherwise (#is_time_in_range can be used to check `time` before calling this method).
        """
        pass

    def request_solutions(
        self, time: List[TypeTimestamp], type: InertialSolutionRangeType
    ) -> List[Message] | None:
        """
        Requests solutions at multiple specific times.

        @param times An array of times at which solutions are requested.
        @param type The type of solution requested.

        @return An array of solutions. Returns None if `type` is unsupported by this inertial or
        every instance of `times` is outside the valid range. Otherwise guaranteed to not be None.
        """
        pass

    def is_time_in_range(self, time: TypeTimestamp) -> bool:
        """
        Check if a solution exists at a given time.

        @param time The query time.

        @return true if a solution exists at `time`, false otherwise. This result is only valid
        until another method (for example, process_pntos_message) is called.

        """
        pass

    def request_earliest_time(self) -> TypeTimestamp:
        """
        Get the earliest available time at which a solution or forces and rates can be requested.

        This result is only valid until another method (for example, process_pntos_message) is
        called.

        """
        pass

    def request_latest_time(self) -> TypeTimestamp:
        """
        Get the latest available time at which a solution or forces and rates can be requested.

        This result is only valid until another method (for example, process_pntos_message) is
        called.

        """
        pass

    def request_process_pntos_message_types(self) -> List[type[AspnBase]]:
        """Returns an array of message types that are supported by this plugin as inputs to #process_pntos_message."""
        pass

    def process_pntos_message(self, message: Message) -> None:
        """A new message to be incorporated into the computed inertial solution."""
        pass

    def request_forces_and_rates(
        self, time: TypeTimestamp
    ) -> InertialForcesRates | None:
        """
        @param time The time at which the forces and rates should be valid.

        @return The instantaneous forces and rates at `time` if `time` is in the valid range, None
        otherwise (#is_time_in_range can be used to check `time` before calling this method).
        """
        pass

    def request_average_forces_and_rates(
        self, time1: TypeTimestamp, time2: TypeTimestamp
    ) -> InertialForcesRates | None:
        """
        Request average forces and rates over a time period.

        @param time1 The start of the time range over which the forces and rates should be valid.
        @param time2 The end of the time range over which the forces and rates should be valid.

        @return The average forces and rates over the period of time defined by `time1` and `time2`
        if at least one of them is in the valid range, None otherwise (#is_time_in_range can be used
        to check both times before calling this method).
        """
        pass


# The external inertial case does not need any extra functionality, so just alias the base class
# rather than inheriting from it and adding nothing.
ExternalInertial = CommonInertial


class StandardInertialMechanization(CommonInertial, Protocol):
    """
    A struct produced by a InertialPlugin. It generates solutions from raw IMU data.

    Caution:
        **Unstable**: This feature is unstable and is not yet considered part of the stable pntOS
        API. Usage of this feature is highly discouraged in non-experimental code, and its
        definition may change at any time.
    """

    def request_reset_message_types(self) -> List[type[AspnBase]] | None:
        """
        Get valid types of reset messages.

        @return An array of message types that are supported by this plugin for resetting the
        inertial solution, or None if resetting the inertial solution is an unsupported operation by
        the inertial plugin.
        """
        pass

    def reset_solution(self, message: Message) -> None:
        """
        Sets the solution to the values in `message`.

        For example, if `message` is PVA then the
        inertial solution will be set to that PVA. If `message` is just position, then only the
        position portion of the inertial solution will be set using `message`.

        @param message A message containing the information necessary to reset the solution. To see
        the types supported by the implementation, call #request_reset_message_types().
        """
        pass

    def correct_sensor_errors(
        self, time: TypeTimestamp, errors: StandardInertialErrors
    ) -> None:
        """
        Reset the current inertial internal bias values.

        Reset the current inertial internal bias values with corrections from an external source,
        such as a filter or error estimator. The errors passed in here will be adjusted for
        internally by the inertial when processing incoming data. Thus, if errors are passed into the
        inertial here they should not be corrected for in an external filter processing the inertial
        output (which would lead to a double correction).

        @param time The time at which `errors` should be valid.
        @param errors An estimate of the inertial sensor's errors.
        """
        pass

    def request_sensor_errors(
        self, time: TypeTimestamp
    ) -> StandardInertialErrors | None:
        """
        @param time Time at which inertial errors should be valid.

        @return Inertial errors at `time` if `time` is in the valid range (is_time_in_range can be
        used to check `time` before calling this method), None otherwise.
        """
        pass


InertialType = StandardInertialMechanization | ExternalInertial


class InertialPlugin(CommonPlugin, Protocol):
    """
    An implementation of an inertial plugin.

    This plugin generates CommonInertial instances which may be used to generate INS solutions
    from raw IMU data.

    Caution:
        **Unstable**: This feature is unstable and is not yet considered part of the stable pntOS
        API. Usage of this feature is highly discouraged in non-experimental code, and its
        definition may change at any time.
    """

    def is_inertial_type_supported(self, type: InertialType) -> bool:
        """Check if the plugin supports a given type of inertial."""
        pass

    def new_inertial(
        self, type: InertialType, solution: Message, config_group: str | None = None
    ) -> CommonInertial | None:
        """
        Create an instance of CommonInertial.

        @param type Specifies the type of inertial that the returned value will support. For
        example, if the user passes in STANDARD_INERTIAL_MECHANIZATION, then the returned
        value will be castable to StandardInertialMechanization. If `type` is unsupported by
        the plugin, then None will be returned. Please use #is_inertial_type_supported to check if
        the type is supported by the plugin.
        @param solution The initial solution (i.e. the alignment) to mechanize from.
        @param config_group An optional parameter which can be used to specify which group in the
        config should be used to initialize the new inertial. This allows for multiple inertial
        instances to exist with unique settings.

        @return A new inertial object. Returns None if `type` is unsupported, `solution` is
        invalid, or `config_group` is invalid. #is_inertial_type_supported can be called to verify
        `type` before calling this method.
        """
