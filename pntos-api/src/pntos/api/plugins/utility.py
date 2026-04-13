"""Python API of pntOS."""

from abc import ABC

from .common import CommonPlugin


class UtilityPlugin(CommonPlugin, ABC):
    """
    A plugin that performs a generic utility function.

    A utility plugin performs implementation-specific functions that may require access
    to pntOS resources (such as the registry) via the :class:`pntos.api.CommonPlugin`
    API. Otherwise, this plugin has no other API-defined functionality.
    """

    pass
