"""Python API of pntOS."""

from typing import List, Protocol

from pntos.api import CommonPlugin


class PlatformIntegrationPlugin(CommonPlugin, Protocol):
    """
    Platform integration plugin.

    A plugin for command, control, solution output, and other behavior of the
    system which is specific to a particular platform. Works closely with the
    controller plugin to fully define the overall behavior of the system.

    Caution:
        **Unstable**: This feature is unstable and is not yet considered part of the stable pntOS
        API. Usage of this feature is highly discouraged in non-experimental code, and its
        definition may change at any time.
    """

    def take_control(
        self,
        plugins: List[CommonPlugin],
        plugin_resources_locations: List[str | None] | None = None,
        initial_config: str | None = None,
    ) -> None:
        """
        Takes over secondary control from the :class:`ControllerPlugin`.

        When pntOS first boots, it passes control over to the :class:`ControllerPlugin`. After the
        :class:`ControllerPlugin` has initialized the plugins it wants to run, it calls this
        plugin's :meth:`take_control` to allow for platform specific control behavior to run. The
        :class:`PlatformIntegrationPlugin` (PIP) is not responsible for calling the
        :meth:`~CommonPlugin.init_plugin` call on any of the plugins passed in its plugins list, and
        thus the list of plugins that is passed to the PIP should be pruned to only those plugins
        the :class:`ControllerPlugin` initialized. The PIP is consequently not responsible for the
        :class:`Mediator` construction or message routing - those responsibilities fall on the
        :class:`ControllerPlugin`. Instead, the PIP is responsible for doing any additional logic
        that may be platform specific.

        Example:
            For example, the PIP may decide to output solutions at a particular rate, or to have the
            :class:`TransportPlugin` passed in its plugins list start/stop listening in response to
            moding commands, or inform the :class:`OrchestrationPlugin` that it should not use a
            particular sensor at runtime (via a registry convention).

        In general, the goal of the PIP is to implement the platform-specific needs, whereas the
        :class:`ControllerPlugin` is designed to be the generic portion of the code. The
        :class:`ControllerPlugin` should be designed to be generic and re-useable, but work
        hand-in-hand with the PIP to fully define the control behavior of the system.

        :class:`ControllerPlugin` responsibilities:
          - Defining concurrency model
          - Initializing plugins (and constructing/passing in :class:`Mediator`)
          - Routing data from transport plugin to orchestration/initialization/inertial plugins
          - Routing requests for registry data to registry plugins

        :class:`PlatformIntegrationPplugin` responsibilities:
          - Platform specific outputs
          - Responding to moding commands from platform
          - Routing situational awareness information to other pntOS plugins (via registry
            convention)

        The parameters to :meth:`PlatformIntegrationPlugin.take_control` should be identical to
        those passed to the :meth:`ControllerPlugin.take_control`, with the exception of the
        ``plugins`` list being a subset of the ``plugins`` passed to the :class:`ControllerPlugin`.
        Which plugins are passed to the PIP is implementation specific and decided by the
        :class:`ControllerPlugin`.

        Args:
            plugins (List[CommonPlugin]): A subset of the ``plugins`` passed to the
                :class:`ControllerPlugin`. Which plugins are passed to the PIP is implementation
                specific and decided by the :class:`ControllerPlugin`.
            plugin_resources_locations (List[str  |  None] | None, optional): Should be identical to
                what was passed to :meth:`ControllerPlugin.take_control`.
            initial_config (str | None, optional): Should be identical to what was passed to
                :meth:`ControllerPlugin.take_control`.
        """
        pass
