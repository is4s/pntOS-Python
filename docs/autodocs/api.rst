
.. _pntos_python_api:

pntOS Python API
----------------

.. automodule:: pntos.api
   :special-members: __contains__, __setitem__, __getitem__, __delitem__, __iter__, __len__

.. class:: RegistryValueType

   A ``TypeVar`` of the types allowed in :class:`pntos.api.KeyValueStore`.

   A ``TypeVar`` is particularly for cases where a method needs to guarantee that
   the type on an input is the same as the returned type.

   Example:
      For example, :meth:`pntos.api.KeyValueStore.get_value` needs to guarantee that
      the input and the return types are the same. Thus, :meth:`pntos.api.KeyValueStore.get_value` would
      be a good place to use ``RegistryValueType`` in the type description::

         def get_value(
             self, key: str, value_type: type[RegistryValueType]
         ) -> RegistryValueType | None

.. class:: RegistryValueTypeUnion

   This is a union of all types allowed in :class:`pntos.api.KeyValueStore`.

   This is particularly for cases where a method does not need to guarantee that
   the type on an input is the same as the returned type.

   Example:
      For example, :meth:`pntos.api.KeyValueStore.set_value` does not need to guarantee that
      the input and the return type are the same since it returns `None`. Thus,
      :meth:`pntos.api.KeyValueStore.set_value` would be a good place to use ``RegistryValueTypeUnion``
      in the type description::

         def set_value(self, key: str, value: RegistryValueTypeUnion) -> None

.. class:: FusionEngineType

   Enumerates the types of fusion engines.

   Currently only StandardFusionEngine is defined, but this TypeVar also includes "Any" in the type
   list for future compatibility.

.. class:: FusionStrategyType

   Enumerates the types of fusion strategies.

   Currently only StandardFusionStrategy is defined, but this TypeVar also includes "Any" in the type
   list for future compatibility.

.. class:: PluginType

   An union of all the types of plugins.

   Can be used by the logging plugin to print which plugin the message originated from.

.. class:: InertialType

   An enumeration of the types of inertials an inertial plugin could provide.

   "Any" is included for future compatibility.

.. class:: InitializationType

   An enumeration of the types of initializers an initializer plugin could provide.

   "Any" is included for future compatibility.

.. class:: StateModelProviderType

   An enumeration of the types of state model providers a state modeling plugin could provide.

   "Any" is included for future compatibility.


.. class:: GenXandP
   A function of type: ``Callable[[list[str]], EstimateWithCovariance | None]``

   Returns the estimate and covariance associated with the states of ``block_labels`` within a
   particular measurement processor or state block. This is used to lazily evaluate estimate and
   covariance.

   Args:
      block_labels (list[str]): Labels for state blocks to generate estimate and
         covariance for.

   Returns:
      Estimate and covariance of the provided block_labels. Returns ``None`` if any label in
      ``block_labels`` does not correspond to a valid block.