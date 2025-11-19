import numpy as np
from aspn23 import (
    MeasurementImu,
    TypeTimestamp,
)
from pntos.api import (
    CommonPlugin,
    EstimateWithCovariance,
    EstimateWithCovarianceType,
    FusionPlugin,
    FusionStrategyPlugin,
    InertialInitializationStrategy,
    InertialPlugin,
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
)
from pntos.cobra.config import (
    InertialConfig,
    TutorialOrchestrationConfig,
    config_from_registry,
)
from pntos.cobra.utils import apply_error_states


class TutorialGpsVelOrchestrationPlugin(OrchestrationPlugin):
    fusion_plugin: FusionPlugin
    fusion_strategy_plugin: FusionStrategyPlugin
    inertial_plugin: InertialPlugin
    preprocessor_time_adjust: Preprocessor
    preprocessor_time_bias: Preprocessor
    preprocessor_imu_rotator: Preprocessor
    mediator: Mediator
    measurement_channels: dict[str, str]
    inertial_channel: str
    fusion_engine: StandardFusionEngine
    inertial: StandardInertialMechanization

    def __init__(self, identifier: str) -> None:
        """
        Tutorial orchestration plugin.

        Args:
            identifier (str): The plugin identifier passed to the
                :meth:`pntos.api.CommonPlugin.identifier` field.
        """
        self.identifier = identifier

    def init_plugin(
        self,
        plugin_resources_location: str | None = None,
        mediator: Mediator | None = None,
    ) -> None:
        self.mediator = mediator

    def shutdown_plugin(self) -> None:
        pass

    def init_orchestration_plugin(
        self, plugins: list[CommonPlugin], stream_config: MessageStreamConfig
    ) -> None:
        stream_config.sequenced_stream_all(enable=True)
        stream_config.immediate_stream_add(message_type=MeasurementImu)

        # This example assumes that this exact list of plugins is sent in this order:
        # FusionPlugin, FusionStrategyPlugin, InertialPlugin, InitializationPlugin, StateModelingPlugin,
        # PreprocessorPlugin
        self.fusion_plugin = plugins[0]
        self.fusion_strategy_plugin = plugins[1]
        self.inertial_plugin = plugins[2]
        self.initialization_plugin = plugins[3]
        self.state_modeling_plugin = plugins[4]

        self._set_up_fusion_engine()

        self._initialize_inertial_and_fusion_engine()

        orch_config = config_from_registry(
            TutorialOrchestrationConfig,
            self.mediator,
            'config/orchestration',
        )

        # Associate incoming channels with measurement processor labels
        self.measurement_channels = {
            orch_config.gps_channel: 'gps',
            orch_config.velocity_channel: 'vel',
        }

        inertial_config = config_from_registry(
            InertialConfig, self.mediator, 'config/inertial'
        )

        self.inertial_channel = inertial_config.channel

        preprocessor_plugin = plugins[5]
        idx = preprocessor_plugin.preprocessor_identifiers.index('time_adjuster')
        self.preprocessor_time_adjust = preprocessor_plugin.new_preprocessor(
            idx, 'config/time_adjuster'
        )
        idx = preprocessor_plugin.preprocessor_identifiers.index('time_bias')
        self.preprocessor_time_bias = preprocessor_plugin.new_preprocessor(
            idx, 'config/time_bias'
        )
        idx = preprocessor_plugin.preprocessor_identifiers.index('imu_rotator')
        self.preprocessor_imu_rotator = preprocessor_plugin.new_preprocessor(
            idx, 'config/imu_rotator'
        )

    def process_pntos_message(self, message: Message, sequenced: bool) -> None:
        # Clean imu timestamps, rotate IMU measurements into platform frame, and send to inertial.
        if message.source_identifier == self.inertial_channel:
            message = self.preprocessor_time_adjust.process_pntos_message(message)[0]
            message = self.preprocessor_imu_rotator.process_pntos_message(message)[0]
            self.inertial.process_pntos_message(message=message)
            return

        if message.source_identifier in self.measurement_channels:
            message = self.preprocessor_time_bias.process_pntos_message(message)[0]
            cur_time = message.wrapped_message.time_of_validity
            label = self.measurement_channels[message.source_identifier]
            self._supply_aux(cur_time=cur_time, label=label)
            self.fusion_engine.propagate(cur_time)
            self.fusion_engine.update(processor_label=label, message=message)

            # Feedback states to inertial, PVA first then sensor biases
            corrected_solution = self._get_best_solution(time=cur_time)

            self.inertial.reset_solution(message=corrected_solution)

            estimate = self.fusion_engine.get_state_block_estimate(
                block_label='pinson15'
            )

            imu_errors = self.inertial.request_sensor_errors(time=cur_time)

            imu_errors.accel_biases -= estimate[9:12, 0]
            imu_errors.gyro_biases -= estimate[12:15, 0]
            self.inertial.correct_sensor_errors(time=cur_time, errors=imu_errors)

            # Zero out error states after applying feedback
            self.fusion_engine.set_state_block_estimate(
                block_label='pinson15', estimate=np.zeros((15, 1))
            )

    @property
    def filter_description_list(self) -> list[str]:
        return ['GPS_INS_BEST_ASPN_MEASUREMENT_POSITION_VELOCITY_ATTITUDE_ESTIMATE']

    def request_solutions(
        self,
        solution_times: list[TypeTimestamp],
        filter_description: str | None = None,
    ) -> list[Message] | None:
        time = self.inertial.request_latest_time()
        solution_out = self._get_best_solution(time=time)
        return [solution_out]

    def _set_up_fusion_engine(self) -> None:
        fusion_engine = self.fusion_plugin.new_fusion_engine(
            fusion_type=StandardFusionEngine
        )

        # Give the fusion engine a strategy
        fusion_engine.strategy = self.fusion_strategy_plugin.new_fusion_strategy(
            fusion_type=StandardFusionStrategy
        )

        # Get state modeling provider from state modeling plugin
        provider = self.state_modeling_plugin.new_state_model_provider(
            fusion_type=StandardStateModelProvider
        )

        # Create pinson15 stateblock and add to fusion engine
        stateblock_index = provider.block_identifiers.index('pinson15')
        stateblock = provider.new_block(
            block_index=stateblock_index,
            engine=fusion_engine,
            label='pinson15',
            config_group='config/inertial_state',
        )
        ewc = EstimateWithCovariance(
            type=EstimateWithCovarianceType.EWC_GENERIC,
            estimate=np.zeros((15, 1)),
            covariance=np.diag(
                np.array(
                    [
                        0.1,
                        0.1,
                        0.1,
                        1e-3,
                        1e-3,
                        1e-3,
                        5e-4,
                        5e-4,
                        5e-4,
                        5.2e-3,
                        5.2e-3,
                        5.2e-3,
                        9e-6,
                        9e-6,
                        9e-6,
                    ]
                )
            ),
        )

        fusion_engine.add_state_block(
            block=stateblock, initial_estimate_covariance=ewc, cross_covariances=None
        )

        # Create error fogm stateblock and add to fusion engine
        fogmblock_index = provider.block_identifiers.index('fogm')
        fogmblock = provider.new_block(
            block_index=fogmblock_index,
            engine=fusion_engine,
            label='pos_fogm',
            config_group='config/pos_sensor_error',
        )
        ewc = EstimateWithCovariance(
            type=EstimateWithCovarianceType.EWC_GENERIC,
            estimate=np.zeros((3, 1)),
            covariance=np.eye(3) * 9.0,
        )

        fusion_engine.add_state_block(
            block=fogmblock, initial_estimate_covariance=ewc, cross_covariances=None
        )

        # Create position measurement processor and add to fusion engine
        processor_index = provider.processor_identifiers.index(
            'pinson_with_ned_fogm_position'
        )
        processor = provider.new_processor(
            processor_index=processor_index,
            engine=fusion_engine,
            label='gps',
            state_block_labels=['pinson15', 'pos_fogm'],
            config_group='config/gp3d_state_modeling',
        )

        fusion_engine.add_measurement_processor(processor=processor)

        # Create velocity measurement processor and add to fusion engine
        vel_processor_index = provider.processor_identifiers.index('pinson_velocity')
        vel_processor = provider.new_processor(
            processor_index=vel_processor_index,
            engine=fusion_engine,
            label='vel',
            state_block_labels=['pinson15'],
            config_group='config/gp3d_state_modeling',
        )
        fusion_engine.add_measurement_processor(processor=vel_processor)

        self.fusion_engine = fusion_engine

    def _initialize_inertial_and_fusion_engine(self) -> None:
        # Set up initializer
        init_strategy = self.initialization_plugin.new_initialization_strategy(
            initialization_type=InertialInitializationStrategy,
            config_group='config/default/alignment',
        )

        # This example uses a hard-coded initializer, so it's ready at the start,
        # but we'll check it anyway just to show how that's done
        init_status = init_strategy.request_current_status()
        if init_status is not InitializationStatus.INITIALIZED_GOOD:
            self.mediator.log_message(
                level=LoggingLevel.ERROR, message='Initializer not ready.'
            )
            return

        # Get the initial solution and extract a few values
        init_solution = init_strategy.request_solution()
        init_pva_message = init_solution.solution
        init_time = init_pva_message.wrapped_message.time_of_validity

        # Initialize inertial mechanization with initial PVA
        self.inertial = self.inertial_plugin.new_inertial(
            inertial_type=StandardInertialMechanization,
            solution=init_pva_message,
            config_group='config/inertial',
        )

        # Pass estimated inertial sensor errors to the inertial for correction of raw measurements
        self.inertial.correct_sensor_errors(
            time=init_time,
            errors=init_solution.inertial_errors,
        )

        # Set initial filter time to match the initialization time
        self.fusion_engine.time = init_time
        self._send_inertial_aux_to_pinson()

        self.mediator.log_message(
            LoggingLevel.INFO,
            f'Aligned filter at {self.fusion_engine.time}.',
        )

    def _get_best_solution(self, time: TypeTimestamp) -> Message:
        """
        Utility function to generate the 'best' solution- raw inertial corrected with error estimates.
        """
        # Get predicted inertial error state and covariance at the requested time
        x_and_p = self.fusion_engine.peek_ahead(time=time, block_labels=['pinson15'])

        # Get the uncorrected inertial solution at the same time
        inertial_solution = self.inertial.request_solution(time=time)

        # Correct the inertial solution with estimated errors to generate best estimate
        corrected_pva = apply_error_states(
            pva=inertial_solution.wrapped_message, x=x_and_p.estimate
        )

        corrected_pva.covariance = x_and_p.covariance[:9, :9]

        return Message(
            wrapped_message=corrected_pva, source_identifier='/solution/pntos/pva'
        )

    def _send_inertial_aux_to_pinson(self) -> None:
        """Send the current inertial solution and forces to the Pinson15 state-block."""
        time = self.fusion_engine.time

        pva_message = self.inertial.request_solution(time=time)

        imu = self.inertial.request_forces_and_rates(time=time)

        imu_message = Message(
            wrapped_message=imu.forces_and_rates,
            source_identifier='Orchestration forces and rates',
        )

        self.fusion_engine.give_state_block_aux_data(
            block_label='pinson15', aux=[pva_message, imu_message]
        )

    def _send_inertial_aux_to_measurement_processor(
        self, time: TypeTimestamp, label: str
    ) -> None:
        """Send the current inertial solution to the position measurement processor."""
        pva_message = self.inertial.request_solution(time=time)

        self.fusion_engine.give_measurement_processor_aux_data(
            processor_label=label, aux=[pva_message]
        )

    def _supply_aux(self, cur_time: TypeTimestamp, label: str) -> None:
        self._send_inertial_aux_to_measurement_processor(time=cur_time, label=label)
        self._send_inertial_aux_to_pinson()
