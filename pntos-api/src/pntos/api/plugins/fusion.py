"""Python API of pntOS."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, List, TypeVar

from aspn23 import TypeTimestamp
from numpy.typing import NDArray

from .common import CommonPlugin, EstimateWithCovariance, Message
from .fusion_strategy import (
    StandardDynamicsModel,
    StandardFusionStrategy,
    StandardMeasurementModel,
)


@dataclass
class CrossCovariances:
    """
    A container for a set of covariances relating a StateBlock to a set of other StateBlocks.

    Suppose that some StateBlock named ``A`` existed. Then this structure could define the cross
    covariance of ``A`` with respect to other StateBlocks named ``B`` and ``C``. In that case,
    :attr:`block_labels` would be an array of 2 strings ``B`` and ``C``, and
    :attr:`cross_covariances` would be a an array of two matrices: the cross-covariance matrix of
    ``A`` and ``B`` and the cross-covariance matrix of ``A`` and ``C``.

    Attributes:
        block_labels (List[str]): A list of labels of the :class:`StandardStateBlock` this structure
            contains the cross-covariances for.
        cross_covariances (List[NDArray]): A list of cross-covariance matrices between a single
            StateBlock and the set of StateBlocks listed in :attr:`block_labels`.
    """

    block_labels: List[str]
    cross_covariances: List[NDArray]


class StandardStateBlock(ABC):
    """
    A description of a set of states and their dynamics.

    Attributes:
        label (str): The unique name for this state block.
        num_states (int): The number of states represented by this state block.
    """

    label: str
    num_states: int

    @abstractmethod
    def receive_aux_data(self, aux: list[Message]) -> None:
        """
        Receive and use an arbitrary collection of aux data.

        This method will be called by the fusion engine when its
        :meth:`StandardFusionEngine.give_state_block_aux_data` is called with a label
        corresponding to this state block's ``label``.

        Args:
            aux (list[Message])
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
        Generate a :class:`StandardDynamicsModel`.

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


class StandardMeasurementProcessor(ABC):
    """
    A class that processes raw measurements/observations.

    The measurements are used to calculate estimated states suitable for a linear or linearized
    filter to use. Each type of measurement should correspond to a
    :class:`StandardMeasurementProcessor` that is supplied to the fusion engine. Incoming
    measurements received by the fusion engine will be routed to the corresponding measurement
    processor (by label) and call :meth:`generate_model` to process the measurement. The resulting
    :class:`StandardMeasurementModel` will be used by the fusion engine to call the underlying
    :meth:`StandardFusionStrategy.update` method to update the filter estimate/error covariance.

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
    """

    label: str
    state_block_labels: list[str]

    @abstractmethod
    def receive_aux_data(self, aux: list[Message]) -> None:
        """
        Receive and use an arbitrary collection of aux data.

        This method will be called by the fusion engine when its
        :meth:`StandardFusionEngine.give_measurement_processor_aux_data` is called with
        a label corresponding to this measurement processor's ``label``.

        Args:
            aux (list[Message])
        """
        pass

    @abstractmethod
    def generate_model(
        self, message: Message, x_and_p: EstimateWithCovariance
    ) -> StandardMeasurementModel | None:
        """
        Generate a :class:`StandardMeasurementModel`.

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


class VirtualStateBlock(ABC):
    """
    A class used to convert a set of states from one representation to another.

    States are converted using a mapping function :math:`f` to convert estimates,
    and the Jacobian of :math:`f()` to map covariances (note that this implies that
    the order/units of terms in the estimate vector and covariance matrix are
    the same). Each instance is associated with two labels, ``source`` and
    ``target``, where ``source`` is the label attached to the quantity to be
    transformed, and ``target`` is the label attached to the result. Typically used
    with a :class:`StandardFusionEngine` where ``source`` refers to a *real*
    :class:`StandardStateBlock` and ``target`` refers to some representation that is
    advantageous for some other element, such as a :class:`StandardMeasurementProcessor`, to use.

    Attributes:
        source (str): The label associated with the representation this instance can transform
            *from*.
        target (str): The label associated with the representation this instance can transform *to*.
    """

    source: str
    target: str

    @abstractmethod
    def receive_aux_data(self, aux: list[Message]) -> None:
        """
        Receive and use an arbitrary collection of aux data.

        This method will be called by the fusion engine when its
        :meth:`StandardFusionEngine.give_virtual_state_block_aux_data` is called with a
        label corresponding to this :class:`VirtualStateBlock` 's ``target``.

        Args:
            aux (list[Message])
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
    def convert_estimate(self, estimate: NDArray, time: TypeTimestamp) -> NDArray:
        """
        Convert just an estimate vector.

        Args:
            estimate (NDArray): Estimate vector to convert, Nx1.
            time (TypeTimestamp): Time that ``estimate`` is valid at.

        Returns:
            NDArray: The converted vector, Mx1.
        """
        pass

    @abstractmethod
    def jacobian(self, estimate: NDArray, time: TypeTimestamp) -> NDArray:
        """
        Obtain the Jacobian of the transform performed by this instance.

        The Jacobian is calculated at an instance in time, given an estimate to
        differentiate with respect to.

        Args:
            estimate (NDArray): Estimate vector associated with the return value of ``source``, Nx1.
            time (TypeTimestamp): Time that ``estimate`` is valid at.

        Returns:
            NDArray: An MxN matrix that may be used to pre-multiply ``estimate`` to obtain an M
            length vector in ``target`` representation (to first order).
        """
        pass


