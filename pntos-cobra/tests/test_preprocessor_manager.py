# ty:ignore[unresolved-attribute]

from collections.abc import Callable
from typing import TypeAlias

import pytest
from pntos.api import (
    Mediator,
    Message,
    Preprocessor,
    PreprocessorPlugin,
    RegistryPlugin,
)
from pntos.cobra import StandardRegistryPlugin
from pntos.cobra.config import (
    BaseConfig,
    PreprocessorConfig,
)
from pntos.cobra.internal import (
    PreprocessorManager,
    StandardMediator,
)
from typing_extensions import override

MediatorFactoryType: TypeAlias = Callable[
    [tuple[PreprocessorConfig, ...] | None], StandardMediator
]

PreprocessorPluginsFactoryType: TypeAlias = Callable[
    [StandardMediator], list[PreprocessorPlugin]
]


class MockPreprocessor(Preprocessor):
    @override
    def process_pntos_message(self, message: Message) -> list[Message] | None:
        return [message]


class MockPreprocessorPlugin(PreprocessorPlugin):
    _mock_preprocessors: tuple = (
        type('MockPreprocessor1', (MockPreprocessor,), {'label': 'p1'}),
        type('MockPreprocessor2', (MockPreprocessor,), {'label': 'p2'}),
        type('MockPreprocessor3', (MockPreprocessor,), {'label': 'p3'}),
        type('MockPreprocessor4', (MockPreprocessor,), {'label': 'p4'}),
        type('MockPreprocessor5', (MockPreprocessor,), {'label': 'p5'}),
        type('MockPreprocessor6', (MockPreprocessor,), {'label': 'p6'}),
    )

    def __init__(self, identifier: str) -> None:
        self.identifier = identifier

    @override
    def init_plugin(
        self,
        plugin_resources_location: str | None = None,
        mediator: Mediator | None = None,
    ) -> None:
        self.mediator = mediator
        self.preprocessor_identifiers = [mp.label for mp in self._mock_preprocessors]

    @override
    def shutdown_plugin(self) -> None:
        return

    @override
    def new_preprocessor(
        self, preprocessor_index: int, config_group: str | None = None
    ) -> Preprocessor | None:
        if 0 < preprocessor_index > len(self._mock_preprocessors) - 1:
            return None
        return self._mock_preprocessors[preprocessor_index]()


@pytest.fixture
def mediator() -> MediatorFactoryType:
    def _mediator(
        preprocessor_configs: tuple[PreprocessorConfig, ...] | None = None,
    ) -> StandardMediator:
        configs: list[BaseConfig] = (
            list(preprocessor_configs) if preprocessor_configs else []
        )
        registry_plugin = StandardRegistryPlugin('Standard registry', config=configs)
        mediator = StandardMediator(registry_plugin.identifier, RegistryPlugin)
        registry_plugin.init_plugin(mediator=mediator)
        registry = registry_plugin.new_registry()
        StandardMediator.registry = registry
        return mediator

    return _mediator


@pytest.fixture
def preprocessor_plugins() -> PreprocessorPluginsFactoryType:
    def _preprocessor_plugins(mediator: StandardMediator) -> list[PreprocessorPlugin]:
        plugin = MockPreprocessorPlugin('Cobra Mock Preprocessor Plugin')
        plugin.init_plugin(mediator=mediator)
        return [plugin]

    return _preprocessor_plugins


@pytest.fixture
def preprocessor_configs() -> tuple[PreprocessorConfig, ...]:
    return (
        PreprocessorConfig(
            group='config/p1', identifier='p1', channels=('/sensor/imu',)
        ),
        PreprocessorConfig(
            group='config/p2', identifier='p2', channels=('/sensor/imu',)
        ),
        PreprocessorConfig(
            group='config/p3', identifier='p3', channels=('/sensor/pos', '/sensor/vel')
        ),
        PreprocessorConfig(
            group='config/p4', identifier='p4', channels=('imu',), regex=True
        ),
        PreprocessorConfig(
            group='config/p5', identifier='p5', channels=('pos|vel',), regex=True
        ),
        PreprocessorConfig(group='config/p6', identifier='p6', channels=None),
    )


@pytest.fixture
def manager(
    mediator: MediatorFactoryType,
    preprocessor_configs: tuple[PreprocessorConfig, ...],
    preprocessor_plugins: PreprocessorPluginsFactoryType,
) -> PreprocessorManager:
    configured_mediator = mediator(preprocessor_configs)
    return PreprocessorManager(
        preprocessor_plugins(configured_mediator),
        preprocessor_configs,
        configured_mediator,
    )


