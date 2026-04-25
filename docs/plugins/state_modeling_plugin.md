# State Modeling Plugin
The {py:obj}`~pntos.api.StateModelingPlugin` is a factory plugin that provides components used in state modeling.
State modeling is a catch-all term for how we represent quantities to be estimated (states),
sensor measurements, and how they all relate to one another.

State modeling in pntos-python uses a multi-tiered factory structure that begins with the
{py:obj}`~pntos.api.StateModelingPlugin`. The plugin is used to generate one or more *StateModelProviders*.
Each StateModelProvider is a collection of state modeling components that can be used to populate a
fusion engine. Currently, pntos-python has one API-defined StateModelProvider called
the {py:obj}`~pntos.api.StandardStateModelProvider`. This class is also a factory, and as its name
suggests, provides state modeling components for the pntOS *Standard Model*. This model includes:

- {py:obj}`~pntos.api.StandardStateBlock`s which define a set of states and provide a means to propagate them
via the {py:obj}`~pntos.api.StandardDynamicsModel`
- {py:obj}`~pntos.api.StandardMeasurementProcessor`s which relate measurements to a set of states
- {py:obj}`~pntos.api.VirtualStateBlock`s which relate one set of states to another (transformation)

The next few sections will discuss particular points of the API and the existing *Standard Model*
implementations in more depth.

## State Modeling API
### StateModelingPlugin
As mentioned above, the {py:obj}`~pntos.api.StateModelingPlugin` itself is essentially a generator
of StateModelProviders. It, like many of the elements described in this document, use the
[factory pattern](../factory_pattern.md). In addition to everything inherited from {py:obj}`~pntos.api.CommonPlugin`,
there are two additional functions: one that generates a new StateModelProvider of a specified type...

```{literalinclude} ../../pntos-api/src/pntos/api/plugins/state_modeling.py
:language: "python"
:pyobject: StateModelingPlugin.new_state_model_provider
:end-at: " ) -> StateModelProviderType | None:"
:lineno-match:
```

...and one that reports if the plugin *can* generate a model of a given type:

```{literalinclude} ../../pntos-api/src/pntos/api/plugins/state_modeling.py
:language: "python"
:pyobject: StateModelingPlugin.is_fusion_type_supported
:end-at: ") -> bool"
:lineno-match:
```

Both of these are generics that depend on the ``TypeVar`` {py:attr}`~pntos.api.StateModelProviderType`:

```{literalinclude} ../../pntos-api/src/pntos/api/plugins/state_modeling.py
:language: "python"
:start-at: "StateModelProviderType = TypeVar"
:end-at: ")"
:lineno-match:
```
```{note}
There is no base class ``StateModelProvider`` that provides core
elements required by any fusion approach. Rather a ``StateModelProvider`` is *any* class that:

1. Can provide a set of state modeling elements that satisfies the needs of some ``FusionEngine``
2. Is a member of the ``TypeVar`` {py:attr}`~pntos.api.StateModelProviderType`
```

Class entries in {py:attr}`~pntos.api.StateModelProviderType` do not have to be related at all.
 
### StateModelProvider
Just as the StateModelingPlugin is a factory that provides one or more types of StateModelProviders,
a StateModelProvider is a factory that provides one or more elements that represent a piece of the
fusion puzzle. For instance, the {py:obj}`~pntos.api.StandardStateModelProvider` can provide
{py:obj}`~pntos.api.StandardStateBlock`s that represent states in a filter and their dynamics. Any fusion
engine that understands StandardStateBlocks (or anything else a StandardStateModelProvider generates)
may make use of any providers of this type.

StateModelProviders use the same typing approach as the StateModelingPlugin to describe the set of
available models:

```{literalinclude} ../../pntos-api/src/pntos/api/plugins/state_modeling.py
:language: "python"
:start-at: "StateModelProviderType = TypeVar("
:end-at: ")"
:lineno-match:
```

Currently, the only explicitly defined `StateModelProviderType` is the {py:obj}`~pntos.api.StandardStateModelProvider`.
Each provider will be designed to work with a specific type of fusion approach and thus must be
described individually. The {py:obj}`~pntos.api.StandardStateModelProvider` is covered in the next section.

