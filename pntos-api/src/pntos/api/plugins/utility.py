"""Python API of pntOS."""

from abc import ABC

from .common import CommonPlugin


class UtilityPlugin(CommonPlugin, ABC):
    """
    A plugin that performs a generic utility function.

    A utility plugin performs functions that may require access to pntOS resources (such
    as the registry) but is not otherwise relied upon to perform any particular
    function.
    """

    pass
