from dataclasses import dataclass
from enum import Enum
from typing import Callable, List, Optional, Protocol, TypeVar

from aspn23.aspn_base import AspnBase
from aspn23.type_timestamp import TypeTimestamp
from numpy import float64
from numpy.typing import NDArray


@dataclass
class Message:
    # TODO: review the below docstring
    """
    A container for an ASPN message. This container may contain either proper
    ASPN messages which are part of the ASPN data model, or extension messages
    specific to pntOS which augment ASPN. For messages of the former type, the
    wrapped message's message_type field should be used directly. For messages
    of the latter type, cast the wrapped message's message_type field to
    PntosMessageType.
    """

    wrapped_message: AspnBase
    source_identifier: str


EstimateWithCovarianceType = Enum(
    "EstimateWithCovarianceType",
    [
        # TODO: review the below docstring
        "PNTOS_EWC_GENERIC",
        """
        Contains a mean (estimate) and covariance describing a multivariate
        Gaussian distribution.
        * PntosEstimateWithCovariance.length reflects the size of the estimate 
          and covariance fields.
        * PntosEstimateWithCovariance.estimate is size Nx1 where N is the 
          length field.
        * PntosEstimateWithCovariance.covariance is size NxN where N is the 
          length field.
        """
        # TODO: review the below docstring
        "PNTOS_EWC_ATTITUDE_QUAT"
        """
        Contains a mean (estimate) and covariance describing a rotation modeled
        by a multivariate Gaussian distribution, but the estimate is in 
        quaternion form and the covariance is in tilt error form.
	    * PntosEstimateWithCovariance.length is unused.
	    * PntosEstimateWithCovariance.estimate is size 4x1
	    * PntosEstimateWithCovariance.covariance is size 3x3, in radians^2.
        """,
    ],
)


@dataclass
class EstimateWithCovariance:
    # Describes how the fields in this struct are used.
    type: EstimateWithCovarianceType

    # The estimate vector.  Usage depends on the #type field.
    estimate: NDArray[float64]

    # An array of doubles representing a square covariance matrix. Data is
    # stored in row major form.  Usage depends on the #type field.
    covariance: NDArray[float64]


