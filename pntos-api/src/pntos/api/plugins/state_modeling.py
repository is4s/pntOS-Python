"""Python API of pntOS."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, TypeVar

from aspn23 import TypeTimestamp
from numpy import float64
from numpy.typing import NDArray

from .common import CommonPlugin, EstimateWithCovariance, Message

if TYPE_CHECKING:
    from .fusion import StandardFusionEngine


@dataclass
class StandardDynamicsModel:
    """
    A description of the propagation dynamics for a set of states.

    This model assumes that the state space :math:`x` can be propagated forward in time by the
    equation:

    .. math::
        x_k = g(x_{k-1}) + w_k

    where :math:`x_k` is the set of states at time :math:`k`, :math:`g` is an arbitrary function,
    and :math:`w_k` is additive white Gaussian noise.

    Attributes:
        g (Callable[[NDArray[float64]], NDArray[float64]]): A function that propagates forward in time a set of
            states.
        Phi (NDArray[float64]): The first-order Taylor series expansion (Jacobian) of the function :math:`g`.
        Qd (NDArray[float64]): The covariance matrix of :math:`w_k`.
    """

    g: Callable[[NDArray[float64]], NDArray[float64]]
    Phi: NDArray[float64]
    Qd: NDArray[float64]


@dataclass
class StandardMeasurementModel:
    """
    A description of how a measurement relates to a state space.

    This model assumes that the relationship between the measurement and state vector is well
    modeled by the equation:

    .. math::
        z=h(x) + v

    where :math:`z` is the measurement itself, :math:`x` is the set of states being estimated,
    :math:`h` is an arbitrary function, and :math:`v` is additive white Gaussian noise.

    Attributes:
        z (NDArray[float64]): A column vector containing the measurement itself.
        h (Callable[[NDArray[float64]], NDArray[float64]]): A function that maps the state space to measurement space.
        H (NDArray[float64]): The first-order Taylor series expansion (i.e. Jacobian) of the function h.
        R (NDArray[float64]): The covariance matrix of :math:`v`.
    """

    z: NDArray[float64]
    h: Callable[[NDArray[float64]], NDArray[float64]]
    H: NDArray[float64]
    R: NDArray[float64]


class StandardStateBlock(ABC):
    """
    A description of a set of states and their dynamics.

    Attributes:
        label (str): The unique name for this state block.
        num_states (int): The number of states represented by this state block.

    Note:
        This class must have an operational ``__deepcopy__`` method. For most classes, the default
        ``__deepcopy__`` method provided by Python will be sufficient. However, if the class has a
        field which does not properly implement its own ``__deepcopy__`` (such as a C object wrapped
        to Python), then the class will need to implement a custom ``__deepcopy__`` which properly
        copies all fields.
    """

    label: str
    num_states: int

    @abstractmethod
    def receive_aux_data(self, aux: list[Message | None]) -> None:
        """
        Receive and use an arbitrary collection of aux data.

        This method will be called by the fusion engine when its
        :meth:`pntos.api.StandardFusionEngine.give_state_block_aux_data` is called with a label
        corresponding to this state block's ``label``.

        Args:
            aux (list[Message | None])
        """
        pass

    @abstractmethod
    def generate_dynamics(
        self,
        x_and_p: EstimateWithCovariance,
        time_from: TypeTimestamp,
        time_to: TypeTimestamp,
    ) -> StandardDynamicsModel | None:
        """
        Generate a :class:`pntos.api.StandardDynamicsModel`.

        The generated model contains a complete description of how to propagate
        this state block forward in time. For simple models, this can simply
        return a set of static matrices that are pre-defined.

        Args:
            x_and_p (EstimateWithCovariance): The current estimate and covariance for this
                state block. Note that this is only valid for the duration of this function, and
                users are strongly discouraged from saving it off for later use.
            time_from (TypeTimestamp): The time to propagate from.
            time_to (TypeTimestamp): The time to propagate to.

        Returns:
            StandardDynamicsModel | None: The description of how to propagate this state block over
            the given time interval, or ``None`` if ``time_from`` is later than ``time_to``.
            Otherwise guaranteed to not return ``None``.
        """
        pass


class VirtualStateBlock(ABC):
    """
    A class used to convert a set of states from one representation to another.

    States are converted using a mapping function :math:`f` to convert estimates,
    and the Jacobian of :math:`f()` to map covariances (note that this implies that
    the order/units of terms in the estimate vector and covariance matrix are
    the same). Each instance is associated with two labels, ``source`` and
    ``target``, where ``source`` is the label attached to the quantity to be
    transformed, and ``target`` is the label attached to the result. Typically used
    with a :class:`pntos.api.StandardFusionEngine` where ``source`` refers to a *real*
    :class:`pntos.api.StandardStateBlock` and ``target`` refers to some representation that is
    advantageous for some other element, such as a :class:`pntos.api.StandardMeasurementProcessor`, to use.

    Attributes:
        source (str): The label associated with the representation this instance can transform
            *from*.
        target (str): The label associated with the representation this instance can transform *to*.

    Note:
        This class must have an operational ``__deepcopy__`` method. For most classes, the default
        ``__deepcopy__`` method provided by Python will be sufficient. However, if the class has a
        field which does not properly implement its own ``__deepcopy__`` (such as a C object wrapped
        to Python), then the class will need to implement a custom ``__deepcopy__`` which properly
        copies all fields.
    """

    source: str
    target: str

    @abstractmethod
    def receive_aux_data(self, aux: list[Message | None]) -> None:
        """
        Receive and use an arbitrary collection of aux data.

        This method will be called by the fusion engine when its
        :meth:`pntos.api.StandardFusionEngine.give_virtual_state_block_aux_data` is called with a
        label corresponding to this :class:`pntos.api.VirtualStateBlock` 's ``target``.

        Args:
            aux (list[Message | None])
        """
        pass

    @abstractmethod
    def convert(
        self,
        estimate_with_covariance: EstimateWithCovariance,
        time: TypeTimestamp,
    ) -> EstimateWithCovariance:
        """
        Convert a full estimate/covariance pair.

        Args:
            estimate_with_covariance (EstimateWithCovariance): Estimate and covariance to convert.
            time (TypeTimestamp): Time that ``estimate_with_covariance`` is valid at.

        Returns:
            EstimateWithCovariance: The converted value.
        """
        pass

    @abstractmethod
    def convert_estimate(
        self, estimate: NDArray[float64], time: TypeTimestamp
    ) -> NDArray[float64]:
        """
        Convert just an estimate vector.

        Args:
            estimate (NDArray[float64]): Estimate vector to convert, Nx1.
            time (TypeTimestamp): Time that ``estimate`` is valid at.

        Returns:
            NDArray[float64]: The converted vector, Mx1.
        """
        pass

    @abstractmethod
    def jacobian(
        self, estimate: NDArray[float64], time: TypeTimestamp
    ) -> NDArray[float64]:
        """
        Obtain the Jacobian of the transform performed by this instance.

        The Jacobian is calculated at an instance in time, given an estimate to
        differentiate with respect to.

        Args:
            estimate (NDArray[float64]): Estimate vector associated with the return value of ``source``, Nx1.
            time (TypeTimestamp): Time that ``estimate`` is valid at.

        Returns:
            NDArray[float64]: An MxN matrix that may be used to pre-multiply ``estimate`` to obtain an M
            length vector in ``target`` representation (to first order).
        """
        pass


class StandardMeasurementProcessor(ABC):
    """
    A class that processes raw measurements/observations.

    The measurements are used to calculate estimated states suitable for a linear or linearized
    filter to use. Each type of measurement should correspond to a
    :class:`pntos.api.StandardMeasurementProcessor` that is supplied to the fusion engine. Incoming
    measurements received by the fusion engine will be routed to the corresponding measurement
    processor (by label) and call :meth:`generate_model` to process the measurement. The resulting
    :class:`pntos.api.StandardMeasurementModel` will be used by the fusion engine to call the underlying
    :meth:`pntos.api.StandardFusionStrategy.update` method to update the filter estimate/error covariance.

    Attributes:
        label (str): A unique name for this measurement processor. This value will be used to
            select a measurement processor to handle new measurements that the strategy
            receives.
        state_block_labels (list[str]): A list of unique state block labels associated with
            measurements received by this processor. The estimate and covariance matrices passed
            into :meth:`generate_model` will be composed of the states associated with these state
            blocks, and the returned StandardMeasurementModel.h and StandardMeasurementModel.H must
            respect these states. Note: ``state_block_labels[i]`` is the identifier for the ``i`` th
            state block this processor relates to.

    Note:
        This class must have an operational ``__deepcopy__`` method. For most classes, the default
        ``__deepcopy__`` method provided by Python will be sufficient. However, if the class has a
        field which does not properly implement its own ``__deepcopy__`` (such as a C object wrapped
        to Python), then the class will need to implement a custom ``__deepcopy__`` which properly
        copies all fields.
    """

    label: str
    state_block_labels: list[str]

    @abstractmethod
    def receive_aux_data(self, aux: list[Message | None]) -> None:
        """
        Receive and use an arbitrary collection of aux data.

        This method will be called by the fusion engine when its
        :meth:`pntos.api.StandardFusionEngine.give_measurement_processor_aux_data` is called with
        a label corresponding to this measurement processor's ``label``.

        Args:
            aux (list[Message | None])
        """
        pass

    @abstractmethod
    def generate_model(
        self, message: Message, x_and_p: EstimateWithCovariance
    ) -> StandardMeasurementModel | None:
        """
        Generate a :class:`pntos.api.StandardMeasurementModel`.

        Args:
            message (Message): The measurement/observation to process.
            x_and_p (EstimateWithCovariance): The current estimate and covariance for the state
                blocks this measurement processor targets. Note that this is only valid for the
                duration of this function, and users are strongly discouraged from saving it off for
                later use. Similarly, the estimate and covariance are invalidated if this function
                adds or removes any state blocks from the fusion engine.

        Returns:
            StandardMeasurementModel | None: A generated model containing the
            parameters required for a filter update. Will be ``None`` when a
            measurement cannot be produced from ``message`` (for example, this
            could happen if the measurement type is unsupported by the
            measurement processor or if it is rejected due to residual
            monitoring).
        """
        pass


class StandardStateModelProvider(ABC):
    """
    A collection of tools for modeling states and measurements.

    These tools are used to model the propagation and innovation of state
    spaces using pntOS's standard fusion model. Specifically, a
    :class:`pntos.api.StandardStateModelProvider` provides three types of tools:

    1. State Blocks - Define a set of states and a model for propagating those states.
    2. Virtual State Blocks - Relate two statespaces to each other.
    3. Measurement Processors - Relate measurements to a statespace.

    A :class:`pntos.api.StandardStateModelProvider` conceptually models a set of zero or more
    :class:`pntos.api.StandardStateBlock` s and a set of zero or more
    :class:`pntos.api.StandardMeasurementProcessor` s which together model the phenomenology of
    sensor data that is being brought into a fusion engine. The first type,
    state blocks, describe how a set of states propagates forward through time.
    The second type, measurement processors, describe how a measurement relates
    to a set of state blocks.

    Each :class:`pntos.api.StandardStateModelProvider` consists of factory methods which generate
    instances of the state blocks and measurement processors it provides. The
    :meth:`pntos.api.StandardStateModelProvider.new_block` method is a factory method that
    returns a newly created state block on each invocation. Because the
    :class:`pntos.api.StandardStateModelProvider` can provide more than one kind of state block,
    the :meth:`pntos.api.StandardStateModelProvider.new_block` method takes a ``block_index``
    parameter which allows the user to request which kind of state block is
    created by the factory. ``block_identifiers[i]`` gives a description of the
    ``i`` th kind of state block returned when ``block_index=i``.

    Similarly, :meth:`pntos.api.StandardStateModelProvider.new_processor` is a factory method for
    returning new measurement processors and ``processor_identifiers`` is a set
    of identifiers for each available kind of measurement processor that can be
    returned by the factory.

    Attributes:
        processor_identifiers (list[str] | None): A list of identifying strings for each kind of
            measurement processor that this :class:`pntos.api.StandardStateModelProvider` can create instances
            of. The ``processor_index`` parameter of :meth:`new_processor` is an index into this
            array. This field will be ``None`` when this state model provider does not provide
            any measurement processors.
        block_identifiers (list[str] | None): A list of identifying strings for each kind of state block
            that this :class:`pntos.api.StandardStateModelProvider` can create instances of.
            The ``block_index`` parameter of :meth:`new_block` is an index into this array.
            This field will be ``None`` when this state model provider does not
            provide any state blocks.
        virtual_block_identifiers (list[str] | None): A list of identifying strings for each kind of
            virtual state block that this :class:`pntos.api.StandardStateModelProvider` can create instances
            of. The ``virtual_block_index`` parameter of :meth:`new_virtual_block` is an index into
            this array. This field will be ``None`` when this state model provider does not
            provide any virtual state blocks.
    """

    processor_identifiers: list[str] | None
    """Strings describing the measurement processors the provider can create.
    """
    block_identifiers: list[str] | None
    """Strings describing the state blocks the provider can create.
    """
    virtual_block_identifiers: list[str] | None
    """Strings describing the virtual state blocks the provider can create.
    """

    @abstractmethod
    def new_processor(
        self,
        processor_index: int,
        engine: StandardFusionEngine | None,
        label: str,
        state_block_labels: list[str],
        config_group: str | None,
    ) -> StandardMeasurementProcessor | None:
        """
        Generate a newly created :class:`pntos.api.StandardMeasurementProcessor`.

        This measurement processor describes the relationship between a
        measurement and a set of state blocks.

        Args:
            processor_index (int): Since the :class:`pntos.api.StandardStateModelProvider` can create
                different kinds of measurement processors, the ``processor_index``
                parameter is used to select which kind of measurement processor
                to create a new instance of. The :attr:`processor_identifiers` field
                contains identifying strings for the kinds of processors. For
                example, if the model can create 45 different processors, the
                identifier of the last processor that can be created is found in
                ``processor_identifiers[44]``. An instance of this processor can be
                created by calling ``new_processor(self, 44, ...)``. Note that ``0
                <= processor_index < len(processor_identifiers)``.
            engine (StandardFusionEngine | None): An optional parameter that may be provided to the
                new processor, such that the processor may interact with the fusion engine it
                is being used in (for example, to add/remove states). Set it to
                ``None`` when no engine is available for the processor to use.
            label (str): A string which will be used to populate the ``label`` field of
                the newly created processor. This ``label`` will be the unique name
                for the returned instance of a processor, and used to track the
                processor throughout its lifecycle. Note that it differs from
                :attr:`processor_identifiers` which is the model's mechanism for
                selecting the *kind* of processor to create.
            state_block_labels (list[str]): A list of strings which will be used to
                populate the ``state_block_labels`` field of the newly created
                processor.
            config_group (str | None): Indicates which (if any) parameter group in the
                registry may be used to obtain additional configuration values to
                generate the new processor. If the processor requires no outside
                configuration, ``config_group`` may be ``None``.

        Returns:
            StandardMeasurementProcessor | None: The newly created
            :class:`pntos.api.StandardMeasurementProcessor` or ``None`` when no measurement processor can be
            produced with the given ``processor_index``, ``engine``, and ``config_group``.
        """
        pass

    @abstractmethod
    def new_block(
        self,
        block_index: int,
        engine: StandardFusionEngine | None,
        label: str,
        config_group: str | None,
    ) -> StandardStateBlock | None:
        """
        Generate a newly created :class:`pntos.api.StandardStateBlock`.

        This state block describes a set of states and how they propagate over
        time.

        Args:
            block_index (int): Since the :class:`pntos.api.StandardStateModelProvider` can create
                different kinds of state blocks, the ``block_index`` parameter is
                used to select which kind of state block to create a new instance
                of. The :attr:`block_identifiers` field contains identifying strings for
                the kinds of state blocks. For example, if the model can create
                45 different state blocks, the identifier of the last state block
                that can be created is found in ``block_identifiers[44]``. An
                instance of this state block can be created by calling
                ``new_block(self, 44, ...)``. Note that ``0 <= block_index <
                len(block_identifiers)``.
            engine (StandardFusionEngine | None): An optional parameter that may be provided to the
                new block, such that the block may interact with the fusion engine it
                is being used in (for example, to add/remove states). Set it to
                ``None`` when no engine is available for the block to use.
            label (str): A string which will be used to populate the ``label`` field
                of the newly created state block. This ``label`` will be the unique
                name for the returned instance of a state block, and used to
                track the state block throughout its lifecycle. Note that it
                differs from :attr:`block_identifiers` which is the model's mechanism
                for selecting the *kind* of state block to create.
            config_group (str | None): Indicates which (if any) parameter group in the
                registry may be used to obtain additional configuration values to
                generate the new state block. If the state block requires no
                outside configuration, ``config_group`` may be ``None``.

        Returns:
            StandardStateBlock | None: The newly created
            :class:`pntos.api.StandardStateBlock` or ``None`` when no state block can be produced
            with the given ``block_index``, ``engine``, and ``config_group``.
        """
        pass

    @abstractmethod
    def new_virtual_block(
        self,
        virtual_block_index: int,
        source_label: str,
        target_label: str,
        config_group: str | None,
    ) -> VirtualStateBlock | None:
        """
        Generate a newly created :class:`pntos.api.VirtualStateBlock`.

        This virtual state block is used to convert a set of states from one
        representation to another.

        Args:
            virtual_block_index (int): Since the :class:`pntos.api.StandardStateModelProvider` can
                create different kinds of virtual state blocks, the
                ``virtual_block_index parameter`` is used to select which kind of
                virtual state block to create a new instance of. The
                :attr:`pntos.api.StandardStateModelProvider.virtual_block_identifiers` field contains identifying strings for
                the kinds of virtual state blocks. For example, if the model can
                create 45 different virtual state blocks, the identifier of the
                last virtual state block that can be created is found in
                ``virtual_block_identifiers[44]``. An instance of this virtual
                state block can be created by calling ``new_virtual_block(self,
                44, ...)``. Note that ``0 <= virtual_block_index <
                len(virtual_block_identifiers)``.
            source_label (str): The label of the state block or virtual state block
                whose states this virtual state block transforms.
            target_label (str): A unique identifier for this virtual state block.
            config_group (str | None): Indicates which (if any) parameter group in the
                registry may be used to obtain additional configuration values to
                generate the new virtual state block. If the virtual state block
                requires no outside configuration, ``config_group`` may be ``None``.

        Returns:
            VirtualStateBlock | None: The newly created :class:`pntos.api.VirtualStateBlock` or ``None`` when
            no virtual state block can be produced with the given ``virtual_block_index`` and
            ``config_group``.
        """
        pass


StateModelProviderType = TypeVar(
    'StateModelProviderType', StandardStateModelProvider, Any
)
"""
An enumeration of the types of state model providers a state modeling plugin could provide.

"Any" is included for future compatibility.
"""


class StateModelingPlugin(CommonPlugin, ABC):
    """A :class:`pntos.api.CommonPlugin` subclass that generates state model providers."""

    @abstractmethod
    def is_fusion_type_supported(
        self, fusion_type: type[StateModelProviderType]
    ) -> bool:
        """
        Check if the plugin supports a given type of fusion. See ``StateModelProviderType``.

        Args:
            fusion_type (StateModelProviderType)

        Returns:
            bool
        """
        pass

    @abstractmethod
    def new_state_model_provider(
        self, fusion_type: type[StateModelProviderType]
    ) -> StateModelProviderType | None:
        """
        Generate a state model provider.

        Args:
            fusion_type (StateModelProviderType): Specifies the type of fusion that the returned value will
                support. For example, if the user passes in ``STANDARD_MODEL``, then the returned
                value will be an implementation of :class:`pntos.api.StandardStateModelProvider`.

        Returns:
            StateModelProviderType | None: A state model provider which implements the specified
            type or None if ``fusion_type`` is not supported (:meth:`is_fusion_type_supported` can be used
            to check ``fusion_type``).
        """
        pass
