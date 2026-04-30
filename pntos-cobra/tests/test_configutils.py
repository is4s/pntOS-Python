import unittest
from dataclasses import dataclass, field, fields
from enum import IntEnum
from pathlib import Path
from typing import Any, get_args, get_origin

import numpy as np
from aspn23 import (
    MeasurementAltitude,
    MeasurementAltitudeErrorModel,
    MeasurementAltitudeReference,
    TypeHeader,
    TypeTimestamp,
)
from numpy import float64, int64, ndarray
from numpy.typing import NDArray
from pntos.api import (
    EstimateWithCovariance,
    EstimateWithCovarianceType,
    Message,
    RegistryValueTypeUnion,
)
from pntos.cobra import StandardRegistryPlugin
from pntos.cobra.config import (
    BaseConfig,
    DownsamplerConfig,
    FogmConfig,
    ImuConfig,
    ImuRotatorConfig,
    InertialConfig,
    ManualAlignmentConfig,
    MountingConfig,
    PinsonStateBlockConfig,
    PinsonVelocityMPConfig,
    PinsonWithNedFogmPositionMPConfig,
    PreprocessorConfig,
    StandardOrchestrationConfig,
    StateBlockConfig,
    StaticAlignmentConfig,
    TimeAdjusterConfig,
    config_from_registry,
    config_to_registry,
)
from pntos.cobra.internal import DummyMediator
from pntos.cobra.utils import validate_manual_ewc


class DummyEnum(IntEnum):
    RED = 0


