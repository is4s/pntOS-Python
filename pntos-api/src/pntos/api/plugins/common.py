"""Python API of pntOS."""

from dataclasses import dataclass
from enum import Enum
from typing import Callable, List, Protocol, TypeVar

from aspn23 import AspnBase, TypeTimestamp
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
            from a :class:`TransportPlugin` and the underlying transport has the concept of a
            channel or topic, this field should be populated by the channel or topic. Otherwise, the
            identifier is populated in a plugin-specific manner by the originating plugin that
            created the message.
    """

    wrapped_message: AspnBase
    source_identifier: str


class EstimateWithCovarianceType(Enum):
    """Describes how the fields in :class:`EstimateWithCovariance` are used."""

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
        estimate (NDArray): An array of doubles representing an estimate vector. Usage depends on
            the ``type`` field.
        covariance (NDArray): An array of doubles representing a square covariance matrix. Data is
            stored in row major form. Usage depends on the ``type`` field.
    """

    type: EstimateWithCovarianceType
    estimate: NDArray
    covariance: NDArray


class FusionType(Enum):
    """
    An enumeration of the types of fusion that can be performed by pntOS.

    An implementation of a :class:`FusionPlugin` will compare a model from this enum in its
    :meth:`~FusionPlugin.is_fusion_type_supported` function. The return of
    :meth:`~FusionPlugin.is_fusion_type_supported` indicates whether the input type of fusion engine
    matches the type that will be produced by :meth:`~FusionPlugin.new_fusion_engine`.

    Example:
        Suppose we have a variable :class:`FusionPlugin` named ``plugin``. Then if the return value
        of ``plugin.is_fusion_type_supported(FusionType.STANDARD_MODEL)`` is ``True``, then that
        means that ``plugin.new_fusion_engine()`` will return a :class:`StandardFusionEngine`.
    """

    STANDARD_MODEL = 0
    """
    The standard model of fusion within pntOS. This model assumes that state estimates are
    representable in a jointly Gaussian state vector and that updates of the state vector contain
    only independent and identically distributed (i.i.d.) additive white Gaussian noise. See
    :class:`StandardFusionEngine` for more information.
    """

    SAMPLED_MODEL = 1
    """
    The sampled model of fusion within pntOS. This model assumes that state
    estimates are represented by discrete stochastic sample points of a 
    probability density function (i.e. particles) and that propagate/update
    functions will receive these samples and be able to arbitrarily modify 
    each particle's weight, location, and add arbitrary noise to them.

    Caution: 
        **Unstable**: This feature is unstable and is not yet considered part of the stable pntOS
        API. Usage of this feature is highly discouraged in non-experimental code, and its
        definition may change at any time.
    """

    TIME_DELAYED_MODEL = 2
    """
    The time delayed model of fusion within pntOS. This model assumes that 
    information about a state is retained across different time epochs and 
    that historical estimate data is available for processing current time 
    data.

    Caution: 
        **Unstable**: This feature is unstable and is not yet considered part of the stable pntOS
        API. Usage of this feature is highly discouraged in non-experimental code, and its
        definition may change at any time.
    """

    STANDARD_COMPILED_MODEL = 3
    """
    The standard model of fusion within pntOS, in compiled format. This 
    model is identical to the standard model, with the exception that model
    information is not available in function pointers on the machine itself
    but instead binary blobs which have been pre-compiled. This mode is 
    intended to facilitate usage in environments such as GPGPU filter 
    implementations.

    Caution: 
        **Unstable**: This feature is unstable and is not yet considered part of the stable pntOS
        API. Usage of this feature is highly discouraged in non-experimental code, and its
        definition may change at any time.
    """


class LoggingLevel(Enum):
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

    An enum that specifies the format of data returned/expected in the :meth:`KeyValueStore.get_raw`
    and :meth:`KeyValueStore.set_raw` methods. This value is otherwise unused when querying a
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


RegistryValueTypes = TypeVar(
    "RegistryValueTypes", str, List[str], int, bool, float, NDArray, Message
)


