from dataclasses import dataclass, field

from pntos.api import EstimateWithCovariance

from .OrchestrationConfig import StateBlockConfig


@dataclass(kw_only=True)
class ClockBiasStateBlockConfig(StateBlockConfig):
    """
    Configuration for the ClockBiasStateBlock, provided by StandardStateModelingPlugin.

    Attributes:
        group (str):
            Inherited from StateBlockConfig. The registry group in which to store this config.
        identifier (str):
            Inherited from StateBlockConfig. The identifier associated with the type of
            state block to use. This field is set to a constant value of `clock_bias`,
            the identifier used to select the ClockBiasStateBlock in the
            StandardStateModelingPlugin.
        label (str):
            Inherited from StateBlockConfig. The unique label to associate with the instance of ClockBiasStateBlock added to the fusion engine.
        estimate_with_covariance (EstimateWithCovariance | None):
            Inherited from StateBlockConfig. The initial estimate and covariance of the clock bias states.
        aux_channels (tuple[str, ...] | None):
            Optional channels to map to this state block's `receive_aux_data` method.
            This field is set to a constant value of None, since the ClockBiasStateBlock
            does not require aux data.
        h_0 (float):
            White noise coefficient of allan deviation.
        h_neg2 (float):
            Random walk coefficient of allan deviation.
        q3 (float | None):
            Optional q3 value for the third state. If None, will use a 2-state model.

    """

    # INHERITED FIELDS
    group: str
    identifier: str = field(default='clock_bias', init=False)
    label: str
    estimate_with_covariance: EstimateWithCovariance | None
    aux_channels: tuple[str, ...] | None = field(default=None, init=False)

    # UNIQUE FIELDS
    h_0: float
    h_neg2: float
    q3: float | None = None
