import numpy as np
from aspn23 import (
    MeasurementImu,
    MeasurementPositionVelocityAttitude,
    MeasurementVelocity,
    MeasurementVelocityReferenceFrame,
)
from numpy import float64
from numpy.typing import NDArray
from pntos.api.plugins.common import (
    EstimateWithCovariance,
    LoggingLevel,
    Mediator,
    Message,
)
from pntos.api.plugins.state_modeling import (
    StandardMeasurementModel,
    StandardMeasurementProcessor,
)
from pntos.cobra.utils import (
    OMEGA_E,
    meridian_radius,
    north_to_delta_lat,
    quat_to_dcm,
    skew,
    transverse_radius,
)


class PinsonBodyVelocityMeasurementProcessor(StandardMeasurementProcessor):
    """
    Generates a model that maps a velocity measurement in the body/sensor frame
    to an inertial error states block.
    """

    _mediator: Mediator
    _inertial_pva: MeasurementPositionVelocityAttitude | None
    _l_ps_p: NDArray[float64]
    _orientation_ps_p: NDArray[float64]

    def __init__(
        self,
        label: str,
        state_block_labels: list[str],
        mediator: Mediator,
        l_ps_p: NDArray[float64],
        orientation_ps_p: NDArray[float64],
    ):
        """
        A Pinson Body/Sensor Velocity Measurement Processor

        Args:
            label (str): Name of processor.
            state_block_labels (list[str]): A 1-element list of labels of state blocks this
                processor can update. The single entry should refer to a Pinson-style
                state block where the first (or only) 15 states must be the same as Pinson15NedBlock.
            mediator (Mediator): a Mediator instance
            l_ps_p (NDArray[float64]): A 3-element array representing the lever arm from the
                platform frame origin to the velocity sensor origin, in the platform frame, in
                units of meters.
            orientation_ps_p (NDArray[float64]): A 4-element quaternion representing the rotational
                difference from the sensor frame to the platform frame. The corresponding DCM would
                be C_sensor_to_platform.
        """
        self.label = label
        self.state_block_labels = state_block_labels
        self._mediator = mediator
        self._l_ps_p = l_ps_p
        self._orientation_ps_p = orientation_ps_p

    def receive_aux_data(self, aux: list[Message]) -> None:
        if not aux:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'PinsonBodyVelocityMeasurementProcessor expected aux data of type MeasurementPositionVelocityAttitude, but received empty list.',
            )
            return

        if len(aux) < 2:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'PinsonBodyVelocityMeasurementProcessor expected two aux messages: MeasurementPositionVelocityAttitude and MeasurementImu, but received {len(aux)} aux messages.',
            )
            return

        if len(aux) > 2:
            self._mediator.log_message(
                LoggingLevel.DEBUG,
                f'PinsonBodyVelocityMeasurementProcessor expected two aux messages: MeasurementPositionVelocityAttitude and MeasurementImu, but received {len(aux)} aux messages. Ignoring all except the first two messages.',
            )

        if not isinstance(aux[0].wrapped_message, MeasurementPositionVelocityAttitude):
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'PinsonBodyVelocityMeasurementProcessor expected aux[0] data of type MeasurementPositionVelocityAttitude, but got message of type {type(aux[0].wrapped_message)}.',
            )
            return

        pva = aux[0].wrapped_message

        if pva.quaternion is None:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'PinsonBodyVelocityMeasurementProcessor received PVA aux data with no quaternion at time {pva.time_of_validity.elapsed_nsec / 1e9}s.',
            )
            return

        self._inertial_pva = pva

        if not isinstance(aux[1].wrapped_message, MeasurementImu):
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'PinsonBodyVelocityMeasurementProcessor expected aux[1] data of type MeasurementImu but got message of type {type(aux[1].wrapped_message)}.',
            )
            return

        self._force_and_rate_aux = aux[1].wrapped_message

    def generate_model(
        self, message: Message, x_and_p: EstimateWithCovariance
    ) -> StandardMeasurementModel | None:
        if not isinstance(message.wrapped_message, MeasurementVelocity):
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'PinsonBodyVelocityMeasurementProcessor expected message of type MeasurementVelocity, but got message of type {type(message.wrapped_message)}. Cannot process message.',
            )
            return None

        vel = message.wrapped_message
        time = vel.time_of_validity
        if self._inertial_pva is None:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'PinsonBodyVelocityMeasurementProcessor cannot process message at time {time.elapsed_nsec / 1e9:.9f}s as it has not received inertial PVA aux data.',
            )
            return None

        pva_aux_time = self._inertial_pva.time_of_validity
        if abs(pva_aux_time.elapsed_nsec - time.elapsed_nsec) > 1000:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'PinsonBodyVelocityMeasurementProcessor cannot process message at time {time.elapsed_nsec / 1e9:.9f}s as inertial PVA aux data is at a different time (t={pva_aux_time.elapsed_nsec / 1e9:.9f}s).',
            )
            return None

        if vel.reference_frame is not MeasurementVelocityReferenceFrame.SENSOR:
            self._mediator.log_message(
                LoggingLevel.ERROR,
                f'PinsonBodyVelocityMeasurementProcessor expected MeasurementVelocity with a reference frame of {MeasurementVelocityReferenceFrame.SENSOR}, but got measurement at time {time.elapsed_nsec / 1e9:.9f}s with a reference frame of {vel.reference_frame}. Cannot process message.',
            )
            return None

        x = x_and_p.estimate
        num_states = x.shape[0]
        inertial_vel = np.array(
            [
                self._inertial_pva.v1,
                self._inertial_pva.v2,
                self._inertial_pva.v3,
            ]
        )

        C_sensor_to_platform = quat_to_dcm(self._orientation_ps_p)
        C_platform_to_sensor = C_sensor_to_platform.T

        # Correct inertial att
        assert self._inertial_pva.quaternion is not None
        uncorr_C_ned_to_imu = quat_to_dcm(self._inertial_pva.quaternion).T
        att_error = x[6:9, 0]
        corr_C_ned_to_imu = uncorr_C_ned_to_imu @ (np.eye(3) + skew(att_error))

        C_ned_to_sensor = C_platform_to_sensor @ corr_C_ned_to_imu

        # Correct inertial vel
        uncorr_C_ned_to_sensor = C_platform_to_sensor @ uncorr_C_ned_to_imu
        inertial_vel_error = x[3:6, 0]
        corr_inertial_vel_ned = inertial_vel + inertial_vel_error

        C_ned_to_sensor_der = -uncorr_C_ned_to_sensor @ skew(corr_inertial_vel_ned)

        z = np.array([[vel.x], [vel.y], [vel.z]])
        H = np.zeros((3, num_states))
        H[:, 3:6] = C_ned_to_sensor
        H[:, 6:9] = C_ned_to_sensor_der

        def h(x: NDArray[float64]) -> NDArray[float64]:
            assert self._inertial_pva is not None and self._inertial_pva.p1 is not None

            # Apply tangential velocity correction (due to rotation about the inertial frame) if any element in the body velocity is non-zero
            tan_vel_sensor = np.zeros(3)
            rotation_rate = self._force_and_rate_aux.meas_gyro
            alt = self._inertial_pva.p3 - x[2, 0]
            lat = self._inertial_pva.p1 + north_to_delta_lat(
                x[0, 0], self._inertial_pva.p1, alt
            )

            # Get gyro bias from state vector otherwise set to zeros
            gyro_bias = x[12:15, 0] if num_states >= 15 else np.zeros(3)

            if np.any(z):
                tan_vel_sensor = self._calc_tan_vel(
                    lat,
                    alt,
                    corr_inertial_vel_ned,
                    rotation_rate,
                    corr_C_ned_to_imu,
                    C_platform_to_sensor,
                    self._l_ps_p,
                    gyro_bias,
                )
            inertial_vel_sensor = C_ned_to_sensor @ corr_inertial_vel_ned
            # Compute estimated sensor velocity in the sensor frame
            sensor_vel_sensor: NDArray[float64] = (
                inertial_vel_sensor + tan_vel_sensor
            ).reshape(3, 1)

            return sensor_vel_sensor

        R = vel.covariance

        return StandardMeasurementModel(z, h, H, R)

    def _calc_tan_vel(
        self,
        lat: float,
        alt: float,
        vel_ned: NDArray[float64],
        rotation_rate: NDArray[float64],
        C_ned_to_platform: NDArray[float64],
        C_platform_to_sensor: NDArray[float64],
        lever_arm: NDArray[float64],
        gyro_bias: NDArray[float64],
    ) -> NDArray[float64]:
        """
        Utility function to calculate tangential velocities for corrections

        Args:
            lat (float): Latitude (rads).
            alt (float): Altitude (m).
            vel_ned (NDArray[float64]): NED velocities (m/s).
            rotation_rate (NDArray[float64]): Rotation rates from IMU gyro (rad/s).
            C_ned_to_platform (NDArray[float64]): DCM converting NED to platform frame.
            C_platfrom_to_sensor (NDArray[float64]): DCM converting platfrom to sensor frame.
            lever_arm (NDArray[float64]): A 3-element array representing the lever arm from the
                platform frame origin to the velocity sensor origin, in the platform frame (m).
            gyro_bias (NDArray[float64]): Current estimate of gyro bias (rad/s).
        """
        rn = meridian_radius(lat)
        re = transverse_radius(lat)
        w_en_n = np.array(
            [
                vel_ned[1] / (re + alt),
                -vel_ned[0] / (rn + alt),
                -vel_ned[1] * np.tan(lat) / (re + alt),
            ]
        )
        w_ie_n = np.array(
            [
                OMEGA_E * np.cos(lat),
                0.0,
                -OMEGA_E * np.sin(lat),
            ]
        )
        # Remove remaining biases (additive error states), earth and transport rates
        rotation_rate = (
            rotation_rate + gyro_bias - C_ned_to_platform @ (w_ie_n - w_en_n)
        )
        tan_vel_imu = np.cross(rotation_rate, lever_arm)
        return C_platform_to_sensor @ tan_vel_imu
