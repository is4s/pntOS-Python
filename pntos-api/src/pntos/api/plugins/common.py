"""Python API of pntOS."""

from abc import ABC, abstractmethod
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import (
    TypeVar,
)

from aspn23 import AspnBase, TypeTimestamp
from numpy import float64
from numpy.typing import NDArray


@dataclass
class Message:
    """
    A container for an ASPN message.

    This container may contain either proper ASPN messages which are part of the ASPN data model, or
    extension messages specific to pntOS which augment ASPN.

    Attributes:
        wrapped_message (AspnBase): Either an ASPN message or a pntOS ASPN Extension message.
        source_identifier (str): Indicates where this message came from. If the message originated
            from a :class:`pntos.api.TransportPlugin` and the underlying transport has the concept of a
            channel or topic, this field should be populated by the channel or topic. Otherwise, the
            identifier is populated in a plugin-specific manner by the originating plugin that
            created the message.
    """

    wrapped_message: AspnBase
    source_identifier: str


class EstimateWithCovarianceType(Enum):
    """Describes how the fields in :class:`pntos.api.EstimateWithCovariance` are used."""

    EWC_GENERIC = 0
    """
    Contains a mean (estimate) and covariance describing a multivariate Gaussian distribution.

      - :attr:`.EstimateWithCovariance.estimate` is size Nx1 where N is the length field.
      - :attr:`.EstimateWithCovariance.covariance` is size NxN where N is the length field.
    """

    EWC_ATTITUDE_QUAT = 1
    """
    Contains a mean (estimate) and covariance describing a rotation modeled by a multivariate
    Gaussian distribution, but the estimate is in quaternion form and the covariance is in tilt
    error form.

      - :attr:`.EstimateWithCovariance.estimate` is size 4x1.
      - :attr:`.EstimateWithCovariance.covariance` is size 3x3, in :math:`\\text{radians}^2`.
    """


@dataclass
class EstimateWithCovariance:
    """
    A container for holding an estimate and covariance.

    Attributes:
        type (EstimateWithCovarianceType): Describes how the fields in this struct are used.
        estimate (NDArray[float64]): An array of doubles representing an estimate vector. Usage depends on
            the ``type`` field.
        covariance (NDArray[float64]): An array of doubles representing a square covariance matrix. Data is
            stored in row major form. Usage depends on the ``type`` field.
    """

    type: EstimateWithCovarianceType
    estimate: NDArray[float64]
    """An estimate vector."""

    covariance: NDArray[float64]
    """A covariance matrix, describing the errors in the estimate."""


class LoggingLevel(IntEnum):
    """An enumeration of the types of log outs that are available in pntOS."""

    ERROR = 0
    """
    This output indicates the program has entered an error state, and
    likely needs to be inspected to discover what went wrong.
    """

    WARN = 1
    """
    This output is designed to warn of a possibly unintended state that may
    be harmless or be indicative of a bug.
    """

    INFO = 2
    """
    This output is designed to be informational, and may indicate correct
    operation.
    """

    DEBUG = 3
    """
    This output is designed to assist in debugging plugins by providing
    additional information about state and behavior which would be
    otherwise unnecessary.
    """


class KeyValueStoreDataFormat(Enum):
    """
    The format of data returned or expected.

    An enum that specifies the format of data returned/expected in the :meth:`pntos.api.KeyValueStore.get_raw`
    and :meth:`pntos.api.KeyValueStore.set_raw` methods. This value is otherwise unused when querying a
    key-value store.
    """

    INI = 0
    """
    Keys and their corresponding values are returned according to the INI
    file format specification.
    """

    UNSPECIFIED = 1
    """
    An opaque type that is undefined by the implementer.
    """