PluginTypes = Enum(
    # TODO: review the below docstring
    """
    An enumeration of the types of plugins supported by pntOS for this loader 
    API version. Each enum entry maps to a corresponding structure with 
    PascalCase naming. For example, the #PNTOS_CONTROLLER_PLUGIN value in this 
    enum is indicating a controller plugin. Note that because the utility 
    plugin has no additional API requirements beyond the PntosCommonPlugin, 
    there is not a `PntosUtilityPlugin`. Instead, implementers of 
    #PNTOS_UTILITY_PLUGIN should implement and return a PntosCommonPlugin.
    """
    "PluginTypes",
    [
        # TODO: review the below docstring
        "PNTOS_UNDEFINED_PLUGIN",
        """ 
        An unused entry, designed to allow code to detect accidentally unset 
        fields. This value must not be used by any plugin implementation, 
        other than to check for an erroneous default value being used.
        """
        # TODO: review the below docstring
        "PNTOS_CONTROLLER_PLUGIN",
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
        # TODO: review the below docstring
        "PNTOS_FUSION_PLUGIN",
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
        # TODO: review the below docstring
        "PNTOS_FUSION_STRATEGY_PLUGIN",
        """
        A low level computational engine that can perform sensor fusion given 
        pre-determined fixed models of errors and raw measurements. Because 
        this plugin requires fixed models, another plugin is required to 
        orchestrate modular descriptions of the fusion problem into a 
        fixed-size problem. The fusion plugin is used to orchestrate modular 
        descriptions into a fixed-size problem suitable for the computational 
        engine in this plugin to consume.
        """
        # TODO: review the below docstring
        "PNTOS_PLATFORM_INTEGRATION_PLUGIN",
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
        # TODO: review the below docstring
        "PNTOS_INITIALIZATION_PLUGIN",
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
        # TODO: review the below docstring
        "PNTOS_DATABASE_PLUGIN",
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
        # TODO: review the below docstring
        "PNTOS_TRANSPORT_PLUGIN",
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
        # TODO: review the below docstring
        "PNTOS_UI_PLUGIN",
        """
        A plugin for enabling user interfaces to be hooked up to pntOS. This 
        plugin is designed to enable displays to users to both see the current 
        state of pntOS and also configure/tweak it. Note that it is *not* 
        designed for hooking up operational displays, but rather debugging / 
        developer consoles. For outputs that will be sent to operational live 
        displays on the platform, the platform integration plugin is preferred.
        """
        # TODO: review the below docstring
        "PNTOS_ORCHESTRATION_PLUGIN",
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
        # TODO: review the below docstring
        "PNTOS_ORCHESTRATION_STRATEGY_PLUGIN",
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
        # TODO: review the below docstring
        "PNTOS_REGISTRY_PLUGIN",
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
        # TODO: review the below docstring
        "PNTOS_INERTIAL_PLUGIN",
        """
        A plugin that generates PVA solutions from an inertial.

        **UNSTABLE**: This feature is unstable and is not yet considered part 
        of the stable pntOS API. Usage of this feature is highly discouraged in
        non-experimental code, and its definition may change at any time.
        """
        # TODO: review the below docstring
        "PNTOS_STATE_MODELING_PLUGIN",
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
        # TODO: review the below docstring
        "PNTOS_LOGGING_PLUGIN",
        """
        A plugin that logs system events to an arbitrary sink. A sink may be a 
        file, a console, an attached GUI, a network destination, or any other destination of interest.
        """
        # TODO: review the below docstring
        "PNTOS_UTILITY_PLUGIN",
        """
        A plugin that performs a generic utility function. A utility plugin 
        performs functions that may require access to pntOS resources (such as 
        the registry) but is not otherwise relied upon to perform any 
        particular function.
        """
        # TODO: review the below docstring
        "PNTOS_PREPROCESSOR_PLUGIN",
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
        """,
    ],
)


FusionType = Enum(
    # TODO: review the below docstring
    """
An enumeration of the types of fusion that can be performed by pntOS. An 
implementation of a #PntosFusionPlugin plugin will compare a model from this 
enum in its PntosFusionPlugin.is_fusion_type_supported function. The return of
PntosFusionPlugin.is_fusion_type_supported indicates whether the input type of 
fusion engine matches the type that will be produced by 
PntosFusionPlugin.new_fusion_engine.

For example, suppose we have a variable `PntosFusionPlugin* plugin`. Then if 
the return value of `plugin->is_fusion_type_supported(plugin, 
PNTOS_FUSION_STANDARD_MODEL)` is true, then that means that 
`plugin->new_fusion_engine(plugin)` will return a `PntosStandardFusionEngine*`.
"""
    "FusionType",
    [
        # TODO: review the below docstring
        "PNTOS_FUSION_STANDARD_MODEL",
        """
        The standard model of fusion within pntOS. This model assumes that 
        state estimates are representable in a jointly Gaussian state vector 
        and that updates of the state vector contain only i.i.d. additive white
        Gaussian noise. See PntosStandardFusionEngine for more information.
        """
        # TODO: review the below docstring
        "PNTOS_FUSION_SAMPLED_MODEL",
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
        # TODO: review the below docstring
        "PNTOS_FUSION_TIME_DELAYED_MODEL",
        """
        The time delayed model of fusion within pntOS. This model assumes that 
        information about a state is retained across different time epochs and 
        that historical estimate data is available for processing current time 
        data.

        **UNSTABLE**: This feature is unstable and is not yet considered part 
        of the stable pntOS API. Usage of this feature is highly discouraged in
        non-experimental code, and its definition may change at any time.
        """
        # TODO: review the below docstring
        "PNTOS_FUSION_STANDARD_COMPILED_MODEL",
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
        """,
    ],
)

LoggingLevel = Enum(
    # TODO: review the below docstring
    """
An enumeration of the types of log outs that are available in pntOS.
"""
    "LoggingLevel",
    [
        # TODO: review the below docstring
        "PNTOS_LOG_LEVEL_ERROR",
        """
        This output indicates the program has entered an error state, and 
        likely needs to be inspected to discover what went wrong.
        """
        # TODO: review the below docstring
        "PNTOS_LOG_LEVEL_WARN",
        """
        This output is designed to warn of a possibly unintended state that may
        be harmless or be indicative of a bug.
        """
        # TODO: review the below docstring
        "PNTOS_LOG_LEVEL_INFO",
        """
        This output is designed to be informational, and may indicate correct 
        operation.
        """
        # TODO: review the below docstring
        "PNTOS_LOG_LEVEL_DEBUG",
        """
        This output is designed to assist in debugging plugins by providing 
        additional information about state and behavior which would be 
        otherwise unnecessary.
        """,
    ],
)


