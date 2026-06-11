from dataclasses import dataclass, field

from .BaseConfig import BaseConfig

CONTROLLER_BUFFER_LENGTH_SEC = 2.0


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
        auto_shutdown (bool): If True, will automatically shut down once 'ready_to_shutdown'
            flag in 'controller/flags' group is set. Otherwise, will simply log a message
            informing the user the app is ready to shut down.
    """

    # INHERITED FIELDS
    group: str = field(default='config/controller', init=False)

    # UNIQUE FIELDS
    buffer_length_sec: float = CONTROLLER_BUFFER_LENGTH_SEC
    publish_interval: float | None = 1.0
    auto_shutdown: bool = True


@dataclass
class BuscatConfig(BaseConfig):
    """Config for BuscatControllerPlugin.

    Attributes:
        group (str): Inherited from BaseConfig. Registry group in which to store this config.
        output_transports (tuple[str, ...]): Identifiers of transport plugins through which to route output messages.
        auto_shutdown (bool): If True, will automatically shut down once 'ready_to_shutdown'
            flag in 'controller/flags' group is set. Otherwise, will simply log a message
            informing the user the app is ready to shut down.
    """

    # INHERITED FIELDS
    group: str = field(default='config/buscat', init=False)

    # UNIQUE FIELDS
    output_transports: tuple[str, ...] | None = None
    """Identifiers of transport plugins through which to route output messages."""

    auto_shutdown: bool = True
