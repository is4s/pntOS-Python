from dataclasses import dataclass
from enum import Enum
from typing import Callable, List, Optional, Protocol, TypeVar

from aspn23.aspn_base import AspnBase
from aspn23.type_timestamp import TypeTimestamp
from numpy import float64
from numpy.typing import NDArray


@dataclass
class Message:
    """
    A container for an ASPN message. This container may contain either proper
    ASPN messages which are part of the ASPN data model, or extension messages
    specific to pntOS which augment ASPN. For messages of the former type, the
    wrapped message's `message_type` field should be used directly. For
    message of the latter type, cast the wrapped message's message_type field
    to `MessageType`.
    """

    wrapped_message: AspnBase
    """
    Either an ASPN message or a pntOS ASPN Extension message, depending on the 
    value of `wrapped_message.message_type`.
    """

    source_identifier: str
    """
    Indicates where this message came from. If the message originated from a 
    transport plugin and the underlying transport has the concept of a channel 
    or topic, this field should be populated by the channel or topic. 
    Otherwise, the identifier is populated in a plugin-specific manner by the
    originating plugin that created the message.
    """


class EstimateWithCovarianceType(Enum):
    """
    Describes how the fields in `EstimateWithCovariance` are used.
    """

    EWC_GENERIC = 0
    """
    Contains a mean (estimate) and covariance describing a multivariate
    Gaussian distribution.
    * `EstimateWithCovariance.estimate` is size Nx1 where N is the length 
      field.
    * `EstimateWithCovariance.covariance` is size NxN where N is the length 
      field.
    """

    EWC_ATTITUDE_QUAT = 1
    """
    Contains a mean (estimate) and covariance describing a rotation modeled
    by a multivariate Gaussian distribution, but the estimate is in quaternion 
    form and the covariance is in tilt error form.
    * `EstimateWithCovariance.estimate` is size 4x1
    * `EstimateWithCovariance.covariance` is size 3x3, in radians^2.
    """


@dataclass
class EstimateWithCovariance:
    """
    A container for holding an estimate and covariance.
    """

    type: EstimateWithCovarianceType
    """ 
    Describes how the fields in this struct are used. 
    """

    estimate: NDArray[float64]
    """ 
    An array of doubles representing an estimate vector. Usage depends on the 
    `type` field.
    """

    covariance: NDArray[float64]
    """
    An array of doubles representing a square covariance matrix. Data is 
    stored in row major form. Usage depends on the `type` field.
    """