RegistryValueType = TypeVar(
    'RegistryValueType',
    str,
    list[str],
    int,
    bool,
    float,
    NDArray[float64],
    Message,
)
"""
A ``TypeVar`` of the types allowed in :class:`pntos.api.KeyValueStore`.

A ``TypeVar`` is particularly for cases where a method needs to guarantee that
the type on an input is the same as the returned type.

Example:
    For example, :meth:`pntos.api.KeyValueStore.get_value` needs to guarantee that
    the input and the return types are the same. Thus, :meth:`pntos.api.KeyValueStore.get_value` would
    be a good place to use :class:`pntos.api.RegistryValueType` in the type description::

        def get_value(
            self, key: str, value_type: type[RegistryValueType]
        ) -> RegistryValueType | None
"""

RegistryValueTypeUnion = (
    str | list[str] | int | bool | float | NDArray[float64] | Message
)
"""
This is a union of all types allowed in :class:`pntos.api.KeyValueStore`.

This is particularly for cases where a method does not need to guarantee that
the type on an input is the same as the returned type.

Example:
    For example, :meth:`pntos.api.KeyValueStore.set_value` does not need to guarantee that
    the input and the return type are the same since it returns `None`. Thus,
    :meth:`pntos.api.KeyValueStore.set_value` would be a good place to use :class:`RegistryValueTypeUnion`
    in the type description::

        def set_value(self, key: str, value: RegistryValueTypeUnion) -> None
"""