KeyValueStoreDataFormat = Enum(
    # TODO: review the below docstring
    """
An enum that specifies the format of data returned/expected in the 
PntosKeyValueStore.get_raw and PntosKeyValueStore.set_raw methods. This value 
is otherwise unused when querying a key-value store.
"""
    "KeyValueStoreDataFormat",
    [
        # TODO: review the below docstring
        "PNTOS_KV_STORE_INI",
        """
        Keys and their corresponding values are returned according to the INI 
        file format specification.
        """
        # TODO: review the below docstring
        "PNTOS_KV_STORE_UNSPECIFIED"
        """
        An opaque type that is undefined by the implementer.
        """,
    ],
)

ValueType = TypeVar(
    "ValueType", None, str, List[str], int, bool, float, NDArray[float64], Message
)
# TODO: make docstring if needed


class KeyValueStore(Protocol):
    # TODO: review the below docstring
    """
    A key-value store implemented with a string-pair key. Each value can be
    looked up by an associated key (string). Values can be a variety of
    different types.

    In general, a KeyValueStore is generated by a Registry and not
    directly by other code. The Registry will return key/value stores on
    demand, utilizing the data backing store chosen by the plugin to store data
    (either ephemerally in memory or permanently in persistent storage). In
    general, it is only valid to call the getters/setters on a KeyValueStore
    during a batch operation. See Registry for more information.
    """

    def get_key_array(self) -> List[str]:
        # TODO: review the below docstring
        """
        Get the array of keys which currently exist in this store. Returns NULL
        if no keys are available.
        """
        pass

    def has_key(self, key: str) -> bool:
        # TODO: review the below docstring
        """
        Returns whether or not a given key exists in the store.
        """
        pass

    def get_value(self, key: str, type: type[ValueType]) -> ValueType:
        # TODO: review the below docstring
        """
        Get the value stored at 'key' with return type 'type'. For example, to
        access altitude in KeyValueStore 'kv_store' as an integer:\n
        altitude = kv_store.get_value("altitude", int) \n
        Returns NULL if the key is not available. The return is guaranteed to
        not be NULL if called with a valid key, which can be checked with
        has_key().
        """
        pass

    def get_raw(self, key: Optional[str]) -> Optional[bytes]:
        # TODO: make a docstring
        pass

    def set_value(self, key: str, value: ValueType) -> None:
        # TODO: review the below docstring
        pass

    def set_raw(self, key: Optional[str], bytes: bytes) -> None:
        pass

    def remove_key(self, key: str) -> bool:
        pass

    def batch_end(self) -> None:
        pass

    def batch_restart(self) -> None:
        pass

    def request_notify(
        self,
        key: Optional[str],
        callback: Callable[[str, List[str], "KeyValueStore"], None],
    ) -> bool:
        pass

    def remove_notify(
        self,
        key: Optional[str],
        callback: Callable[[str, List[str], "KeyValueStore"], None],
    ) -> bool:
        pass

    def set_permanent(self, permanent: bool) -> bool:
        pass

    data_format: KeyValueStoreDataFormat


class Registry(Protocol):
    def batch_start(self, group: str) -> KeyValueStore:
        pass

    def get_group_array(self) -> List[str]:
        pass

    def has_group(self, group: str) -> bool:
        pass

    def request_notify_new_group(self, callback: Callable[[str], None]) -> bool:
        pass


class Mediator(Protocol):
    def get_filter_description_list(self) -> List[str]:
        pass

    def request_solutions(
        self, solution_times: List[TypeTimestamp], filter_description: Optional[str]
    ) -> List[Message]:
        pass

    def process_pntos_message(self, message: Message) -> None:
        pass

    def broadcast_aspn_message(
        self,
        message: Message,
        transport: Optional[str],
        destination_identifier: Optional[str],
    ) -> None:
        pass

    def log_message(self, level: LoggingLevel, message: str) -> None:
        pass

    registry: Registry


class CommonPlugin(Protocol):
    def init_plugin(
        self, plugin_resources_location: Optional[str], mediator: Optional[Mediator]
    ) -> None:
        pass

    def shutdown_plugin(self) -> None:
        pass

    identifier: str
