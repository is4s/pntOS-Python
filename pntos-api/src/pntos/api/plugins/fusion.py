"""Python API of pntOS."""

from dataclasses import dataclass
from typing import List, Protocol

from aspn23 import TypeTimestamp
from numpy.typing import NDArray

from .common import CommonPlugin, EstimateWithCovariance, FusionType, Message
from .fusion_strategy import StandardFusionStrategy
from .state_modeling import (
    StandardMeasurementProcessor,
    StandardStateBlock,
    VirtualStateBlock,
)


class CommonFusionEngine(Protocol):
    """
    Performs sensor fusion, estimating states.

    A dynamic estimator exposing a state model provider consuming API capable of Bayesian inference
    on non-linear discrete-time systems.
    """

    pass


@dataclass
class CrossCovariances:
    """
    A container for a set of covariances relating a StateBlock to a set of other StateBlocks.

    Suppose that some StateBlock named `A` existed. Then this structure could define the cross
    covariance of `A` with respect to other StateBlocks named `B` and `C`. In that case,
    `block_labels` would be an array of 2 strings `B` and `C`, and `cross_covariances` would be a an
    array of two matrices: The cross-covariance matrix of `A` and `B` and the cross-covariance
    matrix of `A` and `C`.
    """

    block_labels: List[str]
    """
    A list of labels of the `StandardStateBlock`s this structure contains the cross-covariances for.
    """

    cross_covariances: List[NDArray]
    """
    A list of cross-covariance matrices between a single StateBlock and the set of StateBlocks
    listed in #block_labels.
    """