class StandardFusionEngine(ABC):
    """
    An implementation of a fusion engine that supports the standard fusion model.

    Assumes the system is described by discrete-time matrices and noise inputs are zero-mean white
    Gaussian. In addition, all covariance matrices / mean vectors are descriptions of
    jointly-Gaussian multivariate distributions. All noise sources are jointly-Gaussian distributed.

    This object requires a :class:`StandardFusionStrategy` to work. Some implementations may be able
    to provide their own. Others will require a strategy to be provided by setting the
    :attr:`StandardFusionEngine.strategy` field. It is possible to check whether a fusion
    engine needs to be provided a fusion strategy by checking the
    :attr:`StandardFusionEngine.strategy` field (if it is ``None`` then this fusion engine
    needs to be provided a strategy). While :attr:`StandardFusionEngine.strategy` is ``None``,
    all other methods are unsafe to be called.

    Caution:
        **Unstable**: This feature is unstable and is not yet considered part of the stable pntOS
        API. Usage of this feature is highly discouraged in non-experimental code, and its
        definition may change at any time.
    """

    @property
    @abstractmethod
    def time(self) -> TypeTimestamp:
        """
        Get the current time of the filter.

        Returns:
            TypeTimestamp
        """
        pass

    @property
    @abstractmethod
    def strategy(self) -> StandardFusionStrategy | None:
        """
        The underlying algorithm used for Bayesian inference.

        Returns:
            StandardFusionStrategy | None: The fusion strategy is the type of filter (EKF, UKF,
            etc.).
        """
        pass

    @abstractmethod
    def get_num_states(self) -> int:
        """
        Get the total number of states currently in the fusion engine.

        Virtual state blocks do not affect this result.

        Returns:
            int: The total number of states currently in the fusion engine.
        """
        pass

    @abstractmethod
    def get_state_block_labels(self) -> List[str] | None:
        """
        Get a list of :class:`StandardStateBlock` labels that have been added to this fusion engine.

        Returns:
            List[str] | None: A list of the :class:`StandardStateBlock` labels that have been added
            to this fusion engine. Returns ``None`` if no state blocks have been added. Guaranteed
            to not return ``None`` if :meth:`get_num_states` returns a value other than 0.
        """
        pass

    @abstractmethod
    def add_state_block(
        self,
        block: StandardStateBlock,
        initial_estimate_covariance: EstimateWithCovariance,
        cross_covariances: CrossCovariances | None = None,
    ) -> None:
        """
        Add the given :class:`StandardStateBlock` to the fusion engine.

        This will expand the state vector being estimated by the value of :meth:`get_num_states`.

        Args:
            block (StandardStateBlock): The :class:`StandardStateBlock` to be added to the fusion
                engine.
            initial_estimate_covariance (EstimateWithCovariance): Contains the initial conditions of
                the states, with ``initial_estimate_covariance.estimate`` being an Nx1 matrix and
                ``initial_estimate_covariance.covariance`` being an NxN matrix, where N is
                ``block.num_states``.
            cross_covariances (CrossCovariances | None, optional): An optional parameter which, if
                non-``None``, contains a description of the newly added StateBlock's cross
                covariances with respect to a set of StateBlocks which already exist inside the
                filter (specified by ``cross_covariances.block_labels``). If the
                ``cross_covariance`` parameter is ``None``, cross covariance between the existing
                states and the added states will be set to zeroes.
        """
        pass

    @abstractmethod
    def get_state_block_estimate(self, block_label: str) -> NDArray | None:
        """
        Get the estimate associated with a state block.

        Find a :class:`StandardStateBlock` or :class:`VirtualStateBlock` within the fusion engine
        matching ``block_label``, and return a copy of its current estimate vector.

        Args:
            block_label (str)

        Returns:
            NDArray | None: A copy of its current estimate vector. If ``block_label`` references a
            virtual state block (VSB) this will return a converted estimate, converted into the VSBs
            coordinate frame. Returns ``None`` if ``block_label`` does not correspond to a block
            that has been added to the fusion engine. Guaranteed to not return ``None`` when
            ``block_label`` is in the list returned by :meth:`get_state_block_labels` and
            :attr:`strategy` is not ``None``.
        """
        pass

    @abstractmethod
    def get_state_block_covariance(self, block_label: str) -> NDArray | None:
        """
        Get the covariance associated with a state block.

        Find a :class:`StandardStateBlock` or :class:`VirtualStateBlock` within the fusion engine
        matching ``block_label``, and return a copy of its current covariance matrix.

        Args:
            block_label (str)

        Returns:
            NDArray | None: A copy of its current covariance matrix. If ``block_label`` references a
            virtual state block (VSB) this will return a converted covariance, converted into the
            VSBs coordinate frame. Returns ``None`` if ``block_label`` does not correspond to a
            block that has been added to the fusion engine. Guaranteed to not return ``None`` when
            ``block_label`` is in the list returned by :meth:`get_state_block_labels` and
            :attr:`strategy` is not ``None``.
        """
        pass

    @abstractmethod
    def get_state_block_cross_covariance(
        self, block_label1: str, block_label2: str
    ) -> NDArray | None:
        """
        Get the cross covariance between the states associated with two state blocks.

        Find the :class:`StandardStateBlock` s within the fusion engine matching ``block_label1``
        and ``block_label2``, and return the cross-covariance matrix between them.

        Args:
            block_label1 (str)
            block_label2 (str)

        Returns:
            NDArray | None: The cross-covariance matrix between ``block_label1`` and
            ``block_label2``. Returns ``None`` if ``block_label1`` or ``block_label2`` do not
            correspond to blocks that have been added to the fusion engine. Guaranteed to not return
            ``None`` when both ``block_label1`` and ``block_label2`` are in the list returned by
            :meth:`get_state_block_labels` and :attr:`strategy` is not ``None``.
        """
        pass

    @abstractmethod
    def set_state_block_estimate(self, block_label: str, estimate: NDArray) -> None:
        """
        Update the estimate associated with a given state block.

        Find a :class:`StandardStateBlock` within the fusion engine matching ``block_label``, and
        change its current estimate vector.

        Note:
            This function may lead to performance degradation with some implementations and thus its
            use is discouraged if other options are available.

        Args:
            block_label (str)
            estimate (NDArray)
        """
        pass

    @abstractmethod
    def set_state_block_covariance(self, block_label: str, covariance: NDArray) -> None:
        """
        Update the covariance associated with a given state block.

        Find a :class:`StandardStateBlock` within the fusion engine matching ``block_label``, and
        change its current covariance matrix.

        Note:
            This function may lead to performance degradation with some implementations and thus its
            use is discouraged if other options are available.

        Args:
            block_label (str)
            covariance (NDArray)
        """
        pass

    @abstractmethod
    def set_state_block_cross_covariance(
        self, block_label1: str, block_label2: str, covariance: NDArray
    ) -> None:
        """
        Update the covariance between two state blocks.

        Find the :class:`StandardStateBlock` s within the fusion engine matching ``block_label1``
        and ``block_label2``, and change the current covariance matrix between them.

        Note:
            This function may lead to performance degradation with some implementations and thus its
            use is discouraged if other options are available.

        Args:
            block_label1 (str)
            block_label2 (str)
            covariance (NDArray)
        """
        pass

    @abstractmethod
    def remove_state_block(self, block_label: str) -> None:
        """
        Remove the :class:`StandardStateBlock` matching ``block_label``.

        This will reduce the state vector being estimated by the number of states that the block
        represents.

        Args:
            block_label (str)
        """
        pass

    @abstractmethod
    def get_virtual_state_block_target_labels(self) -> List[str] | None:
        """
        Gets a list of the target labels of virtual state blocks that have been added.

        A label being returned by this list is not a guarantee that the virtual state block has a
        valid source. For that, call :meth:`has_virtual_state_block`.

        Returns:
            List[str] | None: A list of the target labels of virtual state blocks that have been
            added. Returns ``None`` if no virtual state blocks have been added to this fusion
            engine.
        """
        pass

    @abstractmethod
    def has_virtual_state_block(self, vsb_target_label: str) -> bool:
        """
        Checks if the fusion engine has a :class:`VirtualStateBlock` with a matching target label.

        Args:
            vsb_target_label (str)

        Returns:
            bool: ``True`` if the fusion engine has a :class:`VirtualStateBlock` with a matching
            target label, ``False`` if no virtual state block with matching target label exists or
            if one exists but is not capable of generating an estimate. That is, the VSB's source
            must exist and be in a continuous chain to a concrete state block which also exists in
            the fusion engine in order to return ``True``.
        """
        pass

    @abstractmethod
    def add_virtual_state_block(self, virtual_state_block: VirtualStateBlock) -> None:
        """
        Add the given :class:`VirtualStateBlock` to the fusion engine.

        A virtual state block (VSB) convert from an underlying block coordinate frame into the VSB
        coordinate frame.

        Args:
            virtual_state_block (VirtualStateBlock)
        """
        pass

    @abstractmethod
    def remove_virtual_state_block(self, vsb_target_label: str) -> None:
        """
        Remove the :class:`VirtualStateBlock` matching ``vsb_target_label``.

        Args:
            vsb_target_label (str)
        """
        pass

    @abstractmethod
    def get_measurement_processor_labels(self) -> List[str] | None:
        """
        Get a list of the labels of measurement processors that have been added.

        Returns:
            List[str] | None: List of labels of measurement processors that have been added. Returns
            ``None`` if no measurement processors have been added to this fusion engine.
        """
        pass

    @abstractmethod
    def add_measurement_processor(
        self, processor: StandardMeasurementProcessor
    ) -> None:
        """
        Add a :class:`StandardMeasurementProcessor`.

        This can be used to process future measurements that correspond to ``processor.label``.

        Args:
            processor (StandardMeasurementProcessor)
        """
        pass

    @abstractmethod
    def remove_measurement_processor(self, processor_label: str) -> None:
        """
        Remove a :class:`StandardMeasurementProcessor` previously added to the fusion engine.

        Assumes a measurement processor was previously added via :meth:`add_measurement_processor`
        with the label ``processor_label``.

        Args:
            processor_label (str)
        """
        pass

    @abstractmethod
    def propagate(self, time: TypeTimestamp) -> None:
        """
        Propagate the filter estimate forward in time.

        May be evaluated lazily (when results are requested).

        Args:
            time (TypeTimestamp)
        """
        pass

    @abstractmethod
    def update(self, processor_label: str, message: Message) -> None:
        """
        Update the filter with the given measurement.

        Will propagate first if needed to reach the time encoded inside the measurement.

        Args:
            processor_label (str)
            message (Message)
        """
        pass

    @abstractmethod
    def peek_ahead(
        self, time: TypeTimestamp, block_labels: List[str]
    ) -> EstimateWithCovariance | None:
        """
        Calculates the estimate and covariance at a requested time.

        Uses the state blocks listed in ``block_labels``, without changing the state of the fusion
        engine or its underlying filter. Blocks are assembled in the order that the labels are
        passed in.

        If all of the following are true:

        - ``time`` is equal to or after the filter time (which can be checked with :attr:`time`).
        - All labels in ``block_labels`` correspond to a block that has been added to the fusion
          engine (which can be checked with :meth:`get_state_block_labels`).
        - ``block_labels`` has at least one element.

        Then the result returned is guaranteed to not be ``None``. Otherwise, if any of the above
        are false then the result will be ``None``.

        Args:
            time (TypeTimestamp)
            block_labels (List[str]): An array of strings.

        Returns:
            EstimateWithCovariance | None
        """
        pass

    @abstractmethod
    def generate_x_and_p(
        self, block_labels: List[str]
    ) -> EstimateWithCovariance | None:
        """
        Generates the current estimate and covariance.

        Estimate and covariance are built corresponding to a list of StateBlock labels. Blocks are
        assembled in the order that the labels are passed in.

        If all of the following are true:

            - All labels in ``block_labels`` correspond to a block that has been added to the fusion
              engine (which can be checked with :meth:`get_state_block_labels`).
            - ``block_labels`` has at least one element.

        Then the result returned is guaranteed to not be ``None``. Otherwise, if any of the above
        are false then the result will be ``None``.

        Args:
            block_labels (List[str]): An array of strings.

        Returns:
            EstimateWithCovariance | None
        """
        pass

    @abstractmethod
    def give_state_block_aux_data(self, block_label: str, aux: List[Message]) -> None:
        """
        Route a list of messages of aux data to a :class:`StandardStateBlock`.

        Args:
            block_label (str)
            aux (List[Message])
        """
        pass

    @abstractmethod
    def give_measurement_processor_aux_data(
        self, processor_label: str, aux: List[Message]
    ) -> None:
        """
        Route a list of messages of aux data to a :class:`StandardMeasurementProcessor`.

        Args:
            processor_label (str)
            aux (List[Message])
        """
        pass

    @abstractmethod
    def give_virtual_state_block_aux_data(
        self, target_label: str, aux: List[Message]
    ) -> None:
        """
        Route a list of messages of aux data to a :class:`VirtualStateBlock`.

        Args:
            target_label (str)
            aux (List[Message])
        """
        pass

    @abstractmethod
    def clone(self) -> 'StandardFusionEngine':
        """
        Produce a deep-copy this fusion engine instance.

        All state blocks and measurement processors held by the fusion engine will also be cloned.
        The fusion strategy used by the fusion engine will also be cloned.
        """
        pass