### StandardStateModelProvider
The StandardStateModelProvider generates 3 types of objects that enable sensor fusion for the
{term}`EKF` and similarly structured estimators:
1. The {py:obj}`~pntos.api.StandardStateBlock` models a fixed-size block of related values that need
to be estimated, known as states. It implicitly defines the frames and units associated with each
state via documentation. It is also a factory that provides, through the {py:obj}`~pntos.api.StandardDynamicsModel`,
the dynamics terms an {term}`EKF` or similar estimator requires to propagate its states in time.
2.  The {py:obj}`~pntos.api.StandardMeasurementProcessor` is a factory that produces
{py:obj}`~pntos.api.StandardMeasurementModel`s that relate a measurement to one or more StateBlocks,
used in the filter update step.
3.  The {py:obj}`~pntos.api.VirtualStateBlock` is an optional convenience class that performs transforms
of state vectors and covariances.

For each of the 3 types of objects the StandardStateModelProvider generates, it has a list of labels
that refer to a specific implementation of that object and a bespoke generator function. For instance,
the set of available MeasurementProcessors is described by the class member:

```{literalinclude} ../../pntos-api/src/pntos/api/plugins/state_modeling.py
:language: "python"
:pyobject: StandardStateModelProvider
:start-at: processor_identifiers: list[str] | None
:end-at: processor_identifiers: list[str] | None
```

New processors are generated by evoking:

```{literalinclude} ../../pntos-api/src/pntos/api/plugins/state_modeling.py
:language: "python"
:pyobject: StandardStateModelProvider.new_processor
:end-at: -> StandardMeasurementProcessor | None:
```

Note that this function takes an ``int`` for the first argument to define which processor should be generated,
rather than a ``str`` label. The proper argument is the location of the processor name in the ``processor_identifiers`` list,
found via ``StandardStateModelProvider.processor_identifiers.index('my processor')`` or similar.


The other two objects are created in a like manner and their instantiation is not covered further here.
Next, we'll discuss the three objects the StandardStateModelProvider generates: {py:obj}`~pntos.api.StandardStateBlock`,
{py:obj}`~pntos.api.StandardMeasurementProcessor` and {py:obj}`~pntos.api.VirtualStateBlock`.


### StandardStateBlock
The {py:obj}`~pntos.api.StandardStateBlock` is responsible for defining a specific set of jointly
Gaussian states (described by a state estimate vector and covariance matrix) and how those terms change
with respect to time and other system inputs. Examples include a scalar temperature,
a 3 dimensional point in space, or a collection of error terms associated with a physical sensor.
Each StandardStateBlock has a fixed {py:attr}`~pntos.api.StandardStateBlock.label` that is used to
refer to it and a {py:attr}`~pntos.api.StandardStateBlock.num_states` field that describes the length
of the state vector associated with the StateBlock.

The primary use of a StandardStateBlock is to generate the {py:obj}`~pntos.api.StandardDynamicsModel`
that propagates a set of states forward in time.
```{literalinclude} ../../pntos-api/src/pntos/api/plugins/state_modeling.py
:language: "python"
:pyobject: StandardStateBlock.generate_dynamics
:end-at: -> StandardDynamicsModel | None:
```

```{note}
All discrete time equations in this document use the subscript shorthand $t_k \rightarrow k$ for legibility.  
```

In terms of the {term}`EKF` propagation equations

$$
x_{k + 1} =x_k + \int^{k + 1}_k f(x_k, u_{k, k + 1}) dt  = g(x_k, u_{k, k + 1})

P_{k + 1} = \Phi_k P_k \Phi_k^T + \int^{k + 1}_k \Phi_k M_k Q_k M_k^T \Phi_k^T dt = \Phi_k P_k \Phi_k^T + Q_d
$$

the {py:obj}`~pntos.api.StandardDynamicsModel` provides $g(x, u)$, $\Phi$, and $Qd$. The terms 
$x_k$, $t_k$ and $t_{k + 1}$ all correspond to the arguments to ``generate_dynamics``. Control
(or any other) inputs $u$ that $g()$ requires are not explicitly passed to ``generate_dynamics`` but are
provided through {py:meth}`~pntos.api.StandardStateBlock.receive_aux_data`:

```{literalinclude} ../../pntos-api/src/pntos/api/plugins/state_modeling.py
:language: "python"
:pyobject: StandardStateBlock.receive_aux_data
:end-at: def receive_aux_data(self, aux: list[Message | None]) -> None:
```
The StandardStateBlock is responsible for managing any aux data passed to it and ensuring the correct
values are used in any given evaluation of ``generate_dynamics``. Below is a diagram outlining
construction of a StandardStateBlock, and data flow from the filter to the block in order to generate
new {py:obj}`~pntos.api.StandardDynamicsModel`s.

