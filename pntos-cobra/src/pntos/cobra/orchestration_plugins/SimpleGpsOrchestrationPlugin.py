import numpy as np
from aspn23 import (
    MeasurementImu,
    TypeTimestamp,
)
from numpy import float64
from numpy.typing import NDArray
from pntos.api import (
    CommonPlugin,
    EstimateWithCovariance,
    EstimateWithCovarianceType,
    FusionPlugin,
    FusionStrategyPlugin,
    InertialInitializationStrategy,
    InertialPlugin,
    InitialInertialSolution,
    InitializationPlugin,
    InitializationStatus,
    LoggingLevel,
    Mediator,
    Message,
    MessageStreamConfig,
    OrchestrationPlugin,
    Preprocessor,
    PreprocessorPlugin,
    StandardFusionEngine,
    StandardFusionStrategy,
    StandardInertialMechanization,
    StandardStateModelProvider,
    StateModelingPlugin,
)
from pntos.cobra.config import InertialConfig, OrchestrationConfig, config_from_registry
from pntos.cobra.config import OrchestrationConfig, config_from_registry

from .orchestration_utils import (
    dispatch_to_fusion_engine,
    generate_initial_inertial_solution,
    get_best_solution,
    get_dead_reckoning_solution,
    has_valid_time,
    initialization_ready,
    rotate_imu_meas,
    set_up_initializer,
    sort_and_validate_plugins,
)

# Solution Channels
BEST_SOL_CHANNEL = '/solution/pntos/best'
IMU_SOL_CHANNEL = '/solution/pntos/imu'

# State block parameters
FOGM_STATE_BLOCK_ID = 'fogm'
FOGM_STATE_BLOCK_LABEL = 'pos_fogm'
FOGM_STATE_BLOCK_CONFIG_GROUP = 'config/pos_sensor_error'

STATE_BLOCK_ID = STATE_BLOCK_LABEL = 'pinson15'
STATE_BLOCK_CONFIG_GROUP = 'config/inertial_state'

# Measurement processor parameters
GPS_MEASUREMENT_PROCESSOR_ID = 'pinson_with_ned_fogm_position'
GPS_MEASUREMENT_PROCESSOR_LABEL = 'gps'
GPS_MEASUREMENT_PROCESSOR_CONFIG_GROUP = 'config/gp3d_state_modeling'
GPS_MP_STATE_BLOCK_LABELS = [STATE_BLOCK_LABEL, FOGM_STATE_BLOCK_LABEL]

# Inertial parameters
INERTIAL_GROUP = 'config/inertial'

# Config groups
ALIGNMENT_CONFIG_GROUP = 'config/default/alignment'
PREPROCESSOR_IDS = ['imu_rotator']
PREPROCESSOR_GROUPS = [INERTIAL_GROUP]