class KeyValueStore(Protocol):
    """
    A key-value store implemented with a string-pair key.

    Each value can be looked up by an associated key (string). Values can be a variety
    of different types, depending on which type identifier is specified.

    Example:
        For example, to store a string value "foo" in the key-value store under the key "k1", one
        would write::

            store.set_value("k1", "foo")

        At this point, the key-value store would have recorded the value into its
        internal data storage. Later a user could call::

            store.get_value("k1", str)

        to retrieve the value from the store as a string.

    In general, a :class:`KeyValueStore` is generated by a :class:`Registry` and not directly by
    other code. The :class:`Registry` will return key/value stores on demand, utilizing the data
    backing store chosen by the plugin to store data (either ephemerally in memory or permanently in
    persistent storage). In general, it is only valid to call the getters/setters on a
    :class:`KeyValueStore` during a batch operation. See :class:`Registry` for more information.

    Attributes:
        data_format (KeyValueStoreDataFormat): The data format that is used by the :meth:`set_raw`
            and :meth:`get_raw` methods.
    """

    def get_key_array(self) -> List[str]:
        """
        Get the array of keys which currently exist in this store.

        Returns:
            List[str]: Returns ``None`` if no keys are available.
        """
        pass

    def has_key(self, key: str) -> bool:
        """
        Check whether or not a given key exists in the store.

        Args:
            key (str)

        Returns:
            bool
        """
        pass

    def get_value(
        self, key: str, type: type[RegistryValueTypes]
    ) -> RegistryValueTypes | None:
        """
        Get the value stored at ``key`` with return type ``type``.

        Example:
            For example, to access altitude in a :class:`KeyValueStore` named ``kv_store`` as an
            integer::

                altitude = kv_store.get_value("altitude", int)

        Args:
            key (str)
            type (type[RegistryValueTypes])

        Returns:
            RegistryValueTypes | None: Returns ``None`` if the key is not available. The return is
            guaranteed to not be ``None`` if called with a valid key, which can be checked with
            :meth:`has_key`.
        """
        pass

    def get_raw(self, key: str | None = None) -> bytes | None:
        """
        Get the value for the given ``key`` as an array of bytes.

        Args:
            key (str | None, optional)

        Returns:
            bytes | None: The return format will conform to the definition in
            :attr:`KeyValueStore.data_format`. Returns ``None`` if the given key is not available.
            The return is guaranteed to not be ``None`` if called with a valid key, which can be
            checked with :meth:`has_key`. If ``key`` is ``None``, then this function will return all
            of the keys and values in the group passed to :meth:`Registry.batch_start` and will be
            formatted to conform to keys and values as defined in :attr:`KeyValueStore.data_format`.
        """
        pass

    def set_value(self, key: str, value: RegistryValueTypes) -> None:
        """
        Set the given key to the provided value.

        Args:
            key (str)
            value (RegistryValueTypes): Can be of any type specified by :class:`ValueType`.
        """
        pass

    def set_raw(self, key: str | None, bytes: bytes) -> None:
        """
        Set the given key to the provided value.

        Args:
            key (str | None): If ``key`` is ``None``, then the contents of ``bytes`` must include
                both keys and values and must be formatted to conform to
                :attr:`KeyValueStore.data_format`. ``bytes`` will then be used to set the
                corresponding keys and values in the group passed to :meth:`Registry.batch_start`.
            bytes (bytes): Must be formatted to conform to the definition of a value in
                :attr:`KeyValueStore.data_format`.
        """
        pass

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

    def batch_end(self) -> None:
        """
        Ends a batch operation.

        Ends a batch operation started with a :meth:`Registry.batch_start` call. After calling this,
        the user should not use the :class:`KeyValueStore` they received from
        :meth:`Registry.batch_start` again without calling :meth:`batch_restart` on the
        :class:`KeyValueStore`.

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

    def batch_restart(self) -> None:
        """
        Restarts a batch.

        Restarts a batch that was previously started with :meth:`Registry.batch_start` and
        subsequently ended with :meth:`batch_end`. This method is likely much more efficient than
        :meth:`Registry.batch_start` (depending on the registry implementation) as the
        :meth:`Registry.batch_start` method must find the store again given the group name.

        Note:
            While a batch is active, access to the store may be denied to other users. Thus a user
            should endeavour to call :meth:`batch_end` as soon as possible after they are done
            getting/setting values in the returned :class:`KeyValueStore`.
        """
        pass

    def request_notify(
        self,
        key: str | None,
        callback: Callable[[str, List[str], "KeyValueStore"], None],
    ) -> bool:
        """
        Register a callback which gets called each time a key in the store is updated.

        Allows plugins to respond asynchronously to parameter updates. Returns ``True`` if the
        notifier was successfully registered, and ``False`` if the store is unable to notify the
        requester. If ``key`` is ``None``, then the callback will be invoked when any key in the
        batch's group is modified. Otherwise, the callback will only be invoked when the given key
        is modified.

        Note:
            The callback must not attempt to set any values inside the :class:`KeyValueStore`, as
            the callback is likely being invoked during the processing of another operation. The
            callback should endeavour to store off the updated keys/values as quickly as possible
            and return, leaving the processing of the updates to another context or thread when
            possible. Calling :class:`Mediator` within the callback may be disallowed by the
            controller implementation and lead to undefined behavior.

        Args:
            key (str | None)
            callback (Callable[[str, List[str], "KeyValueStore"], None])

        Returns:
            bool: ``True`` if the notifier was successfully registered, and ``False`` if the store
            is unable to notify the requester.
        """
        pass

    def remove_notify(
        self,
        key: str | None,
        callback: Callable[[str, List[str], "KeyValueStore"], None],
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
            callback (Callable[[str, List[str], "KeyValueStore"], None])

        Returns:
            bool: ``True`` if removal was successful and ``False`` if it was not. ``False`` will be
            returned if a callback did not exist for the group.
        """
        pass

    def set_permanent(self, permanent: bool) -> bool:
        """
        Tag values modified with "set" methods as permanently stored.

        Configure the :class:`KeyValueStore` to tag values modified with "set" methods as
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
            bool: The value of the permanent storage configuration. Callers should check this to
            verify if the set was successful.
        """
        pass

    data_format: KeyValueStoreDataFormat