![image](../images/state_block.png)


### StandardMeasurementProcessor
The {py:obj}`~pntos.api.StandardMeasurementProcessor` is a class that defines how a measurement relates
to one or more states being estimated. Similar to the {py:obj}`~pntos.api.StandardStateBlock`, it
features a {py:attr}`~pntos.api.StandardMeasurementProcessor.label` for identification and a
{py:meth}`~pntos.api.StandardMeasurementProcessor.receive_aux_data()` to accept data
required to generate its models. Additionally it has a {py:attr}`~pntos.api.StandardMeasurementProcessor.state_block_labels`
field that tracks all the StateBlocks this processor can generate models against.

There are two important behaviors related to ``state_block_labels`` that are worth noting:

1. The order of the labels matters. If more than one label is present, then any model terms should
be generated in the order that the labels appear in the list. The {py:obj}`~pntos.api.GenXandP` functions
must adhere to the same rule.
2. The list may be modified by the processor. For instance, a StandardMeasurementProcessor is free to add so-called
nuisance states to the {py:obj}`~pntos.api.StandardFusionEngine` via {py:meth}`~pntos.api.StandardFusionEngine.add_state_block`,
in which case it should extend ``state_block_labels`` accordingly.

The StandardMeasuremementProcessor generates {py:obj}`~pntos.api.StandardMeasurementModel`s by way of the
{py:meth}`~pntos.api.StandardMeasurementProcessor.generate_model` function:

```{literalinclude} ../../pntos-api/src/pntos/api/plugins/state_modeling.py
:language: "python"
:pyobject: StandardMeasurementProcessor.generate_model
:end-at: -> StandardMeasurementModel | None:
```

In this case the function takes 2 inputs- a measurement of some kind, and a function that can provide
the current estimate and covariance of the state blocks referred to in {py:attr}`~pntos.api.StandardMeasurementProcessor.state_block_labels`.
If the processor can interpret the provided measurement and has been passed any additional required data through ``receive_aux_data``
then it may generate a {py:obj}`~pntos.api.StandardMeasurementModel` which may be used to perform an update.

Note that it is permissible for a single MeasurementProcessor to process multiple types of measurement inputs; for example,
generating an altitude update model from any {term}`ASPN` measurement that contains an altitude or related value.
It is also allowable to process similar measurements from multiple data sources. The only requirement is the measurement can be
related to the states in {py:attr}`~pntos.api.StandardMeasurementProcessor.state_block_labels`. Care must be taken in this case
if {py:attr}`~pntos.api.StandardMeasurementProcessor.state_block_labels` contains any sensor-specific
states (e.g. lever arm, bias terms) that models do not incorrectly relate measurements to these states.

In terms of the {term}`EKF` update equations

$$
K = PH^T(HPH^T + R)^{-1}

x^+ =x^- + K(z - h(x^-))

P^+ =P^- + KHP^-
$$

the StandardMeasurementModel provides $z$, $h(x)$, $H$ and $R$.

Below is a diagram outlining construction of a StandardMeasurementProcessor, and data flow from the
filter to the processor in order to generate new {py:obj}`~pntos.api.StandardMeasurementModel`s.
![image](../images/measurement_processor.png)

### VirtualStateBlock
The purpose of a {py:obj}`~pntos.api.VirtualStateBlock` is to provide a mapping
between one standard state representation (Gaussian estimate and covariance) and another. Among other things,
this allows measurement models that were written against a particular state representation
to be used with other states, so long as a continuous mapping exists. For example, if a filter
was tracking a state vector containing Earth-centered, Earth-fixed (ECEF) states,
but a measurement model used latitude-longitude-altitude (LLA), a VirtualStateBlock that implemented
the conversion from ECEF to LLA could be used to bridge the gap between them.

Mathematically speaking we are just decomposing functions into a compositions of functions.
To illustrate, suppose a {py:obj}`~pntos.api.StandardMeasurementModel` was
available and provided the standard model terms with respect to some state vector ``x``:

$$
z = h(x)

H = \frac{\partial h}{\partial x}\rvert_{x=x0}
$$

If the filter has a state representation ``y``, and there exists a continuous and differentiable 
function that maps ``y`` to ``x``

