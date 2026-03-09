# Concurrency

pntOS is designed to allow for concurrent operation of different plugins. Indeed,
different plugins are free to use their own concurrency primitives internally. Because
each plugin may be using its own set of threads, processes, coroutines, or other
primitives internally, some rules must be established on how these plugins interact with
each other.

## Definitions

Fundamentally, pntOS plugins interact with resources handed to them by the [Controller
Plugin](./plugins/controller_plugin.md) (see the [Introduction](./introduction.md) for
more information on the overall pntOS architecture). For example, when a non-[Controller
Plugin](./plugins/controller_plugin.md) is first loaded into pntOS, the
{py:obj}`CommonPlugin.init_plugin<pntos.api.CommonPlugin.init_plugin>` call provides a
[Mediator](./plugins/controller_plugin.md#mediator) object, which may be used by that
plugin to request information from the system. Similarly, the [Orchestration
Plugin](./plugins/orchestration_plugin.md) is handed a set of plugins in the
{py:obj}`OrchestrationPlugin.init_orchestration_plugin<pntos.api.OrchestrationPlugin.init_orchestration_plugin>`
call, which the [Orchestration Plugin](./plugins/orchestration_plugin.md) is free to use
in the future to access system resources. A plugin using a function on the
[Mediator](./plugins/controller_plugin.md#mediator) it was given and the [Orchestration
Plugin](./plugins/orchestration_plugin.md) using a plugin from the list of plugins it
was given are both examples of plugins using system resources given to them by the
system.

Conversely, when the [Controller Plugin](./plugins/controller_plugin.md) starts up it
is handed a list of raw plugins from an {term}`App`. The
[Controller Plugin](./plugins/controller_plugin.md) wants to use these plugins, but
it first must ensure that it adheres to the rules and expectations of these plugins. For
example, before the [Controller Plugin](./plugins/controller_plugin.md) may start
using functionality on a [Transport Plugin](./plugins/transport_plugin.md), it is
required to call {py:obj}`CommonPlugin.init_plugin<pntos.api.CommonPlugin.init_plugin>`
on that [Transport Plugin](./plugins/transport_plugin.md). When the
[Controller Plugin](./plugins/controller_plugin.md) accesses a raw plugin or a
resource returned by a raw plugin, that constitutes the pntOS system accessing a plugin
resource. The above example of the
[Controller Plugin](./plugins/controller_plugin.md) calling
{py:obj}`CommonPlugin.init_plugin<pntos.api.CommonPlugin.init_plugin>` on a
[Transport Plugin](./plugins/transport_plugin.md) is an example of the system
accessing a plugin resource.

Thus, we can say that the [Controller Plugin](./plugins/controller_plugin.md) is
acting as the "pntOS System" and managing the concurrency and data access between
plugins. We will now consider both of these use cases individually:

1. What responsibilities do non-[Controller Plugin](./plugins/controller_plugin.md)s
   have in accessing system resources
2. What responsibilities does the [Controller Plugin](./plugins/controller_plugin.md)
   plugin have in accessing plugin resources

## Plugin Accessing System Resources

Plugins may access system resources at any time. For example, they are free to call
functions on the [Mediator](./plugins/controller_plugin.md#mediator) and on a
{py:obj}`KeyValueStore<pntos.api.KeyValueStore>` instance. If they make such accesses
_concurrently_, they are subject to the following rules:

1. Concurrent access of each system resource from separate threads owned and created by
   the plugin is allowed.
2. Concurrent access of system resources from separate processes is **forbidden**. For
   example, if a plugin called `fork()`, it cannot access the
   [Mediator](./plugins/controller_plugin.md#mediator) from both processes. Access of
   system resources is only allowed from the originating process in which the system
   resources were provided to the plugin.
3. Concurrent access of system resources **may be processed in any order**. The system
   reserves the right to:

   1. Block on a system resource access request while waiting for another call to complete.
   2. Execute system resource access requests in a different order than they
      were made by the plugin.
   3. Utilize each thread that a system resource access request was made on to
      do other work. For example, if a registry key is set using
      {py:obj}`KeyValueStore.set_value<pntos.api.KeyValueStore.set_value>`, the system may in the middle of
      that call process its {py:obj}`KeyValueStore.request_notify<pntos.api.KeyValueStore.request_notify>`
      observers, using that thread to invoke callbacks on other plugins.
   4. Utilize any thread-local storage on the thread that a system resource
      access request was made for any purpose.

   One method of accessing system resources is to have a dedicated system
   resource thread which sequences and makes all system resource requests.
   Concurrent access from multiple threads is also possible as long as the above
   rules are observed. Note that the first two rules make any such concurrent
   accesses a race condition.

4. Concurrent access of system resources using other concurrency primitives
   (such as coroutines) is _unspecified_ and must be coordinated with a
   participating controller. For example, a controller might share a coroutine
   access pool with other plugins, but only if all plugins opt-in. Plugins must
   support falling back to a non-participation mode, where other concurrency
   primitives are not utilized to make concurrent accesses of system resources.

## Controller Accessing Plugin Resources

The system may access resources on a plugin or returned by a plugin (or recursively
returned by a resource previously returned by a plugin) at any time. Such accesses are
usually made by the [Controller Plugin](./plugins/controller_plugin.md) accessing plugin
memory or functions, and are subject to the following rules:

1. Access to a plugin resource must be on a _single_ thread, and concurrent accesses to
   plugin resources are **forbidden**. Thus, a controller must carefully control
   requests made to plugins by the [Mediator](./plugins/controller_plugin.md#mediator)
   and other inter-plugin communications.
2. Access to plugin resources may be made on any thread available to the system.
3. Plugin resources may be accessed from within any process and are not necessarily used
   within the same process that loaded the plugin, however each plugin must only be
   called from **one** process. For example, the controller is free to `fork()` once per
   plugin and use each plugin in a separate process, but it must not call the _same_
   plugin from within both the original process _and_ the `fork()`ed process.
4. Concurrent access of plugin resources using other concurrency primitives (such as
   coroutines) is _unspecified_ and must be coordinated with a participating plugin. For
   example, a controller might share a coroutine access pool with other plugins, but
   only if all plugins opt-in. Plugins must support falling back to a non-participation
   mode, where other concurrency primitives are not utilized to make concurrent accesses
   of plugin resources.

Any of the above rules may be overridden by an API specification. For example, the
registry allows for {py:obj}`KeyValueStore<pntos.api.KeyValueStore>` accesses to be made
concurrently, and the {py:obj}`UiPlugin<pntos.api.UiPlugin>` requires the main thread to
be used under certain conditions.

## Simultaneous Controller and Plugin Accesses

In the last two sections, we discussed the rules for the [Controller
Plugin](./plugins/controller_plugin.md) accessing plugin resources and the plugin
accessing system resources. However, what if these two things happen simultaneously?
That is, a [Controller Plugin](./plugins/controller_plugin.md) accesses a plugin
resource while at the same time the plugin accesses a system resource?

In general, such behavior is _allowed_, meaning that:

1. Plugins must expect that one of their functions may be accessed even if they are
   currently requesting something from the system. The plugin must **not** block on the
   system accessing one of its functions until its current request to the system is
   complete.
2. The [Controller Plugin](./plugins/controller_plugin.md) must expect the plugin to
   request something from the system even if the controller is currently waiting for a
   call it has made to the plugin to complete. The [Controller
   Plugin](./plugins/controller_plugin.md) must **not** block on the plugin request
   until after the [Controller Plugin](./plugins/controller_plugin.md)'s request to the
   plugin is complete.

Taken in whole, this allows for calls one direction to initialize a call the other
direction. For example, if the [Controller Plugin](./plugins/controller_plugin.md) asks
plugin A to perform a task, plugin A may call back into the mediator while it is trying
to perform that task. An example use case is that plugin A may need to get a config
value from the registry to complete its task. The mediator must dispatch the request for
a registry config immediately, as waiting for plugin A's task to complete before
processing the new config variable would result in a deadlock. In particular, plugin A
would be waiting for its config variable to complete the task and the [Controller
Plugin](./plugins/controller_plugin.md) would be waiting for the task to complete before
giving A its config variable.

## Callback Triggering and Call Loops

Because pntOS is a general framework without specific workflow requirements in data
routing between plugins, care must be taken to avoid responsibility loops. For example,
suppose that in the implementation of a
[Mediator](./plugins/controller_plugin.md#mediator), the system uses a [Registry
Plugin](./plugins/registry_plugin.md) to implement the `mediator.registry`
functionality. Further suppose that in the implementation of a [Registry
Plugin](./plugins/registry_plugin.md), the
{py:obj}`KeyValueStore.set_value<pntos.api.KeyValueStore.set_value>` call simply called
back into the [Mediator](./plugins/controller_plugin.md#mediator)'s
`mediator.registry`. We would now be in an infinite loop: the
[Mediator](./plugins/controller_plugin.md#mediator) uses the [Registry
Plugin](./plugins/registry_plugin.md) and the [Registry
Plugin](./plugins/registry_plugin.md) uses the
[Mediator](./plugins/controller_plugin.md#mediator) function, continuing to call each
other until a stack overflow occurs.

While this example is simple and avoidable, there are many possible races, deadlocks,
and starvation conditions that can arise in the implementation of the mediator if
plugins are allowed to call any mediator resources at any time. Consider for example the
following call chain that might occur when the [Controller
Plugin](./plugins/controller_plugin.md) requests something from plugin A:

    Controller -> Plugin A -> Mediator -> Plugin B -> Mediator -> Plugin A

Plugin A calling the mediator for Plugin B's functionality is reasonable, and Plugin B
calling the mediator for Plugin A's functionality is reasonable, but in totality we
would have a broken system, as by the concurrency rules in the previous sections the
system may not call into Plugin A twice.

The solution to this issue is isolation of responsibilities. In general, the following
rules must be followed:

1. Plugins must not call back into functions which they are responsible for
   implementing. For example, a [Registry Plugin](./plugins/registry_plugin.md) may not
   access the [Mediator](./plugins/controller_plugin.md#mediator)'s
   `mediator.registry`. Similarly, the [Orchestration
   Plugin](./plugins/orchestration_plugin.md) must not call into
   {py:obj}`Mediator.request_solutions<pntos.api.Mediator.request_solutions>`, and the
   [Transport Plugin](./plugins/transport_plugin.md) must not call into
   {py:obj}`Mediator.broadcast_aspn_message<pntos.api.Mediator.broadcast_aspn_message>`.
2. Callbacks must not use [Mediator](./plugins/controller_plugin.md#mediator) resources.
   For example, when the callback function to
   {py:obj}`KeyValueStore.request_notify<pntos.api.KeyValueStore.request_notify>` is
   invoked, the callback may not access the
   [Mediator](./plugins/controller_plugin.md#mediator) inside the callback.

## Mutability of Received Resources

In general, resources delivered by a plugin to the system or by the system to a plugin
may be shared by multiple plugins, including the original plugin that produced it
retaining a copy.

By default, all plugins must assume that resources are being shared. Thus if a
`list[str]` is returned by a function call to another plugin, the receiver plugin must
assume that this list is being utilized by multiple plugins and
**cannot be modified or mutated**.

This leads us to the following rule all plugins must follow:

1. All memory passed to another plugin which the originating plugin does not retain a
   reference to must be **mutable**. For example, if the originating plugin wants to
   modify a list after returning it as a resource, it must either modify a copy of the
   returned list or return a copied list.

## PIP and Controller

The [PIP](./plugins/platform_integration_plugin.md) and [Controller
Plugin](./plugins/controller_plugin.md) work closely to handle system resources
concurrently in pntOS. Because of this close relationship, there is no way to
prescriptively lay out a set of rules the
[PIP](./plugins/platform_integration_plugin.md) and [Controller
Plugin](./plugins/controller_plugin.md) must adhere to in order to avoid races,
deadlocks, and other undesirable effects. Instead, for concurrent implementations, the
[PIP](./plugins/platform_integration_plugin.md) must be designed to work specifically
with a chosen [Controller Plugin](./plugins/controller_plugin.md), and document the way
that it coordinates concurrency with the [Controller
Plugin](./plugins/controller_plugin.md).