DEBUG_LOG: Path = Path()
CONFIG_TEST_GROUP = 'config_test_group'
SUPPORTED_TYPES = [
    int,
    float,
    str,
    bool,
    BaseConfig,
    list[int],
    list[float],
    list[str],
    list[BaseConfig],
    list[list[float]],
    list[list[int]],
    tuple[int, ...],
    tuple[str, ...],
    tuple[float, ...],
    tuple[BaseConfig, ...],
    tuple[tuple[float, ...], ...],
    tuple[tuple[int, ...], ...],
    NDArray[float64],  # Any-dimension array of floats (will be 1d for test)
    NDArray[int64],  # Any-dimension array of ints (will be 1d for test)
    ndarray[(2, 2), np.dtype[float64]],  # type: ignore[misc] # 2d array of floats
    ndarray[(2, 2), np.dtype[int64]],  # type: ignore[misc] # 2d array of ints
    ndarray[(2, 2, 2), np.dtype[float64]],  # type: ignore[misc] # 3d array of floats
    ndarray[(2, 2, 2), np.dtype[int64]],  # type: ignore[misc] # 3d array of ints
    DummyEnum,
    EstimateWithCovariance,
]


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

    def test_MountingConfig_to_from_registry(self) -> None:
        test_conf = MountingConfig(
            CONFIG_TEST_GROUP,
            (0.7, 0.8, 0.9),
            (1.1, 2.2, 3.3, 4.4),
        )

        # Test config_to_registry
        config_to_registry(test_conf, self.mediator)
        self._validate_conf_to_registry(test_conf)

        # Test config_from_registry()
        result_conf = config_from_registry(
            MountingConfig, self.mediator, CONFIG_TEST_GROUP
        )
        assert result_conf is not None

        self._validate_conf_from_registry(test_conf, result_conf)

    def test_DownsamplerConfig_to_from_registry(self) -> None:
        test_conf = DownsamplerConfig(
            CONFIG_TEST_GROUP,
            channels_to_downsample=('chan1', 'chan2', 'chan3'),
            downsampling_factors=(1, 2, 3),
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
            alignment_channels=('/sensor/ublox-ZED-F9T/position', '/sensor/vn-100/imu'),
            pinson_sb_config=PinsonStateBlockConfig(
                group='config/pinson_block',
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
            additional_sb_configs=(
                StateBlockConfig(
                    group='config/pos_fogm_block',
                    identifier='fogm',
                    label='pos_sensor_error',
                ),
            ),
            mp_configs=(
                PinsonWithNedFogmPositionMPConfig(
                    group='config/pos_measurement_processor',
                    label='pos',
                    channel='/sensor/ublox-ZED-F9T/position',
                    state_block_labels=('pinson15', 'pos_sensor_error'),
                    lever_arm=(0.7, 0.8, 0.9),
                ),
                PinsonVelocityMPConfig(
                    group='config/vel_measurement_processor',
                    label='vel',
                    channel='/sensor/ublox-ZED-F9T/velocity',
                    state_block_labels=('pinson15',),
                ),
            ),
            inertial_config=InertialConfig(
                group='config/inertial',
                expected_dt=0.01,
                channels=('/sensor/vn-100/imu',),
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
            ),
        )

        # Verify configs survive
        config_to_registry(test_conf, self.mediator)
        result_config = config_from_registry(
            StandardOrchestrationConfig,
            self.mediator,
            StandardOrchestrationConfig.group,
        )
        assert result_config is not None
        self._validate_conf_from_registry(test_conf, result_config)

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
        test_conf = FogmConfig(
            CONFIG_TEST_GROUP,
            (0.1, 0.2, 0.3),
            (0.4, 0.5, 0.6, 0.7),
        )

        # Test config_to_registry
        config_to_registry(test_conf, self.mediator)
        self._validate_conf_to_registry(test_conf)

        # Whoops, modified a value in the registry
        reg = self.mediator.registry.batch_start(CONFIG_TEST_GROUP)
        reg['sigma'] = ['wrong type']
        reg.batch_end()

        # Test config_from_registry()
        result_conf = config_from_registry(FogmConfig, self.mediator, CONFIG_TEST_GROUP)
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
            val: RegistryValueTypeUnion | tuple[Any, ...] | IntEnum | None = kv[
                conf_field.name
            ]
            conf_val = getattr(test_conf, conf_field.name)
            if isinstance(val, np.ndarray):
                assert np.all(val == conf_val)
            elif isinstance(conf_val, IntEnum):
                assert isinstance(val, int)
                val = type(conf_val)(val)
            elif isinstance(val, list):
                val = tuple(val)
            else:
                assert val == conf_val
        kv.batch_end()

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
            assert issubclass(type(test_val), type(result_val))
            if isinstance(test_val, np.ndarray):
                assert np.all(test_val == result_val)
                assert test_val.dtype == result_val.dtype
            elif isinstance(test_val, EstimateWithCovariance):
                self._compare_ewc(test_val, result_val)
            elif isinstance(test_val, (tuple, list)):
                assert len(test_val) > 0
                if isinstance(test_val[0], BaseConfig):
                    for i in range(len(test_val)):
                        assert issubclass(type(test_val[i]), type(result_val[i]))
                        assert test_val[i].group == result_val[i].group
            elif isinstance(test_val, BaseConfig):
                assert test_val.group == result_val.group
            else:
                assert test_val == result_val

        # Make sure there weren't any error messages:
        assert Path() == DEBUG_LOG

    def _make_config(
        self, field_name: str, field_type: type, optional: bool = False
    ) -> type[BaseConfig]:
        annotations: dict[str, Any] = {}

        actual_type = field_type | None if optional else field_type
        annotations['group'] = str
        annotations[field_name] = actual_type

        fields_dict = {
            '__annotations__': annotations,
            'group': field(default='dynamic_test'),
            field_name: field(default=None if optional else ...),
        }

        dynamic_class: type[BaseConfig] = dataclass(
            type('DynamicConfigClass', (BaseConfig,), fields_dict)
        )
        return dynamic_class

    def _create_dummy_value(self, in_type: type[Any]) -> Any:  # noqa: ANN401
        origin = get_origin(in_type)

        if origin is tuple:
            val = self._create_dummy_value(get_args(in_type)[0])
            return (val, val)
        if origin is list:
            val = self._create_dummy_value(get_args(in_type)[0])
            return [val, val]
        if origin is np.ndarray:
            shape, dtype = get_args(in_type)
            val = self._create_dummy_value(get_args(dtype)[0])
            if shape is Any:
                shape = (2,)
            return np.full(shape, val)
        if in_type is bool:
            return True
        # Need this to come before the int check, since IntEnum objects are also an int
        if issubclass(in_type, IntEnum):
            return next(iter(in_type))
        if issubclass(in_type, (int, np.int_)):
            return 1
        if issubclass(in_type, (float, np.floating)):
            return 1.23
        if in_type is str:
            return 'test'
        if issubclass(in_type, BaseConfig):
            return in_type(group='dummy_val_test')
        if issubclass(in_type, Message):
            return in_type(
                wrapped_message=MeasurementAltitude(
                    header=TypeHeader(0, 0, 0, 0),
                    time_of_validity=TypeTimestamp(0),
                    reference=MeasurementAltitudeReference.HAE,
                    altitude=1.0,
                    variance=0.1,
                    error_model=MeasurementAltitudeErrorModel.NONE,
                    error_model_params=np.array([]),
                    integrity=[],
                ),
                source_identifier='dummy',
            )
        if issubclass(in_type, EstimateWithCovariance):
            return in_type(
                type=EstimateWithCovarianceType.EWC_GENERIC,
                estimate=np.zeros((3, 1)),
                covariance=np.eye(3),
            )

        raise ValueError(f"Don't know how to create dummy value for {in_type}")

    def test_supported_types(self) -> None:
        for i in range(3):
            for j, t in enumerate(SUPPORTED_TYPES):
                dynamic_group = f'dynamic_test_{i}{j}'
                DynConf = self._make_config('dynamic_field', t, optional=bool(i))  # type: ignore[arg-type]
                # test with dummy value when type hint is and isn't optional; test with None
                val = self._create_dummy_value(t) if i in {0, 2} else None  # type: ignore[arg-type]
                conf = DynConf(  # type: ignore[call-arg]
                    dynamic_field=val,
                    group=dynamic_group,
                )
                config_to_registry(conf, self.mediator)
                out_conf = config_from_registry(DynConf, self.mediator, dynamic_group)
                assert out_conf is not None
                self._validate_conf_from_registry(conf, out_conf)

    def test_int_to_float_conversion(self) -> None:
        group = 'itfconv'
        DynConf = self._make_config('dynamic_field', float)
        val = 1
        conf = DynConf(  # type: ignore[call-arg]
            dynamic_field=val, group=group
        )
        config_to_registry(conf, self.mediator)
        out_conf = config_from_registry(DynConf, self.mediator, group)
        assert out_conf is not None
        assert conf.dynamic_field == out_conf.dynamic_field  # type: ignore[attr-defined]

    def test_list_to_tuple_conversion(self) -> None:
        group = 'md_list_to_tuple'
        DynConf = self._make_config(
            'dynamic_field', tuple[tuple[float, float], tuple[float, float]]
        )
        val = [[1, 2], [3, 4]]
        conf = DynConf(  # type: ignore[call-arg]
            dynamic_field=val, group=group
        )
        config_to_registry(conf, self.mediator)
        out_conf = config_from_registry(DynConf, self.mediator, group)
        assert out_conf is not None
        assert np.allclose(conf.dynamic_field, out_conf.dynamic_field)  # type: ignore[attr-defined]

        group = 'str_list_to_tuple'
        DynConf = self._make_config('dynamic_field', tuple[str, ...])
        new_val = ['hello', 'world']
        conf = DynConf(  # type: ignore[call-arg]
            dynamic_field=new_val, group=group
        )
        config_to_registry(conf, self.mediator)
        out_conf = config_from_registry(DynConf, self.mediator, group)
        assert out_conf is not None
        for e1, e2 in zip(conf.dynamic_field, out_conf.dynamic_field, strict=False):  # type: ignore[attr-defined]
            assert e1 == e2

    def test_ndarray_to_tuple_conversion(self) -> None:
        group = 'md_ndarray_to_tuple'
        DynConf = self._make_config(
            'dynamic_field', tuple[tuple[float, float], tuple[float, float]]
        )
        val = np.array(((1, 2), (3, 4)))
        conf = DynConf(  # type: ignore[call-arg]
            dynamic_field=val, group=group
        )
        config_to_registry(conf, self.mediator)
        out_conf = config_from_registry(DynConf, self.mediator, group)
        assert out_conf is not None
        assert np.allclose(conf.dynamic_field, out_conf.dynamic_field)  # type: ignore[attr-defined]

    def test_non_uniform_tuple(self) -> None:
        group = 'non_uniform'
        DynConf = self._make_config(
            'dynamic_field', tuple[tuple[float, ...], tuple[float, float]]
        )
        val = ((1, 2, 3, 4, 5), (6, 7))
        conf = DynConf(dynamic_field=val, group=group)  # type: ignore[call-arg]
        config_to_registry(conf, self.mediator)
        out_conf = config_from_registry(DynConf, self.mediator, group)
        assert out_conf is None

    def test_multi_dim_str_tuple(self) -> None:
        group = 'md_tuple_of_str'
        DynConf = self._make_config(
            'dynamic_field', tuple[tuple[str, ...], tuple[str, ...]]
        )
        val = (('hello', 'world'), ('2001', 'a space odyssey'))
        conf = DynConf(dynamic_field=val, group=group)  # type: ignore[call-arg]
        config_to_registry(conf, self.mediator)
        out_conf = config_from_registry(DynConf, self.mediator, group)
        assert out_conf is None

    def test_optional_config(self) -> None:
        # Test optional config when field defaults to None
        @dataclass
        class Foo(BaseConfig):
            foo: int | None = None

        in_foo = Foo(group='foo', foo=None)
        config_to_registry(in_foo, self.mediator)
        out_foo = config_from_registry(Foo, self.mediator, 'foo')
        assert out_foo is not None
        self._validate_conf_from_registry(in_foo, out_foo)

        # Test optional config when field doesn't default to None
        @dataclass
        class Bar(BaseConfig):
            bar: int | None

        in_bar = Bar(group='bar', bar=None)
        config_to_registry(in_bar, self.mediator)
        out_bar = config_from_registry(Bar, self.mediator, 'bar')
        assert out_bar is not None
        self._validate_conf_from_registry(in_bar, out_bar)
