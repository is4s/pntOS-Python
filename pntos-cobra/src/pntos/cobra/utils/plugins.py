import re
from dataclasses import dataclass, field
from typing import Callable

from aspn23 import (
    MeasurementPositionVelocityAttitude,
    MeasurementPositionVelocityAttitudeErrorModel,
    TypeHeader,
    TypeTimestamp,
)
from numpy import array, float64, zeros
from numpy.typing import NDArray

from pntos.api import (
    CommonPlugin,
    ControllerPlugin,
    FusionPlugin,
    FusionStrategyPlugin,
    InertialPlugin,
    InitializationPlugin,
    LoggingLevel,
    LoggingPlugin,
    Message,
    OrchestrationPlugin,
    PlatformIntegrationPlugin,
    PluginType,
    PreprocessorPlugin,
    RegistryPlugin,
    StandardFusionEngine,
    StandardInertialMechanization,
    StateModelingPlugin,
    TransportPlugin,
    UiPlugin,
    UtilityPlugin,
)
from pntos.cobra.utils import (
    correct_dcm_with_tilt,
    dcm_to_quat,
    east_to_delta_lon,
    north_to_delta_lat,
    quat_to_dcm,
)


@dataclass
class SortedPlugins:
    controller_plugins: list[ControllerPlugin] = field(default_factory=list)
    fusion_plugins: list[FusionPlugin] = field(default_factory=list)
    fusion_strategy_plugins: list[FusionStrategyPlugin] = field(default_factory=list)
    inertial_plugins: list[InertialPlugin] = field(default_factory=list)
    initialization_plugins: list[InitializationPlugin] = field(default_factory=list)
    logging_plugins: list[LoggingPlugin] = field(default_factory=list)
    orchestration_plugins: list[OrchestrationPlugin] = field(default_factory=list)
    platform_integration_plugins: list[PlatformIntegrationPlugin] = field(
        default_factory=list
    )
    preprocessor_plugins: list[PreprocessorPlugin] = field(default_factory=list)
    registry_plugins: list[RegistryPlugin] = field(default_factory=list)
    state_modeling_plugins: list[StateModelingPlugin] = field(default_factory=list)
    transport_plugins: list[TransportPlugin] = field(default_factory=list)
    ui_plugins: list[UiPlugin] = field(default_factory=list)
    utility_plugins: list[UtilityPlugin] = field(default_factory=list)


def sort_plugins_dataclass(plugins: list[CommonPlugin]) -> SortedPlugins:
    sorted_data = SortedPlugins()

    for plugin in plugins:
        if isinstance(plugin, ControllerPlugin):
            sorted_data.controller_plugins.append(plugin)
        elif isinstance(plugin, FusionPlugin):
            sorted_data.fusion_plugins.append(plugin)
        elif isinstance(plugin, FusionStrategyPlugin):
            sorted_data.fusion_strategy_plugins.append(plugin)
        elif isinstance(plugin, InertialPlugin):
            sorted_data.inertial_plugins.append(plugin)
        elif isinstance(plugin, InitializationPlugin):
            sorted_data.initialization_plugins.append(plugin)
        elif isinstance(plugin, LoggingPlugin):
            sorted_data.logging_plugins.append(plugin)
        elif isinstance(plugin, OrchestrationPlugin):
            sorted_data.orchestration_plugins.append(plugin)
        elif isinstance(plugin, PlatformIntegrationPlugin):
            sorted_data.platform_integration_plugins.append(plugin)
        elif isinstance(plugin, PreprocessorPlugin):
            sorted_data.preprocessor_plugins.append(plugin)
        elif isinstance(plugin, RegistryPlugin):
            sorted_data.registry_plugins.append(plugin)
        elif isinstance(plugin, StateModelingPlugin):
            sorted_data.state_modeling_plugins.append(plugin)
        elif isinstance(plugin, TransportPlugin):
            sorted_data.transport_plugins.append(plugin)
        elif isinstance(plugin, UiPlugin):
            sorted_data.ui_plugins.append(plugin)
        elif isinstance(plugin, UtilityPlugin):
            sorted_data.utility_plugins.append(plugin)
    return sorted_data