class PluginTypes(Enum):
    """
    An enumeration of the types of plugins supported by pntOS for this loader
    API version. Each enum entry maps to a corresponding structure with
    PascalCase naming. For example, the `CONTROLLER_PLUGIN` value in this
    enum is indicating a plugin represented by the struct
    `ControllerPlugin`. Note that because the utility plugin has no
    additional API requirements beyond the `CommonPlugin`, there is not a
    `UtilityPlugin`. Instead, implementers of `UTILITY_PLUGIN` should implement
    and return a `CommonPlugin`.
    """

    UNDEFINED_PLUGIN = 0
    """ 
    An unused entry, designed to allow code to detect accidentally unset 
    fields. This value must not be used by any plugin implementation, 
    other than to check for an erroneous default value being used.
    """

    CONTROLLER_PLUGIN = 1
    """
    The primary plugin that controls the entire operation of pntOS. After 
    the pntOS loader collects the set of plugins available, execution 
    passes to the controller plugin. At that point, the controller is 
    responsible for deciding how it should use, when it should use, and if 
    it should use the other plugins, including routing communications 
    between them and controlling the concurrency model used.

    The controller plugin is designed to work together with the platform 
    integration plugin (PIP) to control overall behavior of the system. In 
    particular, the controller consists of re-useable logic that is not 
    specific to a particular solution, whereas the PIP consists of 
    platform-specific logic. The primary job of the controller plugin is to
    place each plugin into a concurrency primitive (thread, process, etc.) 
    and then manage the communications between those plugins via the 
    mediator the controller provides. The controller may also configure a 
    single threaded approach if desired.

    Any logic which is specific to a particular solution, platform, or 
    vehicle should be placed in the platform integration plugin instead of 
    the controller. After the controller is done initially setting up the 
    concurrency model, it should hand control to the PIP, to handle command
    and control of the plugins outside the scope of inter-plugin 
    communications and message routing between plugins.  
    """

    PLUGIN = 2
    """
    A plugin that models an information fusion approach. This plugin 
    accepts modular representations of state space models, sensor 
    descriptions, raw measurements, and computational filtering engines, 
    all provided by external sources. It then performs the bookkeeping 
    needed to hook these modules up to each other in a extensible and 
    flexible way. State space models and sensor descriptions are provided 
    by state modeling plugins, raw measurements are provided by transport 
    plugins, and filtering engines are provided by fusion strategy plugins.
    """

    STRATEGY_PLUGIN = 3
    """
    A low level computational engine that can perform sensor fusion given 
    pre-determined fixed models of errors and raw measurements. Because 
    this plugin requires fixed models, another plugin is required to 
    orchestrate modular descriptions of the fusion problem into a 
    fixed-size problem. The fusion plugin is used to orchestrate modular 
    descriptions into a fixed-size problem suitable for the computational 
    engine in this plugin to consume.
    """

    PLATFORM_INTEGRATION_PLUGIN = 4
    """
    An output plugin for pntOS to interact with the platform it is running 
    on. While pntOS uses a uniform set of conventions internally (e.g. ASPN
    messages), pntOS is often used on legacy platforms that are 
    non-cooperative and impose requirements on the input/output expected of
    pntOS. For example, analog time outputs or PVA messages at a certain 
    rate and non-ASPN format might be required by a vehicle that pntOS is 
    running on. The platform integration plugin converts pntOS internal 
    messages into whatever external outputs may be needed on the current 
    platform. It is designed to be the piece of NRE that must be rewritten 
    when using pntOS on a novel platform.

    **UNSTABLE**: This feature is unstable and is not yet considered part 
    of the stable pntOS API. Usage of this feature is highly discouraged in
    non-experimental code, and its definition may change at any time.
    """

    INITIALIZATION_PLUGIN = 5
    """
    A plugin that provides initialization algorithms. In general, this 
    plugin must be able to consume some set of measurements and produce an 
    initial solution for the navigation system. This plugin encompasses 
    everything from a traditional gyrocompass to a cold-start dynamic
    positioning.
    
    **UNSTABLE**: This feature is unstable and is not yet considered part 
    of the stable pntOS API. Usage of this feature is highly discouraged in
    non-experimental code, and its definition may change at any time.
    """

    DATABASE_PLUGIN = 6
    """
    A plugin for storing generic datasets that might be consumed by many 
    plugins. For example, DTED elevation data may be used by many different
    plugins. Thus, a user might write a database plugin that encapsulated 
    tiles of elevation data which is available for query by any other 
    plugin.
    
    **UNSTABLE**: This feature is unstable and is not yet considered part 
    of the stable pntOS API. Usage of this feature is highly discouraged in
    non-experimental code, and its definition may change at any time.
    """

    TRANSPORT_PLUGIN = 7
    """
    A plugin that listens for incoming sensor/other data on a network bus 
    and provides this data to pntOS. pntOS has an internally consistent 
    messaging structure which may not match the messages transmitted over 
    the wire to pntOS. Thus, one of the transport plugin's primary roles is
    to convert arbitrarily formatted data off the wire into the internal 
    pntOS ASPN representation. For network buses that already transmit ASPN
    data, the transport plugin may end up being a trivial plugin, simply 
    marshalling data off of a network connection into the system.
    """

    UI_PLUGIN = 8
    """
    A plugin for enabling user interfaces to be hooked up to pntOS. This 
    plugin is designed to enable displays to users to both see the current 
    state of pntOS and also configure/tweak it. Note that it is *not* 
    designed for hooking up operational displays, but rather debugging / 
    developer consoles. For outputs that will be sent to operational live 
    displays on the platform, the platform integration plugin is preferred.
    """

    ORCHESTRATION_PLUGIN = 9
    """
    A plugin that implements the orchestration monitoring framework. In 
    general, complementary navigation techniques incur a large risk of 
    solution corruption if any one of the new sensors is misconfigured, 
    mismodeled, miscalibrated, or otherwise failing. The orchestration 
    plugin monitors all sensors in the system and generates different 
    orchestration solutions depending on the user's risk tolerance. Because
    there is a huge variety of orchestration approaches, the orchestration 
    plugin is further modularized into orchestration strategy plugins, 
    which implement a particular orchestration approach for a particular 
    sensor or situation.
    """

    ORCHESTRATION_STRATEGY_PLUGIN = 10
    """
    A fine-grained integrity plugin that itself plugins into the larger 
    orchestration plugin. This plugin is designed to be implementable by a 
    developer who is an expert on a particular sensor or phenomenology, 
    without being an expert in the entire orchestration framework used by 
    pntOS. A integrity algorithm specific to a single sensor or situation 
    may be implemented in this plugin, and then injected into the larger 
    orchestration which captures many orchestration strategy plugins for 
    different sensors.

    **UNSTABLE**: This feature is unstable and is not yet considered part 
    of the stable pntOS API. Usage of this feature is highly discouraged in
    non-experimental code, and its definition may change at any time.
    """

    REGISTRY_PLUGIN = 11
    """
    A registry of configuration and status data for pntOS that is available
    to all plugins. Registries allow for plugins to have side-channel 
    information shared between plugins without pntOS being pre-aware of the
    data that needs to be transmitted. For example, a support plugin 
    modeling a vision nav sensor has computed a camera calibration matrix. 
    Simultaneously, a UI plugin would like to show the current calibration 
    matrix to the user, and allow that user to modify the current matrix if
    the user desires. Because the vision nav sensor ordinarily would be 
    modeled by a state modeling plugin and the user-facing UI implemented 
    by a UI plugin, these two plugins would have no way to communicate 
    current/updated values of this matrix. Via the registry, these plugins 
    can decide by convention on a key-value that store the calibration 
    matrix and enable high-speed bi-directional communications of the value 
    of the calibration matrix in a thread-safe way.
    
    The registry supports value observers for listeners to be notified when
    values are changed, monitoring/logging of when values are changed and 
    by what source, and access control lists to guard certain keys.
    """

    INERTIAL_PLUGIN = 12
    """
    A plugin that generates PVA solutions from an inertial.

    **UNSTABLE**: This feature is unstable and is not yet considered part 
    of the stable pntOS API. Usage of this feature is highly discouraged in
    non-experimental code, and its definition may change at any time.
    """

    STATE_MODELING_PLUGIN = 13
    """
    A plugin that models the errors of the various sensors and systems that
    measuring the world. Abstractly, a state modeling plugin includes 
    modular representations of (a) state space models (including nuisance 
    parameters) and (b) state model providers and how measurements are 
    related to the states in the state space. Due to there being several 
    mathematical models of varying fidelity to describe sensors, each state
    modeling plugin must declare what model it is using to represent sensor
    errors. For the standard model, each state modeling plugin is a bundle 
    of zero or more state blocks, zero or more measurement processors, and 
    zero or more virtual state blocks.
    """

    LOGGING_PLUGIN = 14
    """
    A plugin that logs system events to an arbitrary sink. A sink may be a 
    file, a console, an attached GUI, a network destination, or any other 
    destination of interest.
    """

    UTILITY_PLUGIN = 15
    """
    A plugin that performs a generic utility function. A utility plugin 
    performs functions that may require access to pntOS resources (such as 
    the registry) but is not otherwise relied upon to perform any 
    particular function.
    """

    PREPROCESSOR_PLUGIN = 16
    """
    A plugin that processes data received from a transport before it is 
    sent onward into other pntOS plugins. Intended use cases include:
    * fixing erroneous messages that do not conform to the ASPN data model,
    due to e.g. hardware malfunction
    * preprocessing ASPN measurements of one type into one or more 
    alternative ASPN measurements, to make them suitable for processing by 
    currently available measurement processors. For example, a raw image 
    might be delivered to pntOS, and then converted into features such that
    a feature-processing measurement processor could utilize it.

    **UNSTABLE**: This feature is unstable and is not yet considered part 
    of the stable pntOS API. Usage of this feature is highly discouraged in
    non-experimental code, and its definition may change at any time.
    """


