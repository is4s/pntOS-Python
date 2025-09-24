import unittest
from dataclasses import fields
from enum import Enum

import numpy as np
from aspn23 import TypeTimestamp
from pntos.api import (
    EstimateWithCovariance,
    EstimateWithCovarianceType,
    LoggingLevel,
    Mediator,
    Message,
    RegistryValueTypeUnion,
)
from pntos.cobra import StandardRegistryPlugin
from pntos.cobra.config import (
    BaseConfig,
    DownsamplerConfig,
    ImuConfig,
    ImuRotatorConfig,
    InertialConfig,
    ManualAlignmentConfig,
    MeasurementProcessorConfig,
    PinsonStateBlockConfig,
    PreprocessorConfig,
    SensorConfig,
    StandardOrchestrationConfig,
    StateBlockConfig,
    StaticAlignmentConfig,
    TimeAdjusterConfig,
    config_from_registry,
    config_to_registry,
)
from pntos.cobra.utils import validate_manual_ewc

DEBUG_LOG: str = ''
CONFIG_TEST_GROUP = 'config_test_group'


class DummyMediator(Mediator):
    @property
    def filter_description_list(self) -> list[str]:
        return []

    def request_solutions(
        self,
        solution_times: list[TypeTimestamp],
        filter_description: str | None = None,
    ) -> list[Message] | None:
        return None

    def process_pntos_message(self, message: Message) -> None:
        pass

    def broadcast_aspn_message(
        self,
        message: Message,
        transport: str | None = None,
        destination_identifier: str | None = None,
    ) -> None:
        pass

    def log_message(self, level: LoggingLevel, message: str) -> None:
        pass


