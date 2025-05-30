# Controller Plugin

Once an {term}`App` calls
{py:obj}`take_control()<pntos.api.ControllerPlugin.take_control>` on the
{py:obj}`Controller Plugin<pntos.api.ControllerPlugin>`, the {py:obj}`Controller
Plugin<pntos.api.ControllerPlugin>` is responsible for all activity in the app. It may
use any of the plugins it was passed as desired. The {py:obj}`Controller
Plugin<pntos.api.ControllerPlugin>` defines any and all input and output it supports,
which plugins are loaded or used, and the type of fusion being done. The
{py:obj}`Controller Plugin<pntos.api.ControllerPlugin>` should be written generically to
support arbitrary run-time environment sensing. Outside of some initialization in the
{term}`app<App>`, the {py:obj}`Controller Plugin<pntos.api.ControllerPlugin>` is the
conceptual "main" function of the Python pntOS app.

The controller's main responsibility is to choose and initialize the concurrency model
being used by the plugins. For example, a controller might decide on a multithreaded
implementation, or a multiprocessed implementation for better isolation and security. A
simple controller might create a single thread for each plugin it was given and then set
up thread-safe communication pipes between those plugins.

## Mediator

The Controller plugin facilitates communication between plugins via the mediator. It is responsible for defining and initializing the mediator before providing it to the plugins.

Named after the computer science [mediator design
pattern](https://en.wikipedia.org/wiki/Mediator_pattern) concept, the
{py:obj}`Mediator<pntos.api.Mediator>` is an object created by the {py:obj}`Controller
Plugin<pntos.api.ControllerPlugin>` and handed to each plugin. It encapsulates
communication and shared state between the plugins.

Before the controller may use any of the plugins it was passed, it must first call the
{py:obj}`init_plugin()<pntos.api.CommonPlugin.init_plugin()>` function on that plugin
and pass into it a {py:obj}`Mediator<pntos.api.Mediator>`. The
{py:obj}`Mediator<pntos.api.Mediator>` object is the only way that plugins may
communicate back to the {py:obj}`Controller Plugin<pntos.api.ControllerPlugin>`, by
invoking the function pointers on their {py:obj}`Mediator<pntos.api.Mediator>`.

The {py:obj}`Mediator<pntos.api.Mediator>` therefore is where concurrency and
synchronization are decided. Continuing the example of a multithreaded implementation
where each plugin is in a separate thread, the {py:obj}`Controller
Plugin<pntos.api.ControllerPlugin>` might implement a simple
{py:obj}`Mediator<pntos.api.Mediator>` by creating and storing internally a set of mutex
locks, one per thread, and then locking each call to a
{py:obj}`Mediator<pntos.api.Mediator>` function using a mutex. The
{py:obj}`Mediator<pntos.api.Mediator>` function calls would then consist of locking
logic followed by routing calls from one plugin to another. In our current example
illustrated in the above diagram, we are routing data the {py:obj}`Transport
Plugin<pntos.api.TransportPlugin>` received from a sensor through the
{py:obj}`Mediator<pntos.api.Mediator>`, which in turn (after synchronization according
to its concurrency model) sends the data on to the {py:obj}`Orchestration
Plugin<pntos.api.OrchestrationPlugin>`.

As another example, suppose instead we were writing a multiprocessed controller. In this
case, the controller might ``fork()`` to put plugins into their own processes, and then
write a {py:obj}`Mediator<pntos.api.Mediator>` that opens IPC communication primitives
(such as ``/dev/shm`` or sockets) in order to route the data from the {py:obj}`Transport
Plugin<pntos.api.TransportPlugin>` to the {py:obj}`Orchestration
Plugin<pntos.api.OrchestrationPlugin>`, which are now in different processes. Thus the
{py:obj}`Mediator<pntos.api.Mediator>` that is constructed by the {py:obj}`Controller
Plugin<pntos.api.ControllerPlugin>` is tied closely to the concurrency model chosen by
the {py:obj}`Controller Plugin<pntos.api.ControllerPlugin>`.

<!-- TODO (#170) https://git.aspn.us/pntos/pntos-python/-/issues/170 -->