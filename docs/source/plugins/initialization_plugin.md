# Initialization Plugin

The {py:obj}`Initialization Pluign<pntos.api.InitializationPlugin>` is a factory for two
types of initializers: 

| Initialization                                                                     | Description                                                                                                                                                                                                                   |
| ---------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| {py:obj}`InertialInitializationStrategy<pntos.api.InertialInitializationStrategy>` | Calculates an initial solution for inertial mechanization (such as in the {py:obj}`Inertial Plugin<pntos.api.InertialPlugin>`). This could be as simple as a manual alignment, or something more complex like gyrocompassing. |
| {py:obj}`InitialEstimateWithCovariance<pntos.api.InitialEstimateWithCovariance>`   | A more generic initialization strategy, used for setting an initial estimate and covariance. Usually, this would be used to initialize a state block.                                                                         |

Both strategies allow the {py:obj}`Orchestration Plugin<pntos.api.OrchestrationPlugin>`
to query whether motion is needed, stationary data is needed, or if the initializer
doesn't care about motion. Additionally, the {py:obj}`Orchestration
Plugin<pntos.api.OrchestrationPlugin>` can query the status of the initialization so
that the {py:obj}`Orchestration Plugin<pntos.api.OrchestrationPlugin>` knows when the
initial solution is ready.

<!-- TODO (#174) https://git.aspn.us/pntos/pntos-python/-/issues/174 -->