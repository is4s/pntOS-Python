# Orchestration Plugin

The {py:obj}`Orchestration Plugin<pntos.api.OrchestrationPlugin>` contains the core
navigation data fusion and filtering functionality. It is responsible for calculating a
navigation solution from the incoming sensor data. It usually performs this task by calling out
to various plugins which define the actual sensor fusion algorithm, state space, and
sensor error models. Thus its primary duties are to orchestrate the flow of data
into/out of filters, and picking the set of navigation-related plugins which are used to
model errors and generate estimates.

![](../images/pntos_overview3.svg)

The {py:obj}`Orchestration Plugin<pntos.api.OrchestrationPlugin>` could be a single
black box solution or broken up into more modular components. In the latter case, a bank
of one or more filters has access to a bank of filtering plugins. Filtering plugins
might include the:

* [](./fusion_plugin.md)
* [](./fusion_strategy_plugin.md)
* [](./inertial_plugin.md)
* [](./initialization_plugin.md)
* [](./state_modeling_plugin.md)
* [](./preprocessor_plugin.md)

<!-- TODO (#176) https://git.aspn.us/pntos/pntos-python/-/issues/176 -->