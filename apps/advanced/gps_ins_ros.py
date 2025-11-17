#!/usr/bin/env python3

import numpy as np

# API imports
from pntos.api import EstimateWithCovariance, EstimateWithCovarianceType, LoggingLevel

# Import Cobra plugins and config structs
from pntos.cobra import (
    EkfFusionStrategyPlugin,
    ManualHeadingAlignInitializationPlugin,
    StandardControllerPlugin,
    StandardFusionPlugin,
    StandardGpsInsStateModelingPlugin,
    StandardInertialPlugin,
    StandardLoggingPlugin,
    StandardOrchestrationPlugin,
    StandardPreprocessorPlugin,
    StandardRegistryPlugin,
)
from pntos.cobra.advanced_plugins import Aspn23RosTransportPlugin
from pntos.cobra.config import (
    ControllerConfig,
    FogmConfig,
    FogmStateBlockConfig,
    ImuConfig,
    ImuRotatorConfig,
    InertialConfig,
    ManualHeadingAlignmentConfig,
    PinsonStateBlockConfig,
    SensorConfig,
    SensorMeasurementProcessorConfig,
    StandardOrchestrationConfig,
    TimeAdjusterConfig,
    TimeBiasConfig,
)

# Config setup
C_imu_to_platform = (
    (0.99802515, 0.01772605, 0.06026269),
    (-0.01742059, 0.99983262, -0.00559042),
    (-0.0603517, 0.00452957, 0.9981669),
)
imu_model = ImuConfig(
    group='config/inertial_state',
    accel_bias_sigma=(2.4e-3, 2.4e-3, 2.4e-3),
    accel_bias_tau=(300.0, 300.0, 300.0),
    accel_random_walk_sigma=(3.887e-6, 3.887e-6, 3.887e-6),
    gyro_bias_sigma=(2e-4, 2e-4, 2e-4),
    gyro_bias_tau=(500.0, 500.0, 500.0),
    gyro_random_walk_sigma=(9.9e-4, 9.9e-4, 6.7e-5),
    accel_bias_initial_sigma=(0.072, 0.072, 0.072),
    gyro_bias_initial_sigma=(0.003, 0.003, 0.003),
)
my_config = [
    ControllerConfig(group='controller'),
    StandardOrchestrationConfig(
        best_sol_channel='/solution/pntos/pva',
        imu_sol_channel='/solution/pntos-imu/pva',
        alignment_channels=('/sensor/ublox_ZED_F9T/position', '/sensor/vn_100/imu'),
        pinson_sb_config=PinsonStateBlockConfig(
            group='config/pinson_block',
            identifier='pinson15',
            label='pinson15',
            imu_model=imu_model,
        ),
        additional_sb_configs=(
            FogmStateBlockConfig(
                group='config/pos_fogm_block',
                identifier='fogm',
                label='pos_sensor_error',
                estimate_with_covariance=EstimateWithCovariance(
                    type=EstimateWithCovarianceType.EWC_GENERIC,
                    estimate=np.zeros((3,)),
                    covariance=(np.eye(3) * 9.0),
                ),
                fogm_model=FogmConfig(
                    group='config/pos_sensor_error',
                    sigma=(1.5, 1.5, 2.0),
                    tau=(300.0, 300.0, 200.0),
                ),
            ),
        ),
        mp_configs=(
            SensorMeasurementProcessorConfig(
                group='config/gps_measurement_processor',
                identifier='pinson_with_ned_fogm_position',
                label='gps',
                channel='/sensor/ublox_ZED_F9T/position',
                state_block_labels=('pinson15', 'pos_sensor_error'),
                sensor_config=SensorConfig(
                    group='config/gp3d_state_modeling',
                    lever_arm=(-0.50, 0.38, -0.05),
                    orientation=(0.0, 0.0, 0.0, 0.0),
                    sensor_name='position',
                ),
            ),
        ),
        inertial_config=InertialConfig(
            group='config/inertial',
            expected_dt=0.01,
            channel='/sensor/vn_100/imu',
            C_imu_to_platform=C_imu_to_platform,
            inertial_buffer_length=10.0,
        ),
        alignment_config=ManualHeadingAlignmentConfig(
            group='config/default/alignment',
            static_time=10.0,
            imu_model=imu_model,
            heading=0.06895795874629593,
            heading_sigma=0.02236067977,
        ),
        preprocessor_configs=(
            ImuRotatorConfig(
                group='config/imu_rotator',
                identifier='imu_rotator',
                channel='/sensor/vn_100/imu',
                C_imu_to_platform=C_imu_to_platform,
            ),
            TimeAdjusterConfig(
                group='config/time_adjuster',
                identifier='time_adjuster',
                channel_to_correct='/sensor/vn_100/imu',
                expected_dt_nsec=int(0.01 * 1e9),
            ),
            TimeBiasConfig(
                group='config/time_bias',
                identifier='time_bias',
                channels_to_correct=('/sensor/ublox-ZED-F9T/position',),
                time_bias=int(0.15 * 1e9),
            ),
        ),
        group='config/orchestration',
    ),
]
# End Config

# Instantiate all of our plugins
controller = StandardControllerPlugin('Cobra Standard Controller Plugin')
plugins = [
    Aspn23RosTransportPlugin('Cobra ASPN23-ROS Transport Plugin'),
    EkfFusionStrategyPlugin('Cobra EKF Fusion Strategy Plugin'),
    StandardFusionPlugin('Cobra Standard Fusion Plugin'),
    StandardGpsInsStateModelingPlugin('Cobra Standard State Modeling Plugin'),
    StandardInertialPlugin('Cobra Standard Inertial Plugin'),
    ManualHeadingAlignInitializationPlugin(
        'Cobra Manual Heading Static Align Initialization Plugin'
    ),
    StandardLoggingPlugin(
        'Cobra Standard Logging Plugin',
        global_log_level=LoggingLevel.INFO,  # Switch to `DEBUG` for more informative log output
    ),
    StandardRegistryPlugin('Cobra Standard Registry Plugin', config=my_config),
    StandardPreprocessorPlugin('Cobra Standard Preprocessor Plugin'),
    StandardOrchestrationPlugin('Cobra Standard Orchestration Plugin'),
]

# Start the controller, and pass it all of the other plugins to use
controller.init_plugin()
controller.take_control(plugins)
