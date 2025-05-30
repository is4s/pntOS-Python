# Fusion Plugin

The {py:obj}`Fusion Plugin<pntos.api.FusionPlugin>` accepts sensor measurements (and
possibly a reference {term}`PVA` solution from the {py:obj}`Inertial
Plugin<pntos.api.InertialPlugin>`) via the {py:obj}`Orchestration
Plugin<pntos.api.OrchestrationPlugin>` and uses them to generate a fused {term}`PNT` solution.

The Fusion plugin may also dispatch to a {py:obj}`Fusion Strategy
Plugin<pntos.api.FusionStrategyPlugin>` to do the {term}`PNT` fusion. In this case, it does all the book-keeping to keep track of
which state blocks and measurement processors correspond to which states in the
{py:obj}`Fusion Strategy Plugin<pntos.api.FusionStrategyPlugin>`.

<!-- TODO (#171) https://git.aspn.us/pntos/pntos-python/-/issues/171 -->