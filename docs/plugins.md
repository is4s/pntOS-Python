# Plugin Reference

In this section we will explore each type of plugin with greater resolution. As a point
of reference, let's walk through this graphic:

![Overview Image](./images/pntos_yet_another_view.png)

Notice that the {term}`App` starts the [Controller
Plugin](./plugins/controller_plugin.md), which then hands a
[Mediator](./plugins/controller_plugin.md#mediator) to all the other plugins which
controls the flow of data through the system. Data comes into the system from the
platform through [Transport Plugins](./plugins/transport_plugin.md) (or for more
specialized cases, the [Platform Interface
Plugin](./plugins/platform_integration_plugin.md)) which then pass data on to the [Orchestration
Plugin](./plugins/orchestration_plugin.md). 

The [Orchestration
Plugin](./plugins/orchestration_plugin.md) can optionally incorporate other plugins to implement
a sensor fusion filter. These optional plugins include:
* [**Fusion Plugin**](./plugins/fusion_plugin.md): Used by the [Orchestration
Plugin](./plugins/orchestration_plugin.md) to generate a sensor fusion engine. The [Orchestration
Plugin](./plugins/orchestration_plugin.md) can use components from the following
plugins to assemble the fusion engine.
    * [**Fusion Strategy Plugin**](./plugins/fusion_strategy_plugin.md): Provides an
      estimation strategy to the fusion engine.
    * [**State Modeling Plugin**](./plugins/state_modeling_plugin.md): Keeps track of
      states and how measurements should update those states.
* [**Inertial Plugin**](./plugins/inertial_plugin.md): Performs mechanization for an {term}`IMU`.
* [**Initialization Plugin**](./plugins/initialization_plugin.md): Performs any filter
  initialization (e.g. implementing an {term}`IMU` alignment strategy).
* [**Preprocessor Plugin**](./plugins/preprocessor_plugin.md): Performs any preprocessing of
  data before it reaches the filter (e.g. performing sensor-to-platform frame rotations).

Additionally, all plugins have access to the [Registry
Plugin](./plugins/registry_plugin.md) and [Logging Plugin](./plugins/logging_plugin.md)
via the mediator. 

Other plugins such as the [UI Plugin](./plugins/ui_plugin.md),
[Platform Integration Plugin](./plugins/platform_integration_plugin.md), or the [Utility
Plugin](./plugins/utility_plugin.md) optionally provide the system with expanded
capabilities.


<!-- TODO (#116) https://git.aspn.us/pntos/pntos-python/-/issues/116 -->

See the below pages for descriptions of various plugins, as well as any related components:

```{toctree}
plugins/controller_plugin
plugins/fusion_plugin
plugins/fusion_strategy_plugin
plugins/inertial_plugin
plugins/initialization_plugin
plugins/logging_plugin
plugins/orchestration_plugin
plugins/platform_integration_plugin
plugins/preprocessor_plugin
plugins/registry_plugin
plugins/state_modeling_plugin
plugins/transport_plugin
plugins/ui_plugin
plugins/utility_plugin
```