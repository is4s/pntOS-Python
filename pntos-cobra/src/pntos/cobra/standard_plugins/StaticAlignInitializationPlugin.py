from navtk.inertial import StaticAlignment
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
)
from pntos.cobra.config import config_from_registry, imu_model_from_config
from pntos.cobra.config.StaticAlignmentConfig import (
    StaticAlignmentConfig,
)
from pntos.cobra.utils import convert_alignment, convert_message, convert_status
from typing_extensions import override


class StaticAlign(InertialInitializationStrategy):
    """
    Static alignment for an inertial.

    This initialization strategy can be used to produce an initial PVA to initialize an inertial
    mechanization. It requires position and IMU data, performing gyrocompassing to estimate an
    initial attitude from the IMU data. It does not estimate initial inertial errors.
    """

    aligner: StaticAlignment
    mediator: Mediator

    def __init__(self, config_group: str, mediator: Mediator) -> None:
        """
        Args:
            config_group (str): A :class:`pntos.cobra.config.StaticAlignmentConfig` config group.
            mediator (Mediator): A :class:`pntos.api.Mediator` instance.
        """
        self.mediator = mediator
        config = config_from_registry(StaticAlignmentConfig, mediator, config_group)
        if config is None:
            self.mediator.log_message(
                LoggingLevel.ERROR,
                f'Failed to populate config from registry to config type StaticAlignmentConfig and group {config_group}.',
            )
            return
        imu_model = imu_model_from_config(config.imu_model)
        self.aligner = StaticAlignment(imu_model, config.static_time)

    @override
    def request_motion_needed(self) -> InitializationMotionNeeded:
        return InitializationMotionNeeded.NO_MOTION

    @override
    def request_current_status(self) -> InitializationStatus:
        return convert_status(self.aligner.check_alignment_status(), self.mediator)

    @override
    def process_pntos_message(self, message: Message) -> None:
        converted_message = convert_message(message.wrapped_message)
        if converted_message is not None:
            self.aligner.process(converted_message)
        else:
            self.mediator.log_message(LoggingLevel.ERROR, 'Could not convert message')

    @override
    def request_solution(self) -> InitialInertialSolution:
        unchecked_solution = self.aligner.get_computed_alignment()
        unchecked_covariance = self.aligner.get_computed_covariance()
        unchecked_imu_errors = self.aligner.get_imu_errors()
        status = convert_status(self.aligner.check_alignment_status(), self.mediator)
        return convert_alignment(
            unchecked_solution, unchecked_covariance, unchecked_imu_errors, status
        )


class StaticAlignInitializationPlugin(InitializationPlugin):
    """
    A static alignment initialization plugin that provides the :class:`internal.StaticAlign` strategy.
    """

    mediator: Mediator

    def __init__(self, identifier: str) -> None:
        """
        Cobra Static Alignment Initialization Plugin

        Args:
          identifier: A string identifier uniquely identifying this plugin.
        """
        self.identifier = identifier

    @override
    def init_plugin(
        self,
        plugin_resources_location: str | None = None,
        mediator: Mediator | None = None,
    ) -> None:
        if mediator is not None:
            self.mediator = mediator
        else:
            print(f'Error ({self.__class__.__name__}): mediator cannot be None')

    @override
    def shutdown_plugin(self) -> None:
        pass

    @override
    def is_initialization_type_supported(
        self, initialization_type: type[InitializationType]
    ) -> bool:
        return initialization_type == InertialInitializationStrategy

    @override
    def new_initialization_strategy(
        self,
        initialization_type: type[InitializationType],
        config_group: str | None = None,
    ) -> InitializationType | None:
        if config_group is None:
            self.mediator.log_message(
                LoggingLevel.ERROR,
                'config_group is a required parameter for this plugin and cannot be None',
            )
            return None
        if issubclass(initialization_type, InertialInitializationStrategy):
            return StaticAlign(config_group, self.mediator)  # ty:ignore[invalid-return-type]
        self.mediator.log_message(LoggingLevel.ERROR, 'Unsupported type requested')
        return None