def find_base_plugin_type(plugin: CommonPlugin) -> PluginType:
    if isinstance(plugin, ControllerPlugin):
        return ControllerPlugin
    elif isinstance(plugin, FusionPlugin):
        return FusionPlugin
    elif isinstance(plugin, FusionStrategyPlugin):
        return FusionStrategyPlugin
    elif isinstance(plugin, InertialPlugin):
        return InertialPlugin
    elif isinstance(plugin, InitializationPlugin):
        return InitializationPlugin
    elif isinstance(plugin, LoggingPlugin):
        return LoggingPlugin
    elif isinstance(plugin, OrchestrationPlugin):
        return OrchestrationPlugin
    elif isinstance(plugin, PlatformIntegrationPlugin):
        return PlatformIntegrationPlugin
    elif isinstance(plugin, PreprocessorPlugin):
        return PreprocessorPlugin
    elif isinstance(plugin, RegistryPlugin):
        return RegistryPlugin
    elif isinstance(plugin, StateModelingPlugin):
        return StateModelingPlugin
    elif isinstance(plugin, TransportPlugin):
        return TransportPlugin
    elif isinstance(plugin, UiPlugin):
        return UiPlugin
    elif isinstance(plugin, UtilityPlugin):
        return UtilityPlugin
    else:
        raise TypeError(
            f'Plugin of type {type(plugin).__name__} has no base plugin type.'
        )


def camel_to_snake(name: str) -> str:
    """
    Utility function to go from class name to SortedPlugins data field name.

    Example:
        This is particularly useful for iterating through a list of plugin types when
        paired with getattr and setattr on a controller or orchestration plugin::

            def _sort_and_validate_plugins(self, plugins: list[CommonPlugin]) -> None:
                sorted_plugins: SortedPlugins = sort_plugins_dataclass(plugins)
                expected_plugin_types = [LoggingPlugin, OrchestrationPlugin, ...]
                for t in expected_plugin_types:
                    t_snake = camel_to_snake(t.__name__)
                    plugins_of_type_t = getattr(sorted_plugins, t_snake + 's')
                    n_plugins_of_type_t = len(plugins_of_type_t)
                    if n_plugins_of_type_t != 1:
                        log_func(
                            LoggingLevel.ERROR,
                            f'Expected one {t.__name__}, but received {n_plugins_of_type_t}.',
                        )
                        return
                    setattr(self, t_snake, plugins_of_type_t[0])

    """
    return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()


def validate_plugins(
    orch_plugin: OrchestrationPlugin,
    sorted_plugins: SortedPlugins,
    log_func: Callable[[LoggingLevel, str], None],
) -> None:
    """
    Utility function that verifies the number of plugins within ``sorted_plugins`` match
    the respetive expected amount.

    For example, the current ``pntos.src.cobra.SimpleOrchestrationPlugin`` expects 1 inertial.
    This function then validates there is 1 inertial.
    """
    # Fusion Plugin
    if len(sorted_plugins.fusion_plugins) != 1:
        log_func(
            LoggingLevel.ERROR,
            f'Expected one FusionPlugin - received {len(sorted_plugins.fusion_plugins)}'
            + f': {[p.identifier for p in sorted_plugins.fusion_plugins]}',
        )
        return
    orch_plugin.fusion_plugin = sorted_plugins.fusion_plugins[0]

    # Fusion Strategy Plugin
    if len(sorted_plugins.fusion_strategy_plugins) != 1:
        log_func(
            LoggingLevel.ERROR,
            'Expected one FusionStrategyPlugin - received '
            + f'{len(sorted_plugins.fusion_strategy_plugins)}',
        )
        return
    orch_plugin.fusion_strategy_plugin = sorted_plugins.fusion_strategy_plugins[0]

    # Inertial Plugin
    if len(sorted_plugins.inertial_plugins) != 1:
        log_func(
            LoggingLevel.ERROR,
            f'Expected one InertialPlugin - received '
            + f'{len(sorted_plugins.inertial_plugins)}',
        )
        return
    orch_plugin.inertial_plugin = sorted_plugins.inertial_plugins[0]

    # Initialization Plugin
    if len(sorted_plugins.initialization_plugins) != 1:
        log_func(
            LoggingLevel.ERROR,
            'Expected one InitializationPlugin - received '
            + f'{len(sorted_plugins.initialization_plugins)}',
        )
        return
    orch_plugin.initialization_plugin = sorted_plugins.initialization_plugins[0]

    # State Modeling Plugin
    if len(sorted_plugins.state_modeling_plugins) == 0:
        log_func(
            LoggingLevel.ERROR,
            f'Expected at least one StateModelingPlugin - received none.',
        )
        return
    orch_plugin.state_modeling_plugins = sorted_plugins.state_modeling_plugins