class Registry(Protocol):
    """
    A registry of key/value data which is organized by (string) groups.

    In order to get/set a key in the registry, one must call :meth:`Registry.batch_start` with the
    group the key is stored under and then use the resulting :class:`KeyValueStore` to get/set the
    key/value pair. When one is done accessing keys in the :class:`KeyValueStore`, they must call
    :meth:`KeyValueStore.batch_end`. It is not permitted to access any member inside the
    :class:`KeyValueStore` after a batch has ended. If a user has ended a batch and then desires to
    access the :class:`KeyValueStore` again, they may use the :meth:`KeyValueStore.batch_restart`
    method.
    """

    def batch_start(self, group: str) -> KeyValueStore:
        """
        Begin a batch get/set operation.

        Begin a batch get/set operation wherein the user may make any number of modifications to the
        keys/values in the ``group``. The registry implementation may wait to batch these requests
        until :meth:`KeyValueStore.batch_end` is called for better performance. For example, a lock
        may be obtained at the beginning of a :meth:`batch_start` and not released until a
        :meth:`KeyValueStore.batch_end` call is encountered. Thus, a plugin that calls
        :meth:`batch_start` should endeavour to make its calls to the ``set_``, ``get_``, and
        ``register`` methods as quickly as possible and call :meth:`KeyValueStore.batch_end`
        immediately, as doing otherwise may be locking other plugins out of access to the registry
        (depending on the registry plugin implementation). If a plugin supports
        :meth:`KeyValueStore.request_notify`, then notifications of updates may be suspended until
        the batch ends. After a batch is ended, the returned :class:`KeyValueStore` can still be
        used to access the store via :meth:`KeyValueStore.batch_restart`.

        Note:
            While a batch is active, access to the store may be denied to other users. Thus a user
            should endeavour to call :meth:`KeyValueStore.batch_end` as soon as possible after they
            are done getting/setting values in the returned :meth:`KeyValueStore`.

        Args:
            group (str)

        Returns:
            KeyValueStore
        """
        pass

    def get_group_array(self) -> List[str]:
        """
        Get the array of groups which currently exist.

        Returns:
            List[str]: The array of groups which currently exists. Returns ``None`` if no groups
            exist.
        """
        pass

    def has_group(self, group: str) -> bool:
        """
        Checks whether or not a given group has had any values added to it (for any key).

        Args:
            group (str)

        Returns:
            bool
        """
        pass

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