$$
x = g(y)
$$

then the VirtualStateBlock can provide ``g()``, which can be used to make ``h()`` a function of ``y``:

$$
z = h(g(y))
$$

``H`` can similarly be mapped using only the derivative of ``g(y)`` provided by the VirtualStateBlock
due to the chain rule:

$$
\frac{\partial h}{\partial y} = 

\frac{\partial h}{\partial g(y)} \frac{\partial g}{\partial y} = 

\frac{\partial h}{\partial x} \frac{\partial g}{\partial y} = 

H\frac{\partial g}{\partial y}\rvert_{y=y0} = 

HG 
$$

Also due to the chain rule, multiple VirtualStateBlocks may be deployed in sequence to provide a
series of mappings, e.g. $x = g(f(e(y)))$

To support these operations, a VirtualStateBlock must implement the following functions:

1. {py:meth}`~pntos.api.VirtualStateBlock.convert_estimate` maps one state vector representation to another; equivalent to $g(y)$.
```{literalinclude} ../../pntos-api/src/pntos/api/plugins/state_modeling.py
:language: "python"
:pyobject: VirtualStateBlock.convert_estimate
:end-at: -> NDArray[float64]:
```

2. {py:meth}`~pntos.api.VirtualStateBlock.jacobian` returns the partial derivative of $g(y)$ w.r.t. $y$, a.k.a. $G$:
```{literalinclude} ../../pntos-api/src/pntos/api/plugins/state_modeling.py
:language: "python"
:pyobject: VirtualStateBlock.jacobian
:end-at: -> NDArray[float64]:
```

3. {py:meth}`~pntos.api.VirtualStateBlock.convert` is a convenience function that not only maps $x = g(y)$ but the associated covariance of 
$y$ into $x$-space as well:
```{literalinclude} ../../pntos-api/src/pntos/api/plugins/state_modeling.py
:language: "python"
:pyobject: VirtualStateBlock.convert
:end-at: -> EstimateWithCovariance:
```

4. Finally, if $g(y)$ requires any additonal inputs other than $y$ to be evaluated, they may be
passed in through the {py:meth}`~pntos.api.VirtualStateBlock.receive_aux_data` function:
```{literalinclude} ../../pntos-api/src/pntos/api/plugins/state_modeling.py
:language: "python"
:pyobject: VirtualStateBlock.receive_aux_data
:end-at: def receive_aux_data(self, aux: list[Message | None]) -> None:
```

Note that use of VirtualStateBlocks is entirely optional and can contribute significant overhead in
some cases. In resource-constrained applications, use of measurement processors that interact with
non-virtual states directly is recommended. 


## Cobra Implementation: StandardStateModelingPlugin
The {py:obj}`~pntos.cobra.StandardStateModelingPlugin`
is a simple factory class that only provides objects the {py:obj}`pntos.cobra.internal.StandardStateModelProvider`,
which is an implementation of the {py:obj}`API class <pntos.api.StandardStateModelProvider>` of the same name. 

### StandardStateModelProvider
As with the {py:obj}`~pntos.cobra.StandardStateModelingPlugin`, the
{py:obj}`~pntos.cobra.internal.StandardStateModelProvider` is just a factory that follows a
pretty standard template. However, this class makes available a number of other classes that assist
in modeling {term}`IMU` errors. These are summarized in the following tables.

