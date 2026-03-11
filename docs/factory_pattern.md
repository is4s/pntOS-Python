# The Factory Pattern in pntOS-Python

Many plugins don't do much work themselves, but are factories which provide a component to be used
by another plugin to accomplish a task. Some examples include:

- the {py:obj}`InertialPlugin<pntos.api.InertialPlugin>`, which provides inertials
- the {py:obj}`InitializationPlugin<pntos.api.InitializationPlugin>`, which provides initializers
- the {py:obj}`FusionPlugin<pntos.api.FusionPlugin>`, which provides fusion engines
- the {py:obj}`FusionStrategyPlugin<pntos.api.FusionStrategyPlugin>`, which provides fusion
  strategies
- the {py:obj}`RegistryPlugin<pntos.api.RegistryPlugin>`, which provides
  {py:obj}`Registry<pntos.api.Registry>`s
- the {py:obj}`StateModelingPlugin<pntos.api.StateModelingPlugin>`, which provides state model
  providers

The last one is of particular interest, as the state model provider is itself a factory pattern
which provides measurement processors, state blocks, and virtual state blocks.

## The Advantages of the Factory Pattern in pntOS-Python

This approach adds quite a bit of complexity to the API but also comes with a few distinct
benefits.

### Flexibility in Design

Say a developer wants to implement multiple preprocessors. The factory pattern provides the
developer with the flexibility to decide whether to bundle these preprocessors into a single
Preprocessor plugin or to split them up, one per Preprocessor plugin.

### Get the Job Done With Fewer Plugins

Consider a particular pntOS-Python implementation which requires ten instances of the same class of
preprocessor. With the factory pattern, the implementation can accomplish this with a single
Preprocessor plugin. Without the factory pattern, the implementation would need to create ten
instances of the same Preprocessor plugin.

This applies to all of the plugins which leverage the factory pattern. At first it might not be
immediately clear why an implementation of pntOS-Python would use multiple instances of a particular
component. But consider the cases where an Orchestration plugin is managing multiple filters
simultaneously. In this case, it might require an instance of each component (e.g. inertial,
initializer, fusion engine, fusion strategy, and state modeling plugin) for each filter.

The above example covers all the plugins which are typically used by the Orchestration plugin, but
what about the Registry plugin? One example use-case is the segmented registry. In order to increase
security, plugins that don't need to communicate with each other through the registry could be given
their own instance of the registry. Then, for example, a corrupted plugin would have limited impact
on the rest of the system.

### Maintaining Backwards Compatibility

Say the API were updated to add support for a more advanced filtering model to the {py:obj}`State
Modeling plugin<pntos.api.StateModelingPlugin>`. Usually a change of that magnitude would require
incrementing the major version of the API. However, the factory pattern allows for this sort of
change to be made without breaking existing implementations of pntOS-Python. Existing
implementations of State Modeling plugins which produce instances of
{py:obj}`StandardStateModelProvider<pntos.api.StandardStateModelProvider>` would still be considered
valid and not require any updates after updating the API.