class Mediator(Protocol):
    """
    A set of callbacks which are handed to a pntOS plugin upon initialization.

    When a plugin is first initialized into pntOS, it is guaranteed that the plugin will be passed
    an instance of this struct via an invocation of :meth:`CommonPlugin.init_plugin` (See
    :class:`CommonPlugin` for more information). The plugin may then use the set of function calls
    in this class to make requests of the :class:`ControllerPlugin`.

    All of the functions on this class (and any returned values from those functions) are guaranteed
    to be thread-safe for use by all plugins. Thus, after a pntOS plugin has received a copy of a
    :class:`Mediator` it can freely call the functions contained therein without doing any explicit
    locking. This thread safety is implemented by the :class:`ControllerPlugin` when it creates the
    mediator before passing them to other plugins.

    Callers must still take care to only call functions in :class:`Mediator` which they are not
    themselves responsible for implementing. The details of which plugins are used in the
    implementation of any particular function on this struct is decided by the
    :class:`ControllerPlugin`, and thus is implementation specific to the :class:`ControllerPlugin`
    used.

    Attributes:
        registry (Registry): A :class:`Registry` object that can be used to update keys/values in
            the pntOS global registry.
    """

    def get_filter_description_list(self) -> List[str]:
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
            List[str]: A list of strings describing the solutions available.
        """
        pass

    def request_solutions(
        self,
        solution_times: List[TypeTimestamp],
        filter_description: str | None = None,
    ) -> List[Message]:
        """
        Request filtering solutions at the times specified in the array ``solution_times``.

        Args:
            solution_times (List[TypeTimestamp]): The number of time entries in ``solution_times``
                is specified by ``num_solution_times``.
            filter_description (str | None, optional): To select which filter(s) to request
                solutions from, enter a valid filter description string in ``filter_description``.
                Valid filter description strings can be obtained by calling
                :meth:`get_filter_description_list`. Passing in ``None`` will provide a result
                specific to a particular implementation. When ``filter_description`` is ``None``,
                the implementation should endeavor to return its best solution.

        Returns:
            List[Message]: An array of messages containing the filter solutions for the requested
            ``solution_times``. The number of solutions should equal ``num_solution_times``,
            although some entries may be ``None`` if they are unavailable at the corresponding time
            in ``solution_times``. The returned :class:`Message` array may be ``None`` if
            ``filter_description`` is invalid.
        """
        pass

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
                :attr:`CommonPlugin.identifier` string of a :class:`TransportPlugin` active in the
                system. If the transport parameter is ``None``, this indicates that the message
                should be broadcast to all available transports.
            destination_identifier (str | None, optional): A transport-specific identifier that
                allows transports to determine how to route the message. If the destination
                transport has the concept of a channel or topic, ``destination_identifier`` should
                be populated by the channel or topic. Otherwise, the identifier is populated in a
                plugin-specific manner defined by the destination transport. If
                ``destination_identifier`` is ``None``, then the transport should output the message
                in the "default" output channel/topic and route being used by pntOS.
        """
        pass

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


class CommonPlugin(Protocol):
    """
    Common definitions that all plugins must provide.

    This structure should not be used directly (except in the case of a utility plugin), but instead
    is composed as the first field on all of the concrete pntOS plugin structures. For example, the
    transport plugin is specified as::

        class TransportPlugin(CommonPlugin, Protocol):

            def init_plugin(...):
                ...init_plugin implementation...

            def ...other function implementations...


    Thus this class defines a set of functions and variables that all plugins have. The
    :meth:`CommonPlugin.init_plugin` function is guaranteed to be called by pntOS when the plugin is
    first loaded into memory by the system.

    Example:
        When defining a new transport plugin, the plugin writer is responsible for implementing all
        fields on the :class:`TransportPlugin` class. Thus, the fields of the :class:`CommonPlugin`
        nested on the :class:`TransportPlugin` are implemented by the plugin writer.

    Attributes:
        identifier (str): A string identifier uniquely identifying this plugin. This string will be
            used to determine the unique space this plugin receives in the system config.
    """

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
        instance of :class:`Mediator` will be passed which the plugin should save off for later use.
        Whenever the plugin needs to make a request of pntOS, it should use one of the fields in the
        :class:`Mediator` instance received by the plugin in this function call.

        Note:
            Implementation note: This inversion of control allows the controller to implement the
            :class:`Mediator` class, and abstracts away the return communication channel from the
            plugin to the rest of the system. Thus, the plugin need only implement :class:`Mediator`
            by simply saving a copy of the functions that the controller passes into it. Then, when
            the plugin later needs to make requests of the system, it may call a function in its
            copy of :class:`Mediator`, without needing any knowledge of how the controller
            implemented :class:`Mediator`. This allows controllers to implement arbitrary
            concurrency models, including single-threaded, multi-threaded, multi-process, and
            distributed computing.

        Args:
            plugin_resources_location (str | None, optional): Specifies the location of the plugin's
                resources.  The location is determined by the controller plugin, and therefore is
                controller implementation specific. Plugin implementers wishing to provide a
                resource to their plugin should consult the documentation of the controller to
                determine which location scheme will be passed into this function.
            mediator (Mediator | None, optional): ``None``-able if the plugin type being initialized
                is a :class:`ControllerPlugin`. Non-controller plugins may assume that the mediator
                parameter is not ``None``.
        """
        pass

    def shutdown_plugin(self) -> None:
        """
        A function that will be called by pntOS when it is done using the plugin.

        Here the plugin should release any resources it has acquired (including the
        :class:`Mediator` if it kept a reference to that when :meth:`init_plugin` was called). When
        this function call returns pntOS may only call the destructor function (it will not call any
        other functions of this plugin). The plugin may not call any function on any other plugin,
        mediator, or use any resource that was given to it by pntOS after it returns from this
        function.
        """
        pass

    identifier: str
