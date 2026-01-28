# Fusion Strategy Plugin

The {py:obj}`Fusion Strategy Plugin<pntos.api.FusionStrategyPlugin>` does the core
estimation work. It determines what type of estimator is used, such as an Extended
Kalman Filter (EKF), Rao-Blackwellized Particle Filter (RBPF), or something else. It
usually receives models from the state blocks, virtual state blocks, and measurement
processors in the {py:obj}`State Modeling Plugin<pntos.api.StateModelingPlugin>` via the
{py:obj}`Fusion Plugin<pntos.api.FusionPlugin>` and propagates and updates its states
accordingly.

<!-- TODO (#172) https://git.aspn.us/pntos/pntos-python/-/issues/172 -->