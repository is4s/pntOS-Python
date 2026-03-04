# Orchestration Plugin

The {py:obj}`Orchestration Plugin<pntos.api.OrchestrationPlugin>` can be viewed as the core of the
pntOS filter. It is responsible for ingesting sensor data and using it to calculate a solution.
The plugin was designed to be generic enough to allow a full, navigation solution to be developed
within it or to utilize a bank of filtering plugins such as the following:

* [](./fusion_plugin.md)
* [](./fusion_strategy_plugin.md)
* [](./inertial_plugin.md)
* [](./initialization_plugin.md)
* [](./state_modeling_plugin.md)
* [](./preprocessor_plugin.md)

In the latter case, the orchestration plugin is responsible for configuring and managing these
plugins to achieve its primary goal - producing a solution. Whether the plugin is implemented to be
a black box solution or a modular approach, any given orchestration plugin should expect a
{py:obj}`MessageStreamConfig<pntos.api.MessageStreamConfig>`. This class gives the Orchestration
Plugin control over which messages are buffered (delayed and sequenced) and which are not (immediate).
The control over delivery is vital for certain navigation algorithms, so it was built-in as a
requirement in the API for every orchestration plugin.

## Orchestration Plugin API

In addition to the methods required of all plugins, an orchestration plugin must implement the
following methods:

1. {py:obj}`init_orchestration_plugin()<pntos.api.OrchestrationPlugin.init_orchestration_plugin>` -
This method, called by the {py:obj}`ControllerPlugin<pntos.api.ControllerPlugin>`, gives the
plugin the opportunity to configure any data structures, filtering plugins, or streaming config.
By the design of the API, this **must** be called before any call to the methods listed below.

1. {py:obj}`process_pntos_message()<pntos.api.OrchestrationPlugin.process_pntos_message>` - This
method is called by the {py:obj}`Mediator<pntos.api.Mediator>` and, when repeatedly called, is how
the plugin receives its stream of external data. This is where the plugin actually orchestrates the
flow of data, so within the call of this method, the {py:obj}`pntOS Message<pntos.api.Message>`
should be processed and used however the plugin sees fit. The processing all depends on the design
of the implementation. In the next section we will discuss how Cobra approaches fulfilling this
function.

1. {py:obj}`filter_description_list<pntos.api.OrchestrationPlugin.filter_description_list>` -
When called, this property returns a list of strings that describe the different types of filters
the orchestration plugin can provide. Each string must follow strict conventions documented in the
API so that there is consistency and a qualified expectation between plugins. For more information,
see the API description linked above.

1. {py:obj}`request_solutions()<pntos.api.OrchestrationPlugin.request_solutions>` - This method is
responsible for returning a solution that satisfies the parameters passed in. `solution_times`
allows the caller to specify what time(s) it wants a solution for. In addition to that, the caller
can also request what filter it wants a solution from via `filter_description`. The method should
compare `filter_description` with the plugin's list of filter descriptions and return the solution
if there is a match.

```{note}
This method returns `list[Message | None] | None`. If the filter description is invalid, it simply
returns `None`. Otherwise, it returns a list of the same length as `solution_times`. For any given
timestamp it cannot generate a solution for, the corresponding entry in the list will be `None`.
This means the caller must validate the solution it receives each time it calls this method.
```

Through the combination of these methods, the orchestration plugin is able to consume and distribute
external sensor data as a means to generate and output a set of full navigation solutions - a vital
instrument in the pntOS architecture.

## Cobra Orchestration Plugin Implementation

Cobra's off-the-shelf orchestration plugin implementation is the 
{py:obj}`StandardOrchestrationPlugin<pntos.cobra.StandardOrchestrationPlugin>`. Its design
takes the modular approach where it configures and defers filtering responsibilities to other
plugins listed at the beginning of this document. If the developed orchestration plugin was just a
black box navigation solution, then swapping out the underlying filter would involve writing an
entirely new orchestration plugin. Modularity allows for more of a "plug and play" approach where
an app has more control over the behavior of the implementation of pntOS. Let's jump into the
details of the `StandardOrchestrationPlugin`.

```{note}
There are a variety of functions developed within the `StandardOrchestrationPlugin` that handle
important pieces of logic. We won't walk through them here due to the time it would take to do so.
Rather, we will focus on the API-defined functions and step through them at a high level.
```

`StandardOrchestrationPlugin.init_orchestration_plugin()` accomplishes all three of the behaviors
described in the API section above and more. Let's walk through them!
- It uses the `stream_config` to make sure all messages are delivered in order (based on
timestamps) except for inertial measurements; it requests those be sent immediately. Inertial data
is a pre-requisite for many measurement processors to generate their update model so we configured
the `StandardOrchestrationPlugin` this way to guarantee the fusion engine receives the inertial 
data some time `t` before it receives a corresponding measurement at time `t`.
- The method uses the {py:obj}`RegistryPlugin<pntos.api.RegistryPlugin>` to grab config data
and subsequently setup data structures to store the config. 
- The method then validates that is has every plugin it expects and uses the saved config data to
initialize all of these plugins.
- Finally, the method was designed to also handle the case where the
{py:obj}`InitializationPlugin<pntos.api.InitializationPlugin>` is finished by the end of the
`init_orchestration_plugin()` call. It then proceeds to effectively start the filter.

The `StandardOrchestrationPlugin.process_pntos_message()` method takes the following approach to
data flow:

1. Preprocesses incoming messages through the full chain of preprocessors the app defines.
1. If the filter wasn't started in `init_orchestration_plugin()`, the messages have their
identifiers compared against the list of alignment channels the orchestration config specifies. If
the message is an alignment message, it is passed to the initializer until initialization is
complete and the filter starts.
1. Once the filter has been started, all messages with valid timestamps are directed to either the
inertial or the filter. If the message's identifier matches the inertial channel, it is dispatched
to the inertial plugin for processing. However, if the message is destined for the filter, the
orchestration plugin:
    - requests the fusion engine to propagate to the time of the message
    - passes the measurement to the fusion engine
1. The method then checks what state blocks, virtual state blocks, and measurement processors require
the message as auxiliary data and forwards the measurement accordingly.
1. Last but not least, the method ensures the filter continues propagating, even in the case of an
outage.

`filter_description_list` is very straightforward as it just iteratively generates the list of
filter solutions the plugin implementation can provide. Currently, the plugin only provides two
solutions:

- `GPS_INS_BEST_ASPN_MEASUREMENT_POSITION_VELOCITY_ATTITUDE_ESTIMATE` - the best solution
- `GPS_INS_DEAD_RECKONING_ASPN_MEASUREMENT_POSITION_VELOCITY_ATTITUDE_ESTIMATE` - the inertial
only solution

Finally, `StandardOrchestrationPlugin.request_solutions()`. For simplicity, the current implementation
only supports requesting a solution for a single timestamp per call. The
method takes the following approach:
1. Check if initialization is complete, if it isn't a solution cannot be provided.
1. Only one solution per call is supported, so validate only a single time has been passed.
1. Validate the requested timestamp is within the time of the inertial, if not replace the
timestamp with the latest inertial time.
1. Use `filter_description` to determine what to query for and if a solution is available, return
it.