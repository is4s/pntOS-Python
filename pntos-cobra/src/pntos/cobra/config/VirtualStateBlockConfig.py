from dataclasses import dataclass, field

from .BaseConfig import BaseConfig


@dataclass(kw_only=True)
class VirtualStateBlockConfig(BaseConfig):
    """
    Configuration used to generate a new virtual state block.
    """

    group: str

    identifier: str
    """
    An identifier that determines the type of virtual state block to use.

    This field will be matched against the `virtual_block_identifiers` field on the state model provider.
    """

    source: str
    """
    The label associated with state representation this virtual state block can transform from.
    """

    target: str
    """
    The label that describes the state representation this virtual state block can transform to.

    This label should be unique from all other `pntos.cobra.config.VirtualStateBlockConfig.target`
    and `pntos.cobra.config.StateBlockConfig.label` values.
    """

    aux_channels: tuple[str, ...] | None = None
    """
    Optional channels to map to this block's `receive_aux_data` method.

    The following channel strings are reserved:
        - INERTIAL_PVA: Should be added to `aux_channels` if this virtual state block needs the inertial PVA as aux data.
        - INERTIAL_FORCES_AND_RATES: Should be added to `aux_channels` if this virtual state block needs the inertial forces and/or rates as aux data.
    """


@dataclass(kw_only=True)
class PinsonErrorToStandardVSBConfig(VirtualStateBlockConfig):
    """
    Configuration used to generate a new PinsonErrorToStandard virtual state block.
    """

    group: str

    identifier: str = field(default='pinson_error_to_standard', init=False)

    source: str

    target: str

    aux_channels: tuple[str, ...] | None = field(default=('INERTIAL_PVA',), init=False)


@dataclass(kw_only=True)
class StateExtractorConfig(VirtualStateBlockConfig):
    """
    Configuration used to generate a new StateExtractor Virtual State Block.
    """

    # INHERITED FIELDS
    group: str

    identifier: str = field(default='state_extractor', init=False)

    source: str

    target: str

    aux_channels: tuple[str, ...] | None = field(default=None, init=False)

    # UNIQUE FIELDS
    incoming_state_size: int
    """
    The number of states in the state block `source` refers to
    """

    indices_to_extract: tuple[int, ...]
    """
    The series of indices that correspond to the states to extract from `source` and comprise `target`
    """