class KeyValueStore(ABC):
    """
    A key-value store implemented with a string-pair key.

    This key-value store is intended to function as an expanded python
    dictionary.

    Each value can be looked up by an associated key (string). Values can be of
    any type specified by :class:`RegistryValueType`/:class:`RegistryValueTypeUnion`.

    Example:
        For example, to store a string value "foo" in the key-value store under the key "k1", one
        would write either of the following::

            store.set_value("k1", "foo")
            store["k1"] = "foo"

        At this point, the key-value store would have recorded the value into its
        internal data storage. Later a user could call either of these lines::

            foo = store.get_value("k1", str)
            foo = store["k1"]

        to retrieve the value at key "k1".

        The advantage of ``get_value`` is that if the conversion is possible, the
        user can specify a different type to return than the type that was
        originally stored in the key-value store. For example, these two lines
        demonstrate a user saving an integer to the key-value store and then
        retrieving it as a string::

            store["k2"] = 42
            val = store.get_value("k2", str) # val now equals "42"

    In general, a :class:`pntos.api.KeyValueStore` is generated by a :class:`pntos.api.Registry` and not directly by
    other code. The :class:`pntos.api.Registry` will return key/value stores on demand, utilizing the data
    backing store chosen by the plugin to store data (either ephemerally in memory or permanently in
    persistent storage). In general, it is only valid to call the getters/setters on a
    :class:`pntos.api.KeyValueStore` during a batch operation. See :class:`pntos.api.Registry` for more information.

    Attributes:
        data_format (KeyValueStoreDataFormat): The data format that is used by the :meth:`set_raw`
            and :meth:`get_raw` methods.
    """

    @abstractmethod
    def keys(self) -> list[str] | None:
        """
        Get the array of keys which currently exist in this store.

        Returns:
            list[str] | None: Returns the keys in the store or ``None`` if no keys are present.
        """
        pass

    @abstractmethod
    def __contains__(self, key: str) -> bool:
        """
        Check whether or not a given key exists in the store.

        Particularly, this function allows the
        user to use python "if in" statements::

            if key in store:
                ...

        Args:
            key (str)

        Returns:
            bool
        """
        pass

    @abstractmethod
    def get_value(
        self, key: str, value_type: type[RegistryValueType]
    ) -> RegistryValueType | None:
        """
        Get the value stored at ``key`` with return type ``value_type``.

        Example:
            For example, to access altitude in a :class:`pntos.api.KeyValueStore` named ``kv_store`` as an
            integer::

                altitude = kv_store.get_value("altitude", int)

        Args:
            key (str)
            value_type (type[RegistryValueType])

        Returns:
            :class:`pntos.api.RegistryValueType` | None: Returns ``None`` if the key is not available. The return is
            guaranteed to not be ``None`` if called with a valid key (which can be checked with
            :meth:`pntos.api.KeyValueStore.__contains__`) and if the store can convert the value to the requested type.
        """
        pass

    @abstractmethod
    def __getitem__(self, key: str) -> RegistryValueTypeUnion | None:
        """
        Gets an item in the key-value store.

        This function enables python bracket indexing to return a value from the
        store for a given key.

        Example:
            For example::

                if key in store:
                    foo = store[key] # foo is now the value stored at key

        Args:
            key (str)

        Returns:
            :class:`RegistryValueTypeUnion` | None: This is guaranteed to return a value
            of the same type as :meth:`get_type` returns for the given key, if
            the key exists. If :meth:`get_type` returns ``None`` (indicating
            type information is not available), then this method will only
            return values as strings or Messages.
        """
        pass

    @abstractmethod
    def get_raw(self, key: str | None = None) -> bytes | None:
        """
        Get the value for the given ``key`` as an array of bytes.

        Args:
            key (str | None, optional)

        Returns:
            bytes | None: The return format will conform to the definition in
            :attr:`pntos.api.KeyValueStore.data_format`. Returns ``None`` if the given key is not available.
            The return is guaranteed to not be ``None`` if called with a valid key, which can be
            checked with :meth:`pntos.api.KeyValueStore.__contains__`::

                if key in store:
                ...

            If ``key`` is ``None``, then this function will return all
            of the keys and values in the group passed to :meth:`pntos.api.Registry.batch_start` and will be
            formatted to conform to keys and values as defined in :attr:`pntos.api.KeyValueStore.data_format`.
        """
        pass

    @abstractmethod
    def set_value(self, key: str, value: RegistryValueTypeUnion) -> None:
        """
        Set the given key to the provided value.

        Args:
            key (str)
            value (RegistryValueTypeUnion): Can be of any type specified by
                :class:`pntos.api.RegistryValueTypeUnion`.
        """
        pass

    @abstractmethod
    def __setitem__(self, key: str, value: RegistryValueTypeUnion) -> None:
        """
        Set an item in the key-value store.

        Same functionality as :meth:`set_value`, but allows python bracket
        indexing to set values in the store.

        Example:
            For example::

                store["key"] = 42

        Args:
            key (str)
            value (RegistryValueTypeUnion): Can be of any type specified by
                :class:`pntos.api.RegistryValueTypeUnion`.
        """
        pass

    @abstractmethod
    def set_raw(self, key: str | None, bytes: bytes) -> None:
        """
        Set the given key to the provided value.

        Args:
            key (str | None): If ``key`` is ``None``, then the contents of ``bytes`` must include
                both keys and values and must be formatted to conform to
                :attr:`pntos.api.KeyValueStore.data_format`. ``bytes`` will then be used to set the
                corresponding keys and values in the group passed to :meth:`pntos.api.Registry.batch_start`.
            bytes (bytes): Must be formatted to conform to the definition of a value in
                :attr:`pntos.api.KeyValueStore.data_format`.
        """
        pass

    @abstractmethod
    def remove_key(self, key: str) -> bool:
        """
        Remove the given key from the registry.

        Args:
            key (str)

        Returns:
            bool: ``True`` if ``key`` is successfully removed, and ``False`` otherwise. Keys may
            fail to be removed if the key does not currently exist, or the backend is unable to
            remove the key.
        """
        pass

    @abstractmethod
    def batch_end(self) -> None:
        """
        Ends a batch operation.

        Ends a batch operation started with a :meth:`pntos.api.Registry.batch_start` call. After calling this,
        the user should not use the :class:`pntos.api.KeyValueStore` they received from
        :meth:`pntos.api.Registry.batch_start` again without calling :meth:`pntos.api.KeyValueStore.batch_restart` on the
        :class:`pntos.api.KeyValueStore`.

        If keys in the batch were acted upon with :meth:`set_permanent` turned on, and the plugin
        supports permanent storage, this call will save changes to permanent storage if
        :meth:`set_permanent` is ``True`` during the call to :meth:`batch_end`. Enacts equivalent of
        ``set_permanent(self,false)`` before return. If any :meth:`request_notify` observers have
        been added, they will be processed prior to this call returning.

        Example:
            Example 1: Flushing to permanent storage on :meth:`batch_end`::

                store = registry.batch_start("group")
                ...work...
                store.set_permanent(true) # if not disabled, flush on batch_end
                ...work...
                store.batch_end()    # will flush values

            Example 2: Not flushing to permanent storage on :meth:`batch_end`::

                store = registry.batch_start("group")
                ...work...
                store.set_permanent(true)  # tag some values
                ...work...
                store.set_permanent(false) # do not flush on batch_end
                store.batch_end()          # will not flush values

        In the second example above, values set with "set" methods after the initial
        :meth:`set_permanent` call are still stored for potential saving to permanent storage.
        """
        pass

    @abstractmethod
    def batch_restart(self) -> None:
        """
        Restarts a batch.

        Restarts a batch that was previously started with :meth:`pntos.api.Registry.batch_start` and
        subsequently ended with :meth:`pntos.api.KeyValueStore.batch_end`. This method is likely
        much more efficient than :meth:`pntos.api.Registry.batch_start` (depending on the registry
        implementation) as the :meth:`pntos.api.Registry.batch_start` method must find the store
        again given the group name.

        Note:
            While a batch is active, access to the store may be denied to other users. Thus a user
            should endeavour to call :meth:`batch_end` as soon as possible after they are done
            getting/setting values in the returned :class:`pntos.api.KeyValueStore`.
        """
        pass

    @abstractmethod
    def request_notify(
        self,
        key: str | None,
        callback: Callable[[str, list[str], 'KeyValueStore'], None],
    ) -> bool:
        """
        Register a callback which gets called each time a key in the store is updated.

        Allows plugins to respond asynchronously to parameter updates. Returns ``True`` if the
        notifier was successfully registered, and ``False`` if the store is unable to notify the
        requester. If ``key`` is ``None``, then the callback will be invoked when any key in the
        batch's group is modified. Otherwise, the callback will only be invoked when the given key
        is modified.

        Note:
            The callback must not attempt to set any values inside the :class:`pntos.api.KeyValueStore`, as
            the callback is likely being invoked during the processing of another operation. The
            callback should endeavour to store off the updated keys/values as quickly as possible
            and return, leaving the processing of the updates to another context or thread when
            possible. Calling :class:`pntos.api.Mediator` within the callback may be disallowed by the
            controller implementation and lead to undefined behavior.

        Args:
            key (str | None)
            callback (Callable[[str, list[str], KeyValueStore], None]): A
                function with a function definition compatible with::

                    def my_callback(group: str, modified_keys: list[str], kv: KeyValueStore) -> None:
                        ...

        Returns:
            bool: ``True`` if the notifier was successfully registered, and ``False`` if the store
            is unable to notify the requester.
        """
        pass

    @abstractmethod
    def remove_notify(
        self,
        key: str | None,
        callback: Callable[[str, list[str], 'KeyValueStore'], None],
    ) -> bool:
        """
        Removes a notification as requested by :meth:`request_notify`.

        The group and callback must match the parameters passed to :meth:`request_notify`
        in order to successfully remove a callback.

        Note:
            This will remove all matching callbacks that have a matching group and callback. If a
            user registers the same callback twice this will remove both.

        Args:
            key (str | None)
            callback (Callable[[str, list[str], KeyValueStore], None])

        Returns:
            bool: ``True`` if removal was successful and ``False`` if it was not. ``False`` will be
            returned if a callback did not exist for the group.
        """
        pass

    @abstractmethod
    def __delitem__(self, key: str) -> None:
        """
        Delete the item with the specified key.

        Must remove the given key and the associated value from the store, along
        with any callbacks or permanency settings.

        This enables the python ``del`` operator.

        Example:
            For example::

                for key in keys_to_remove:
                    del store[key]

        Args:
            key (str)
        """
        pass

    @abstractmethod
    def __iter__(self) -> Iterator[str]:
        """
        Return an iterator over the keys in the store.

        This allows for easy iteration over the key-value store.

        Example:
            For example::

                for key in store:
                    ...

        Returns:
            Iterator
        """
        pass

    @abstractmethod
    def __len__(self) -> int:
        """
        Return the number of items in the store.

        This allows the use of python's ``len`` function.

        Example:
            For example::

                num_elements = len(key_val_store)

        Returns:
            int
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """Remove all items from key-value store."""
        pass

    @abstractmethod
    def set_permanent(self, permanent: bool) -> bool:
        """
        Tag values modified with "set" methods as permanently stored.

        Configure the :class:`pntos.api.KeyValueStore` to tag values modified with "set" methods as
        permanently stored (as opposed to ephemerally stored in memory). Only values acted upon with
        "set" methods while :meth:`set_permanent` is ``True`` will be tagged. Values will be flushed
        according to registry configuration settings or per :meth:`batch_end` API. Returns the value
        of the permanent storage configuration. Callers should check this to verify if the set was
        successful.

        Example:
            Tagging specific keys to be permanently stored::

                store: PntosKeyValueStore = registry.batch_start("group")
                store.set_value("key1",1234.56) # does not tag this value as permanently stored
                store.set_permanent(True)       # start tagging set calls as permanently stored
                store.set_value("key1",987.65)
                store.set_value("key2",123)     # both key1 and key2 values tagged
                store.set_permanent(False)      # disable permanent storage
                store.set_value("key1",456.78)  # key1 = 456.78 is value of key1 in store
                                                # key1 = 987.65 tagged to be permanently stored
                                                # key2 = 123    tagged to be permanently stored

        Args:
            permanent (bool)

        Returns:
            bool: The value of the permanent storage configuration. Callers
            should check this to verify if the set was successful.
        """
        pass

    @abstractmethod
    def values(self) -> list[RegistryValueTypeUnion]:
        """
        Returns a list of the key-value store's values.

        This method is useful for unloading all values from a key-value store.

        Example:
            For example::

                def get_mean_of_kv_store(kv: KeyValueStore) -> float | None:
                    '''Returns the mean of a key-value store if all values are int or float'''
                    values = kv.values()
                    if all(isinstance(x, (int, float)) for x in values):
                        return sum(values) / len(values)
                    return None

        Returns:
            list[RegistryValueTypeUnion]: A list of all values in the store.

        """
        pass

    @abstractmethod
    def items(self) -> list[tuple[str, RegistryValueTypeUnion]]:
        """
        Returns a list of the items (key-value pairs) in the store.

        This method is useful for when you need to iterate over both keys and
        values in a dictionary.

        Example:
            For example::

                for key, value in my_dict.items()
                    printf('Key: {key}, Value: {value}')

        Returns:
            list[tuple[str, RegistryValueTypeUnion]]: A list of the key-value pairs (as
            tuples) in the store.
        """
        pass

    @abstractmethod
    def get_type(self, key: str) -> type[RegistryValueTypeUnion] | None:
        """
        Returns the type of a value in the KeyValueStore.

        This is helpful for situations when it is advantageous to know the
        type of a value in the store without need for the value itself.

        Example:
            For example, it might be useful for these situations where different
            callbacks are needed depending on what type is in the store::

                if key in kv_store:
                    val_type = kv_store.get_type(key)
                    if val_type is int:
                        kv_store.request_notify(key, int_callback)
                    elif val_type is Message:
                        kv_store.request_notify(key, message_callback)
                    else:
                        kv_store.request_notify(key, generic_callback)

        Args:
            key (str)

        Returns:
            type[RegistryValueTypeUnion] | None: If key exists in registry,
            this is guaranteed to return the return type of :meth:`pntos.api.KeyValueStore.__getitem__`
            for the given key. Else, it returns ``None`` if type information is
            not available or key does not exist in registry.
        """
        pass

    data_format: KeyValueStoreDataFormat
    """Defines the underlying format which the data in the key-value store will be stored as.
    """


class Registry(ABC):
    """
    A registry of key/value data which is organized by (string) groups.

    In order to get/set a key in the registry, one must call :meth:`pntos.api.Registry.batch_start` with the
    group the key is stored under and then use the resulting :class:`pntos.api.KeyValueStore` to get/set the
    key/value pair. When one is done accessing keys in the :class:`pntos.api.KeyValueStore`, they must call
    :meth:`pntos.api.KeyValueStore.batch_end`. It is not permitted to access any member inside the
    :class:`pntos.api.KeyValueStore` after a batch has ended. If a user has ended a batch and then desires to
    access the :class:`pntos.api.KeyValueStore` again, they may use the :meth:`pntos.api.KeyValueStore.batch_restart`
    method.
    """

    @abstractmethod
    def batch_start(self, group: str) -> KeyValueStore:
        """
        Begin a batch get/set operation.

        Begin a batch get/set operation wherein the user may make any number of modifications to the
        keys/values in the ``group``. The registry implementation may wait to batch these requests
        until :meth:`pntos.api.KeyValueStore.batch_end` is called for better performance. For example, a lock
        may be obtained at the beginning of a :meth:`batch_start` and not released until a
        :meth:`pntos.api.KeyValueStore.batch_end` call is encountered. Thus, a plugin that calls
        :meth:`batch_start` should endeavour to make its calls to the ``set_``, ``get_``, and
        ``register`` methods as quickly as possible and call :meth:`pntos.api.KeyValueStore.batch_end`
        immediately, as doing otherwise may be locking other plugins out of access to the registry
        (depending on the registry plugin implementation). If a plugin supports
        :meth:`pntos.api.KeyValueStore.request_notify`, then notifications of updates may be suspended until
        the batch ends. After a batch is ended, the returned :class:`pntos.api.KeyValueStore` can still be
        used to access the store via :meth:`pntos.api.KeyValueStore.batch_restart`.

        Note:
            While a batch is active, access to the store may be denied to other users. Thus a user
            should endeavour to call :meth:`pntos.api.KeyValueStore.batch_end` as soon as possible after they
            are done getting/setting values in the returned :class:`pntos.api.KeyValueStore`.

        Args:
            group (str)

        Returns:
            KeyValueStore
        """
        pass

    @property
    @abstractmethod
    def group_array(self) -> list[str] | None:
        """
        Get the array of groups which currently exist.

        Returns:
            list[str] | None: The array of groups which currently exists. Returns ``None`` if no groups
            exist.
        """
        pass

    @abstractmethod
    def has_group(self, group: str) -> bool:
        """
        Checks whether or not a given group has had any values added to it (for any key).

        Args:
            group (str)

        Returns:
            bool
        """
        pass

    @abstractmethod
    def request_notify_new_group(self, callback: Callable[[str], None]) -> bool:
        """
        Register a callback which gets called each time a new group is made in the registry.

        Args:
            callback (Callable[[str], None])

        Returns:
            bool: ``True`` if the notifier was successfully registered, and ``False`` if the
            registry is unable to notify the requester.
        """
        pass


class Mediator(ABC):
    """
    A set of callbacks which are handed to a pntOS plugin upon initialization.

    When a plugin is first initialized into pntOS, it is guaranteed that the plugin will be passed
    an instance of this struct via an invocation of :meth:`pntos.api.CommonPlugin.init_plugin` (See
    :class:`pntos.api.CommonPlugin` for more information). The plugin may then use the set of function calls
    in this class to make requests of the :class:`pntos.api.ControllerPlugin`.

    All of the functions on this class (and any returned values from those functions) are guaranteed
    to be thread-safe for use by all plugins. Thus, after a pntOS plugin has received a copy of a
    :class:`pntos.api.Mediator` it can freely call the functions contained therein without doing any explicit
    locking. This thread safety is implemented by the :class:`pntos.api.ControllerPlugin` when it creates the
    mediator before passing them to other plugins.

    Callers must still take care to only call functions in :class:`pntos.api.Mediator` which they are not
    themselves responsible for implementing. The details of which plugins are used in the
    implementation of any particular function on this struct is decided by the
    :class:`pntos.api.ControllerPlugin`, and thus is implementation specific to the :class:`pntos.api.ControllerPlugin`
    used.

    Attributes:
        registry (Registry): A :class:`pntos.api.Registry` object that can be used to update keys/values in
            the pntOS global registry.
    """

    @property
    @abstractmethod
    def filter_description_list(self) -> list[str]:
        """
        Request a list of strings describing the solutions available.

        One of these description strings may be used when calling :meth:`request_solutions`. For
        consistency, these strings should adhere to the following conventions:

        - Strings should be upper case and have words and acronyms separated by underscores
          (``UPPER_SNAKE_CASE``).
        - Strings should contain the substring ``BEST`` when they represent the primary solution.
        - Strings should contain the substring ``DEAD_RECKONING`` when they represent a solution
          suitable for estimating relative motion or rotation over a period of time. This solution
          may drift more than ``BEST`` solutions, as the goal is to allow a user to get an estimate
          of the relative motion between different times. In the calculation of this solution, some
          sensor measurement might be excluded. For example, a system with an IMU might provide a
          ``DEAD_RECKONING`` solution which is the solution from its free-running inertial
          mechanization, with resets disabled during the time intervals between ``solution_times``
          (but resets applied before all of the ``solution_times``).
        - Strings should include a substring indicating the type of solution returned. This
          substring should contain the string-equivalent to the corresponding ASPN message class
          name, converted to UPPER_SNAKE_CASE, followed by the string ``_ESTIMATE``. This allows the
          user to perform substring matching without a risk of getting a false positive match from a
          type whose string would be a subset of another type.

        Example:
            If the primary solution is an ASPN PVA then the string
            ``MY_BEST_ASPN_MEASUREMENT_POSITION_VELOCITY_ATTITUDE_ESTIMATE`` would fulfill the
            convention.

        These conventions allow the user to identify their desired type of solution using substring
        matching.

        Returns:
            list[str]: A list of strings describing the solutions available.
        """
        pass

    @abstractmethod
    def request_solutions(
        self,
        solution_times: list[TypeTimestamp],
        filter_description: str | None = None,
    ) -> list[Message | None] | None:
        """
        Request filtering solutions at the times specified in the array ``solution_times``.

        Args:
            solution_times (list[TypeTimestamp]): The times at which to return solutions.
            filter_description (str | None, optional): To select which filter(s) to request
                solutions from, enter a valid filter description string in ``filter_description``.
                Valid filter description strings can be obtained by calling
                :attr:`filter_description_list`. Passing in ``None`` will provide a result
                specific to a particular implementation. When ``filter_description`` is ``None``,
                the implementation should endeavor to return its best solution.

        Returns:
            list[Message | None] | None: An array of messages containing the filter solutions for the requested
            ``solution_times``. Some entries may be ``None`` if they are unavailable at the corresponding time
            in ``solution_times``. The returned :class:`pntos.api.Message` array may be ``None`` if
            ``filter_description`` is invalid.
        """
        pass

    @abstractmethod
    def process_pntos_message(self, message: Message) -> None:
        """
        Send a new message to the system for arbitrary processing.

        For example, this function is useful for plugins who have just received new
        sensor data that they wish to relay to the system to be used in a sensor fusion
        solution.

        Args:
            message (Message)
        """
        pass

    @abstractmethod
    def broadcast_aspn_message(
        self,
        message: Message,
        transport: str | None = None,
        destination_identifier: str | None = None,
    ) -> None:
        """
        Request that pntOS broadcast the provided message out to the network.

        Args:
            message (Message)
            transport (str | None, optional): The identifier of a transport plugin that the message
                should be routed to. The transport parameter should match the
                :attr:`pntos.api.CommonPlugin.identifier` string of a
                :class:`pntos.api.TransportPlugin` active in the system. If the transport parameter
                is ``None``, this indicates that the message should be broadcast to all available
                transports.
            destination_identifier (str | None, optional): A transport-specific identifier that
                allows transports to determine how to route the message. If the destination
                transport has the concept of a channel or topic, ``destination_identifier`` should
                be populated by the channel or topic. Otherwise, the identifier is populated in a
                plugin-specific manner defined by the destination transport. If
                ``destination_identifier`` is ``None``, then the transport should output the message
                in the "default" output channel/topic and route being used by pntOS.
        """
        pass

    @abstractmethod
    def log_message(self, level: LoggingLevel, message: str) -> None:
        """
        Log a message.

        Send a loggable message to the system, to be logged through the current
        logging infrastructure enabled (e.g. the console, a logfile, etc.).

        Args:
            level (LoggingLevel)
            message (str)
        """
        pass

    registry: Registry


class CommonPlugin(ABC):
    """
    Common definitions that all plugins must provide.

    This structure should not be used directly (except in the case of a utility plugin), but instead
    is composed as the first field on all of the concrete pntOS plugin structures. For example, the
    transport plugin is specified as::

        class TransportPlugin(CommonPlugin, ABC):

            def init_plugin(...):
                ...init_plugin implementation...

            def ...other function implementations...


    Thus this class defines a set of functions and variables that all plugins have. The
    :meth:`pntos.api.CommonPlugin.init_plugin` function is guaranteed to be called by pntOS when the plugin is
    first loaded into memory by the system.

    Example:
        When defining a new transport plugin, the plugin writer is responsible for implementing all
        fields on the :class:`pntos.api.TransportPlugin` class. Thus, the fields of the :class:`pntos.api.CommonPlugin`
        nested on the :class:`pntos.api.TransportPlugin` are implemented by the plugin writer.

    Attributes:
        identifier (str): A string identifier uniquely identifying this plugin. This string will be
            used to determine the unique space this plugin receives in the system config.
    """

    @abstractmethod
    def init_plugin(
        self,
        plugin_resources_location: str | None = None,
        mediator: Mediator | None = None,
    ) -> None:
        """
        The first plugin method called; initializes the plugin.

        A function that will be called by pntOS once and only once when it first initializes the
        plugin before any other functions on the plugin are called. Here the plugin may do dynamic
        runtime initialization of its members, and is given the full path to the location of a data
        folder specific to the plugin, in case it needs to acquire additional files. An
        instance of :class:`pntos.api.Mediator` will be passed which the plugin should save off for later use.
        Whenever the plugin needs to make a request of pntOS, it should use one of the fields in the
        :class:`pntos.api.Mediator` instance received by the plugin in this function call.

        Note:
            Implementation note: This inversion of control allows the controller to implement the
            :class:`pntos.api.Mediator` class, and abstracts away the return communication channel from the
            plugin to the rest of the system. Thus, the plugin need only implement :class:`pntos.api.Mediator`
            by simply saving a copy of the functions that the controller passes into it. Then, when
            the plugin later needs to make requests of the system, it may call a function in its
            copy of :class:`pntos.api.Mediator`, without needing any knowledge of how the controller
            implemented :class:`pntos.api.Mediator`. This allows controllers to implement arbitrary
            concurrency models, including single-threaded, multi-threaded, multi-process, and
            distributed computing.

        Args:
            plugin_resources_location (str | None, optional): Specifies the location of the plugin's
                resources.  The location is determined by the controller plugin, and therefore is
                controller implementation specific. Plugin implementers wishing to provide a
                resource to their plugin should consult the documentation of the controller to
                determine which location scheme will be passed into this function.
            mediator (Mediator | None, optional): ``None``-able if the plugin type being initialized
                is a :class:`pntos.api.ControllerPlugin`. Non-controller plugins may assume that the mediator
                parameter is not ``None``.
        """
        pass

    @abstractmethod
    def shutdown_plugin(self) -> None:
        """
        A function that will be called by pntOS when it is done using the plugin.

        Here the plugin should release any resources it has acquired. When this function call
        returns pntOS may only call the destructor function (it will not call any other functions of
        this plugin). The plugin may not call any function on any other plugin, mediator, or use any
        resource that was given to it by pntOS after it returns from this function.
        """
        pass

    identifier: str
    """ A string identifier uniquely identifying this plugin.

    This string will be used to determine the unique space this plugin receives in the system
    config.
    """
