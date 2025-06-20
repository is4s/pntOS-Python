from dataclasses import dataclass

from .BaseConfig import BaseConfig


@dataclass
class TimeAdjusterConfig(BaseConfig):
    """
    Configuration for the time adjuster preprocessor.
    """

    channel_to_correct: str
    """
    The name of the channel to correct.
    """

    expected_dt_nsec: int
    """
    The expected time between messages in nanoseconds.

    For example, a 100 Hz sensor sends 100 messages per second which is 0.01 seconds per message (interval in seconds).
    Convert that to nanoseconds like so `int(0.01 * 1e9)`.
    """

    group: str
