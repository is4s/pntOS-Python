
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
