# Fusion Plugin

The {py:obj}`Fusion Plugin<pntos.api.FusionPlugin>` is a plugin which can be optionally used by the
{py:obj}`Orchestration Plugin<pntos.api.OrchestrationPlugin>`. It is a factory that produces fusion
engines. Currently, {py:obj}`StandardFusionEngine<pntos.api.StandardFusionEngine>` is the only type
of fusion engine specified by the API, although future versions could define more advanced types
(like a sampled model).

## The Fusion Engine

The fusion engine performs sensor fusion on behalf of the orchestration plugin. It is the glue
between the [State Modeling Plugin](state_modeling_plugin.md) and the [Fusion Strategy
Plugin](fusion_strategy_plugin.md). It consumes state blocks, measurement processors, and virtual
state blocks from the state model provider and dispatches to the fusion strategy for the actual
estimation work.

For example, when the orchestration plugin adds a state block to the fusion engine, the fusion
engine should tell the fusion strategy to add states equal to the number of states the new block
provides. It will also need to maintain a mapping of the fusion strategy states to the states of the
new block so that it can perform future operations on them.

### State Interactions

The fusion engine allows the user to set and get state estimates and covariances via state block
labels. Its bookkeeping enables it to translate between indices in the fusion strategy and the
corresponding block label.

In the case where the user requests a state estimate or covariance using a virtual state block
label, the fusion engine should convert the state estimate or covariance
using the corresponding virtual state block.

## The {py:obj}`StandardFusionEngine<pntos.api.StandardFusionEngine>`

This type of fusion engine generally assumes either linear (or linearized) models for state
propagation and updates.

### Propagation

One of the major functions of the {py:obj}`StandardFusionEngine<pntos.api.StandardFusionEngine>` is
propagation (also known as prediction). During propagation, the filter time is advanced to
produce new state estimates and covariances by leveraging the models provided by the state blocks.

The {py:obj}`StandardFusionEngine<pntos.api.StandardFusionEngine>` propagates the filter by:

1. Querying the fusion strategy for the current estimate and covariance
2. Providing each state block with the estimate and covariance from `1.` and querying each for a
   dynamics model
3. Combining each dynamics model into one large model
4. Passing the combined model to the fusion strategy

### Update

The other major function of the fusion engine is to update the filter states. In Kalman filtering the
update step incorporates a new sensor measurement, producing a new state estimate and shrinking the
state covariance.

The {py:obj}`StandardFusionEngine<pntos.api.StandardFusionEngine>` consumes sensor measurements by:

1. Querying the fusion strategy for the current estimate and covariance of the states which will be
   mapped to the measurement
2. Providing the corresponding measurement processor with the estimate and covariance from `1.`,
   based on its list of state block labels, in order to query it for a measurement model
3. Passing that model to the fusion strategy

:::{admonition} Virtual state blocks
:class: note
If the measurement processor references the label of a virtual state block in step `2.`, then the
measurement processor will be producing a model for an aliased set of states. In this case, the
{py:obj}`StandardFusionEngine<pntos.api.StandardFusionEngine>` must post-process the update model by
using the corresponding virtual state block to convert the representation to that of the states held
by the fusion strategy.
:::

## The Cobra {py:obj}`StandardFusionEngine<pntos.cobra.internal.StandardFusionEngine>`

Most of the implementation of the Cobra `StandardFusionEngine` is fairly straightforward. However,
there are a couple of design decisions which may be noteworthy.

### The Fusion Strategy

The Cobra `StandardFusionEngine` does not provide its own fusion strategy. A fusion strategy must be
supplied before it can be used.

### Virtual State Block Support

The Cobra `StandardFusionEngine` does support the use of virtual state blocks. This support requires
a significant amount of additional work to form chains of
{py:obj}`VirtualStateBlock<pntos.api.VirtualStateBlock>`s originating from a
{py:obj}`StandardStateBlock<pntos.api.StandardStateBlock>`. Most of this work is delegated to an internal
{py:obj}`VirtualStateBlockManager<pntos.cobra.internal.VirtualStateBlockManager>`.