class StandardFusionEngine(CommonFusionEngine, Protocol):
    """
    An implementation of a fusion engine that supports the standard fusion model.

    Assumes the system is described by discrete-time matrices and noise inputs are zero-mean white
    Gaussian. In addition, all covariance matrices / mean vectors are descriptions of
    jointly-Gaussian multivariate distributions. All noise sources are jointly-Gaussian distributed.

    This object requires a StandardFusionStrategy to work. Some implementations may be able to
    provide their own. Others will require a strategy to be provided via the
    StandardFusionEngine.set_strategy method. It is possible to check whether a fusion engine needs
    to be provided a fusion strategy by calling the StandardFusionEngine.get_strategy method (if the
    return is None then this fusion engine needs to be provided a strategy). While
    StandardFusionEngine.get_strategy returns None, all other methods are unsafe to be called.

    **UNSTABLE**: This feature is unstable and is not yet considered part of the stable pntOS API.
    Usage of this feature is highly discouraged in non-experimental code, and its definition may
    change at any time.
    """

    def set_time(self, time: TypeTimestamp) -> None:
        """Set the current time of the filter to the parameter."""
        pass

    def get_time(self) -> TypeTimestamp:
        """Get the current time of the filter."""
        pass

    def set_strategy(self, strategy: StandardFusionStrategy) -> None:
        """
        Set the underlying algorithm used for Bayesian inference.

        The fusion strategy is the type of filter (EKF, UKF, etc.).
        """
        pass

    def get_strategy(self) -> StandardFusionStrategy | None:
        """
        @return The underlying algorithm used for Bayesian inference.

        The fusion strategy is the type of filter (EKF, UKF, etc.). Returns None if this fusion
        engine does not have a strategy. If that is the case, the fusion engine must be provided
        with a strategy via #set_strategy.
        """
        pass

    def get_num_states(self) -> int:
        """
        Get the total number of states currently in the fusion engine.

        Virtual state blocks do no affect this result.
        """
        pass

    def get_state_block_labels(self) -> List[str] | None:
        """
        Gets a list of the `StandardStateBlock`s labels that have been added to this fusion engine.

        Returns None if no state blocks have been added. Guaranteed to not return None if
        #get_num_states returns a value other than 0.
        """
        pass

    def has_block(self, block_label: str) -> bool:
        """Returns true if the fusion engine has a `StandardStateBlock` with a matching label."""
        pass

    def add_state_block(
        self,
        block: StandardStateBlock,
        initial_estimate_covariance: EstimateWithCovariance,
        cross_covariances: CrossCovariances | None = None,
    ) -> None:
        """
        Add the given StandardStateBlock to the fusion engine.

        This will expand the state vector being estimated by the value of `block.get_num_states()`.
        The `initial_estimate_covariance` parameter contains the initial conditions of the states,
        with `initial_estimate_covariance.estimate` being an Nx1 matrix and
        `initial_estimate_covariance.covariance` being an NxN matrix, where N is
        `block.get_num_states()`. The `cross_covariances` are an optional parameter which, if
        non-None, contains a description of the newly added StateBlock's cross covariances with
        respect to a set of StateBlocks which already exist inside the filter (specified by
        `cross_covariances.block_labels`). If the `cross_covariance` parameter is None, cross
        covariance between the existing states and the added states will be set to zeroes.
        """
        pass

    def get_state_block_estimate(self, block_label: str) -> NDArray | None:
        """
        Get the estimate associated with a state block.

        Find a `StandardStateBlock` or `VirtualStateBlock` within the fusion engine matching
        `block_label`, and return a copy of its current estimate vector. If `block_label` references
        a virtual state block (VSB) this will return a converted estimate, converted into the VSBs
        coordinate frame. Returns None if `block_label` does not correspond to a block that has been
        added to the fusion engine. Guaranteed to not return None when #has_block returns true for
        `block_label` and #get_strategy does not return None.
        """
        pass

    def get_state_block_covariance(self, block_label: str) -> NDArray | None:
        """
        Get the covariance associated with a state block.

        Find a `StandardStateBlock` or `VirtualStateBlock` within the fusion engine matching
        `block_label`, and return a copy of its current covariance matrix. If `block_label`
        references a virtual state block (VSB) this will return a converted covariance, converted
        into the VSBs coordinate frame. Returns None if `block_label` does not correspond to a block
        that has been added to the fusion engine. Guaranteed to not return None when #has_block
        returns true for `block_label` and #get_strategy does not return None.
        """
        pass

    def get_state_block_cross_covariance(
        self, block_label1: str, block_label2: str
    ) -> NDArray | None:
        """
        Get the cross covariance between the states associated with two state blocks.

        Find the `StandardStateBlocks` within the fusion engine matching `block_label1` and
        `block_label2`, and return the cross-covariance matrix between them. Returns None if
        `block_label1` or `block_label2` do not correspond to blocks that gave been added to the
        fusion engine. Guaranteed to not return None when #has_block returns true for both
        `block_label` and `block_label2` and #get_strategy does not return None.
        """
        pass

    def set_state_block_estimate(self, block_label: str, estimate: NDArray) -> None:
        """
        Update the estimate associated with a given state block.

        Find a `StandardStateBlock` within the fusion engine matching `block_label`, and change its
        current estimate vector. Note that this function may lead to performance degradation with
        some implementations and thus its use is discouraged if other options are available.
        """
        pass

    def set_state_block_covariance(self, block_label: str, covariance: NDArray) -> None:
        """
        Update the covariance associated with a given state block.

        Find a `StandardStateBlock` within the fusion engine matching `block_label`, and change its
        current covariance matrix. Note that this function may lead to performance degradation with
        some implementations and thus its use is discouraged if other options are available.
        """
        pass

    def set_state_block_cross_covariance(
        self, block_label1: str, block_label2: str, covariance: NDArray
    ) -> None:
        """
        Update the covariance between two state blocks.

        Find the `StandardStateBlock`s within the fusion engine matching `block_label1` and
        `block_label2`, and change the current covariance matrix between them. Note that this
        function may lead to performance degradation with some implementations and thus its use is
        discouraged if other options are available.
        """
        pass

    def remove_state_block(self, block_label: str) -> None:
        """
        Remove the `StandardStateBlock` matching `block_label`.

        This will reduce the state vector being estimated by the number of states that the block
        represents.
        """
        pass

    def get_virtual_state_block_target_labels(self) -> List[str] | None:
        """
        Gets a list of the target labels of virtual state blocks that have been added.

        A label being returned by this list is not a guarantee that the virtual state block has a
        valid source. For that, call has_virtual_state_block().

        Returns None if no virtual state blocks have been added to this fusion engine.
        """
        pass

    def has_virtual_state_block(self, vsb_target_label: str) -> bool:
        """
        Returns true if the fusion engine has a `VirtualStateBlock` with a matching target label.

        Will return false if no virtual state block with matching target label exists or if one
        exists but is not capable of generating an estimate. That is, the VSB's source must exist
        and be in a continuous chain to a concrete state block which also exists in the fusion
        engine in order to return true.
        """
        pass

    def add_virtual_state_block(self, virtual_state_block: VirtualStateBlock) -> None:
        """
        Add the given `VirtualStateBlock` to the fusion engine.

        A virtual state block (VSB) convert from an underlying block coordinate frame into the VSB
        coordinate frame.
        """
        pass

    def remove_virtual_state_block(self, vsb_target_label: str) -> None:
        """Remove the `VirtualStateBlock` matching `vsb_target_label`."""
        pass

    def get_measurement_processor_labels(self) -> List[str] | None:
        """
        Gets a list of the labels of measurement processors that have been added.

        Returns None if no measurement processors have been added to this fusion engine.
        """
        pass

    def has_processor(self, processor_label: str) -> bool:
        """Returns true if the fusion engine has a measurement processor with a matching label."""
        pass

    def add_measurement_processor(
        self, processor: StandardMeasurementProcessor
    ) -> None:
        """
        Add a StandardMeasurementProcessor.

        This can be used to process future measurements that correspond to `processor.get_label()`;
        """
        pass

    def remove_measurement_processor(self, processor_label: str) -> None:
        """
        Remove a StandardMeasurementProcessor previously added to the fusion engine.

        Assumes a measurement processor was previously added via #add_measurement_processor with the
        label `processor_label`.
        """
        pass

    def propagate(self, time: TypeTimestamp) -> None:
        """
        Propagate the filter estimate forward in time.

        May be evaluated lazily (when results are requested).
        """
        pass

    def update(self, processor_label: str, message: Message) -> None:
        """
        Update the filter with the given measurement.

        Will propagate first if needed to reach the time encoded inside the measurement.
        """
        pass

    def peek_ahead(
        self, time: TypeTimestamp, block_labels: List[str]
    ) -> EstimateWithCovariance | None:
        """
        Calculates the estimate and covariance at a requested time.

        Uses the state blocks listed in `block_labels`, without changing the state of the fusion
        engine or its underlying filter. Blocks are assembled in the order that the labels are
        passed in.

        `block_labels` is an array of strings.

        If all of the following are true:

        - `time` is equal to or after the filter time (which can be checked with #get_time)
        - all labels in `block_labels` correspond to a block that has been added to the fusion
            engine (which can be checked with #has_block)
        - `block_labels` has at least one element

        Then the result returned is guaranteed to not be None. Otherwise, if any of the above are
        false then the result will be None.
        """
        pass

    def generate_x_and_p(
        self, block_labels: List[str]
    ) -> EstimateWithCovariance | None:
        """
        Generates the current estimate and covariance.

        Estimate and covariance are built corresponding to a list of State Block labels. Blocks are
        assembled in the order that the labels are passed in.

        `block_labels` is an array of strings.

        If all of the following are true:

        - all labels in `block_labels` correspond to a block that has been added to the fusion
            engine (which can be checked with #has_block)
        - `block_labels` has at least one element

        Then the result returned is guaranteed to not be None. Otherwise, if any of the above are
        false then the result will be None.
        """

    def give_state_block_aux_data(self, block_label: str, aux: List[Message]) -> None:
        """Route a list of messages of aux data to a `StandardStateBlock`."""
        pass

    def give_measurement_processor_aux_data(
        self, processor_label: str, aux: List[Message]
    ) -> None:
        """Route a list of messages of aux data to a `StandardMeasurementProcessor`."""
        pass

    def give_virtual_state_block_aux_data(
        self, target_label: str, aux: List[Message]
    ) -> None:
        """Route a list of messages of aux data to a `VirtualStateBlock`."""
        pass

    def clone(self) -> "StandardFusionEngine":
        """
        Produce a deep-copy this fusion engine instance.

        All state blocks and measurement processors held by the fusion engine will also be cloned.
        The fusion strategy used by the fusion engine will also be cloned.
        """
        pass


class FusionPlugin(CommonPlugin, Protocol):
    """
    Plugin that provides a `CommonFusionEngine`.

    A fusion engine allows data from multiple sensors to be integrated into a unified state
    estimate.
    """

    def is_fusion_type_supported(self, type: FusionType) -> bool:
        """Return if the plugin supports a given type of fusion."""

    def new_fusion_engine(self, type: FusionType) -> CommonFusionEngine | None:
        """
        Create an instance of #CommonFusionEngine.

        The #FusionType parameter specifies the type of fusion that the returned value will support.
        For example, if the user passes in FUSION_STANDARD_MODEL, then the returned value will be a
        #StandardFusionEngine. Returns None if `type` is not supported by this fusion plugin
        (#is_fusion_type_supported can be used to check the type before calling this method).
        Otherwise the return is guaranteed to not be None.
        """
        pass