class FusionType(Enum):
    """
    An enumeration of the types of fusion that can be performed by pntOS. An
    implementation of a `FusionPlugin` plugin will compare a model from this
    enum in its `FusionPlugin.is_fusion_type_supported` function. The return of
    `FusionPlugin.is_fusion_type_supported` indicates whether the input type of
    fusion engine matches the type that will be produced by
    `FusionPlugin.new_fusion_engine`.

    For example, suppose we have a variable `FusionPlugin* plugin`. Then if the
    return value of `plugin->is_fusion_type_supported(plugin,
    STANDARD_MODEL)` is true, then that means that
    `plugin->new_fusion_engine(plugin)` will return a `StandardFusionEngine*`.
    """

    STANDARD_MODEL = 0
    """
    The standard model of fusion within pntOS. This model assumes that 
    state estimates are representable in a jointly Gaussian state vector 
    and that updates of the state vector contain only i.i.d. additive white
    Gaussian noise. See `StandardFusionEngine` for more information.
    """

    SAMPLED_MODEL = 1
    """
    The sampled model of fusion within pntOS. This model assumes that state
    estimates are represented by discrete stochastic sample points of a 
    probability density function (i.e. particles) and that propagate/update
    functions will receive these samples and be able to arbitrarily modify 
    each particle's weight, location, and add arbitrary noise to them.

    **UNSTABLE**: This feature is unstable and is not yet considered part 
    of the stable pntOS API. Usage of this feature is highly discouraged in
    non-experimental code, and its definition may change at any time.
    """

    TIME_DELAYED_MODEL = 2
    """
    The time delayed model of fusion within pntOS. This model assumes that 
    information about a state is retained across different time epochs and 
    that historical estimate data is available for processing current time 
    data.

    **UNSTABLE**: This feature is unstable and is not yet considered part 
    of the stable pntOS API. Usage of this feature is highly discouraged in
    non-experimental code, and its definition may change at any time.
    """

    STANDARD_COMPILED_MODEL = 3
    """
    The standard model of fusion within pntOS, in compiled format. This 
    model is identical to the standard model, with the exception that model
    information is not available in function pointers on the machine itself
    but instead binary blobs which have been pre-compiled. This mode is 
    intended to facilitate usage in environments such as GPGPU filter 
    implementations.

    **UNSTABLE**: This feature is unstable and is not yet considered part 
    of the stable pntOS API. Usage of this feature is highly discouraged in
    non-experimental code, and its definition may change at any time.
    """


