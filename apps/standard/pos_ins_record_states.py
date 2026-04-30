#!/usr/bin/env python3

"""This app is nearly identical to the apps/standard/pos_ins.py, with 2 key differences:

1. The filter states are recorded after each propagation and update step and saved to an
   HDF5 file. After running this app, these states can be plotted along with the filter
   solution via:

    ./postprocessing/plot_results.py pntos_output.log --hdf5-file=OUTPUT.hdf5

2. The inertial error states modeled by the Pinson15NedBlock are reset only after one or
   more of the position error states reaches 100 m. This differs from the base app,
   which resets these states after every measurement update.
"""

import sys

import numpy as np

# API imports
from pntos.api import EstimateWithCovariance, EstimateWithCovarianceType, LoggingLevel

# Import Cobra plugins and config structs
from pntos.cobra import (
    DiagnosticLogPlugin,
    EkfFusionStrategyPlugin,
    LcmLogTransportPlugin,
    ManualHeadingAlignInitializationPlugin,
    StandardControllerPlugin,
    StandardFusionPlugin,
    StandardInertialPlugin,
    StandardLoggingPlugin,
    StandardOrchestrationPlugin,
    StandardPreprocessorPlugin,
    StandardRegistryPlugin,
    StandardStateModelingPlugin,
)
from pntos.cobra.config import (
    AspnVersion,
    ControllerConfig,
    FeedbackConfig,
    FogmConfig,
    FogmStateBlockConfig,
    FusionEngineConfig,
    ImuConfig,
    ImuRotatorConfig,
    InertialConfig,
    LcmLogTransportConfig,
    ManualHeadingAlignmentConfig,
    PinsonStateBlockConfig,
    PinsonWithNedFogmPositionMPConfig,
    StandardOrchestrationConfig,
    TimeAdjusterConfig,
    TimeBiasConfig,
)
from pntos_python_datasets_lcm import EXAMPLE_LCM_LOG

OUTPUT_LOG = sys.argv[1] if len(sys.argv) > 1 else 'pntos_output.log'

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
    LcmLogTransportConfig(
        input_file=EXAMPLE_LCM_LOG,
        output_file=OUTPUT_LOG,
        output_version=AspnVersion.V23,
        channels_to_process=(
            '/sensor/vn-100/imu',
            '/sensor/ublox-ZED-F9T/position',
        ),
    ),
    ControllerConfig(),
    FusionEngineConfig(save_x_and_p_after_prop=True, save_x_and_p_after_update=True),
    StandardOrchestrationConfig(
        best_sol_channel='/solution/pntos/pva',
        imu_sol_channel='/solution/pntos-imu/pva',
        alignment_channels=('/sensor/ublox-ZED-F9T/position', '/sensor/vn-100/imu'),
        pinson_sb_config=PinsonStateBlockConfig(
            group='config/pinson_block',
            label='pinson15',
            imu_model=imu_model,
        ),
        additional_sb_configs=(
            FogmStateBlockConfig(
                group='config/pos_fogm_block',
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
            PinsonWithNedFogmPositionMPConfig(
                group='config/pos_measurement_processor',
                label='pos',
                channel='/sensor/ublox-ZED-F9T/position',
                state_block_labels=('pinson15', 'pos_sensor_error'),
                lever_arm=(-0.50, 0.38, -0.05),
            ),
        ),
        inertial_config=InertialConfig(
            group='config/inertial',
            expected_dt=0.01,
            channels=('/sensor/vn-100/imu',),
            C_imu_to_platform=C_imu_to_platform,
            inertial_buffer_length=10.0,
        ),
        feedback_config=FeedbackConfig(
            'config/inertial_feedback', pos_error_threshold=100.0
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
                channel='/sensor/vn-100/imu',
                C_imu_to_platform=C_imu_to_platform,
            ),
            TimeAdjusterConfig(
                group='config/time_adjuster',
                channel_to_correct='/sensor/vn-100/imu',
                expected_dt_nsec=int(0.01 * 1e9),
            ),
            TimeBiasConfig(
                group='config/time_bias',
                channels_to_correct=('/sensor/ublox-ZED-F9T/position',),
                time_bias=int(0.15 * 1e9),
            ),
        ),
    ),
]
# End Config

# Instantiate all of our plugins
controller = StandardControllerPlugin('Cobra Standard Controller Plugin')
plugins = [
    LcmLogTransportPlugin('Cobra LCM Log Transport Plugin'),
    EkfFusionStrategyPlugin('Cobra EKF Fusion Strategy Plugin'),
    StandardFusionPlugin('Cobra Standard Fusion Plugin'),
    StandardStateModelingPlugin('Cobra Standard State Modeling Plugin'),
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
    DiagnosticLogPlugin('Cobra HDF5 Diagnostic Log Plugin'),
]

# Start the controller, and pass it all of the other plugins to use
controller.init_plugin()
controller.take_control(plugins)