#### MeasurementProcessors
|Class and Identifier|Accepted Measurements|Required StateBlocks|Description|
|-----|---|---|-----------|
|{py:obj}`~pntos.cobra.internal.PinsonPositionMeasurementProcessor`</br>pinson_position|MeasurementPosition (Geodetic)|pinson|Direct update of pinson position error states via the delta </br> between input measurement and nominal (aux data) positions.</br>Includes lever arm correction via configuration.|
|{py:obj}`~pntos.cobra.internal.PinsonVelocityMeasurementProcessor`</br>pinson_velocity|MeasurementVelocity (NED)|pinson|Direct update of pinson velocity error states via the delta </br> between input measurement and nominal (aux data) velocities.</br>Measurement and nominal NED frames are assumed coincident.|
|{py:obj}`~pntos.cobra.internal.PinsonWithNedFogmPositionMeasurementProcessor`</br>pinson_with_ned_fogm_position|MeasurementPosition (Geodetic)|pinson,</br> fogm (3)|As {py:obj}`~pntos.cobra.internal.PinsonPositionMeasurementProcessor`, but with the addition</br>of a 3-element FOGM to model arbitrary NED-frame measurement</br>errors. Includes lever arm correction via configuration.|
|{py:obj}`~pntos.cobra.internal.AltitudeMeasurementProcessor`</br>pinson_altitude|MeasurementPosition (Geodetic),</br> MeasurementAltitude,</br>MeasurementPositionVelocityAttitude(Geodetic)|pinson,</br> fogm (1)|Generates an altitude error update via the delta between the measurement</br>altitude and the nominal, with a FOGM-modeled altitude sensor bias in meters.|
|{py:obj}`~pntos.cobra.internal.PinsonWithLeverArmPositionMeasurementProcessor`</br>pinson_with_lever_arm_position|MeasurementPosition (Geodetic)|pinson,</br>fogm (3),</br>fogm (3)|As {py:obj}`~pntos.cobra.internal.PinsonWithNedFogmPositionMeasurementProcessor`, but with the</br>inclusion of an additional state block to estimate additional lever arm offset</br>from the nominal value provided through configuration.|
|{py:obj}`~pntos.cobra.internal.PinsonBodyVelocityMeasurementProcessor`</br>pinson_body_velocity|MeasurementVelocity (Sensor)|pinson|Updates pinson velocity error states using a velocity measurement in an</br>arbitrary, platform-fixed sensor frame, where the lever-arm and orientation</br>between the sensor and platform are known and provided through</br>configuration.|
|{py:obj}`~pntos.cobra.internal.PinsonPosVelMeasurementProcessor`</br>pinson_posvel|MeasurementPositionVelocityAttitude (Geodetic)|pinson|A processor that effectively joins {py:obj}`~pntos.cobra.internal.PinsonPositionMeasurementProcessor`</br>and {py:obj}`~pntos.cobra.internal.PinsonVelocityMeasurementProcessor`.|
|{py:obj}`~pntos.cobra.internal.PositionMeasurementProcessor`</br>position|MeasurementPosition (Geodetic)|PVA states,</br> fogm (3)|A position update for whole-valued {term}`PVA` states. Can be used with</br>``pinson``-style error state blocks in conjunction</br>with {py:obj}`~pntos.cobra.internal.PinsonErrorToStandard` VirtualStateBlock.|
|{py:obj}`~pntos.cobra.internal.Direction3DToPointsMeasurementProcessor`</br>direction3D_to_points|MeasurementDirection3DToPoints|pinson|Updates pinson error states using the difference between the predicted</br>and measured lateral and down units vectors pointing to features</br>whose locations are known.|

```{note}
In the above table
1. Required frames noted in parentheses refer to an ASPN23 frame, usually indicated by the ``reference_frame`` member of the message.
   If no frame is listed any are acceptable.
2. Numbers in parantheses indicate the required number of states a particular state block must have.
3. `pinson` refers to any state block that adheres to our typical pinson state layout, meaning 9 PVA
   related states followed by sensor error states. This means that one could provide an
   'extended' pinson model that adds additional states to the end of the
   {py:obj}`Pinson15NedBlock <pntos.cobra.internal.Pinson15NedBlock>` and the processor will still work.
4. PVA states means whole-valued states; see the linked processor for more details.
```

#### StateBlocks
|Class|Identifier|Description|
|-----|----------|-----------|
|{py:obj}`~pntos.cobra.internal.Pinson15NedBlock`|pinson15|A state block that models INS error states.|
|{py:obj}`~pntos.cobra.internal.FogmBlock`|fogm|A configurable-length set of FOGM-modeled states.||
|{py:obj}`~pntos.cobra.internal.ClockBiasStateBlock`|clock_bias|Models a clock bias and 1-2 derivative terms.|
|{py:obj}`~pntos.cobra.internal.ConstantStateBlock`|constant|A configurable-length set of constant model states.|

#### VirtualStateBlocks
|Class|Identifier|Description|
|-----|----------|-----------|
|{py:obj}`~pntos.cobra.internal.PinsonErrorToStandard`|pinson_error_to_standard|Maps ``pinson``-type state blocks to whole state estimates by combining the error states with the corresponding nominal PVA.|
|{py:obj}`~pntos.cobra.internal.StateExtractor`|state_extractor|Extracts a subset from a larger set of states, preserving frames, units etc.|
