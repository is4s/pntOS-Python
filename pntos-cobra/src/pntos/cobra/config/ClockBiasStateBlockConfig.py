from dataclasses import dataclass

from pntos.api import EstimateWithCovariance

from .OrchestrationConfig import StateBlockConfig


@dataclass(kw_only=True)
class ClockBiasStateBlockConfig(StateBlockConfig):
    """
    Configuration for the ClockBiasStateBlock, provided by GpsInsStateModelingPlugin.

    Attributes:
        group (str):
            Inherited from StateBlockConfig. The registry group in which to store this config.
        identifer (str):
            Inherited from StateBlockConfig. The identifier associated with the type of state block to use.
        label (str):
            Inherited from StateBlockConfig. The unique label to associate with the instance of ClockBiasStateBlock added to the fusion engine.
        estimate_with_covariance (EstimateWithCovariance | None):
            Inerhtied from StateBlockConfig. The initial estimate and covariance of the clock bias states.
        h_0 (float):
            White noise coefficient of allan deviation.
        h_neg2 (float):
            Random walk coefficient of allan deviation.
        q3 (float | None):
            Optional q3 value for the third state. If None, will use a 2-state model.

    """

    # INHERITED FIELDS
    group: str
    identifier: str
    label: str
    estimate_with_covariance: EstimateWithCovariance | None

    # UNIQUE FIELDS
    h_0: float
    h_neg2: float
    q3: float | None = None