class SimpleGpsOrchestrationPlugin(OrchestrationPlugin):
    mediator: Mediator
    init_solution: InitialInertialSolution | None
    fusion_plugin: FusionPlugin
    fusion_strategy_plugin: FusionStrategyPlugin
    inertial_plugin: InertialPlugin
    state_modeling_plugins: list[StateModelingPlugin]
    preprocessors: list[Preprocessor]
    initialization_plugin: InitializationPlugin
    initialization_state: InitializationStatus
    initializer: InertialInitializationStrategy
    inertial: StandardInertialMechanization
    fusion_engine: StandardFusionEngine
    measurement_channels: dict[str, str]
    alignment_channels: list[str]
    C_inertial_to_platform: NDArray[float64]

    def __init__(self, identifier: str) -> None:
        """
        Simple orchestration plugin.

        Args:
            identifier (str): The plugin identifier passed to the
                :meth:`pntos.api.CommonPlugin.identifier` field.
        """
        self.identifier: str = identifier
        self.log_level_strings: dict[LoggingLevel, str] = {
            LoggingLevel.INFO: 'INFO:',
            LoggingLevel.DEBUG: 'DEBUG:',
            LoggingLevel.ERROR: 'ERROR:',
            LoggingLevel.WARN: 'WARNING:',
        }
        self.initialization_state = InitializationStatus.WAITING
        self.init_solution = None
        self.preprocessors = []

    def init_plugin(
        self,
        plugin_resources_location: str | None = None,
        mediator: Mediator | None = None,
    ) -> None:
        if mediator is None:
            self._log(
                LoggingLevel.ERROR,
                'Orchestration was not handed a mediator. '
                + 'Orchestration will be disabled.',
            )
            return
        self.mediator = mediator

    def shutdown_plugin(self) -> None:
        pass

    def _log(self, level: LoggingLevel, message: str) -> None:
        """
        Send informational log messages to pntOS.

        If no mediator is provided, manually print the messages. Otherwise, pass
        through to the mediator's ``log_message`` method.
        """
        if self.mediator is not None:
            self.mediator.log_message(level, message)
        else:
            print(f'[{self.identifier}] {self.log_level_strings[level]} {message}')  # type: ignore[unreachable]

    def init_orchestration_plugin(
        self, plugins: list[CommonPlugin], stream_config: MessageStreamConfig
    ) -> None:
        stream_config.sequenced_stream_all(True)
        stream_config.immediate_stream_add(MeasurementImu)

        orch_config = config_from_registry(
            OrchestrationConfig, self.mediator, 'config/orchestration'
        )
        inertial_config = config_from_registry(
            InertialConfig, self.mediator, INERTIAL_GROUP
        )

        if orch_config is None or inertial_config is None:
            self._log(
                LoggingLevel.ERROR,
                'Unable to grab the orchestration config from the registry. Filter cannot be implemented.',
            )
            return

        self.measurement_channels = {
            orch_config.gps_channel: GPS_MEASUREMENT_PROCESSOR_LABEL,
        }
        self.alignment_channels = [
            orch_config.gps_channel,
            inertial_config.channel,
        ]
        self.inertial_channel = inertial_config.channel

        sort_and_validate_plugins(self, plugins)

        self._set_up_fusion_engine()
        set_up_initializer(self, ALIGNMENT_CONFIG_GROUP)

        if initialization_ready(self):
            generate_initial_inertial_solution(self, STATE_BLOCK_LABEL, INERTIAL_GROUP)

    def _sort_and_validate_plugins(self, plugin_list: list[CommonPlugin]) -> None:
        """
        Utility function to sort plugins_list and make sure there is only one of the
        following plugins:
        - FusionPlugin
        - FusionStrategyPlugin
        - InertialPlugin
        - InitializationPlugin
        - StateModelingPlugin
        """
        sorted_plugins: SortedPlugins = sort_plugins_dataclass(plugin_list)

        validate_plugins(self, sorted_plugins)

        # Find and store preprocessors
        for identifier, config_group in zip(PREPROCESSOR_IDS, PREPROCESSOR_GROUPS):
            for plugin in sorted_plugins.preprocessor_plugins:
                for idx in range(len(plugin.preprocessor_identifiers)):
                    if plugin.preprocessor_identifiers[idx] == identifier:
                        preprocessor = plugin.new_preprocessor(idx, config_group)
                        if preprocessor is not None:
                            self.preprocessors.append(preprocessor)

    def _set_up_initializer(self) -> None:
        """Set up inertial initialization strategy, and initialize filter solution if initializer is immediately ready."""
        # Set up initializer
        init_strategy: InertialInitializationStrategy | None = (
            self.initialization_plugin.new_initialization_strategy(
                InertialInitializationStrategy, config_group=ALIGNMENT_CONFIG_GROUP
            )
        )
        if init_strategy is None:
            self._log(
                LoggingLevel.ERROR,
                'InertialInitializationStrategy not supported by '
                + f'{self.initialization_plugin}. Unable to continue.',
            )
            return None
        self.initializer = init_strategy

    def _set_up_fusion_engine(self) -> None:
        """
        Utility function to put together the components of the fusion engine.

        Returns:
            :class:`pntos.api.StandardFusionEngine` | None: Returns a functional fusion engine
            with all necessary components, or ``None`` if fusion engine setup fails.
        """
        # Make a fusion engine
        fusion_engine: StandardFusionEngine | None = (
            self.fusion_plugin.new_fusion_engine(StandardFusionEngine)
        )
        if fusion_engine is None:
            self._log(
                LoggingLevel.ERROR,
                'Unable to make new fusion engine - cannot continue.',
            )
            return

        # Give the fusion engine a strategy
        fusion_engine.strategy = self.fusion_strategy_plugin.new_fusion_strategy(
            StandardFusionStrategy
        )

        # Get state blocks and measurement processor
        pinson_block = None
        fogm_block = None
        gps_processor = None
        for plugin in self.state_modeling_plugins:
            provider: StandardStateModelProvider | None = (
                plugin.new_state_model_provider(StandardStateModelProvider)
            )
            if provider is not None:
                if STATE_BLOCK_ID in provider.block_identifiers:
                    pinson_block = provider.new_block(
                        provider.block_identifiers.index(STATE_BLOCK_ID),
                        fusion_engine,
                        STATE_BLOCK_LABEL,
                        STATE_BLOCK_CONFIG_GROUP,
                    )
                if FOGM_STATE_BLOCK_ID in provider.block_identifiers:
                    fogm_block = provider.new_block(
                        provider.block_identifiers.index(FOGM_STATE_BLOCK_ID),
                        fusion_engine,
                        FOGM_STATE_BLOCK_LABEL,
                        FOGM_STATE_BLOCK_CONFIG_GROUP,
                    )
                if GPS_MEASUREMENT_PROCESSOR_ID in provider.processor_identifiers:
                    gps_processor = provider.new_processor(
                        provider.processor_identifiers.index(
                            GPS_MEASUREMENT_PROCESSOR_ID
                        ),
                        fusion_engine,
                        GPS_MEASUREMENT_PROCESSOR_LABEL,
                        GPS_MP_STATE_BLOCK_LABELS,
                        GPS_MEASUREMENT_PROCESSOR_CONFIG_GROUP,
                    )

        # Make state blocks
        if pinson_block is None:
            self._log(
                LoggingLevel.ERROR,
                f'Unable to find state block "{STATE_BLOCK_LABEL}" - cannot initialize filter.',
            )
            return
        ewc = EstimateWithCovariance(
            EstimateWithCovarianceType.EWC_GENERIC,
            estimate=np.zeros((pinson_block.num_states, 1)),
            covariance=np.zeros((pinson_block.num_states, pinson_block.num_states)),
        )
        fusion_engine.add_state_block(pinson_block, ewc, None)

        if fogm_block is None:
            self._log(
                LoggingLevel.WARN,
                f'Unable to find state block "{FOGM_STATE_BLOCK_LABEL}" - continuing.',
            )
        else:
            # TODO how are configuring initial conditions for blocks
            ewc = EstimateWithCovariance(
                EstimateWithCovarianceType.EWC_GENERIC,
                estimate=np.zeros((fogm_block.num_states, 1)),
                covariance=(np.eye(fogm_block.num_states) * 9.0),
            )
            fusion_engine.add_state_block(fogm_block, ewc, None)

        if gps_processor is None:
            assert provider is not None
            self._log(
                LoggingLevel.ERROR,
                f'Unable to find measurement processor "{GPS_MEASUREMENT_PROCESSOR_ID}" -'
                + f' cannot initialize filter. Available measurement processors: {provider.processor_identifiers}',
            )
            return
        fusion_engine.add_measurement_processor(gps_processor)

        self.fusion_engine = fusion_engine

    def _preprocess_message(self, message: Message) -> Message | None:
        """Process the given message by the full chain of preprocessors.

        Note: This function assumes all the preprocessors in the chain will either
        return 0 or 1 messages. Any additional messages will be ignored.

        Args:
            message (Message): The message to process.

        Returns:
            Message | None: The output message, or None if one of the preprocessors dropped the input message.
        """
        for preprocessor in self.preprocessors:
            messages = preprocessor.process_pntos_message(message)
            if not messages:
                return None
            elif len(messages) > 1:
                self._log(
                    LoggingLevel.WARN,
                    f'Preprocessor {preprocessor} returned {len(messages)} messages. Ignoring all but the first.',
                )
            message = messages[0]

        return message

    def process_pntos_message(self, message: Message, sequenced: bool) -> None:
        preprocessed_message = self._preprocess_message(message)
        if not preprocessed_message:
            # Message dropped in preprocessing
            return

        message = preprocessed_message

        if not has_valid_time(self, message):
            return

        # If filter solution is not initialized, send messages to the initializer.
        if not initialization_ready(self):
            if message.source_identifier not in self.alignment_channels:
                return

            self.initializer.process_pntos_message(message)
            if not initialization_ready(self):
                generate_initial_inertial_solution(
                    self, STATE_BLOCK_LABEL, INERTIAL_GROUP
                )
            else:
                return

        # If aligned, send messages to IMU or filter
        if message.source_identifier == self.inertial_channel:
            self.inertial.process_pntos_message(message)
        elif message.source_identifier in self.measurement_channels:
            dispatch_to_fusion_engine(self, message, STATE_BLOCK_LABEL)

    def get_filter_description_list(self) -> list[str]:
        descriptions = []
        aspn_pva = 'ASPN_MEASUREMENT_POSITION_VELOCITY_ATTITUDE_ESTIMATE'
        for label in ['GPS_INS']:
            for solution_type in ['BEST', 'DEAD_RECKONING']:
                descriptions += [f'{label}_{solution_type}_{aspn_pva}']

        return descriptions

    def request_solutions(
        self,
        solution_times: list[TypeTimestamp],
        filter_description: str | None = None,
    ) -> list[Message] | None:
        if not initialization_ready(self) or self.init_solution is None:
            self._log(
                LoggingLevel.DEBUG,
                'Unable to provide a solution - initialization not ready.',
            )
            return None

        if len(solution_times) != 1:
            self._log(
                LoggingLevel.ERROR,
                'This implementation of request_solutions requires a time array'
                + f' of length one but received a time array of length {len(solution_times)}',
            )
            return None

        time = solution_times[0]

        if not self.inertial.is_time_in_range(time):
            latest_time = self.inertial.request_latest_time()
            earliest_time = self.inertial.request_earliest_time()
            self._log(
                LoggingLevel.DEBUG,
                f'Requested time ({time.elapsed_nsec}) is outside inertial '
                + f'time range ({earliest_time.elapsed_nsec} - '
                + f'{latest_time.elapsed_nsec}). Replacing requested time with '
                + 'the latest inertial time.',
            )
            time = latest_time

        if filter_description is None or 'BEST' in filter_description:
            solution_out = get_best_solution(
                self, time, STATE_BLOCK_LABEL, BEST_SOL_CHANNEL
            )

        elif 'DEAD_RECKONING' in filter_description:
            solution_out = get_dead_reckoning_solution(self, time, IMU_SOL_CHANNEL)

        else:
            descriptions = ', '.join(self.get_filter_description_list())
            self._log(
                LoggingLevel.ERROR,
                f'Solution {filter_description} was requested, but available solution '
                + f'types are: {descriptions}',
            )
            return None

        if solution_out is None:
            return None
        return [solution_out]