FusionEngineType = TypeVar('FusionEngineType', StandardFusionEngine, Any)


class FusionPlugin(CommonPlugin, ABC):
    """
    Plugin that provides a fusion engine.

    A fusion engine allows data from multiple sensors to be integrated into a unified state
    estimate.
    """

    @abstractmethod
    def is_fusion_type_supported(self, type: type[FusionEngineType]) -> bool:
        """
        Check if the plugin supports a given type of fusion.

        Args:
            type (type[FusionEngineType])

        Returns:
            bool
        """
        pass

    @abstractmethod
    def new_fusion_engine(
        self, type: type[FusionEngineType]
    ) -> FusionEngineType | None:
        """
        Create a fusion engine.

        Args:
            type (type[FusionEngineType]): This parameter specifies the type of fusion engine that
            will be returned.

        Returns:
            FusionEngineType | None: The ``type`` parameter specifies the type of fusion engine
            that will be returned. For example, if the user passes in :class:`StandardFusionEngine`,
            then an implementation of :class:`StandardFusionEngine` will be returned. Returns
            ``None`` if ``type`` is not supported by this fusion plugin
            (:meth:`is_fusion_type_supported` can be used to check the type before calling this
            method). Otherwise the return is guaranteed to not be ``None``.
        """
        pass