def update_filter_and_feedback_states(
    fusion_engine: StandardFusionEngine,
    inertial: StandardInertialMechanization,
    message: Message,
    mp_label: str,
    sb_label: str,
    log_func: Callable[[LoggingLevel, str], None],
) -> None:
    meas_time = message.wrapped_message.time_of_validity
    # Propagate to measurement time
    fusion_engine.propagate(meas_time)

    # Update filter.
    fusion_engine.update(mp_label, message)

    # Feedback states to inertial.
    estimate = fusion_engine.get_state_block_estimate(sb_label)
    if estimate is None:
        log_func(
            LoggingLevel.ERROR,
            'Unable to obtain estimate from fusion engine.',
        )
        return

    cur_time = fusion_engine.time
    inertial_pva_message = inertial.request_solution(cur_time)

    if inertial_pva_message is None:
        log_func(
            LoggingLevel.ERROR,
            f'Unable to obtain solution from inertial at time {cur_time}.',
        )
        return

    if not isinstance(
        inertial_pva_message.wrapped_message,
        MeasurementPositionVelocityAttitude,
    ):
        log_func(
            LoggingLevel.ERROR,
            'Did not receive PVA message from inertial. Received '
            + f'{type(inertial_pva_message.wrapped_message)} instead.',
        )
        return

    inertial_pva = inertial_pva_message.wrapped_message

    corrected_pva = apply_error_states(inertial_pva, estimate)

    message = Message(corrected_pva, 'python orchestration')

    inertial.reset_solution(message)

    imu_errors = inertial.request_sensor_errors(cur_time)
    if imu_errors is None:
        log_func(
            LoggingLevel.ERROR,
            f'Unable to obtain sensor errors from inertial at time {cur_time}.',
        )
        return

    imu_errors.accel_biases -= estimate[9:12, 0]
    imu_errors.gyro_biases -= estimate[12:15, 0]
    inertial.correct_sensor_errors(cur_time, imu_errors)

    # Assume zero error in states after applying feedback
    fusion_engine.set_state_block_estimate(sb_label, zeros((15, 1)))


def apply_error_states(
    pva: MeasurementPositionVelocityAttitude, x: NDArray[float64]
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
        pva.p1 + north_to_delta_lat(x[0, 0], pva.p1, pva.p3),
        pva.p2 + east_to_delta_lon(x[1, 0], pva.p1, pva.p3),
        pva.p3 - x[2, 0],
        pva.v1 + x[3, 0],
        pva.v2 + x[4, 0],
        pva.v3 + x[5, 0],
        dcm_to_quat(correct_dcm_with_tilt(quat_to_dcm(pva.quaternion), x[6:9, 0])),
        pva.covariance.copy(),
        MeasurementPositionVelocityAttitudeErrorModel.NONE,
        array([]),
        [],
    )
