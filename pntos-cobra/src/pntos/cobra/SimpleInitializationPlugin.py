import numpy as np
from aspn23 import (
    MeasurementPositionVelocityAttitude,
    MeasurementPositionVelocityAttitudeErrorModel,
    MeasurementPositionVelocityAttitudeReferenceFrame,
    TypeHeader,
    TypeTimestamp,
)
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

        # TODO Get values from registry. Set status to failed if it cannot retrieve from registry.
        config = AlignmentConfig.from_registry(mediator, config_group)
        self.solution = Message(self._create_pva(), 'Cobra simple initialization')
        self.imu_errors = None
        self.covariance = None

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

    def _create_pva(self) -> MeasurementPositionVelocityAttitude:
        header = TypeHeader(
            0,
            0,
            0,
            0,
        )
        time = TypeTimestamp(0)
        return MeasurementPositionVelocityAttitude(
            header=header,
            time_of_validity=time,
            reference_frame=MeasurementPositionVelocityAttitudeReferenceFrame.GEODETIC,
            p1=0,
            p2=0,
            p3=0,
            v1=0,
            v2=0,
            v3=0,
            quaternion=np.zeros(4),
            covariance=np.eye(9),
            error_model=MeasurementPositionVelocityAttitudeErrorModel.NONE,
            error_model_params=np.array([]),
            integrity=[],
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
