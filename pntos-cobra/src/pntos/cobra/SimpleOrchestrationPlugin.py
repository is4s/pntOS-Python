from typing import Callable

import numpy as np
from aspn23 import (
    AspnBase,
    MeasurementImu,
    MeasurementPositionVelocityAttitude,
    MeasurementPositionVelocityAttitudeErrorModel,
    TypeHeader,
    TypeTimestamp,
)
from numpy import float64
from numpy.typing import NDArray
from scipy.linalg import block_diag

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
    StandardFusionEngine,
    StandardFusionStrategy,
    StandardInertialMechanization,
    StandardStateModelProvider,
    StateModelingPlugin,
)
from pntos.cobra.utils import (
    correct_dcm_with_tilt,
    dcm_to_quat,
    east_to_delta_lon,
    north_to_delta_lat,
    quat_to_dcm,
)
from pntos.cobra.utils.pluginutils import SortedPlugins, sort_plugins_dataclass

# Enums for SimpleMessageStreamConfig
IMMEDIATE_STREAM = False
SEQUENCED_STREAM = True

# Solution Channels
BEST_SOL_CHANNEL = '/solution/pntos/best'
IMU_SOL_CHANNEL = '/solution/pntos/imu'

# Sensor input channels
IMU_CHANNEL = '/sensor/sagem/imu'
GPS_CHANNEL = '/sensor/ublox-neo-m9n-update/geodetic_pos'

# Process_pntos_message mapping
MEASUREMENT_CHANNELS = [GPS_CHANNEL]
ALIGNMENT_CHANNELS = [GPS_CHANNEL, IMU_CHANNEL]

# State block parameters
STATE_BLOCK_ID = 'pinson15'
STATE_BLOCK_LABEL = 'pinson'
STATE_BLOCK_LABELS = [STATE_BLOCK_LABEL]
STATE_BLOCK_CONFIG_GROUP = 'config/inertial_state'

# Measurement processor parameters
MEASUREMENT_PROCESSOR_ID = 'geodeticposition3d'
MEASUREMENT_PROCESSOR_LABEL = 'gps'
MEASUREMENT_PROCESSOR_CONFIG_GROUP = 'config/gp3d_state_modeling'

# Inertial parameters
INERTIAL_GROUP = 'config/inertial'
INERTIAL_CHANNEL = IMU_CHANNEL

# Config groups
ALIGNMENT_CONFIG_GROUP = 'config/default/alignment'


