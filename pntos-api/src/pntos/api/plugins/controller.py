"""Python API of pntOS."""

from typing import List, Protocol

from pntos.api import CommonPlugin


class ControllerPlugin(CommonPlugin, Protocol):
    """
    Controller plugin.

    An implementation of a primary controller in charge of defining the usage of all other pntOS
    plugins.

    In ordinary operation, an app will import plugins, initializing a controller plugin, and then
    calling :meth:`ControllerPlugin.take_control` on the controller plugin, passing in a list of
    ``plugins`` that it imported.

    From that point forward, the controller is responsible for all activity. It may 
    use any or none of the plugins in the ``plugins`` list as desired. In general, it may do
    anything it wants, within the following guidelines:

    - The controller should not load new plugins - it should work with the ``plugins`` passed to it
      in the :meth:`take_control` parameters.

    - The controller must call :meth:`CommonPlugin.init_plugin` on any plugin it wishes to use prior
      to using any other functionality on that plugin. The controller must pass a :class:`Mediator`
      that the plugin may use to communicate back to the controller. This callback design allows the
      controller to abstract away the concurrency model - in particular, a callback function may be
      anything from a direct invocation of a Python function to a shim that utilizes IPC channels to
      communicate to process-separated or machine-separated plugins.

    Outside of these requirements, the controller defines any and all I/O it supports, which pntOS
    plugins are loaded / used, and the type of fusion being done. The controller can be hard-coded
    to support only a specific sensor configuration or written generically to support arbitrary
    run-time environment sensing. Outside of some initialization in the app, the controller is the
    conceptual "main" function.

    When the controller is provided a :class:`PlatformIntegrationPlugin` as one of the plugins in
    the ``plugins`` list passed to :meth:`take_control`, that indicates to the controller that
    platform-specific control logic exists and must be used. In this case, the controller's primary
    objective's are to:

    - Pick the concurrency model being used (multiprocessed, multithreaded, coroutines,
      single-threaded, etc.).
    - Spin up the concurrency primitives to implement the chosen concurrency type.
    - Provide a :class:`Mediator` to all plugins in their :meth:`CommonPlugin.init_plugin` call that
      enables inter-plugin communication.

    After that task is accomplished, the controller should call the
    :meth:`PlatformIntegrationPlugin.take_control` function and allow the
    :class:`PlatformIntegrationPlugin` (PIP) to actively call functions on the ``plugins`` list.
    Once the :meth:`PlatformIntegrationPlugin.take_control` has been called, the controller must
    lock/synchronize the controller's and the PIP's access to function calls in the ``plugins``
    list, such that any action the PIP might take will not interfere with the controller's actions
    (or, equivalently, actions that the mediator provided by the controller is taking). One simple
    approach to synchronizing access to the plugins list across the controller and PIP is for the
    plugins list provided to the PIP to be a facade that actually routes messages through to the
    mediator, such that the mediator handles all requests and can synchronously dispatch them. More
    efficient approaches exist, however, it is the responsibility of the controller to make sure
    that all accesses the PIP makes to resources passed to it are synchronized with respect to the
    controller's chosen concurrency primitive.
    """

    def take_control(
        self,
        plugins: List[CommonPlugin],
        plugin_resources_locations: List[str | None] | None = None,
        initial_config: str | None = None,
    ) -> None:
        """
        Takes over primary control of the program from the app.

        Takes over primary control of the program from the app, using the ``plugins`` to process
        data, generate fused estimates, and ultimately produce and output PNT solutions.
        :meth:`take_control` must use the plugins passed to it and construct a full pntOS system.
        Please see the description of the :class:`PlatformIntegrationPlugin` (PIP) for a description
        of duties of this function compared to the duties of the
        :meth:`PlatformIntegrationPlugin.take_control` method (if a PIP is in the ``plugins`` list).

        Args:
            plugins (List[CommonPlugin]): An array of plugins available to the controller`.
            plugin_resources_locations (List[str  |  None] | None, optional): A list of strings
                which represent a list of locations, one for each plugin in ``plugins``, where those
                plugins may find auxiliary data if needed. The array can be ``None``, 
                otherwise the array is of the same length as ``plugins``. Each string may be
                ``None``, filesystem paths, or adhere to some scheme, such as the URI scheme, for
                defining the resource's location.
            initial_config (str | None, optional): Represents a source of values to initialize the
                primary pntOS configuration. This could be ``None`` or a ``str``. Examples of
                possible values for the latter are:

                1. The entire config.
                2. A local file path on systems which support them.
                3. A string adhering to the URI scheme.
        """
    pass
