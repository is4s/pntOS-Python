import numpy as np
from numpy import float64
from numpy.typing import NDArray
from pntos.api.plugins.common import FusionType
from pntos.api.plugins.fusion_strategy import (
    FusionStrategyPlugin,
    StandardDynamicsModel,
    StandardFusionStrategy,
    StandardMeasurementModel,
)
from pntos.cobra.SimpleEkfFusionStrategyPlugin import SimpleEkfFusionStrategyPlugin


def print_ekf(ekf: StandardFusionStrategy, Annotation: str = 'None'):
    if Annotation != 'None':
        print(Annotation)
    print('Num states = ', ekf.get_num_states())
    print('x = ', ekf.get_estimate())
    print('P = ', ekf.get_covariance())


plugin = SimpleEkfFusionStrategyPlugin('ekf')
print(
    'fusion type supported = ',
    plugin.is_fusion_type_supported(FusionType.STANDARD_MODEL),
)

ekf = plugin.new_fusion_strategy(FusionType.STANDARD_MODEL)
print_ekf(ekf, '\nInitial')

n = ekf.add_states(
    initial_estimate=1 * np.ones([1, 1]), initial_covariance=1 * np.ones([1, 1])
)
# cross_covariance: Optional[NDArray] = None,)
print_ekf(ekf, '\nAdded 1 state')
print('index of first state added = ', n)


n = ekf.add_states(
    initial_estimate=2 * np.ones([2, 1]), initial_covariance=2 * np.ones([2, 2])
)
# cross_covariance: Optional[NDArray] = None,)
print_ekf(ekf, '\nAdded 2 states')
print('index of first state added = ', n)

n = ekf.add_states(
    initial_estimate=3 * np.ones([3, 1]),
    initial_covariance=3 * np.ones([3, 3]),
    cross_covariance=np.random.randn(3, 3),
)
print_ekf(ekf, '\nAdded 3 states')
print('index of first state added = ', n)

ekf.set_estimate_slice(new_estimate=0.5 * np.ones([3, 1]), first_index=2)
ekf.set_covariance_slice(
    new_covariance=-0.75 * np.ones([2, 2]), first_row=2, first_col=3
)
print_ekf(ekf, '\nchanged estimate and covariance slices')

ekf.remove_states(first_index=2, count=2)
print_ekf(ekf, '\nremoved 2 states starting with index 2')

ekf2 = ekf.clone()
print_ekf(ekf2, '\nClone')

ekf.remove_states(0, ekf.get_num_states())
print_ekf(ekf, '\nremoved all states')


n = ekf.add_states(initial_estimate=np.zeros([2, 1]), initial_covariance=np.eye(2))
# cross_covariance: Optional[NDArray] = None,)
print_ekf(ekf, '\nAdded 2 states')
print('index of first state added = ', n)

dt = 1
Phi = np.array([[1, dt], [0, 1]])


def g(x: NDArray):
    return Phi @ x


H = np.array([[1, 0]])


def h(x: NDArray):
    return H @ x


R = np.eye(1)
Qd = np.zeros([2, 2])
Qd[1, 1] = 0.01
z = np.array([[2.0]])

meas_model = StandardMeasurementModel(z=z, h=h, H=H, R=R)
dynamics_model = StandardDynamicsModel(g=g, Phi=Phi, Qd=Qd)

for j in range(1, 10):
    ekf.propagate(dynamics_model)
    print_ekf(ekf, '\nafter propagate to ' + str(j * dt))

    ekf.update(meas_model)
    print_ekf(ekf, '\nafter update at ' + str(j * dt))


# Original from Kyle
""""
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

    my_H = np.array([[1, 0, 0]])

    def my_h(x: NDArray):
        return my_H @ x

    filter.update(
        StandardMeasurementModel(z=np.array([1]), h=my_h, H=my_H, R=np.array([5]))
    )

    print(filter.get_estimate())
    print(filter.get_covariance())

use_plugin(EkfFusionStrategyPlugin('ekf_strategy'))
"""
