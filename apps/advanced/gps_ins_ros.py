#!/usr/bin/env python3

import numpy as np

# API imports
from pntos.api import EstimateWithCovariance, EstimateWithCovarianceType, LoggingLevel

# Import Cobra plugins and config structs
from pntos.cobra import (
    EkfFusionStrategyPlugin,
    SimpleControllerPlugin,
    StandardFusionPlugin,
    StandardGpsInsStateModelingPlugin,
    StandardInertialPlugin,
    StandardLoggingPlugin,
    StandardOrchestrationPlugin,
    StandardPreprocessorPlugin,
    StandardRegistryPlugin,
    TutorialInitializationPlugin,
)
from pntos.cobra.advanced_plugins import Aspn23RosTransportPlugin
from pntos.cobra.config import (
    FogmConfig,
    FogmStateBlockConfig,
    ImuConfig,
    ImuRotatorConfig,
    InertialConfig,
    ManualAlignmentConfig,
    PinsonStateBlockConfig,
    SensorConfig,
    SensorMeasurementProcessorConfig,
    StandardOrchestrationConfig,
    TimeAdjusterConfig,
)

# Config setup
C_imu_to_platform = (
    (0.99776363, 0.01784622, 0.06441467),
    (-0.01741603, 0.99982216, -0.00723391),
    (-0.06453231, 0.00609588, 0.997897),
)
my_config = [
    StandardOrchestrationConfig(
        best_sol_channel='/solution/pntos/pva',
        imu_sol_channel='/solution/pntos-imu/pva',
        alignment_channels=['/sensor/ublox_ZED_F9T/position', '/sensor/vn_100/imu'],
        pinson_sb_config=PinsonStateBlockConfig(
            group='config/pinson_block',
            identifier='pinson15',
            label='pinson15',
            imu_model=ImuConfig(
                group='config/inertial_state',
                accel_bias_sigma=(2.4e-3, 2.4e-3, 2.4e-3),
                accel_bias_tau=(300.0, 300.0, 300.0),
                accel_random_walk_sigma=(3.887e-6, 3.887e-6, 3.887e-6),
                gyro_bias_sigma=(2e-4, 2e-4, 2e-4),
                gyro_bias_tau=(500.0, 500.0, 500.0),
                gyro_random_walk_sigma=(9.9e-4, 9.9e-4, 6.7e-5),
            ),
        ),
        additional_sb_configs=[
            FogmStateBlockConfig(
                group='config/fogm_block',
                identifier='fogm',
                label='pos_fogm',
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
        ],
        mp_configs=[
            SensorMeasurementProcessorConfig(
                group='config/gps_measurement_processor',
                identifier='pinson_with_ned_fogm_position',
                label='gps',
                channel='/sensor/ublox_ZED_F9T/position',
                state_block_labels=['pinson15', 'pos_fogm'],
                sensor_config=SensorConfig(
                    group='config/gp3d_state_modeling',
                    lever_arm=(-0.50, 0.38, -0.05),
                    orientation=(0.0, 0.0, 0.0, 0.0),
                    sensor_name='position',
                ),
            ),
        ],
        inertial_config=InertialConfig(
            group='config/inertial',
            expected_dt=0.01,
            channel='/sensor/vn_100/imu',
            C_imu_to_platform=C_imu_to_platform,
            inertial_buffer_length=10.0,
        ),
        alignment_config=ManualAlignmentConfig(
            group='config/default/alignment',
            initial_pos_var=(0.1, 0.1, 0.1),
            initial_vel_var=(1e-3, 1e-3, 1e-3),
            initial_tilt_var=(5e-4, 5e-4, 5e-4),
            initial_accel_bias_var=(5.2e-3, 5.2e-3, 5.2e-3),
            initial_gyro_bias_var=(9e-6, 9e-6, 9e-6),
            initial_accel_bias=(-0.0023383, 0.00085563, -0.05412892),
            initial_accel_scale_factor=(0.0, 0.0, 0.0),
            initial_accel_scale_factor_var=(0.0, 0.0, 0.0),
            initial_gyro_bias=(-0.00160958, -0.00204483, -0.00267885),
            initial_gyro_scale_factor=(0.0, 0.0, 0.0),
            initial_gyro_scale_factor_var=(0.0, 0.0, 0.0),
            initial_pos=(0.6938996038254822, -1.4679920679462133, 225.493),
            initial_rpy=(
                -0.014713125594312194,
                -0.040718531449027706,
                0.06895795874629593,
            ),
            initial_time=1747680879.539799718,
            initial_vel=(0.0, 0.0, 0.0),
        ),
        preprocessor_configs=[
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
        ],
        group='config/orchestration',
    ),
]
# End Config

# Instantiate all of our plugins
controller = SimpleControllerPlugin('Cobra Simple Controller Plugin')
plugins = [
    Aspn23RosTransportPlugin('Cobra ASPN23-ROS Transport Plugin'),
    EkfFusionStrategyPlugin('Cobra EKF Fusion Strategy Plugin'),
    StandardFusionPlugin('Cobra Standard Fusion Plugin'),
    StandardGpsInsStateModelingPlugin('Cobra Standard State Modeling Plugin'),
    StandardInertialPlugin('Cobra Standard Inertial Plugin'),
    TutorialInitializationPlugin('Cobra Manual Initialization Plugin'),
    StandardLoggingPlugin(
        'Cobra Standard Logging Plugin',
        global_log_level=LoggingLevel.INFO,  # Switch to `DEBUG` for more informative log output
    ),
    StandardRegistryPlugin('Cobra Standard Registry Plugin', config=my_config),  # type: ignore[arg-type]
    StandardPreprocessorPlugin('Cobra Standard Preprocessor Plugin'),
    StandardOrchestrationPlugin('Cobra Standard Orchestration Plugin'),
]

# Start the controller, and pass it all of the other plugins to use
controller.init_plugin()
controller.take_control(plugins)
