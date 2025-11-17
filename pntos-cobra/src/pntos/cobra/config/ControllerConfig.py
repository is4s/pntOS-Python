from dataclasses import dataclass

from .BaseConfig import BaseConfig


@dataclass
class ControllerConfig(BaseConfig):
    """Config for SimpleControllerPlugin.

    Attributes:
        group (str): Inherited from BaseConfig. Registry group in which to store this config.
        publish_interval (float): Minimum time (in seconds) between requesting solutions
            from orchestration. If None, will not request any solution.
    """

    # INHERITED FIELDS
    group: str

    # UNIQUE FIELDS
    publish_interval: float | None = 1.0
