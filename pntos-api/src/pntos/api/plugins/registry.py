"""Python API of pntOS."""

from abc import ABC, abstractmethod

from pntos.api import CommonPlugin, Registry


class RegistryPlugin(CommonPlugin, ABC):
    """
    Registry plugin.

    A plugin for a global key-value registry. See the `pntOS Registry` page in
    the `Internals` section for more information on the goal of this plugin.
    """

    @abstractmethod
    def new_registry(self, initial_config: str | None = None) -> Registry:
        """
        Create a new registry based on the initial values stored in ``initial_config``.

        Args:
            initial_config (str | None, optional): The initial values the new registry should be
                based on. The format of ``initial_config`` is implementation
                specific, and plugins are free to support any or no format. Possible formats may
                include:

                - ``None``, in which case the plugin is free to choose initial values. Choices may
                  include hard-coded in the plugin or none at all.
                - A ``str``.  Examples of possible values the parameter could hold:

                    1. The entire config.
                    2. A local file path on systems which support them.
                    3. A string adhering to the URI scheme.

        Returns:
            Registry: The newly created registry.

        Note:
            The returned :class:`Registry` should be capable of producing :class:`KeyValueStore`
            structs that are able to be used concurrently. Thus if the user uses the return value of
            this method to start two batches, one on group "foo" and the other on group "bar", then
            concurrent access to both of the resulting :class:`KeyValueStore` structs for "foo" and
            "bar" should be supported (i.e. no shared mutable state between them that is not
            synchronized).
        """
        pass
