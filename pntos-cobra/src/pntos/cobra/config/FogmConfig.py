from dataclasses import dataclass

from .BaseConfig import BaseConfig


@dataclass
class FogmConfig(BaseConfig):
    """
    First-Order Gauss-Markov (FOGM) error model.
    """

    group: str

    sigma: tuple[float, ...]
    """
    The steady-state sigma(s) in application-specific units.
    """

    tau: tuple[float, ...]
    """
    The time constant(s) in seconds.
    """
