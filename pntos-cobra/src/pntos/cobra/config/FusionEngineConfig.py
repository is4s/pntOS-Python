from dataclasses import dataclass, field

from .BaseConfig import BaseConfig


@dataclass(kw_only=True)
class FusionEngineConfig(BaseConfig):
    """Configuration for StandardFusionEngine.

    Attributes:
        save_x_and_p_after_prop: Whether to save state estimate and sigma to registry right after each propagate.
        save_x_and_p_after_update: Whether to save state estimate and sigma to registry right after each update.
    """

    group: str = field(default='config/fusion_engine', init=False)

    save_x_and_p_after_prop: bool = False
    """Whether to save state estimate and sigma to registry right after each propagate.

    The following key-value pairs will be recorded to the `diagnostics` registry group:
        - `state_labels`: An array of labels associated with each state in the form
          "{state_block_label}_state{state_index}".
        - `time`: Current time in nanoseconds
        - `estimate`: Current estimate vector
        - `sigma`: Current 1-sigma estimate uncertainty

    Enabling this feature could allow another plugin (such as a UI plugin or utility
    plugin) to grab this information and display or record it in some manner.
    """

    save_x_and_p_after_update: bool = False
    """Whether to save state estimate and sigma to registry right after each update.

    The following key-value pairs will be recorded to the `diagnostics` registry group:
        - `state_labels`: An array of labels associated with each state in the form
          "{state_block_label}_state{state_index}".
        - `time`: Current time in nanoseconds
        - `estimate`: Current estimate vector
        - `sigma`: Current 1-sigma estimate uncertainty

    Enabling this feature could allow another plugin (such as a UI plugin or utility
    plugin) to grab this information and display or record it in some manner.
    """
