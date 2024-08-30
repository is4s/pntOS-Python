import numpy as np
from numpy.typing import NDArray
from pntos.api.plugins.fusion_strategy import (
    FusionStrategyPlugin,
    FusionType,
    StandardDynamicsModel,
    StandardFusionStrategy,
    StandardMeasurementModel,
)


def use_plugin(plugin: FusionStrategyPlugin):
    assert plugin.is_fusion_type_supported(FusionType.STANDARD_MODEL)
    filter = plugin.new_fusion_strategy(FusionType.STANDARD_MODEL)
    assert isinstance(filter, StandardFusionStrategy)
    filter.add_states(
        initial_estimate=np.zeros((3, 1)), initial_covariance=np.zeros((3, 3))
    )

    def my_g(x: NDArray):
        return x + 1

    filter.propagate(StandardDynamicsModel(g=my_g, Phi=np.eye(3, 3), Qd=np.eye(3, 3)))

    print(filter.get_estimate())
    print(filter.get_covariance())

    my_H = np.array([1, 0, 0])

    def my_h(x: NDArray):
        return my_H @ x

    filter.update(
        StandardMeasurementModel(z=np.array([1]), h=my_h, H=my_H, R=np.array([5]))
    )

    print(filter.get_estimate())
    print(filter.get_covariance())


# use_plugin(EkfStrategyPlugin())
