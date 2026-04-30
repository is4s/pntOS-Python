from dataclasses import dataclass, field

from pntos.api import EstimateWithCovariance

from .OrchestrationConfig import StateBlockConfig


@dataclass(kw_only=True)
class ConstantStateBlockConfig(StateBlockConfig):
    """
    Configuration for the ConstantStateBlock, provided by StandardStateModelingPlugin.

    Attributes:
        group (str):
            Inherited from StateBlockConfig. The registry group in which to store this config.
        identifier (str):
            Inherited from StateBlockConfig. The identifier associated with the type of
            state block to use. This field is set to a constant value of `constant`,
            the identifier used to select the ConstantStateBlock in the
            StandardStateModelingPlugin.
        label (str):
            Inherited from StateBlockConfig. The unique label to associate with the instance of ClockBiasStateBlock added to the fusion engine.
        estimate_with_covariance (EstimateWithCovariance | None):
            Inherited from StateBlockConfig. The initial estimate and covariance of the clock bias states.
        aux_channels (tuple[str, ...] | None):
            Optional channels to map to this state block's `receive_aux_data` method.
            This field is set to a constant value of None, since the ConstantStateBlock
            does not require aux data.
        Q (NDArray[float64] | None):
            Optional continuous time propagation noise covariance matrix. If None, no noise will be added during propagation.
    """

    # INHERITED FIELDS
    group: str
    identifier: str = field(default='constant', init=False)
    label: str
    estimate_with_covariance: EstimateWithCovariance | None
    aux_channels: tuple[str, ...] | None = field(default=None, init=False)

    # UNIQUE FIELDS
    Q: tuple[tuple[float, ...], ...] | None = None
