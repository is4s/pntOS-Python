import numpy as np
from aspn23 import (
    MeasurementPositionVelocityAttitude,
    MeasurementPositionVelocityAttitudeErrorModel,
    MeasurementPositionVelocityAttitudeReferenceFrame,
    TypeHeader,
    TypeTimestamp,
)
from navtk.navutils import rpy_to_quat
from numpy.typing import NDArray

from pntos.api import (
    InertialInitializationStrategy,
    InitialInertialSolution,
    InitializationMotionNeeded,
    InitializationPlugin,
    InitializationStatus,
    InitializationType,
    LoggingLevel,
    Mediator,
    Message,
    StandardInertialErrors,
)
from pntos.cobra.config import (
    config_from_registry,
)
from pntos.cobra.config.AlignmentConfig import AlignmentConfig


class SimpleInitialization(InertialInitializationStrategy):
    config_group: str
    mediator: Mediator
    status: InitializationStatus
    solution: Message | None
    imu_errors: StandardInertialErrors | None
    covariance: NDArray[np.float64] | None

    def __init__(self, config_group: str, mediator: Mediator):
        self.config_group = config_group
        self.mediator = mediator
        config = config_from_registry(AlignmentConfig, mediator, config_group)
        if config is None:
            self.mediator.log_message(
                LoggingLevel.ERROR,
                f'Failed to populate config from registry to config type AlignmentConfig and group {config_group}',
            )
            return
        self.solution = Message(self._create_pva(config), 'Cobra simple initialization')
        self.imu_errors = self._create_imu_errors(config)
        self.covariance = np.diag(
            np.concatenate(
                (
                    np.array(config.initial_accel_bias_var),
                    np.array(config.initial_gyro_bias_var),
                    np.zeros(3),
                    np.zeros(3),
                )
            )
        )

        self.status = InitializationStatus.INITIALIZED_GOOD

    def request_motion_needed(self) -> InitializationMotionNeeded:
        return InitializationMotionNeeded.ANY_MOTION

    def request_current_status(self) -> InitializationStatus:
        return self.status

    def process_pntos_message(self, message: Message) -> None:
        self.mediator.log_message(
            LoggingLevel.WARN, 'process_pntos_message is unused, discarding message'
        )

    def request_solution(self) -> InitialInertialSolution:
        return InitialInertialSolution(
            solution=self.solution,
            inertial_errors=self.imu_errors,
            inertial_error_covariance=self.covariance,
            status=self.status,
        )

    def _create_pva(
        self, config: AlignmentConfig
    ) -> MeasurementPositionVelocityAttitude:
        header = TypeHeader(
            0,
            0,
            0,
            0,
        )
        time = TypeTimestamp(int(config.initial_time * 1000000000))
        initial_position_variances = np.array(config.initial_pos_var)
        initial_velocity_variances = np.array(config.initial_vel_var)
        initial_tilt_variances = np.array(config.initial_tilt_var)
        initial_variances = np.concatenate(
            (
                initial_position_variances,
                initial_velocity_variances,
                initial_tilt_variances,
            )
        )
        initial_covariance = np.diag(initial_variances)
        return MeasurementPositionVelocityAttitude(
            header=header,
            time_of_validity=time,
            reference_frame=MeasurementPositionVelocityAttitudeReferenceFrame.GEODETIC,
            p1=config.initial_pos[0],
            p2=config.initial_pos[1],
            p3=config.initial_pos[2],
            v1=config.initial_vel[0],
            v2=config.initial_vel[1],
            v3=config.initial_vel[2],
            quaternion=rpy_to_quat(np.array(config.initial_rpy)),
            covariance=initial_covariance,
            error_model=MeasurementPositionVelocityAttitudeErrorModel.NONE,
            error_model_params=np.array([]),
            integrity=[],
        )

    def _create_imu_errors(self, config: AlignmentConfig) -> StandardInertialErrors:
        return StandardInertialErrors(
            accel_biases=np.array(config.initial_accel_bias),
            gyro_biases=np.array(config.initial_gyro_bias),
            accel_scale_factors=np.zeros((3)),
            gyro_scale_factors=np.zeros((3)),
        )


class SimpleInitializationPlugin(InitializationPlugin):
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
            print('Error: mediator cannot be None')

    def shutdown_plugin(self) -> None:
        return

    def is_initialization_type_supported(self, type: InitializationType) -> bool:
        return type == InertialInitializationStrategy  # type: ignore[no-any-return]

    def new_initialization_strategy(
        self, type: type[InitializationType], config_group: str | None = None
    ) -> InitializationType | None:
        if config_group is None:
            self.mediator.log_message(
                LoggingLevel.ERROR,
                'config_group is a required parameter for this plugin and cannot be None',
            )
            return None
        if issubclass(type, InertialInitializationStrategy):
            return SimpleInitialization(config_group, self.mediator)
        else:
            self.mediator.log_message(LoggingLevel.ERROR, 'Unsupported type requested')
            return None