class SimpleOrchestrationPlugin(OrchestrationPlugin):
    mediator: Mediator
    init_solution: InitialInertialSolution | None
    fusion_plugin: FusionPlugin
    fusion_strategy_plugin: FusionStrategyPlugin
    inertial_plugin: InertialPlugin
    state_modeling_plugins: list[StateModelingPlugin]

    def __init__(self, identifier: str) -> None:
        """
        Simple orchestration plugin.

        Args:
            identifier (str): The plugin identifier passed to the
            :meth:`CommonPlugin.identifier` field.
        """
        self.identifier: str = identifier
        self.log_level_strings: dict[LoggingLevel, str] = {
            LoggingLevel.INFO: 'INFO:',
            LoggingLevel.DEBUG: 'DEBUG:',
            LoggingLevel.ERROR: 'ERROR:',
            LoggingLevel.WARN: 'WARNING:',
        }
        SimpleMessageStreamConfig._log = self._log
        self.initialization_state: InitializationStatus = InitializationStatus.WAITING
        self.init_solution = None
        self.C_inertial_to_platform = np.array(
            [[0.0, 1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, -1.0]], dtype=float64
        )

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
        stream_config.immediate_stream_all(True)  # Take all messages as they come

        self.measurement_channels: list[str] = MEASUREMENT_CHANNELS
        self.alignment_channels: list[str] = ALIGNMENT_CHANNELS

        self._sort_and_validate_plugins(plugins)

        self._set_up_fusion_engine()
        self._set_up_initializer()

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

        # Fusion Plugin
        if len(sorted_plugins.fusion_plugins) != 1:
            self._log(
                LoggingLevel.ERROR,
                f'Expected one FusionPlugin - received {len(sorted_plugins.fusion_plugins)}',
            )
            return
        self.fusion_plugin = sorted_plugins.fusion_plugins[0]

        # Fusion Strategy Plugin
        if len(sorted_plugins.fusion_strategy_plugins) != 1:
            self._log(
                LoggingLevel.ERROR,
                'Expected one FusionStrategyPlugin - received '
                + f'{len(sorted_plugins.fusion_strategy_plugins)}',
            )
            return
        self.fusion_strategy_plugin = sorted_plugins.fusion_strategy_plugins[0]

        # Inertial Plugin
        if len(sorted_plugins.inertial_plugins) != 1:
            self._log(
                LoggingLevel.ERROR,
                f'Expected one InertialPlugin - received '
                + f'{len(sorted_plugins.inertial_plugins)}',
            )
            return
        self.inertial_plugin = sorted_plugins.inertial_plugins[0]

        # Initialization Plugin
        if len(sorted_plugins.initialization_plugins) != 1:
            self._log(
                LoggingLevel.ERROR,
                'Expected one InitializationPlugin - received '
                + f'{len(sorted_plugins.initialization_plugins)}',
            )
            return
        self.initialization_plugin = sorted_plugins.initialization_plugins[0]

        # State Modeling Plugin
        if len(sorted_plugins.state_modeling_plugins) == 0:
            self._log(
                LoggingLevel.ERROR,
                f'Expected at least one StateModelingPlugin - received none.',
            )
            return
        self.state_modeling_plugins = sorted_plugins.state_modeling_plugins

    def _set_up_initializer(self) -> None:
        """Set up inertial initialization strategy, and initialize filter solution if initializer is immediately ready."""
        # Set up initializer
        init_strategy: InertialInitializationStrategy | None = (
            self.initialization_plugin.new_initialization_strategy(
                InertialInitializationStrategy
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

        # Initialize filter if initializer is already ready
        if self._initialization_ready():
            self._generate_initial_inertial_solution()

    def _set_up_fusion_engine(self) -> None:
        """
        Utility function to put together the components of the fusion engine.

        Returns:
            :class:`StandardFusionEngine` | None: Returns a functional fusion engine
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

        # Get Pinson block and measurement processor
        block = None
        processor = None
        for plugin in self.state_modeling_plugins:
            provider: StandardStateModelProvider | None = (
                plugin.new_state_model_provider(StandardStateModelProvider)
            )
            if provider is not None:
                if STATE_BLOCK_ID in provider.block_identifiers:
                    block = provider.new_block(
                        provider.block_identifiers.index(STATE_BLOCK_ID),
                        fusion_engine,
                        STATE_BLOCK_LABEL,
                        STATE_BLOCK_CONFIG_GROUP,
                    )
                if MEASUREMENT_PROCESSOR_ID in provider.processor_identifiers:
                    processor = provider.new_processor(
                        provider.processor_identifiers.index(MEASUREMENT_PROCESSOR_ID),
                        fusion_engine,
                        MEASUREMENT_PROCESSOR_LABEL,
                        STATE_BLOCK_LABELS,
                        MEASUREMENT_PROCESSOR_CONFIG_GROUP,
                    )

        # Make state block
        if block is None:
            self._log(
                LoggingLevel.ERROR,
                f'Unable to find state block "{STATE_BLOCK_ID}" - cannot initialize filter.',
            )
            return
        ewc = EstimateWithCovariance(
            EstimateWithCovarianceType.EWC_GENERIC,
            estimate=np.zeros(15),
            covariance=np.zeros((15, 15)),
        )
        fusion_engine.add_state_block(block, ewc, None)

        if processor is None:
            self._log(
                LoggingLevel.ERROR,
                f'Unable to find measurement processor "{MEASUREMENT_PROCESSOR_ID}" - cannot initialize filter.',
            )
            return
        fusion_engine.add_measurement_processor(processor)

        self.fusion_engine = fusion_engine

    def _rotate_imu_meas(self, imu: MeasurementImu) -> None:
        """Rotate IMU measurement into platform frame.

        Args:
            message (MeasurementImu): IMU ASPN message to rotate.
        """
        imu.meas_accel = self.C_inertial_to_platform @ imu.meas_accel
        imu.meas_gyro = self.C_inertial_to_platform @ imu.meas_gyro

    def _dispatch_to_initializer(self, message: Message) -> None:
        """Send ``message`` to the initializer for alignment, and grab initial solution if available."""
        self.initializer.process_pntos_message(message)

        if self._initialization_ready():
            self._generate_initial_inertial_solution()

    def _dispatch_to_fusion_engine(self, message: Message) -> None:
        """Send message to the fusion engine to update the filter.

        Applies feedback to inertial solution and biases, and resets pinson error states afterward."""

        # Update filter.
        self.fusion_engine.update(MEASUREMENT_PROCESSOR_LABEL, message)

        # Feedback states to inertial.
        estimate = self.fusion_engine.get_state_block_estimate(STATE_BLOCK_LABEL)
        if estimate is None:
            self._log(
                LoggingLevel.ERROR,
                'Unable to obtain estimate from fusion engine.',
            )
            return

        cur_time = self.fusion_engine.time
        inertial_pva_message = self.inertial.request_solution(cur_time)

        if inertial_pva_message is None:
            self._log(
                LoggingLevel.ERROR,
                f'Unable to obtain solution from inertial at time {cur_time}.',
            )
            return

        if not isinstance(
            inertial_pva_message.wrapped_message,
            MeasurementPositionVelocityAttitude,
        ):
            self._log(
                LoggingLevel.ERROR,
                'Did not receive PVA message from inertial. Received '
                + f'{type(inertial_pva_message.wrapped_message)} instead.',
            )
            return

        inertial_pva = inertial_pva_message.wrapped_message

        corrected_pva = self._apply_error_states(inertial_pva, estimate)

        message = Message(corrected_pva, 'python orchestration')

        self.inertial.reset_solution(message)

        imu_errors = self.inertial.request_sensor_errors(cur_time)
        if imu_errors is None:
            self._log(
                LoggingLevel.ERROR,
                f'Unable to obtain sensor errors from inertial at time {cur_time}.',
            )
            return

        imu_errors.accel_biases -= estimate[9:12]
        imu_errors.gyro_biases -= estimate[12:15]
        self.inertial.correct_sensor_errors(cur_time, imu_errors)

        # Assume zero error in states after applying feedback
        self.fusion_engine.set_state_block_estimate(STATE_BLOCK_LABEL, np.zeros(15))

    def _generate_initial_inertial_solution(self) -> None:
        """Get the solution from the initialization strategy and initialize the inertial from it."""
        self.init_solution = self.initializer.request_solution()

        if (
            self.init_solution.solution is None
            or self.init_solution.inertial_errors is None
            or self.init_solution.inertial_error_covariance is None
        ):
            self._log(
                LoggingLevel.ERROR,
                'Invalid InitialInertialSolution returned from init strategy - unable to proceed.',
            )
            return

        if not isinstance(
            self.init_solution.solution.wrapped_message,
            MeasurementPositionVelocityAttitude,
        ):
            self._log(
                LoggingLevel.ERROR,
                'Expected PVA solution from init strategy - unable to proceed.',
            )
            return

        inertial_init_message = Message(
            self.init_solution.solution, 'python orchestration'
        )

        inertial: StandardInertialMechanization | None = (
            self.inertial_plugin.new_inertial(
                StandardInertialMechanization,
                inertial_init_message,
                INERTIAL_GROUP,
            )
        )
        if inertial is None:
            self._log(
                LoggingLevel.ERROR,
                'StandardInertialMechanization not supported by inertial '
                + f'({self.inertial_plugin.identifier})',
            )
            return

        self.inertial = inertial

        inertial.correct_sensor_errors(
            self.fusion_engine.time, self.init_solution.inertial_errors
        )

        pva_cov = self.init_solution.solution.wrapped_message.covariance  # 9x9
        bias_cov = self.init_solution.inertial_error_covariance  # 6x6
        init_pinson_cov = block_diag(pva_cov, bias_cov)
        self.fusion_engine.set_state_block_covariance(
            STATE_BLOCK_LABEL,
            init_pinson_cov,
        )

        self._send_inertial_aux_to_pinson()

        init_time = self.init_solution.solution.wrapped_message.time_of_validity
        self._log(
            LoggingLevel.INFO,
            f'Aligned filter at {init_time}.',
        )

    def _has_valid_time(self, message: Message) -> bool:
        """
        Utility function which returns true if the message's time of validity is greater
        than the current fusion engine time.
        """
        measurement = message.wrapped_message
        # get time - check for old messages
        if hasattr(measurement, 'time_of_validity'):
            message_time = measurement.time_of_validity.elapsed_nsec
            if self.fusion_engine.time.elapsed_nsec <= message_time:
                return True
            else:  # Discard old messages
                self._log(
                    LoggingLevel.DEBUG,
                    f'Received old message ({message_time}ns) - discarding.',
                )
                return False
        else:
            self._log(
                LoggingLevel.ERROR,
                f'Measurement of type {type(measurement)} does not contain '
                + '"time_of_validity" field.',
            )
            return False

    def _initialization_ready(self) -> bool:
        """
        Utility function to poll the state of the init strategy plugin.

        Populates self.initialization_state with the relevant :class:`InitializationStatus`.
        """
        self.initialization_state = self.initializer.request_current_status()
        return self.initialization_state is InitializationStatus.INITIALIZED_GOOD

    def process_pntos_message(self, message: Message, sequenced: bool) -> None:
        if sequenced:
            self._log(LoggingLevel.ERROR, 'Sequenced streamed messages not supported.')
            return None

        # Rotate IMU measurements into platform frame
        if isinstance(message.wrapped_message, MeasurementImu):
            self._rotate_imu_meas(message.wrapped_message)

        if not self._has_valid_time(message):
            return

        # If filter solution is not initialized, send messages to the alignment algorithm.
        if (
            not self._initialization_ready()
            and message.source_identifier in self.alignment_channels
        ):
            self._dispatch_to_initializer(message)

        # If aligned, send messages to IMU or filter
        if self._initialization_ready():
            if message.source_identifier == INERTIAL_CHANNEL:
                self.inertial.process_pntos_message(message)
            elif message.source_identifier in self.measurement_channels:
                self._dispatch_to_fusion_engine(message)

    def get_filter_description_list(self) -> list[str]:
        descriptions = []
        aspn_pva = 'ASPN_MEASUREMENT_POSITION_VELOCITY_ATTITUDE_ESTIMATE'
        for label in ['GPS_INS']:
            for solution_type in ['BEST', 'DEAD_RECKONING']:
                descriptions += [f'{label}_{solution_type}_{aspn_pva}']

        return descriptions

    def _get_dead_reckoning_solution(self, time: TypeTimestamp) -> Message | None:
        """
        Utility function to request the IMU-only dead-reckoning solution. Returns
        ``None`` if the inertial is unable to provide a solution for the requested time.
        """
        message = self.inertial.request_solution(time)
        if message is not None:
            return Message(message.wrapped_message, IMU_SOL_CHANNEL)
        else:
            self._log(
                LoggingLevel.ERROR,
                'Unable to get PVA message from inertial.'
                + ' Cannot generate DEAD_RECKONING solution.',
            )
            return None

    def _get_best_solution(self, time: TypeTimestamp) -> Message | None:
        """
        Utility function to request the best fusion strategy solution. Returns
        ``None`` if the fusion engine is unable to provide a solution for the requested time.
        """
        x_and_p: EstimateWithCovariance | None = self.fusion_engine.peek_ahead(
            time, [STATE_BLOCK_LABEL]
        )
        if x_and_p is None:
            self._log(
                LoggingLevel.WARN,
                f'Cannot get filter solution at time {time}. Filter is already at time {self.fusion_engine.time}.',
            )
            return None

        inertial_solution: Message | None = self.inertial.request_solution(time)

        if inertial_solution is None:
            self._log(
                LoggingLevel.ERROR,
                f'Unable to obtain solution from inertial at time {time}. Cannot generate BEST solution.',
            )
            return None

        if not isinstance(
            inertial_solution.wrapped_message,
            MeasurementPositionVelocityAttitude,
        ):
            self._log(
                LoggingLevel.ERROR,
                f'Expected PVA solution from inertial, but got type {type(inertial_solution.wrapped_message)}. Cannot generate BEST solution.',
            )
            return None

        corrected_pva = self._apply_error_states(
            inertial_solution.wrapped_message, x_and_p.estimate
        )

        covariance = x_and_p.covariance
        corrected_pva.covariance = covariance[:9, :9]

        return Message(corrected_pva, BEST_SOL_CHANNEL)

    def request_solutions(
        self,
        solution_times: list[TypeTimestamp],
        filter_description: str | None = None,
    ) -> list[Message]:
        if not self._initialization_ready() or self.init_solution is None:
            self._log(
                LoggingLevel.DEBUG,
                'Unable to provide a solution - initialization not ready.',
            )
            return []

        if len(solution_times) != 1:
            self._log(
                LoggingLevel.ERROR,
                'This implementation of request_solutions requires a time array'
                + f' of length one but received a time array of length {len(solution_times)}',
            )
            return []

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
            solution_out = self._get_best_solution(time)

        elif 'DEAD_RECKONING' in filter_description:
            solution_out = self._get_dead_reckoning_solution(time)

        else:
            descriptions = ', '.join(self.get_filter_description_list())
            self._log(
                LoggingLevel.ERROR,
                f'Solution {filter_description} was requested, but available solution '
                + f'types are: {descriptions}',
            )
            return []

        if solution_out is None:
            return []
        return [solution_out]

    def _send_inertial_aux_to_pinson(self) -> None:
        """Send the current inertial solution and forces to the Pinson15 state-block."""
        time = self.fusion_engine.time
        pva_message = self.inertial.request_solution(time)
        if pva_message is None:
            self._log(
                LoggingLevel.ERROR,
                f'Cannot send inertial aux to pinson block. Solution not available at time {time}',
            )
            return
        imu = self.inertial.request_forces_and_rates(time)
        if imu is None:
            self._log(
                LoggingLevel.ERROR,
                f'Cannot send inertial aux to pinson block. Forces not available at time {time}',
            )
            return
        imu_message = Message(imu.forces_and_rates, 'Orchestration forces and rates')

        self.fusion_engine.give_state_block_aux_data(
            STATE_BLOCK_LABEL, [pva_message, imu_message]
        )

    def _apply_error_states(
        self, pva: MeasurementPositionVelocityAttitude, x: NDArray[float64]
    ) -> MeasurementPositionVelocityAttitude:
        """Correct PVA using inertial PVA error states."""
        # These fields should never be None unless we already encountered a different
        # error, so assert instead of log
        assert (
            pva.p1 is not None
            and pva.p2 is not None
            and pva.p3 is not None
            and pva.v1 is not None
            and pva.v2 is not None
            and pva.v3 is not None
            and pva.quaternion is not None
        )

        return MeasurementPositionVelocityAttitude(
            TypeHeader(
                pva.header.vendor_id,
                pva.header.device_id,
                pva.header.context_id,
                pva.header.sequence_id,
            ),
            TypeTimestamp(pva.time_of_validity.elapsed_nsec),
            pva.reference_frame,
            pva.p1 + north_to_delta_lat(x[0], pva.p1, pva.p3),
            pva.p2 + east_to_delta_lon(x[1], pva.p1, pva.p3),
            pva.p3 - x[2],
            pva.v1 + x[3],
            pva.v2 + x[4],
            pva.v3 + x[5],
            dcm_to_quat(correct_dcm_with_tilt(quat_to_dcm(pva.quaternion), x[6:9])),
            pva.covariance.copy(),
            MeasurementPositionVelocityAttitudeErrorModel.NONE,
            np.array([]),
            [],
        )


class SimpleMessageStreamConfig(MessageStreamConfig):
    # _message_lookup[type(AspnMessage)][source_identifier] -> is_sequenced?
    _immediate_stream: set[type[AspnBase]] = set([])
    _sequenced_stream: set[type[AspnBase]] = set([])
    _last_all_call: bool = False  # True -> sequenced, False -> immediate
    _log: Callable[[LoggingLevel, str], None] | None = None

    def __init__(self) -> None:
        pass

    def _handle_source_identifier(self, source_identifier: str | None) -> None:
        if source_identifier is not None:
            if self._log is not None:
                self._log(
                    LoggingLevel.ERROR,
                    'Filtering on source identifier is unimplemented.',
                )
            else:
                print(
                    '[MessageStreamConfig] ERROR: Filtering on source '
                    + 'identifier is unimplemented.'
                )

    def sequenced_stream_add(
        self, type: type[AspnBase], source_identifier: str | None = None
    ) -> None:
        self._handle_source_identifier(source_identifier)
        if type in self._immediate_stream:
            self._immediate_stream.remove(type)
        self._sequenced_stream.add(type)

    def sequenced_stream_remove(
        self, type: type[AspnBase], source_identifier: str | None = None
    ) -> None:
        self._handle_source_identifier(source_identifier)
        if type in self._sequenced_stream:
            self._sequenced_stream.remove(type)

    def sequenced_stream_all(self, enable: bool) -> None:
        self._sequenced_stream = set([])
        self._immediate_stream = set([])
        self._last_all_call = SEQUENCED_STREAM

    def immediate_stream_add(
        self, type: type[AspnBase], source_identifier: str | None = None
    ) -> None:
        self._handle_source_identifier(source_identifier)
        if type in self._sequenced_stream:
            self._sequenced_stream.remove(type)
        self._immediate_stream.add(type)

    def immediate_stream_remove(
        self, type: type[AspnBase], source_identifier: str | None = None
    ) -> None:
        self._handle_source_identifier(source_identifier)
        if type in self._immediate_stream:
            self._immediate_stream.remove(type)

    def immediate_stream_all(self, enable: bool) -> None:
        self._sequenced_stream = set([])
        self._immediate_stream = set([])
        self._last_all_call = IMMEDIATE_STREAM

    def get_stream_status(
        self, type: type[AspnBase], source_identifier: str | None = None
    ) -> bool:
        """
        Returns true if the requested type will be streamed sequentially, and
        False if the requested type will be immediately streamed.
        """
        self._handle_source_identifier(source_identifier)
        if type in self._immediate_stream:
            return IMMEDIATE_STREAM
        if type in self._sequenced_stream:
            return SEQUENCED_STREAM
        # If type is not in either list, return the default
        return self._last_all_call


if __name__ == '__main__':
    SimpleMessageStreamConfig()