class LoggingLevel(Enum):
    """
    An enumeration of the types of log outs that are available in pntOS.
    """

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
    An enum that specifies the format of data returned/expected in the
    `KeyValueStore.get_raw` and `KeyValueStore.set_raw` methods.
    This value is otherwise unused when querying a key-value store.
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
    "RegistryValueTypes", str, List[str], int, bool, float, NDArray[float64], Message
)


class KeyValueStore(Protocol):
    """
    A key-value store implemented with a string-pair key. Each value can be
    looked up by an associated key (string). Values can be a variety of
    different types, depending on which type identifier is specified. For
    example, to store a string value "foo" in the key-value store under the key
    "k1", one would write:

    ```
    store.set_value("k1", "foo");
    ```

    At this point, the key-value store would have recorded the value into its
    internal data storage. Later a user could call

    ```
    store.get_value("k1", str);
    ```

    To retrieve the value from the store as a string.

    In general, a `KeyValueStore` is generated by a `Registry` and not directly
    by other code. The `Registry` will return key/value stores on demand,
    utilizing the data backing store chosen by the plugin to store data (either
    ephemerally in memory or permanently in persistent storage). In general, it
    is only valid to call the getters/setters on a `KeyValueStore` during a
    batch operation. See `Registry` for more information.
    """

    def get_key_array(self) -> List[str]:
        """
        Get the array of keys which currently exist in this store. Returns None
        if no keys are available.
        """
        pass

    def has_key(self, key: str) -> bool:
        """
        Returns whether or not a given key exists in the store.
        """
        pass

    def get_value(
        self, key: str, type: type[RegistryValueTypes]
    ) -> RegistryValueTypes | None:
        """
        Get the value stored at `key` with return type `type`.

        For example, to access altitude in KeyValueStore `kv_store` as an
        integer:

        ```
        altitude = kv_store.get_value("altitude", int)
        ```

        Returns None if the key is not available. The return is guaranteed to
        not be None if called with a valid key, which can be checked with
        `has_key()`.
        """
        pass

    def get_raw(self, key: Optional[str]) -> Optional[bytes]:
        """
        Get the value for the given key as an array of bytes. The return format
        will conform to the definition in `data_format`. Returns None if the
        given key is not available. The return is guaranteed to not be None if
        called with a valid key, which can be checked with `has_key`.

        If `key` is None, then this function will return all of the keys and
        values in the group passed to `Registry.batch_start()` and will be
        formatted to conform to keys and values as defined in `data_format`.
        """
        pass

    def set_value(self, key: str, value: RegistryValueTypes) -> None:
        """
        Set the given key to the provided value. `value` can be of any type
        specified by `ValueType`
        """
        pass

    def set_raw(self, key: Optional[str], bytes: bytes) -> None:
        """
        Set the given key to the provided value. `bytes` must be formatted to
        conform to the definition of a value in `data_format`.

        If `key` is None, then the contents of `bytes` must include both keys
        and values and must be formatted to conform to `data_format`. `bytes`
        will then be used to set the corresponding keys and values in the group
        passed to `Registry.batch_start`.
        """
        pass

    def remove_key(self, key: str) -> bool:
        """
        Remove the given key from the registry. Returns true if `key` is
        successfully removed, and false otherwise. Keys may fail to be removed
        if the key does not currently exist, or the backend is unable to remove
        the key.
        """
        pass

    def batch_end(self) -> None:
        """
        Ends a batch operation started with a `Registry.batch_start` call.
        After calling this, the user should not use the `KeyValueStore` they
        received from `Registry.batch_start()` again without calling
        `batch_restart` on the `KeyValueStore`.

        If keys in the batch were acted upon with `set_permanent` turned on,
        and the plugin supports permanent storage, this call will save changes
        to permanent storage if set_permanent is true during the call to
        `batch_end`. Enacts equivalent of `set_permanent(self,false)` before
        return. If any request_notify observers have been added, they will be
        processed prior to this call returning.

        EXAMPLE 1: Flushing to permanent storage on `batch_end`

        ```
            store = registry.batch_start("group")
            ...work...
            store.set_permanent(true) # if not disabled, flush on batch_end
            ...work...
            store.batch_end()    # will flush values
        ```

        EXAMPLE 2: Not flushing to permanent storage on `batch_end`

        ```
            store = registry.batch_start("group")
            ...work...
            store.set_permanent(true)  # tag some values
            ...work...
            store.set_permanent(false) # do not flush on batch_nd
            store.batch_end()          # will not flush values
        ```

        In the second example above, values set with "set" methods after the
        initial `set_permanent` call are still stored for potential saving to
        permanent storage.
        """
        pass

    def batch_restart(self) -> None:
        """
        Restarts a batch that was previously started with
        `Registry.batch_start` and subsequently ended with `batch_end`. This
        method is likely much more efficient than 'Registry.batch_start'
        (depending on the registry implementation) as the
        `Registry.batch_start` method must find the store again given the group
        name.

        NOTE: While a batch is active, access to the store may be denied to
        other users. Thus a user should endeavour to call `batch_end` as soon
        as possible after they are done getting/setting values in the returned
        KeyValueStore.
        """
        pass

    def request_notify(
        self,
        key: Optional[str],
        callback: Callable[[str, List[str], "KeyValueStore"], None],
    ) -> bool:
        """
        Register a callback which gets called each time a key in the store is
        updated. Allows plugins to respond asynchronously to parameter updates.
        Returns true if the notifier was successfully registered, and false if
        the store is unable to notify the requester. If key is None, then the
        callback will be invoked when any key in the batch's group is modified.
        Otherwise, the callback will only be invoked when the given key is
        modified. The receiver argument, if non-None, will be passed through to
        the callback's receiver parameter when the callback is invoked. The
        receiver argument is designed to allow the caller of `request_notify`
        to pass a context object through, such that the same context object is
        available when the callback is run.

        NOTE: The callback must not attempt to set any values inside the
        KeyValueStore, as the callback is likely being invoked during the
        processing of another operation. The callback should endeavour to store
        off the updated keys/values as quickly as possible and return, leaving
        the processing of the updates to another context or thread when
        possible. Calling `Mediator` within the callback may be disallowed by
        the controller implementation and lead to undefined behavior.

        NOTE: This method will retain the receiver beyond the lifetime of the
        function call, as the purpose of that parameter is to pass it back
        later in the callback. However, the `KeyValueStore` will never
        dereference the pointer, and thus it is safe to pass in a receiver that
        does not survive longer than the lifetime of the function call, as long
        as the callback checks for validity of the receiver before using it.
        """
        pass

    def remove_notify(
        self,
        key: Optional[str],
        callback: Callable[[str, List[str], "KeyValueStore"], None],
    ) -> bool:
        """
        Removes a notification as requested by `request_notify`. The group,
        receiver, and callback must match the parameters passed to
        `request_notify` in order to successfully remove a callback.

        NOTE: This will remove all matching callbacks that have a matching
        group, receiver, and callback. If a user registers the same callback
        twice this will remove both.

        Returns `true` if removal was successful and `false` if it was not.
        `false` will be returned if a callback did not exist for the
        group/receiver combination.
        """
        pass

    def set_permanent(self, permanent: bool) -> bool:
        """
        Configure the KeyValueStore to tag values modified with "set" methods
        as permanently stored (as opposed to ephemerally stored in memory).
        Only values acted upon with "set" methods while `set_permanent` is
        `true` will be tagged. Values will be flushed according to registry
        configuration settings or per `batch_end` API. Returns the value of the
        permanent storage configuration. Callers should check this to verify if
        the set was successful.

        EXAMPLE: Tagging specific keys to be permanently stored

        ```
        PntosKeyValueStore* store = registry.batch_start("group")
        store.set_value("key1",1234.56) # does not tag this value as permanently stored
        store.set_permanent(true)       # start tagging set* calls as permanently stored
        store.set_value("key1",987.65)
        store.set_value("key2",123)     # both key1 and key2 values tagged
        store.set_permanent(false)      # disable permanent storage
        store.set_value("key1",456.78)  # key1 = 456.78 is value of key1 in store
                                        # key1 = 987.65 tagged to be permanently stored
                                        # key2 = 123    tagged to be permanently stored
        ```
        """
        pass

    data_format: KeyValueStoreDataFormat
    """
    The data format that is used by the #set_raw and #get_raw methods.
    """


