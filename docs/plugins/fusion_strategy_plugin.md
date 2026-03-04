# Fusion Strategy Plugin

The {py:obj}`Fusion Strategy Plugin<pntos.api.FusionStrategyPlugin>` is a plugin which can be
optionally used by the {py:obj}`Orchestration Plugin<pntos.api.OrchestrationPlugin>`, usually in
conjunction with a {py:obj}`Fusion Plugin<pntos.api.FusionPlugin>`. It is a factory that produces
fusion strategies. Currently, {py:obj}`StandardFusionStrategy<pntos.api.StandardFusionStrategy>` is
the only type of fusion strategy specified by the API, although future versions could define more
advanced types (like a sampled model).

## The Fusion Strategy

The fusion strategy does the core estimation work and is where the actual states are stored. It
determines what type of estimator is used, such as an Extended Kalman Filter (EKF),
Rao-Blackwellized Particle Filter (RBPF), or something else. It usually receives models from the
state blocks, virtual state blocks, and measurement processors via the {py:obj}`Fusion
Plugin<pntos.api.FusionPlugin>` propagating and updating its states accordingly.

# Cobra EKF Strategy Plugin

The Cobra {py:obj}`pntos.cobra.internal.EkfFusionStrategy` implements an EKF using the
{py:obj}`StandardFusionStrategy<pntos.api.StandardFusionStrategy>` model.

While most of this implementation is pretty straightforward, there are a couple of design decisions
documented below.

## Covariance Symmetrization

Mathematically, the covariance matrix should always be symmetric. However, numerical instability can
result in a non-symmetric covariance matrix developing over time. If left as-is, this can result in
more serious issues down the line.

To mitigate this issue, this implementation periodically re-symmetrizes the covariance matrix. It
checks if the covariance matrix is symmetric within a tolerance. If not it applies the following
correction:

$$
P = \frac{P + P^T}{2}
$$

## Matrices

This implementation generally assumes all numpy arrays on API boundaries are are two-dimensional
(matrices). Parameters that would usually be considered one-dimensional (e.g. a measurement vector)
are assumed to be represented as an `Nx1` matrix, where `N` is the length of the vector.

This includes:

- All numpy array parameters
- {py:obj}`pntos.api.StandardMeasurementModel` inputs
- {py:obj}`pntos.api.StandardDynamicsModel` inputs

If this assumption is violated, the plugin will log an `ERROR` message.
