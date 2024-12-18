from typing import TYPE_CHECKING

from pntos.api import (
    ControllerPlugin,
    KeyValueStore,
    OrchestrationPlugin,
    Registry,
    RegistryPlugin,
)
from pntos.cobra import (
    SimpleControllerPlugin,
    SimpleOrchestrationPlugin,
    SimpleRegistryPlugin,
)


def test_completeness() -> None:
    if TYPE_CHECKING:
        _cnt_plug: ControllerPlugin = SimpleControllerPlugin('my_controller')
        _reg_plug: RegistryPlugin = SimpleRegistryPlugin('my_registry')
        _orc_plug: OrchestrationPlugin = SimpleOrchestrationPlugin('my_orchestration')

        _reg: Registry = _reg_plug.new_registry()
        _kv: KeyValueStore = _reg.batch_start('123')
