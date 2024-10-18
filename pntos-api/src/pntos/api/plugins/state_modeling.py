"""Python API of pntOS."""

from typing import Protocol

from .common import CommonPlugin, FusionType
from .fusion import (
    StandardFusionEngine,
    StandardMeasurementProcessor,
    StandardStateBlock,
    VirtualStateBlock,
)


class CommonStateModelProvider(Protocol):
    """A collection of tools for modeling states and measurements."""

    engine_type: FusionType
    """The type of fusion model used by this state model provider"""


class StandardStateModelProvider(CommonStateModelProvider, Protocol):
    """
    A collection of tools for modeling states and measurements.

    These tools are used to model the propagation and innovation of state
    spaces using pntOS' standard fusion model. Specifically, a
    StandardStateModelProvider provides three types of tools:

    1. State Blocks - Define a set of states and a model for propagating those
       states
    2. Virtual State Blocks - Relate two statespaces to each other
    3. Measurement Processors - Relate measurements to a statespace

    A StandardStateModelProvider conceptually models a set of zero or more
    `StandardStateBlock`s and a set of zero or more
    `StandardMeasurementProcessor`s which together model the phenomenology of
    sensor data that is being brought into a fusion engine. The first type,
    state blocks, describe how a set of states propagates forward through time.
    The second type, measurement processors, describe how a measurement relates
    to a set of state blocks.

    Each StandardStateModelProvider consists of factory methods which generate
    instances of the state blocks and measurement processors it provides. The
    StandardStateModelProvider.new_block method is a factory method that
    returns a newly created state block on each invocation. Because the
    StandardStateModelProvider can provide more than one kind of state block,
    the StandardStateModelProvider.new_block method takes a `block_index`
    parameter which allows the user to request which kind of state block is
    created by the factory. `block_identifiers[i]` gives a description of the
    `i`th kind of state block returned when `block_index=i`.

    Similarly, StandardStateModelProvider.new_processor is a factory method for
    returning new measurement processors and `processor_identifiers` is a set
    of identifiers for each available kind of measurement processor that can be
    returned by the factory.
    """

    processor_identifiers: list[str]
    """
    A list of identifying strings for each kind of measurement processor that
    this StandardStateModelProvider can create instances of.

    The `processor_index` parameter of #new_processor is an index into this
    array.

    This field will be an empty list when this state model provider does not
    provide any measurement processors.
    """

    block_identifiers: list[str]
    """
    A list of identifying strings for each kind of state block that this
    StandardStateModelProvider can create instances of.

    The `block_index` parameter of #new_block is an index into this array.

    This field will be an empty list when this state model provider does not
    provide any state blocks.
    """

    virtual_block_identifiers: list[str]
    """
    A list of identifying strings for each kind of virtual state block that
    this StandardStateModelProvider can create instances of.

    The `virtual_block_index` parameter of #new_virtual_block is an index into
    this array.

    This field will be an empty list when this state model provider does not
    provide any virtual state blocks.
    """

    def new_processor(
        self,
        processor_index: int,
        engine: StandardFusionEngine | None,
        label: str,
        state_block_labels: list[str],
        config_group: str,
    ) -> StandardMeasurementProcessor | None:
        r"""
        Generate a newly created StandardMeasurementProcessor.

        This measurement processor describes the relationship between a
        measurement and a set of state blocks. Returns None when no measurement
        processor can be produced with the given \p processor_index, \p engine,
        and \p config_group.

        Args:
            processor_index: Since the StandardStateModelProvider can create
              different kinds of measurement processors, the \p processor_index
              parameter is used to select which kind of measurement processor
              to create a new instance of. The #processor_identifiers field
              contains identifying strings for the kinds of processors. For
              example, if the model can create 45 different processors, the
              identifier of the last processor that can be created is found in
              `processor_identifiers[44]`. An instance of this processor can be
              created by calling `new_processor(self, 44, ...)`. Note that `0
              <= processor_index < len(processor_identifiers)`.

            engine: An optional parameter that may be provided to the new
              processor, such that the processor may interact with the fusion
              engine it is being used in (for example, to add/remove states).
              Set it to None when no engine is available for the processor to
              use.

            label: A string which will be used to populate the `label` field of
              the newly created processor. This label will be the unique name
              for the returned instance of a processor, and used to track the
              processor throughout its lifecycle. Note that it differs from
              `processor_identifiers` which is the model's mechanism for
              selecting the *kind* of processor to create.

            state_block_labels: A list of strings which will be used to
              populate the `state_block_labels` field of the newly created
              processor.

            config_group: Indicates which (if any) parameter group in the
              registry may be used to obtain additional configuration values to
              generate the new processor. If the processor requires no outside
              configuration, \p config_group may be None.
        """
        pass

    def new_block(
        self,
        block_index: int,
        engine: StandardFusionEngine | None,
        label: str,
        config_group: str,
    ) -> StandardStateBlock | None:
        r"""
        Generate a newly created StandardStateBlock.

        This state block describes a set of states and how they propagate over
        time. The return value will be None when no state block can be produced
        with the given \p block_index, \p engine, and \p config_group.

        Args:
            block_index: Since the StandardStateModelProvider can create
              different kinds of state blocks, the \p block_index parameter is
              used to select which kind of state block to create a new instance
              of. The #block_identifiers field contains identifying strings for
              the kinds of state blocks. For example, if the model can create
              45 different state blocks, the identifier of the last state block
              that can be created is found in `block_identifiers[44]`. An
              instance of this state block can be created by calling
              `new_block(self, 44, ...)`. Note that `0 <= block_index <
              len(block_identifiers)`.

            engine: An optional parameter that may be provided to the new
              block, such that the block may interact with the fusion engine it
              is being used in (for example, to add/remove states). Set it to
              None when no engine is available for the block to use.

            label: A string which will be used to populate the `label` field
              of the newly created state block. This label will be the unique
              name for the returned instance of a state block, and used to
              track the state block throughout its lifecycle. Note that it
              differs from `block_identifiers` which is the model's mechanism
              for selecting the *kind* of state block to create.

            config_group: Indicates which (if any) parameter group in the
              registry may be used to obtain additional configuration values to
              generate the new state block. If the state block requires no
              outside configuration, \p config_group may be None.
        """
        pass

    def new_virtual_block(
        self,
        virtual_block_index: int,
        source_label: str,
        target_label: str,
        config_group: str,
    ) -> VirtualStateBlock | None:
        r"""
        Generate a newly created VirtualStateBlock.

        This virtual state block is used to convert a set of states from one
        representation to another. Returns None when no virtual state block can
        be produced with the given \p virtual_block_index and \p config_group.

        Args:
            virtual_block_index: Since the StandardStateModelProvider can
              create different kinds of virtual state blocks, the \p
              virtual_block_index parameter is used to select which kind of
              virtual state block to create a new instance of. The
              #virtual_block_identifiers field contains identifying strings for
              the kinds of virtual state blocks. For example, if the model can
              create 45 different virtual state blocks, the identifier of the
              last virtual state block that can be created is found in
              `virtual_block_identifiers[44]`. An instance of this virtual
              state block can be created by calling `new_virtual_block(self,
              44, ...)`. Note that `0 <= virtual_block_index <
              len(virtual_block_identifiers)`.

            source_label: The label of the state block or virtual state block
              whose states this virtual state block transforms.

            target_label: A unique identifier for this virtual state block.

            config_group: Indicates which (if any) parameter group in the
              registry may be used to obtain additional configuration values to
              generate the new virtual state block. If the virtual state block
              requires no outside configuration, \p config_group may be None.
        """
        pass


class StateModelingPlugin(CommonPlugin, Protocol):
    """A CommonPlugin subclass that generates CommonStateModelProviders."""

    def is_fusion_type_supported(self, type: FusionType) -> bool:
        """Return if the plugin supports a given type of fusion. See #FusionType."""
        pass

    def new_state_model_provider(
        self, type: FusionType
    ) -> CommonStateModelProvider | None:
        r"""
        Generate an instance of CommonStateModelProvider.

        Returns None if \p type is not supported (#is_fusion_type_supported can
        be used to check \p type).

        Args:
            type: Specifies the type of fusion that the returned value will
            support. For example, if the user passes in #STANDARD_MODEL, then
            the returned value will be castable to StandardStateModelProvider.

        Returns:
            CommonStateModelProvider: A state model provider of the specified
            FusionType.
        """
        pass