def test_with_none_configs(
    mediator: MediatorFactoryType,
    preprocessor_plugins: PreprocessorPluginsFactoryType,
) -> None:
    unconfigured_mediator = mediator(None)
    manager = PreprocessorManager(
        preprocessor_plugins(unconfigured_mediator), (), unconfigured_mediator
    )
    assert manager._mediator
    assert not manager._descriptors
    assert not manager._chains


def test_with_none_plugins(
    mediator: MediatorFactoryType,
    preprocessor_configs: tuple[PreprocessorConfig, ...],
) -> None:
    manager = PreprocessorManager(
        [],
        preprocessor_configs,
        mediator(preprocessor_configs),
    )
    assert not manager._descriptors


def test__find_preprocessor(
    mediator: MediatorFactoryType,
    preprocessor_configs: tuple[PreprocessorConfig, ...],
    preprocessor_plugins: PreprocessorPluginsFactoryType,
) -> None:
    for preprocessor_config in preprocessor_configs:
        preprocessor = PreprocessorManager._find_preprocessor(
            preprocessor_config.identifier,
            preprocessor_config.group,
            preprocessor_plugins(mediator(preprocessor_configs)),
        )
        assert preprocessor


def test_preprocess_message_no_channel_matches(manager: PreprocessorManager) -> None:
    manager.preprocess_message(Message(None, source_identifier='/sensor/'))
    preprocessors: list[Preprocessor] | None = manager._chains['/sensor/']

    assert preprocessors
    assert len(preprocessors) == 1
    assert all(issubclass(type(p), MockPreprocessor) for p in preprocessors)

    # MockPreprocessor6 has field `channels` == None; it is expected to be in this preprocessor chain
    assert preprocessors[0].label == 'p6'


def test_preprocess_message_one_channel_one_preprocessor_match(
    manager: PreprocessorManager,
) -> None:
    manager.preprocess_message(Message(None, source_identifier='/sensor/vel'))
    preprocessors: list[Preprocessor] | None = manager._chains['/sensor/vel']

    assert preprocessors
    assert len(preprocessors) == 3
    assert all(issubclass(type(p), MockPreprocessor) for p in preprocessors)

    assert preprocessors[0].label == 'p3'

    # Included because 'p5' has regex match and 'p6' has channels=None
    assert preprocessors[1].label == 'p5'
    assert preprocessors[2].label == 'p6'


def test_preprocess_message_one_channel_two_preprocessor_matches(
    manager: PreprocessorManager,
) -> None:
    manager.preprocess_message(Message(None, source_identifier='/sensor/imu'))
    preprocessors: list[Preprocessor] | None = manager._chains['/sensor/imu']

    assert preprocessors
    assert len(preprocessors) == 4
    assert all(issubclass(type(p), MockPreprocessor) for p in preprocessors)

    assert preprocessors[0].label == 'p1'
    assert preprocessors[1].label == 'p2'

    # Included because 'p4' has regex match and 'p6' has channels=None
    assert preprocessors[2].label == 'p4'
    assert preprocessors[3].label == 'p6'


def test_preprocess_message_nonetype_in_config_channels(
    manager: PreprocessorManager,
) -> None:
    manager.preprocess_message(Message(None, source_identifier='/sensor/'))
    preprocessors: list[Preprocessor] | None = manager._chains['/sensor/']

    assert preprocessors
    assert len(preprocessors) == 1
    assert all(issubclass(type(p), MockPreprocessor) for p in preprocessors)
    assert preprocessors[0].label == 'p6'


def test_preprocess_message_with_regex_in_config_channels(
    manager: PreprocessorManager,
) -> None:
    manager.preprocess_message(Message(None, source_identifier='/sensor/imu'))
    preprocessors: list[Preprocessor] | None = manager._chains['/sensor/imu']

    assert preprocessors
    assert len(preprocessors) == 4
    assert all(issubclass(type(p), MockPreprocessor) for p in preprocessors)

    assert preprocessors[0].label == 'p1'
    assert preprocessors[1].label == 'p2'
    assert preprocessors[2].label == 'p4'
    assert preprocessors[3].label == 'p6'

    manager.preprocess_message(Message(None, source_identifier='/sensor/pos'))
    preprocessors: list[Preprocessor] | None = manager._chains['/sensor/pos']

    assert preprocessors
    assert len(preprocessors) == 3
    assert all(issubclass(type(p), MockPreprocessor) for p in preprocessors)

    assert preprocessors[0].label == 'p3'
    assert preprocessors[1].label == 'p5'
    assert preprocessors[2].label == 'p6'