class Registry(Protocol):
    """
    A registry of key/value data which is organized by (string) groups. In
    order to get/set a key in the registry, one must call
    `Registry.batch_start` with the group the key is stored under and then use
    the resulting `KeyValueStore` to get/set the key/value pair. When one is
    done accessing keys in the `KeyValueStore`, they must call
    `KeyValueStore.batch_end`. It is not permitted to access any member inside
    the `KeyValueStore` after a batch has ended. If a user has ended a batch
    and then desires to access the `KeyValueStore` again, they may use the
    `KeyValueStore.batch_restart` method.
    """

    def batch_start(self, group: str) -> KeyValueStore:
        """
        Begin a batch get/set operation wherein the user may make any number of
        modifications to the keys/values in the `group`. The registry
        implementation may wait to batch these requests until `
        KeyValueStore.batch_end` is called for better performance. For example,
        a lock may be obtained at the beginning of a `batch_start` and not
        released until a `KeyValueStore.batch_end` call is encountered. Thus, a
        plugin that calls `batch_start` should endeavour to make its calls to
        the `set_`, `get_`, and `register` methods as quickly as possible and
        call `KeyValueStore.batch_end` immediately, as doing otherwise may be
        locking other plugins out of access to the registry (depending on the
        registry plugin implementation). If a plugin supports
        `KeyValueStore.request_notify`, then notifications of updates may be
        suspended until the batch ends. After a batch is ended, the returned
        `KeyValueStore` can still be used to access the store via
        `KeyValueStore.batch_restart`.

        NOTE: While a batch is active, access to the store may be denied to
        other users. Thus a user should endeavour to call
        `KeyValueStore.batch_end` as soon as possible after they are done
        getting/setting values in the returned `KeyValueStore`.
        """
        pass

    def get_group_array(self) -> List[str]:
        """
        Get the array of groups which currently exist. Returns None if no
        groups exist.
        """
        pass

    def has_group(self, group: str) -> bool:
        """
        Returns whether or not a given group has had any values added to it
        (for any key).
        """
        pass

    def request_notify_new_group(self, callback: Callable[[str], None]) -> bool:
        """
        Register a callback which gets called each time a new group is made in
        the registry. Returns true if the notifier was successfully registered,
        and false if the registry is unable to notify the requester. The
        callback will receive the same receiver as was passed into this method,
        which may be used as a context object.

        NOTE: This method will retain the receiver beyond the lifetime of the
        function call, as the purpose of that parameter is to pass it back
        later in the callback. However, the method will never dereference the
        receiver pointer, and thus it is safe to pass in a receiver that does
        not survive longer than the lifetime of the function call, as long as
        the callback checks for validity of the receiver before using it.
        """
        pass


