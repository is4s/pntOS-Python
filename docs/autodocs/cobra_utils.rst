.. _cobra-utils:

Cobra Utils
============

These are all the objects and functions that can be directly imported from ``pntos.cobra.utils``. 

.. automodule:: pntos.cobra.utils
   :private-members:
   :exclude-members: _abc_impl, _is_protocol, _is_runtime_protocol


.. data:: ValueType
   :type: TypeVar

   A ``TypeVar`` bound to ``pntos.api.RegistryValueTypeUnion``. This allows fields of
   type ``ValueType`` to be of type ``pntos.api.RegistryValueTypeUnion``, or any subset of
   that union.