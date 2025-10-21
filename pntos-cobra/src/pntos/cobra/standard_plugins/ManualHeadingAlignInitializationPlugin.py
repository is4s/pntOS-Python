from navtk.inertial import ManualHeadingAlignment
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
from pntos.cobra.config.ManualHeadingAlignmentConfig import (
    ManualHeadingAlignmentConfig,
)
from pntos.cobra.utils import convert_alignment, convert_message, convert_status


class ManualHeadingAlign(InertialInitializationStrategy):
    """
    Static alignment for an inertial, requiring a user-provided heading.

    This initialization strategy can be used to produce an initial PVA to initialize an inertial
    mechanization. It requires both position and IMU measurements, as well as an initial heading
    provided via config. It is also capable of estimating inertial biases.
    """

    aligner: ManualHeadingAlignment
    mediator: Mediator

    def __init__(self, config_group: str, mediator: Mediator) -> None:
        """
        Args:
            config_group (str): A :class:`pntos.cobra.config.ManualHeadingAlignmentConfig` config group.
            mediator (Mediator): A :class:`pntos.api.Mediator` instance.
        """
        self.mediator = mediator
        config = config_from_registry(
            ManualHeadingAlignmentConfig, mediator, config_group
        )
        if config is None:
            self.mediator.log_message(
                LoggingLevel.ERROR,
                f'Failed to populate config from registry to config type ManualHeadingAlignmentConfig and group {config_group}.',
            )
            return
        imu_model = imu_model_from_config(config.imu_model)

        self.aligner = ManualHeadingAlignment(
            config.heading,
            config.heading_sigma,
            imu_model,
            config.static_time,
        )

    def request_motion_needed(self) -> InitializationMotionNeeded:
        return InitializationMotionNeeded.NO_MOTION

    def request_current_status(self) -> InitializationStatus:
        return convert_status(self.aligner.check_alignment_status(), self.mediator)

    def process_pntos_message(self, message: Message) -> None:
        converted_message = convert_message(message.wrapped_message)
        if converted_message is not None:
            self.aligner.process(converted_message)
        else:
            self.mediator.log_message(LoggingLevel.ERROR, 'Could not convert message')

    def request_solution(self) -> InitialInertialSolution:
        unchecked_solution = self.aligner.get_computed_alignment()
        unchecked_covariance = self.aligner.get_computed_covariance()
        unchecked_imu_errors = self.aligner.get_imu_errors()
        status = convert_status(self.aligner.check_alignment_status(), self.mediator)
        return convert_alignment(
            unchecked_solution, unchecked_covariance, unchecked_imu_errors, status
        )


class ManualHeadingAlignInitializationPlugin(InitializationPlugin):
    """
    A static alignment initialization plugin that provides the :class:`internal.ManualHeadingAlign` strategy.
    """

    mediator: Mediator

    def __init__(self, identifier: str) -> None:
        """
        Cobra Static Alignment Initialization Plugin

        Args:
          identifier: A string identifier uniquely identifying this plugin.
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
            print(f'Error ({self.__class__.__name__}): mediator cannot be None')

    def shutdown_plugin(self) -> None:
        pass

    def is_initialization_type_supported(
        self, initialization_type: type[InitializationType]
    ) -> bool:
        return initialization_type == InertialInitializationStrategy

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
            return ManualHeadingAlign(config_group, self.mediator)
        self.mediator.log_message(LoggingLevel.ERROR, 'Unsupported type requested')
        return None