class Mediator(Protocol):
    """
    A set of callbacks which are handed to a pntOS plugin upon initialization.

    When a plugin is first initialized into pntOS, it is guaranteed that the
    plugin will be passed an instance of this struct via an invocation of
    `CommonPlugin.init_plugin` (See `CommonPlugin` for more information).
    The plugin may then use the set of function calls in this class to make
    requests of the controller.

    All of the functions on this class (and any returned values from those
    functions) are guaranteed to be thread-safe for use by all plugins. Thus,
    after a pntOS plugin has received a copy of a `Mediator` it can freely call
    the functions contained therein without doing any explicit locking. This
    thread safety is implemented by the controller when it creates the mediator
    before passing them to other plugins.

    Callers must still take care to only call functions in `Mediator` which
    they are not themselves responsible for implementing. The details of which
    plugins are used in the implementation of any particular function on this
    struct is decided by the `ControllerPlugin`, and thus is implementation
    specific to the controller used.
    """

    def get_filter_description_list(self) -> List[str]:
        """
        Request a list of strings describing the solutions available. One of
        these description strings may be used when calling `request_solutions`.
        For consistency, these strings should adhere to the following
        conventions:

        - Strings should be upper case and have words and acronyms separated by
          underscores (`UPPER_SNAKE_CASE`).
        - Strings should contain the substring `BEST` when they represent the
          primary solution.
        - Strings should contain the substring `DEAD_RECKONING` when they
          represent a solution suitable for estimating relative motion or
          rotation over a period of time. This solution may drift more than
          `BEST` solutions, as the goal is to allow a user to get an estimate
          of the relative motion between different times. In the calculation of
          this solution, some sensor measurement might be excluded. For
          example, a system with an IMU might provide a `DEAD_RECKONING`
          solution which is the solution from its free-running inertial
          mechanization, with resets disabled during the time intervals between
          `solution_times` (but resets applied before all of the
          `solution_times`).
        - Strings should include a substring indicating the type of solution
          returned. This substring should contain the string-equivalent to the
          AspnMessageType enum value, followed by the string `_ESTIMATE`. This
          allows the user to perform substring matching without a risk of
          getting a false positive match from a type whose string would be a
          subset of another type.

        For example, if the primary solution is an ASPN PVA then the string
        `MY_BEST_ASPN_MEASUREMENT_POSITION_VELOCITY_ATTITUDE_ESTIMATE` would
        fulfill the convention.

        These conventions allow the user to identify their desired type of
        solution using substring matching.
        """
        pass

    def request_solutions(
        self, solution_times: List[TypeTimestamp], filter_description: Optional[str]
    ) -> List[Message]:
        """
        Request filtering solutions at the times specified in the array
        `solution_times`. The number of time entries in `solution_times` is
        specified by `num_solution_times`.

        To select which filter(s) to request solutions from, enter a valid
        filter description string in `filter_description`. Valid filter
        description strings can be obtained by calling
        `get_filter_description_list`. Passing in None will provide a result
        specific to a particular implementation. When `filter_description` is
        None, the implementation should endeavor to return its best solution.

        Returned will be an array of messages containing the filter solutions
        for the requested `solution_times`. The number of solutions should
        equal `num_solution_times`, although some entries may be None if they
        are unavailable at the corresponding time in `solution_times`. The
        returned `Message` array may be None if `filter_description` is
        invalid.
        """
        pass

    def process_pntos_message(self, message: Message) -> None:
        """
        Send a new message to the system for arbitrary processing. For example,
        this function is useful for plugins who have just received new sensor
        data that they wish to relay to the system to be used in a sensor
        fusion solution.
        """
        pass

    def broadcast_aspn_message(
        self,
        message: Message,
        transport: Optional[str],
        destination_identifier: Optional[str],
    ) -> None:
        """
        Request that pntOS broadcast the provided message out to the network.
        The `destination_identifier` parameter is a transport-specific
        identifier that allows transports to determine how to route the
        message. If the destination transport has the concept of a channel or
        topic, `destination_identifier` should be populated by the channel or
        topic. Otherwise, the identifier is populated in a plugin-specific
        manner defined by the destination transport. If
        `destination_identifier` is None, then the transport should output the
        message in the "default" output channel/topic and route being used by
        pntOS.

        The `transport` parameter is the identifier of a transport plugin that
        the message should be routed to. The transport parameter should match
        the `CommonPlugin.identifier` string of a `TransportPlugin` active in
        the system. If the transport parameter is None, this indicates that the
        message should be broadcast to all available transports.
        """
        pass

    def log_message(self, level: LoggingLevel, message: str) -> None:
        """
        Send a loggable message to the system, to be logged through the current
        logging infrastructure enabled (e.g. the console, a logfile, etc.).
        """
        pass

    registry: Registry
    """
    A pointer to a `Registry` object that can be used to update keys/values in 
    the pntOS global registry.
    """


