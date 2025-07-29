import unittest
from dataclasses import fields
from enum import Enum

import numpy as np
from aspn23 import TypeTimestamp
from pntos.api import LoggingLevel, Mediator, Message, RegistryValueTypeUnion
from pntos.cobra import StandardRegistryPlugin
from pntos.cobra.config import (
    AlignmentStrategy,
    BaseConfig,
    DownsamplerConfig,
    ImuConfig,
    ManualAlignmentConfig,
    SensorConfig,
    StaticAlignmentConfig,
    config_from_registry,
    config_to_registry,
)

DEBUG_LOG: str = ''
CONFIG_TEST_GROUP = 'config_test_group'


class DummyMediator(Mediator):
    def get_filter_description_list(self) -> list[str]:
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
        DEBUG_LOG = message


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
            True,
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
            CONFIG_TEST_GROUP, ['chan1', 'chan2', 'chan3'], [1, 2, 3]
        )
        # Test config_to_registry
        config_to_registry(test_conf, self.mediator)
        self._validate_conf_to_registry(test_conf)

        result_conf = config_from_registry(
            DownsamplerConfig, self.mediator, CONFIG_TEST_GROUP
        )
        assert result_conf is not None
        self._validate_conf_from_registry(test_conf, result_conf)

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
        config = StaticAlignmentConfig(
            CONFIG_TEST_GROUP, AlignmentStrategy.STATIC, 1.23, imu_model
        )

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
            True,
            'NCC-1701',
        )

        # Test config_to_registry
        config_to_registry(test_conf, self.mediator)
        self._validate_conf_to_registry(test_conf)

        # Whoops, modified a value in the registry
        reg = self.mediator.registry.batch_start(CONFIG_TEST_GROUP)
        reg['use_for_alignment'] = ['wrong type']
        reg.batch_end()

        # Test config_from_registry()
        result_conf = config_from_registry(
            SensorConfig, self.mediator, CONFIG_TEST_GROUP
        )
        assert result_conf is None

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
        for test_field, result_field in zip(test_fields, result_fields):
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
