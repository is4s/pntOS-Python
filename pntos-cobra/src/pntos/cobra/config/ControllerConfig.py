from dataclasses import dataclass

from .BaseConfig import BaseConfig


@dataclass
class ControllerConfig(BaseConfig):
    """Config for StandardControllerPlugin.

    Attributes:
        group (str): Inherited from BaseConfig. Registry group in which to store this config.
        buffer_length_sec (float): Length of measurement buffer (in seconds). Any measurements
            that are sequenced-streamed and not immediate-streamed will be buffered for this
            amount of time before being passed to the orchestration plugin.
        publish_interval (float): Minimum time (in seconds) between requesting solutions
            from orchestration. If None, will not request any solution.
    """

    # INHERITED FIELDS
    group: str

    # UNIQUE FIELDS
    buffer_length_sec: float = 2.0
    publish_interval: float | None = 1.0


@dataclass
class BuscatConfig(BaseConfig):
    """Config for BuscatControllerPlugin.

    Attributes:
        group (str): Inherited from BaseConfig. Registry group in which to store this config.
        output_transport (tuple[str, ...]): Identifiers of transport plugins through which to route output messages.
    """

    # INHERITED FIELDS
    group: str
    """Inherited from BaseConfig. Registry group in which to store this config."""

    # UNIQUE FIELDS
    output_transports: tuple[str, ...]
    """Identifiers of transport plugins through which to route output messages."""
