"""Python API of pntOS."""

from abc import ABC, abstractmethod

from pntos.api import CommonPlugin


class PlatformIntegrationPlugin(CommonPlugin, ABC):
    """
    Platform integration plugin.

    A plugin for command, control, solution output, and other behavior of the
    system which is specific to a particular platform. Works closely with the
    :class:`pntos.api.ControllerPlugin` to fully define the overall behavior of the system.

    Caution:
        **Unstable**: This feature is unstable and is not yet considered part of the stable pntOS
        API. Usage of this feature is highly discouraged in non-experimental code, and its
        definition may change at any time.
    """

    @abstractmethod
    def take_control(
        self,
        plugins: list[CommonPlugin],
        plugin_resources_locations: list[str | None] | None = None,
        initial_config: str | None = None,
    ) -> None:
        """
        Takes over secondary control from the :class:`pntos.api.ControllerPlugin`.

        When pntOS first boots, it passes control over to the :class:`pntos.api.ControllerPlugin`. After the
        :class:`pntos.api.ControllerPlugin` has initialized the plugins it wants to run, it calls this
        plugin's :meth:`take_control` to allow for platform specific control behavior to run. The
        :class:`pntos.api.PlatformIntegrationPlugin` (PIP) is not responsible for calling the
        :meth:`pntos.api.CommonPlugin.init_plugin` call on any of the plugins passed in its plugins list, and
        thus the list of plugins that is passed to the PIP should be pruned to only those plugins
        the :class:`pntos.api.ControllerPlugin` initialized. The PIP is consequently not responsible for the
        :class:`pntos.api.Mediator` construction or message routing - those responsibilities fall on the
        :class:`pntos.api.ControllerPlugin`. Instead, the PIP is responsible for doing any additional logic
        that may be platform specific.

        Example:
            For example, the PIP may decide to output solutions at a particular rate, or to have the
            :class:`pntos.api.TransportPlugin` passed in its plugins list start/stop listening in response to
            moding commands, or inform the :class:`pntos.api.OrchestrationPlugin` that it should not use a
            particular sensor at runtime (via a registry convention).

        In general, the goal of the PIP is to implement the platform-specific needs, whereas the
        :class:`pntos.api.ControllerPlugin` is designed to be the generic portion of the code. The
        :class:`pntos.api.ControllerPlugin` should be designed to be generic and re-useable, but work
        hand-in-hand with the PIP to fully define the control behavior of the system.

        :class:`pntos.api.ControllerPlugin` responsibilities:
          - Defining concurrency model.
          - Initializing plugins (and constructing/passing in :class:`pntos.api.Mediator`).
          - Routing data from transport plugin to orchestration/initialization/inertial plugins.
          - Routing requests for registry data to registry plugins.

        :class:`pntos.api.PlatformIntegrationPlugin` responsibilities:
          - Platform specific outputs.
          - Responding to moding commands from platform.
          - Routing situational awareness information to other pntOS plugins (via registry
            convention).

        The parameters to :meth:`pntos.api.PlatformIntegrationPlugin.take_control` should be identical to
        those passed to the :meth:`pntos.api.ControllerPlugin.take_control`, with the exception of the
        ``plugins`` list being a subset of the ``plugins`` passed to the :class:`pntos.api.ControllerPlugin`.
        Which plugins are passed to the PIP is implementation specific and decided by the
        :class:`pntos.api.ControllerPlugin`.

        Args:
            plugins (list[CommonPlugin]): A subset of the ``plugins`` passed to the
                :class:`pntos.api.ControllerPlugin`. Which plugins are passed to the PIP is implementation
                specific and decided by the :class:`pntos.api.ControllerPlugin`.
            plugin_resources_locations (list[str  |  None] | None, optional): Should be identical to
                what was passed to :meth:`pntos.api.ControllerPlugin.take_control`.
            initial_config (str | None, optional): Should be identical to what was passed to
                :meth:`pntos.api.ControllerPlugin.take_control`.
        """
        pass
