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
    StandardFusionEngine,
    StandardFusionStrategy,
    StandardInertialMechanization,
    StandardStateModelProvider,
    StateModelingPlugin,
)
from pntos.cobra.config import (
    MeasurementProcessorConfig,
    PinsonStateBlockConfig,
    PreprocessorConfig,
    StandardOrchestrationConfig,
    StateBlockConfig,
)
from pntos.cobra.config.utils import config_from_registry
from pntos.cobra.utils import (
    SortedPlugins,
    dispatch_to_fusion_engine,
    get_best_solution,
    get_dead_reckoning_solution,
    has_valid_time,
    initialization_ready,
    send_inertial_aux_to_pinson,
    set_up_inertial_mechanization,
    set_up_initializer,
    sort_plugins_dataclass,
    validate_manual_ewc,
    validate_plugins,
)
from scipy.linalg import block_diag

BUFFER_TIME_NSEC = 2_000_000_000  # this value should match the number of seconds that sequenced messages are delayed by in the controller


class StandardOrchestrationPlugin(OrchestrationPlugin):
    """
    The standard orchestration plugin designed to take multiple state blocks and measurement processors.
    """

    mediator: Mediator
    init_solution: InitialInertialSolution | None
    init_pinson_cov: NDArray[float64] | None
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
    pinson_config: PinsonStateBlockConfig
    alignment_channels: list[str]
    inertial_drift_prop_dt: int
    prop_interval: int

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
        self.measurement_channels = {}
        self.inertial_drift_prop_dt = int(0.1 * 1e9)
        self.prop_interval = int(0.25 * 1e9)

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
        Send an informational log message to pntOS.

        If no mediator is provided, manually print the message. Otherwise, pass
        through to the mediator's ``log_message`` method.
        """
        if self.mediator is not None:
            self.mediator.log_message(level, message)
        else:
            print(f'[{self.identifier}] {self.log_level_strings[level]} {message}')  # type: ignore[unreachable]

    def init_orchestration_plugin(
        self, plugins: list[CommonPlugin] | None, stream_config: MessageStreamConfig
    ) -> None:
        stream_config.sequenced_stream_all(True)
        stream_config.immediate_stream_add(MeasurementImu)

        if plugins is None:
            self._log(
                LoggingLevel.ERROR,
                'No plugins were provided. Filter cannot be implemented.',
            )
            return

        # Grab orchestration config
        orch_config = config_from_registry(
            StandardOrchestrationConfig, self.mediator, 'config/orchestration'
        )
        if orch_config is None:
            self._log(
                LoggingLevel.ERROR,
                'Unable to grab the orchestration config from the registry. Filter cannot be implemented.',
            )
            return
        # Store orchestration config fields
        self._store_config_data(orch_config)

        sorted_plugins = sort_plugins_dataclass(plugins)
        if not validate_plugins(
            sorted_plugins,
            self._log,
            fusion_plugins=(1, 1),
            fusion_strategy_plugins=(1, 1),
            inertial_plugins=(1, 1),
            initialization_plugins=(1, 1),
            state_modeling_plugins=(1, 1000),
        ):
            return
        self.fusion_plugin = sorted_plugins.fusion_plugins[0]
        self.fusion_strategy_plugin = sorted_plugins.fusion_strategy_plugins[0]
        self.inertial_plugin = sorted_plugins.inertial_plugins[0]
        self.initialization_plugin = sorted_plugins.initialization_plugins[0]
        self.state_modeling_plugins = sorted_plugins.state_modeling_plugins

        # Set up preprocessors
        if orch_config.preprocessor_configs is not None:
            self.preprocessors = self._set_up_preprocessors(
                sorted_plugins, orch_config.preprocessor_configs
            )
        self._set_up_fusion_engine(
            orch_config.additional_sb_configs, orch_config.mp_configs
        )
        initializer = set_up_initializer(
            self.initialization_plugin, orch_config.alignment_config.group, self._log
        )
        if initializer is None:
            return
        self.initializer = initializer

        if initialization_ready(self.initialization_state, self.initializer):
            self._generate_initial_inertial_solution()
            self._initialize_filter()
            send_inertial_aux_to_pinson(
                self.inertial,
                self.fusion_engine,
                self.pinson_sb_config.label,
                self._log,
            )

    def _set_up_preprocessors(
        self,
        sorted_plugins: SortedPlugins,
        preprocessor_configs: list[PreprocessorConfig],
    ) -> list[Preprocessor]:
        """
        Finds and creates a list of preprocessors based on the information from ``preprocessor_configs``.

        Args:
            sorted_plugins (SortedPlugins): A `SortedPlugins` instance.
            preprocessor_configs (list[PreprocessorConfig]):

        Returns:
            list[Preprocessor]
        """
        preprocessors = []
        for config in preprocessor_configs:
            for plugin in sorted_plugins.preprocessor_plugins:
                for idx in range(len(plugin.preprocessor_identifiers)):
                    if plugin.preprocessor_identifiers[idx] == config.identifier:
                        preprocessor = plugin.new_preprocessor(idx, config.group)
                        if preprocessor is not None:
                            preprocessors.append(preprocessor)
        return preprocessors

    def _generate_initial_inertial_solution(self) -> None:
        """Utility function that generates the initial inertial solution."""
        inertial_info = set_up_inertial_mechanization(
            self.initializer,
            self.inertial_plugin,
            self.inertial_group,
            self._log,
        )
        if inertial_info is None:
            return
        self.inertial = inertial_info[0]
        self.init_solution = inertial_info[1]

    def _store_config_data(self, orch_config: StandardOrchestrationConfig) -> None:
        """
        Utility function to store the orchestration config fields in easily accessible data structures.

        Args:
            orch_config (StandardOrchestrationConfig): The ``StandardOrchestrationConfig`` containing the data
                to be stored.
        """
        # Pinson state block
        self.pinson_sb_config = orch_config.pinson_sb_config
        # pntOS Solution
        self.best_sol_channel = orch_config.best_sol_channel
        self.imu_sol_channel = orch_config.imu_sol_channel
        # Alignment
        self.alignment_channels = orch_config.alignment_channels
        # Inertial
        self.inertial_channel = orch_config.inertial_config.channel
        self.inertial_group = orch_config.inertial_config.group

    def _initialize_filter(self) -> None:
        """
        Creates a pinson state block with a covariance calculated during alignment.
        Then adds the block and time to the fusion engine effectively beginning the filter.
        """
        # get pinson covariance
        pva_cov = self.init_solution.solution.wrapped_message.covariance  # type: ignore[union-attr] # 9x9
        bias_cov = self.init_solution.inertial_error_covariance  # type: ignore[union-attr] # 6x6
        self.init_pinson_cov = block_diag(pva_cov, bias_cov)

        # add pinson state block
        providers = []
        for plugin in self.state_modeling_plugins:
            provider: StandardStateModelProvider | None = (
                plugin.new_state_model_provider(StandardStateModelProvider)
            )
            if provider is not None:
                providers.append(provider)

        self._add_state_block(providers, self.pinson_sb_config)

        # sync fusion engine and initial solution time
        init_time = self.init_solution.solution.wrapped_message.time_of_validity  # type: ignore[union-attr]
        self.fusion_engine.time = init_time
        self._log(
            LoggingLevel.INFO, f'Aligned filter at {init_time.elapsed_nsec * 1e-9:.9f}s'
        )

    def _add_state_block(
        self,
        providers: list[StandardStateModelProvider],
        sb_config: StateBlockConfig,
    ) -> None:
        """
        Utility function to add a state block to the fusion engine.
        """
        for provider in providers:
            block_ids = provider.block_identifiers
            if block_ids is None:
                continue
            if sb_config.identifier in block_ids:
                state_block = provider.new_block(
                    block_ids.index(sb_config.identifier),
                    self.fusion_engine,
                    sb_config.label,
                    sb_config.group,
                )
                if state_block is None:
                    self._log(
                        LoggingLevel.ERROR,
                        f'Unable to create state block "{sb_config.label}" with identifier "{sb_config.identifier}"'
                        + f' from config group "{sb_config.group}" - cannot set up fusion engine or initialize filter.',
                    )
                    return
                ewc = self._create_state_block_ewc(
                    sb_config.identifier,
                    state_block.num_states,
                    sb_config.estimate_with_covariance,
                )
                if ewc is None:
                    return
                self.fusion_engine.add_state_block(state_block, ewc, None)

    def _add_measurement_processor(
        self,
        providers: list[StandardStateModelProvider],
        mp_config: MeasurementProcessorConfig,
    ) -> None:
        """
        Utility function to add a measurement processor to the fusion engine.
        """
        for provider in providers:
            mp_ids = provider.processor_identifiers
            if mp_ids is None:
                continue
            if mp_config.identifier in mp_ids:
                processor = provider.new_processor(
                    mp_ids.index(mp_config.identifier),
                    self.fusion_engine,
                    mp_config.label,
                    mp_config.state_block_labels,
                    mp_config.group,
                )
                if processor is None:
                    self._log(
                        LoggingLevel.ERROR,
                        f'Unable to create measurement processor "{mp_config.label}" with identifier "{mp_config.identifier}"'
                        + f' from config group "{mp_config.group}" - cannot set up fusion engine or initialize filter.',
                    )
                    return
                self.fusion_engine.add_measurement_processor(processor)

    def _set_up_fusion_engine(
        self,
        sb_configs: list[StateBlockConfig] | None,
        mp_configs: list[MeasurementProcessorConfig] | None,
    ) -> None:
        """
        Utility function to assemble the components of and create a fusion engine.
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
        fusion_engine.strategy = self.fusion_strategy_plugin.new_fusion_strategy(  # type: ignore[assignment]
            StandardFusionStrategy
        )

        # Store fusion engine
        self.fusion_engine = fusion_engine

        # Create and store state blocks and measurement processors
        providers = []
        for plugin in self.state_modeling_plugins:
            provider: StandardStateModelProvider | None = (
                plugin.new_state_model_provider(StandardStateModelProvider)
            )
            if provider is not None:
                providers.append(provider)

        if sb_configs is not None:
            for sb_config in sb_configs:
                self._add_state_block(providers, sb_config)

        if mp_configs is not None:
            for mp_config in mp_configs:
                self._add_measurement_processor(providers, mp_config)
                # Measurement Channels used in fusion engine
                self.measurement_channels[mp_config.channel] = mp_config.label

    def _create_state_block_ewc(
        self,
        state_block_id: str,
        num_states: int,
        ewc: EstimateWithCovariance | None = None,
    ) -> EstimateWithCovariance | None:
        if state_block_id == 'pinson15':
            # use alignment for pinson if manual is not provided
            if ewc is None and self.init_pinson_cov is not None:
                return EstimateWithCovariance(
                    EstimateWithCovarianceType.EWC_GENERIC,
                    estimate=np.zeros((num_states, 1)),
                    covariance=self.init_pinson_cov,
                )
        if ewc is not None:
            # manual EWC config was provided
            return validate_manual_ewc(ewc, num_states, self.mediator)

        return None

    def _preprocess_message(self, message: Message) -> list[Message] | None:
        """Process the given message by the full chain of preprocessors.

        Args:
            message (Message): The message to process.

        Returns:
            list[Message] | None: The output messages, or None if one of the preprocessors dropped the input message.
        """
        out_list = [message]
        for preprocessor in self.preprocessors:
            if len(out_list) == 0:
                return None
            tmp_list = out_list.copy()
            out_list = []
            for message in tmp_list:
                new_messages = preprocessor.process_pntos_message(message)
                if new_messages is not None:
                    out_list.extend(new_messages)

        if len(out_list) > 0:
            return out_list
        return None

    def _propagate_to_time(self, target_time: TypeTimestamp) -> None:
        filter_time = self.fusion_engine.time
        while filter_time.elapsed_nsec < target_time.elapsed_nsec:
            send_inertial_aux_to_pinson(
                self.inertial,
                self.fusion_engine,
                self.pinson_sb_config.label,
                self._log,
            )
            fixed_prop_interval = filter_time.elapsed_nsec + self.prop_interval
            if target_time.elapsed_nsec < fixed_prop_interval:
                prop_time = target_time
            else:
                prop_time = TypeTimestamp(fixed_prop_interval)
            self.fusion_engine.propagate(prop_time)
            filter_time = prop_time

    def _propagate_during_outage(self) -> None:
        if initialization_ready(self.initialization_state, self.initializer):
            earliest_time = self.inertial.request_earliest_time()
            latest_time = self.inertial.request_latest_time()
            prop_time = TypeTimestamp(
                earliest_time.elapsed_nsec + self.inertial_drift_prop_dt
            )
            if prop_time.elapsed_nsec < latest_time.elapsed_nsec - BUFFER_TIME_NSEC:
                self._propagate_to_time(prop_time)
            else:
                self._propagate_to_time(earliest_time)

    def process_pntos_message(self, message: Message, sequenced: bool) -> None:
        preprocessed_messages = self._preprocess_message(message)
        if preprocessed_messages is None:
            # Message dropped in preprocessing
            return

        for message in preprocessed_messages:
            # If filter solution is not initialized, send messages to the initializer.
            if not initialization_ready(self.initialization_state, self.initializer):
                if message.source_identifier in self.alignment_channels:
                    self.initializer.process_pntos_message(message)
                    if initialization_ready(
                        self.initialization_state, self.initializer
                    ):
                        self._generate_initial_inertial_solution()
                        self._initialize_filter()
                        send_inertial_aux_to_pinson(
                            self.inertial,
                            self.fusion_engine,
                            self.pinson_sb_config.label,
                            self._log,
                        )
                continue
            # Don't use old, out-of-date messages
            if not has_valid_time(
                self.init_solution, self.fusion_engine, message, self._log
            ):
                continue
            # If aligned, send messages to IMU or filter
            if message.source_identifier == self.inertial_channel:
                self.inertial.process_pntos_message(message)
            elif message.source_identifier in self.measurement_channels:
                dispatch_to_fusion_engine(
                    self.inertial,
                    self.fusion_engine,
                    message,
                    self.pinson_sb_config.label,
                    self.measurement_channels,
                    self._log,
                )
        # Continue to propagate filter during outage
        self._propagate_during_outage()

    @property
    def filter_description_list(self) -> list[str]:
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
        if (
            not initialization_ready(self.initialization_state, self.initializer)
            or self.init_solution is None
        ):
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
                self.fusion_engine,
                self.inertial,
                time,
                self.pinson_sb_config.label,
                self.best_sol_channel,
                self._log,
            )

        elif 'DEAD_RECKONING' in filter_description:
            solution_out = get_dead_reckoning_solution(
                self.inertial, time, self.imu_sol_channel, self._log
            )

        else:
            descriptions = ', '.join(self.filter_description_list)
            self._log(
                LoggingLevel.ERROR,
                f'Solution {filter_description} was requested, but available solution '
                + f'types are: {descriptions}',
            )
            return None

        if solution_out is None:
            return None
        return [solution_out]
