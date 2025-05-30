# State Modeling Plugin

The {py:obj}`State Modeling Plugin<pntos.api.StateModelingPlugin>` contains lists of
{py:obj}`Measurement Processor<pntos.api.StandardMeasurementProcessor>`s, {py:obj}`State
Block<pntos.api.StandardStateBlock>`s, and {py:obj}`Virtual State
Block<pntos.api.VirtualStateBlock>`s and a factory to construct them (the {py:obj}`State
Model Provider<pntos.api.StandardStateModelProvider>`). At the {py:obj}`Orchestration
Plugin<pntos.api.OrchestrationPlugin>`'s request it constructs these objects and adds
them to the fusion engine (e.g.
{py:obj}`StandardFusionEngine<pntos.api.StandardFusionEngine>`).

Below is some very brief information about {py:obj}`Measurement
Processor<pntos.api.StandardMeasurementProcessor>`s, {py:obj}`State
Block<pntos.api.StandardStateBlock>`s, and {py:obj}`Virtual State
Block<pntos.api.VirtualStateBlock>`s.

## Measurement Processor

{py:obj}`Measurement Processor<pntos.api.StandardMeasurementProcessor>`s are
responsible for providing the model that the Filter Strategy uses to update its states
given a sensor measurement.

![image](../images/measurement_processor.svg)

## State Block

{py:obj}`State Block<pntos.api.StandardStateBlock>`s provide the Filter Strategy with
states and a model to propagate those states.

![image](../images/state_block.svg)

## Virtual State Block

Consider the case where a given {py:obj}`State Block<pntos.api.StandardStateBlock>`
provides three latitude-longitude-altitude (LLH) states and a given {py:obj}`Measurement
Processor<pntos.api.StandardMeasurementProcessor>` provides a model to update three
Earth-centered, Earth-fixed (ECEF) position states. Normally this {py:obj}`Measurement
Processor<pntos.api.StandardMeasurementProcessor>` and {py:obj}`State
Block<pntos.api.StandardStateBlock>` would be incompatible with each other, but a
{py:obj}`Virtual State Block<pntos.api.VirtualStateBlock>` that converts between ECEF
position and LLH position could bridge the gap.

In short, {py:obj}`Virtual State Block<pntos.api.VirtualStateBlock>`s convert the
states provided by {py:obj}`State Block<pntos.api.StandardStateBlock>`s.



<!-- TODO (#179) https://git.aspn.us/pntos/pntos-python/-/issues/179 -->