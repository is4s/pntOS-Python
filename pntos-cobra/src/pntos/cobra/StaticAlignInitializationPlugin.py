from navtk.inertial import AlignBase, ManualHeadingAlignment, StaticAlignment
from navtk.utils import to_positionvelocityattitude

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
from pntos.cobra.config.StaticAlignmentConfig import (
    AlignmentStrategy,
    StaticAlignmentConfig,
)
from pntos.cobra.utils import convert_message, convert_pva_from_cpp


class StaticAlign(InertialInitializationStrategy):
    """
    Static alignment for an inertial.

    This initialization strategy can be used to produce an initial PVA to initialize an inertial
    mechanization. It supports two algorithms; see AlignmentStrategy for more info on each.
    """

    aligner: AlignBase
    mediator: Mediator

    def __init__(self, config_group: str, mediator: Mediator):
        self.mediator = mediator
        config = config_from_registry(StaticAlignmentConfig, mediator, config_group)
        if config is None:
            self.mediator.log_message(
                LoggingLevel.ERROR,
                f'Failed to populate config from registry to config type StaticAlignmentConfig and group {config_group}.',
            )
            return
        imu_model = imu_model_from_config(config.imu_model)
        if config.strategy == AlignmentStrategy.STATIC:
            self.aligner = StaticAlignment(imu_model, config.static_time)
        elif config.strategy == AlignmentStrategy.MANUAL_HEADING:
            heading_config = config_from_registry(
                ManualHeadingAlignmentConfig, mediator, config_group
            )
            if heading_config is None:
                self.mediator.log_message(
                    LoggingLevel.ERROR,
                    f'Failed to populate config from registry to config type ManualHeadingAlignmentConfig and group {config_group}.',
                )
                return
            self.aligner = ManualHeadingAlignment(
                heading_config.heading,
                heading_config.heading_sigma,
                imu_model,
                config.static_time,
            )

    def request_motion_needed(self) -> InitializationMotionNeeded:
        return InitializationMotionNeeded.NO_MOTION

    def request_current_status(self) -> InitializationStatus:
        return self._convert_status(self.aligner.check_alignment_status())

    def process_pntos_message(self, message: Message) -> None:
        converted_message = convert_message(message.wrapped_message)
        if converted_message is not None:
            self.aligner.process(converted_message)
        else:
            self.mediator.log_message(LoggingLevel.ERROR, 'Could not convert message')

    def request_solution(self) -> InitialInertialSolution:
        unchecked_solution = self.aligner.get_computed_alignment()
        unchecked_covariance = self.aligner.get_computed_covariance()
        message = None
        if unchecked_solution[0]:
            navtk_solution = unchecked_solution[1]
            pva_cpp = to_positionvelocityattitude(navtk_solution)
            pva_covariance = None
            if unchecked_covariance[0]:
                pva_covariance = unchecked_covariance[1][0:9, 0:9]
            pva = convert_pva_from_cpp(pva_cpp, pva_covariance)
            message = Message(pva, 'Cobra initializer')
        covariance = None
        if unchecked_covariance[0]:
            covariance = unchecked_covariance[1][9:15, 9:15]
        unchecked_imu_errors = self.aligner.get_imu_errors()
        imu_errors = None
        if unchecked_imu_errors[0]:
            imu_errors = unchecked_imu_errors[1]
        return InitialInertialSolution(
            solution=message,
            inertial_errors=imu_errors,
            inertial_error_covariance=covariance,
            status=self._convert_status(self.aligner.check_alignment_status()),
        )

    def _convert_status(
        self, status: AlignBase.AlignmentStatus
    ) -> InitializationStatus:
        match status:
            case AlignBase.AlignmentStatus.ALIGNING_COARSE:
                return InitializationStatus.INITIALIZING_COARSE
            case AlignBase.AlignmentStatus.ALIGNING_FINE:
                return InitializationStatus.INITIALIZING_FINE
            case AlignBase.AlignmentStatus.ALIGNED_GOOD:
                return InitializationStatus.INITIALIZED_GOOD
        self.mediator.log_message(
            LoggingLevel.ERROR, 'Could not convert alignment status'
        )
        return InitializationStatus.INITIALIZATION_FAILED


class StaticAlignInitializationPlugin(InitializationPlugin):
    """
    InitializationPlugin that provides a InertialInitializationStrategy.
    """

    mediator: Mediator

    def __init__(self, identifier: str):
        """
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

    def shutdown_plugin(self):
        self.mediator = None

    def is_initialization_type_supported(self, type: InitializationType) -> bool:
        return type == InertialInitializationStrategy

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
            return StaticAlign(config_group, self.mediator)
        else:
            self.mediator.log_message(LoggingLevel.ERROR, 'Unsupported type requested')
            return None