class TestConfigUtils(unittest.TestCase):
    def __init__(self, name: str) -> None:
        # Set up registry and mediator
        registry_plugin = StandardRegistryPlugin('Standard Registry Plugin')
        registry_plugin.init_plugin(mediator=DummyMediator())
        DummyMediator.registry = registry_plugin.new_registry()
        self.mediator = DummyMediator()

        super().__init__(name)

    def test_ManualAlignmentConfig_to_and_from_registry(self) -> None:
        test_conf = ManualAlignmentConfig(
            CONFIG_TEST_GROUP,
            (1, 2, 3),
            (4, 5, 6),
            (7, 8, 9),
            (10, 11, 12),
            (13, 14, 15),
            (16, 17, 18),
            (19, 20, 21),
            1.23,
            (8.1, 8.2, 8.3),
            (9.1, 9.2, 9.3),
            (10.1, 10.2, 10.3),
            (11.1, 11.2, 11.3),
            (12.1, 12.2, 12.3),
            (13.1, 13.2, 13.3),
            (14.1, 15.2, 16.3),
        )

        # Test config_to_registry
        config_to_registry(test_conf, self.mediator)
        self._validate_conf_to_registry(test_conf)

        # Test config_from_registry()
        result_conf = config_from_registry(
            ManualAlignmentConfig, self.mediator, CONFIG_TEST_GROUP
        )
        assert result_conf is not None

        self._validate_conf_from_registry(test_conf, result_conf)

    def test_ImuConfig_to_from_registry(self) -> None:
        test_conf = ImuConfig(
            CONFIG_TEST_GROUP,
            (2.1, 2.2, 2.3),
            (3.1, 3.2, 3.3),
            (4.1, 4.2, 4.3),
            (5.1, 5.2, 5.3),
            (6.1, 6.2, 6.3),
            (7.1, 7.2, 7.3),
        )

        # Test config_to_registry
        config_to_registry(test_conf, self.mediator)
        self._validate_conf_to_registry(test_conf)

        # Test config_from_registry()
        result_conf = config_from_registry(ImuConfig, self.mediator, CONFIG_TEST_GROUP)
        assert result_conf is not None

        self._validate_conf_from_registry(test_conf, result_conf)

    def test_SensorConfig_to_from_registry(self) -> None:
        test_conf = SensorConfig(
            CONFIG_TEST_GROUP,
            (0.7, 0.8, 0.9),
            (1.1, 2.2, 3.3, 4.4),
            'NCC-1701',
        )

        # Test config_to_registry
        config_to_registry(test_conf, self.mediator)
        self._validate_conf_to_registry(test_conf)

        # Test config_from_registry()
        result_conf = config_from_registry(
            SensorConfig, self.mediator, CONFIG_TEST_GROUP
        )
        assert result_conf is not None

        self._validate_conf_from_registry(test_conf, result_conf)

    def test_DownsamplerConfig_to_from_registry(self) -> None:
        test_conf = DownsamplerConfig(
            CONFIG_TEST_GROUP, 'downsampler', ['chan1', 'chan2', 'chan3'], [1, 2, 3]
        )
        # Test config_to_registry
        config_to_registry(test_conf, self.mediator)
        self._validate_conf_to_registry(test_conf)

        result_conf = config_from_registry(
            DownsamplerConfig, self.mediator, CONFIG_TEST_GROUP
        )
        assert result_conf is not None
        self._validate_conf_from_registry(test_conf, result_conf)

    def test_PreprocessorConfig_to_from_registry(self) -> None:
        test_conf = PreprocessorConfig(CONFIG_TEST_GROUP, 'downsampler')
        # Test config_to_registry
        config_to_registry(test_conf, self.mediator)
        self._validate_conf_to_registry(test_conf)

        result_conf = config_from_registry(
            PreprocessorConfig, self.mediator, CONFIG_TEST_GROUP
        )
        assert result_conf is not None
        self._validate_conf_from_registry(test_conf, result_conf)

    def test_OrchestrationConfig_to_from_registry(self) -> None:
        C_imu_to_platform = (
            (0.99776363, 0.01784622, 0.06441467),
            (-0.01741603, 0.99982216, -0.00723391),
            (-0.06453231, 0.00609588, 0.997897),
        )
        test_conf = StandardOrchestrationConfig(
            best_sol_channel='/solution/pntos/best',
            imu_sol_channel='/solution/pntos/imu',
            alignment_channels=['/sensor/ublox-ZED-F9T/position', '/sensor/vn-100/imu'],
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
                StateBlockConfig(
                    group='config/fogm_block',
                    identifier='fogm',
                    label='pos_fogm',
                ),
            ],
            mp_configs=[
                MeasurementProcessorConfig(
                    group='config/gps_measurement_processor',
                    identifier='pinson_with_ned_fogm_position',
                    label='gps',
                    channel='/sensor/ublox-ZED-F9T/position',
                    state_block_labels=['pinson15', 'pos_fogm'],
                ),
                MeasurementProcessorConfig(
                    group='config/vel_measurement_processor',
                    identifier='pinson_velocity',
                    label='vel',
                    channel='/sensor/ublox-ZED-F9T/velocity',
                    state_block_labels=['pinson15'],
                ),
            ],
            inertial_config=InertialConfig(
                group='config/inertial',
                expected_dt=0.01,
                channel='/sensor/vn-100/imu',
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
                    channel='/sensor/vn-100/imu',
                    C_imu_to_platform=C_imu_to_platform,
                ),
                TimeAdjusterConfig(
                    group='config/time_adjuster',
                    identifier='time_adjuster',
                    channel_to_correct='/sensor/vn-100/imu',
                    expected_dt_nsec=int(0.01 * 1e9),
                ),
            ],
            group=CONFIG_TEST_GROUP,
        )

        # Verify configs survive
        config_to_registry(test_conf, self.mediator)
        result_config = config_from_registry(
            StandardOrchestrationConfig, self.mediator, CONFIG_TEST_GROUP
        )
        assert result_config is not None
        assert result_config.additional_sb_configs is not None
        assert result_config.mp_configs is not None
        assert result_config.inertial_config is not None
        assert result_config.preprocessor_configs is not None

    def test_static_align_config_to_from_registry(self) -> None:
        imu_model = ImuConfig(
            CONFIG_TEST_GROUP,
            (1.23, 2.34, 3.45),
            (12.3, 23.4, 34.5),
            (123.0, 234.0, 345.0),
            (1e-1, 1e-2, 1e-3),
            (2e-2, 3e-3, 4e-4),
            (1.23e-10, 2.34e-10, 3.45e-10),
        )
        config = StaticAlignmentConfig(CONFIG_TEST_GROUP, 1.23, imu_model)

        # Verify config survives round trip
        config_to_registry(config, self.mediator)
        result_config = config_from_registry(
            StaticAlignmentConfig, self.mediator, CONFIG_TEST_GROUP
        )
        assert result_config is not None
        assert result_config.imu_model == config.imu_model
        assert config == result_config

    def test_config_from_registry_return_none(self) -> None:
        test_conf = SensorConfig(
            CONFIG_TEST_GROUP,
            (0.1, 0.2, 0.3),
            (0.4, 0.5, 0.6, 0.7),
            'NCC-1701',
        )

        # Test config_to_registry
        config_to_registry(test_conf, self.mediator)
        self._validate_conf_to_registry(test_conf)

        # Whoops, modified a value in the registry
        reg = self.mediator.registry.batch_start(CONFIG_TEST_GROUP)
        reg['lever_arm'] = ['wrong type']
        reg.batch_end()

        # Test config_from_registry()
        result_conf = config_from_registry(
            SensorConfig, self.mediator, CONFIG_TEST_GROUP
        )
        assert result_conf is None

    def test_manual_ewc_validation(self) -> None:
        # Test valid ewc is returned in the same state
        type = EstimateWithCovarianceType.EWC_GENERIC
        est = np.zeros((3, 1))
        cov = np.eye(3)
        valid_ewc = EstimateWithCovariance(type, est, cov)
        ret_ewc = validate_manual_ewc(valid_ewc, 3, self.mediator)
        assert ret_ewc is not None
        self._compare_ewc(ret_ewc, valid_ewc)
        # Test convertable dimensionality
        est = np.zeros((3,))
        cov = np.array([1, 1, 1])
        convertable_ewc = EstimateWithCovariance(type, est, cov)
        ret_ewc = validate_manual_ewc(convertable_ewc, 3, self.mediator)
        assert ret_ewc is not None
        self._compare_ewc(ret_ewc, valid_ewc)
        assert ret_ewc.estimate.ndim == 2
        assert ret_ewc.covariance.ndim == 2
        # Test invalid dimensionality for est and cov
        assert (
            validate_manual_ewc(
                EstimateWithCovariance(type, np.zeros((3, 1, 3)), cov), 3, self.mediator
            )
            is None
        )
        assert (
            validate_manual_ewc(
                EstimateWithCovariance(type, est, np.zeros((3, 3, 3))), 3, self.mediator
            )
            is None
        )
        # Test state count mismatch for est and cov
        assert (
            validate_manual_ewc(
                EstimateWithCovariance(type, est, cov), 4, self.mediator
            )
            is None
        )
        assert (
            validate_manual_ewc(
                EstimateWithCovariance(type, np.zeros((4,)), cov), 4, self.mediator
            )
            is None
        )
        # Test wrong size in 2nd dimension
        assert (
            validate_manual_ewc(
                EstimateWithCovariance(type, np.zeros((3, 2)), cov), 3, self.mediator
            )
            is None
        )
        assert (
            validate_manual_ewc(
                EstimateWithCovariance(type, est, np.zeros((3, 2))), 3, self.mediator
            )
            is None
        )

    def _compare_ewc(
        self, ewc1: EstimateWithCovariance, ewc2: EstimateWithCovariance
    ) -> None:
        assert ewc1.type == ewc2.type
        assert np.allclose(ewc1.estimate, ewc2.estimate)
        assert np.allclose(ewc1.covariance, ewc2.covariance)

    def _validate_conf_to_registry(self, test_conf: BaseConfig) -> None:
        kv = self.mediator.registry.batch_start(CONFIG_TEST_GROUP)
        conf_fields = [f for f in fields(test_conf) if f.name != 'group']
        for conf_field in conf_fields:
            val: RegistryValueTypeUnion | Enum | None = kv[conf_field.name]
            conf_val = getattr(test_conf, conf_field.name)
            if isinstance(val, np.ndarray):
                assert np.all(val == conf_val)
            elif isinstance(conf_val, Enum):
                val = type(conf_val)(val)
            else:
                assert val == conf_val

    def _validate_conf_from_registry(
        self, test_conf: BaseConfig, result_conf: BaseConfig
    ) -> None:
        # Go through config values and validate that they were received correctly
        test_fields = fields(test_conf)
        result_fields = fields(result_conf)
        assert test_fields == result_fields
        for test_field, result_field in zip(test_fields, result_fields, strict=True):
            assert test_field.name == result_field.name
            test_val = getattr(test_conf, test_field.name)
            result_val = getattr(result_conf, result_field.name)
            assert type(test_val) is type(result_val)
            if isinstance(test_val, np.ndarray):
                assert np.all(test_val == result_val)
                assert test_val.dtype == result_val.dtype
            else:
                assert test_val == result_val

        # Make sure there weren't any error messages:
        assert DEBUG_LOG == ''
