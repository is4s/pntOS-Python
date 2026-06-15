import numpy as np
from aspn23 import (
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
    BufferMode,
    FeedbackConfig,
    MeasurementProcessorConfig,
    PinsonStateBlockConfig,
    PreprocessorConfig,
    StandardOrchestrationConfig,
    StateBlockConfig,
    StreamConfig,
    VirtualStateBlockConfig,
)
from pntos.cobra.config.utils import config_from_registry
from pntos.cobra.utils import (
    ASPN_MESSAGE_TYPE_MAP,
    Cache,
    EstimateWithCovarianceEntry,
    FilterSolutionEntry,
    InertialSolutionEntry,
    SortedPlugins,
    get_best_solution,
    get_dead_reckoning_solution,
    has_valid_time,
    initialization_ready,
    print_message,
    set_up_inertial_mechanization,
    set_up_initializer,
    sort_plugins_dataclass,
    validate_manual_ewc,
    validate_plugins,
)
from scipy.linalg import block_diag


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
    feedback_config: FeedbackConfig | None
    last_feedback_time_ns: int
    fusion_engine: StandardFusionEngine
    measurement_channels: dict[str, list[str]]
    pinson_sb_config: PinsonStateBlockConfig
    alignment_channels: tuple[str, ...]
    inertial_drift_prop_dt: int
    cache: Cache
    vsb_labels: list[str]

    def __init__(self, identifier: str) -> None:
        """
        Args:
            identifier (str): The plugin identifier passed to the
                :meth:`pntos.api.CommonPlugin.identifier` field.
        """
        self.identifier: str = identifier
        self.initialization_state = InitializationStatus.WAITING
        self.init_solution = None
        self.preprocessors = []
        self.measurement_channels = {}
        self.inertial_drift_prop_dt = int(0.1 * 1e9)
        self.cache = Cache()
        self.sb_aux_channels: dict[str, list[str]] = {}
        self.mp_aux_channels: dict[str, list[str]] = {}
        self.vsb_aux_channels: dict[str, list[str]] = {}
        self.needs_inertial_pva: dict[str, bool] = {}
        self.needs_inertial_f_and_r: dict[str, bool] = {}
        self.vsbs_needing_pva: dict[str, list[str]] = {}
        self.vsbs_needing_f_and_r: dict[str, list[str]] = {}
        self.vsb_target_to_source: dict[str, str] = {}

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
            print_message(level, OrchestrationPlugin.__name__, message)  # type: ignore[unreachable]

    def _set_stream_config(
        self,
        registry_stream_config: StreamConfig,
        controller_stream_config: MessageStreamConfig,
    ) -> None:
        """Use stream config from registry to set stream config for controller."""
        if registry_stream_config.default_buffer_mode == BufferMode.SEQUENCED:
            controller_stream_config.sequenced_stream_all(True)
            override_stream_func = controller_stream_config.immediate_stream_add
        else:
            controller_stream_config.immediate_stream_all(True)
            override_stream_func = controller_stream_config.sequenced_stream_add

        # After setting default stream, add any message-type or channel-specific overrides
        override_streams = registry_stream_config.override_streams
        if override_streams is None:
            return
        for stream in override_streams:
            message_type = ASPN_MESSAGE_TYPE_MAP[stream.message_type]
            override_stream_func(
                message_type=message_type, source_identifier=stream.source_identifier
            )

    def init_orchestration_plugin(
        self, plugins: list[CommonPlugin] | None, stream_config: MessageStreamConfig
    ) -> None:
        if plugins is None:
            self._log(
                LoggingLevel.ERROR,
                'No plugins were provided. Filter cannot be implemented.',
            )
            return

        # Grab orchestration and controller configs
        orch_config = config_from_registry(
            StandardOrchestrationConfig,
            self.mediator,
            StandardOrchestrationConfig.group,
        )
        if orch_config is None:
            self._log(
                LoggingLevel.ERROR,
                'Unable to grab the orchestration config from the registry. Filter cannot be implemented.',
            )
            return

        self._set_stream_config(orch_config.stream_config, stream_config)

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
            orch_config.additional_sb_configs,
            orch_config.mp_configs,
            orch_config.vsb_configs,
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
            self._send_inertial_aux_to_pinson()

    def _set_up_preprocessors(
        self,
        sorted_plugins: SortedPlugins,
        preprocessor_configs: tuple[PreprocessorConfig, ...],
    ) -> list[Preprocessor]:
        """
        Finds and creates a list of preprocessors based on the information from ``preprocessor_configs``.

        Args:
            sorted_plugins (SortedPlugins): A `SortedPlugins` instance.
            preprocessor_configs (tuple[PreprocessorConfig, ...]):

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
        assert self.init_solution.solution is not None

    def _store_config_data(
        self,
        orch_config: StandardOrchestrationConfig,
    ) -> None:
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
        self.publish_before_update = orch_config.publish_before_update
        self.publish_after_update = orch_config.publish_after_update
        # Alignment
        self.alignment_channels = orch_config.alignment_channels
        # Inertial
        self.inertial_channels = orch_config.inertial_config.channels
        self.inertial_group = orch_config.inertial_config.group
        self.max_prop_dt_ns = int(orch_config.max_prop_interval * 1e9)
        self.buffer_time_ns = int(orch_config.max_filter_lag * 1e9)
        self.feedback_config = orch_config.feedback_config

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
        self.last_feedback_time_ns = init_time.elapsed_nsec

        self.cache.set(
            'inertial solution',
            InertialSolutionEntry(
                self.fusion_engine,
                self.inertial,
                self.imu_sol_channel,
                self.mediator.log_message,
            ),
        )
        self.cache.set(
            'pinson',
            EstimateWithCovarianceEntry(
                self.fusion_engine, self.pinson_sb_config.label
            ),
        )
        self.cache.set(
            'filter solution',
            FilterSolutionEntry(
                self.fusion_engine,
                self.best_sol_channel,
                'inertial solution',
                'pinson',
            ),
        )

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

                if sb_config.aux_channels is not None:
                    for channel in sb_config.aux_channels:
                        sb_map = self.sb_aux_channels.setdefault(channel, [])
                        sb_map.append(sb_config.label)

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
                    list(mp_config.state_block_labels),
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

                self.needs_inertial_pva[mp_config.label] = False
                self.needs_inertial_f_and_r[mp_config.label] = False
                if mp_config.aux_channels is not None:
                    for channel in mp_config.aux_channels:
                        mp_map = self.mp_aux_channels.setdefault(channel, [])
                        mp_map.append(mp_config.label)

                        if channel == 'INERTIAL_PVA':
                            self.needs_inertial_pva[mp_config.label] = True
                        elif channel == 'INERTIAL_FORCES_AND_RATES':
                            self.needs_inertial_f_and_r[mp_config.label] = True

    def _add_virtual_state_block(
        self,
        providers: list[StandardStateModelProvider],
        vsb_config: VirtualStateBlockConfig,
    ) -> None:
        """
        Utility function to add a virtual state block to the fusion engine.
        """
        for provider in providers:
            vsb_ids = provider.virtual_block_identifiers
            if vsb_ids is None:
                continue
            if vsb_config.identifier in vsb_ids:
                vsb = provider.new_virtual_block(
                    vsb_ids.index(vsb_config.identifier),
                    vsb_config.source,
                    vsb_config.target,
                    vsb_config.group,
                )
                if vsb is None:
                    self._log(
                        LoggingLevel.ERROR,
                        f'Unable to create virtual state block "{vsb_config.identifier}" from config group "{vsb_config.group}" - cannot set up fusion engine or initialize filter.',
                    )
                    return
                self.fusion_engine.add_virtual_state_block(vsb)

                self.needs_inertial_pva[vsb_config.target] = False
                self.needs_inertial_f_and_r[vsb_config.target] = False
                self.vsb_target_to_source[vsb_config.target] = vsb_config.source
                if vsb_config.aux_channels is not None:
                    for channel in vsb_config.aux_channels:
                        vsb_map = self.vsb_aux_channels.setdefault(channel, [])
                        vsb_map.append(vsb_config.target)

                        if channel == 'INERTIAL_PVA':
                            self.needs_inertial_pva[vsb_config.target] = True
                        elif channel == 'INERTIAL_FORCES_AND_RATES':
                            self.needs_inertial_f_and_r[vsb_config.target] = True

    def _map_vsb_inertial_needs(
        self, mp_configs: tuple[MeasurementProcessorConfig, ...]
    ) -> None:
        """
        Utility function that maps measurement processor labels to VSB labels
        that need forces and rates or the inertial PVA prior to performing a
        filter update using this measurement processor.
        """
        for mp_config in mp_configs:
            sb_labels = mp_config.state_block_labels

            needs_pva = []
            needs_fnr = []
            for label in sb_labels:
                # Get VSBs that need inertial aux before performing an update with this
                # MP. Note that this may not just include VSBs that the MP directly
                # targets, but any VSB in a chain of source->target labels, where the MP
                # updates the last VSB in this chain.
                cur_vsb_label: str | None = label
                while cur_vsb_label is not None:
                    if self.needs_inertial_pva.get(cur_vsb_label):
                        needs_pva.append(cur_vsb_label)
                    if self.needs_inertial_f_and_r.get(cur_vsb_label):
                        needs_fnr.append(cur_vsb_label)

                    # Get source label
                    cur_vsb_label = self.vsb_target_to_source.get(cur_vsb_label)

            self.vsbs_needing_pva[mp_config.label] = needs_pva
            self.vsbs_needing_f_and_r[mp_config.label] = needs_fnr

    def _set_up_fusion_engine(
        self,
        sb_configs: tuple[StateBlockConfig, ...] | None,
        mp_configs: tuple[MeasurementProcessorConfig, ...] | None,
        vsb_configs: tuple[VirtualStateBlockConfig, ...] | None,
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
                if mp_config.channel not in self.measurement_channels:
                    self.measurement_channels[mp_config.channel] = []
                self.measurement_channels[mp_config.channel].append(mp_config.label)

        if vsb_configs is not None:
            for vsb_config in vsb_configs:
                self._add_virtual_state_block(providers, vsb_config)

        # must be called after blocks and processors have been added
        if mp_configs is not None:
            self._map_vsb_inertial_needs(mp_configs)

    def _create_state_block_ewc(
        self,
        state_block_id: str,
        num_states: int,
        ewc: EstimateWithCovariance | None = None,
    ) -> EstimateWithCovariance | None:
        # use alignment for pinson if manual is not provided
        if (
            state_block_id == 'pinson15'
            and ewc is None
            and self.init_pinson_cov is not None
        ):
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
            for out_message in tmp_list:
                new_messages = preprocessor.process_pntos_message(out_message)
                if new_messages is not None:
                    out_list.extend(new_messages)

        if len(out_list) > 0:
            return out_list
        return None

    def _propagate_to_time(self, target_time: TypeTimestamp) -> None:
        """Propagate up to target time in max steps of self.max_prop_dt_ns"""
        filter_time = self.fusion_engine.time
        while filter_time.elapsed_nsec < target_time.elapsed_nsec:
            self._send_inertial_aux_to_pinson()
            prop_time = TypeTimestamp(filter_time.elapsed_nsec + self.max_prop_dt_ns)
            if target_time.elapsed_nsec < prop_time.elapsed_nsec:
                prop_time = target_time

            self.fusion_engine.propagate(prop_time)
            filter_time = prop_time

    def _publish_solution(self, solution: Message | None, group: str, key: str) -> None:
        """Publish solution to registry and over transport."""
        if solution is None:
            return

        kv = self.mediator.registry.batch_start(group)
        kv[key] = solution
        kv.batch_end()

        self.mediator.broadcast_aspn_message(solution, None, solution.source_identifier)

    def _get_inertial_forces(
        self, t1: TypeTimestamp | None = None, t2: TypeTimestamp | None = None
    ) -> Message | None:
        """Get inertial foces at the current filter time."""
        t1 = (
            self.fusion_engine.time
            if t1 is None
            else max(
                t1, self.inertial.request_earliest_time(), key=lambda t: t.elapsed_nsec
            )
        )
        t2 = (
            self.fusion_engine.time
            if t2 is None
            else min(
                t2, self.inertial.request_latest_time(), key=lambda t: t.elapsed_nsec
            )
        )
        if t1 == t2:
            self._inertial_forces = self.inertial.request_forces_and_rates(t1)
        else:
            self._inertial_forces = self.inertial.request_average_forces_and_rates(
                t1, t2
            )
        if self._inertial_forces is None:
            self.mediator.log_message(
                LoggingLevel.ERROR,
                f'Cannot get inertial aux. Forces not available spanning time [{t1.elapsed_nsec / 1e9:.9f}, {t2.elapsed_nsec / 1e9:.9f}]',
            )
            return None
        return Message(
            self._inertial_forces.forces_and_rates, 'Orchestration forces and rates'
        )

    def _send_inertial_aux_to_measurement_processor(self, mp_label: str) -> None:
        """Send the current inertial solution and/or forces to the specified measurement processor."""
        needs_pva = self.needs_inertial_pva[mp_label]
        needs_forces = self.needs_inertial_f_and_r[mp_label]
        if not needs_pva and not needs_forces:
            return

        aux: list[Message | None] = []

        if needs_pva:
            pva = self.cache.get('inertial solution')
            aux.append(pva)
        if needs_forces:
            filter_time = self.fusion_engine.time
            t1 = TypeTimestamp(filter_time.elapsed_nsec - 500_000_000)
            t2 = TypeTimestamp(filter_time.elapsed_nsec + 500_000_000)
            forces = self._get_inertial_forces(t1, t2)
            aux.append(forces)

        self.fusion_engine.give_measurement_processor_aux_data(mp_label, aux)

    def _send_inertial_aux_to_pinson(self) -> None:
        """
        Send the current inertial solution, forces, and rates to the pinson state block.
        """
        pva = self.cache.get('inertial solution')
        forces = self._get_inertial_forces()
        aux: list[Message | None] = [pva, forces]
        self.fusion_engine.give_state_block_aux_data(self.pinson_sb_config.label, aux)

    def _send_inertial_aux_to_vsbs(self, mp_label: str) -> None:
        """
        Send the current inertial solution, forces, and/or rates to any virtual blocks targeted by the given measurement processor that need it.
        """
        needs_pva = self.vsbs_needing_pva[mp_label]
        needs_forces = self.vsbs_needing_f_and_r[mp_label]
        if not needs_pva and not needs_forces:
            return

        if needs_pva:
            pva = self.cache.get('inertial solution')
            for vsb_label in needs_pva:
                self.fusion_engine.give_virtual_state_block_aux_data(vsb_label, [pva])
        if needs_forces:
            forces = self._get_inertial_forces()
            for vsb_label in needs_forces:
                self.fusion_engine.give_virtual_state_block_aux_data(
                    vsb_label, [forces]
                )

    def _ready_to_apply_feedback(self) -> bool:
        if self.feedback_config is None:
            return True

        surpassed_time_threshold = True
        surpassed_error_threshold = True

        if self.feedback_config.time_threshold:
            time_since_last_feedback = (
                self.fusion_engine.time.elapsed_nsec - self.last_feedback_time_ns
            ) * 1e-9
            surpassed_time_threshold = (
                time_since_last_feedback >= self.feedback_config.time_threshold
            )

        if self.feedback_config.pos_error_threshold:
            pinson_x_and_p: EstimateWithCovariance = self.cache.get('pinson')
            surpassed_error_threshold = np.any(  # type: ignore[assignment]
                np.abs(pinson_x_and_p.estimate[:3])
                >= self.feedback_config.pos_error_threshold
            )

        return surpassed_time_threshold and surpassed_error_threshold

    def _apply_inertial_feedback(self) -> None:
        """Correct inertial solution with pinson error states and reset states."""
        if not self._ready_to_apply_feedback():
            return

        solution = self.cache.get('filter solution')
        if solution is None:
            return

        self.inertial.reset_solution(solution)

        cur_time = self.fusion_engine.time
        imu_errors = self.inertial.request_sensor_errors(cur_time)
        if imu_errors is None:
            self.mediator.log_message(
                LoggingLevel.ERROR,
                f'Unable to obtain sensor errors from inertial at time {cur_time.elapsed_nsec / 1e9:.9f}s.',
            )
            return

        pinson_x_and_p: EstimateWithCovariance = self.cache.get('pinson')
        imu_errors.accel_biases -= pinson_x_and_p.estimate[9:12, 0]
        imu_errors.gyro_biases -= pinson_x_and_p.estimate[12:15, 0]
        self.inertial.correct_sensor_errors(cur_time, imu_errors)

        # Assume zero error in states after applying feedback
        self.fusion_engine.set_state_block_estimate(
            self.pinson_sb_config.label, np.zeros((15, 1))
        )

        # Inertial reset modified the solution at the current time, invalidating the
        # cached solution
        self.cache.clear('inertial solution')
        self.last_feedback_time_ns = cur_time.elapsed_nsec

    def _perform_measurement_update(self, message: Message, target_mp: str) -> None:
        """
        Send message to the fusion engine to update the filter.

        After performing update, applies feedback to inertial solution and biases, and
        resets pinson error states.
        """
        # Make sure measurement processor has most current aux data before update
        self._send_inertial_aux_to_measurement_processor(target_mp)
        self._send_inertial_aux_to_vsbs(target_mp)

        if self.publish_before_update:
            self._publish_solution(
                self.cache.get('inertial solution'),
                group='inertial solution',
                key='before feedback',
            )
            self._publish_solution(
                self.cache.get('filter solution'),
                group='filter solution',
                key='before update',
            )

        # Update filter.
        self.fusion_engine.update(target_mp, message)

        # Filter update modified the pinson states and filter solution at the current
        # time, invalidating the cached solution.
        self.cache.clear('filter solution')
        self.cache.clear('pinson')

        self._apply_inertial_feedback()

        if self.publish_after_update:
            self._publish_solution(
                self.cache.get('inertial solution'),
                group='inertial solution',
                key='after feedback',
            )
            self._publish_solution(
                self.cache.get('filter solution'),
                group='filter solution',
                key='after update',
            )

    def _propagate_during_outage(self) -> None:
        if initialization_ready(self.initialization_state, self.initializer):
            earliest_time = self.inertial.request_earliest_time()
            latest_time = self.inertial.request_latest_time()
            prop_time = TypeTimestamp(
                earliest_time.elapsed_nsec + self.inertial_drift_prop_dt
            )
            if prop_time.elapsed_nsec < latest_time.elapsed_nsec - self.buffer_time_ns:
                self._propagate_to_time(prop_time)
            else:
                self._propagate_to_time(earliest_time)

    def _send_message_as_aux_data(self, message: Message) -> None:
        channel = message.source_identifier
        if channel in self.sb_aux_channels:
            sb_labels = self.sb_aux_channels[channel]
            for label in sb_labels:
                self.fusion_engine.give_state_block_aux_data(label, [message])

        if channel in self.mp_aux_channels:
            mp_labels = self.mp_aux_channels[channel]
            for label in mp_labels:
                self.fusion_engine.give_measurement_processor_aux_data(label, [message])

        if channel in self.vsb_aux_channels:
            vsb_labels = self.vsb_aux_channels[channel]
            for label in vsb_labels:
                self.fusion_engine.give_virtual_state_block_aux_data(label, [message])

    def process_pntos_message(self, message: Message, sequenced: bool) -> None:
        preprocessed_messages = self._preprocess_message(message)
        if preprocessed_messages is None:
            # Message dropped in preprocessing
            return

        for msg in preprocessed_messages:
            channel = msg.source_identifier

            # If filter solution is not initialized, send messages to the initializer.
            if not initialization_ready(self.initialization_state, self.initializer):
                if channel in self.alignment_channels:
                    self.initializer.process_pntos_message(msg)
                    if initialization_ready(
                        self.initialization_state, self.initializer
                    ):
                        self._generate_initial_inertial_solution()
                        self._initialize_filter()
                        self._send_inertial_aux_to_pinson()
                continue

            # Don't use old, out-of-date messages
            if not has_valid_time(
                self.init_solution, self.fusion_engine, message, self._log
            ):
                continue

            # If aligned, send messages to IMU or filter
            if channel in self.inertial_channels:
                self.inertial.process_pntos_message(message)
            elif target_mps := self.measurement_channels.get(channel):
                time = msg.wrapped_message.time_of_validity  # type: ignore[attr-defined]
                self._propagate_to_time(time)
                for mp in target_mps:
                    self._perform_measurement_update(msg, mp)
            # Send message to any MPs or SBs that require it as aux data
            if (
                channel in self.sb_aux_channels
                or channel in self.mp_aux_channels
                or channel in self.vsb_aux_channels
            ):
                self._send_message_as_aux_data(msg)

        # Continue to propagate filter during outage
        self._propagate_during_outage()

    @property
    def filter_description_list(self) -> list[str]:
        descriptions = []
        aspn_pva = 'ASPN_MEASUREMENT_POSITION_VELOCITY_ATTITUDE_ESTIMATE'
        for label in ['POS_INS']:
            for solution_type in ['BEST', 'DEAD_RECKONING']:
                descriptions += [f'{label}_{solution_type}_{aspn_pva}']

        return descriptions

    def request_solutions(
        self,
        solution_times: list[TypeTimestamp],
        filter_description: str | None = None,
    ) -> list[Message | None] | None:
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
                self.mediator.log_message,
            )

        elif 'DEAD_RECKONING' in filter_description:
            solution_out = get_dead_reckoning_solution(
                self.inertial, time, self.imu_sol_channel, self.mediator.log_message
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