class CommonPlugin(Protocol):
    """
    Common definitions that all plugins must provide. This structure should not
    be used directly (except in the case of a utility plugin), but instead is
    composed as the first field on all of the concrete pntOS plugin structures.
    For example, the transport plugin is specified as:

    ```
    class TransportPlugin(CommonPlugin, Protocol):

        def init_plugin(...):
            ...init_plugin implementation...

        def ...other function implementations...
    ```

    Thus this class defines a set of functions and variables that all plugins
    have. The `CommonPlugin.init_plugin` function is guaranteed to be called by
    pntOS when the plugin is first loaded into memory by the system.

    When defining a new e.g. transport plugin, the plugin writer is responsible
    for implementing all fields on the `TransportPlugin` class. Thus, the
    fields of the `CommonPlugin` nested on the `TransportPlugin` are
    implemented by the plugin writer.
    """

    def init_plugin(
        self, plugin_resources_location: Optional[str], mediator: Optional[Mediator]
    ) -> None:
        """
        A function that will be called by pntOS once and only once when it
        first initializes the plugin before any other functions on the plugin
        are called. Here the plugin may do dynamic runtime initialization of
        its members, and is given the full path to the location of a data
        folder specific to the plugin, in case it needs to acquire additional
        files. A pointer to an instance of `Mediator` will be passed which the
        plugin should save off for later use. Whenever the plugin needs to make
        a request of pntOS, it should use one of the fields in the `Mediator`
        instance received by the plugin in this function call.

        Implementation note:

        This inversion of control allows the controller to implement the
        `Mediator` class, and abstracts away the return communication channel
        from the plugin to the rest of the system. Thus, the plugin need only
        implement `Mediator` by simply saving a copy of the functions that the
        controller passes into it. Then, when the plugin later needs to make
        requests of the system, it may call a function in its copy of
        `Mediator`, without needing any knowledge of how the controller
        implemented `Mediator`. This allows controllers to implement arbitrary
        concurrency models, including single-threaded, multi-threaded,
        multi-process, and distributed computing.

        `plugin_resources_location` specifies the location of the plugin's
        resources.  The location is determined by the controller plugin, and
        therefore is controller implementation specific. Plugin implementers
        wishing to provide a resource to their plugin should consult the
        documentation of the controller to determine which location scheme will
        be passed into this function.

        `mediator` is None-able if the plugin type being initialized is a
        `ControllerPlugin`. Non-controller plugins may assume that the mediator
        parameter is not None.
        """
        pass

    def shutdown_plugin(self) -> None:
        """
        A function that will be called by pntOS when it is done using the
        plugin. Here the plugin should release any resources it has acquired
        (including the `Mediator` if it kept a reference to that when
        `init_plugin` was called). When this function call returns pntOS may
        only call the destructor function (it will not call any other functions
        of this plugin). The plugin may not call any function on any other
        plugin, mediator, or use any resource that was given to it by pntOS
        after it returns from this function.
        """
        pass

    identifier: str
    """
    A string identifier uniquely identifying this plugin. This string will be 
    used to determine the unique space this plugin receives in the system 
    config.
    """
