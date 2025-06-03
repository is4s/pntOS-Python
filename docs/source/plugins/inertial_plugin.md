# Inertial Plugin

The {py:obj}`Inertial Plugin<pntos.api.InertialPlugin>` serves as a factory for
inertials. There are two types: the {py:obj}`pntos.api.StandardInertialMechanization` and the {py:obj}`pntos.api.ExternalInertial`.

The {py:obj}`pntos.api.StandardInertialMechanization` receives an
initial {term}`PVA` alignment and {term}`IMU` measurements which it mechanizes to
produce {term}`INS` solutions. It might also handle inertial feedback from the {py:obj}`Orchestration
Plugin<pntos.api.OrchestrationPlugin>`.

The other type of inertial is the {py:obj}`pntos.api.ExternalInertial`, which tracks an
external {term}`INS` and buffers the solution.

<!-- TODO (#173) https://git.aspn.us/pntos/pntos-python/-/issues/173 -->