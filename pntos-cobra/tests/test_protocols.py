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
    SimpleGpsOrchestrationPlugin,
    SimpleRegistryPlugin,
)


def test_completeness() -> None:
    if TYPE_CHECKING:
        _cnt_plug: ControllerPlugin = SimpleControllerPlugin('my_controller')
        _reg_plug: RegistryPlugin = SimpleRegistryPlugin('my_registry')
        _orc_plug: OrchestrationPlugin = SimpleGpsOrchestrationPlugin(
            'my_orchestration'
        )

        _reg: Registry = _reg_plug.new_registry()
        _kv: KeyValueStore = _reg.batch_start('123')
