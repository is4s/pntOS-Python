from dataclasses import dataclass
from enum import IntEnum

from aspn23_xtensor import AspnMessageType

from .BaseConfig import BaseConfig


class BufferMode(IntEnum):
    IMMEDIATE = 0
    SEQUENCED = 1


@dataclass
class Stream(BaseConfig):
    group: str
    message_type: AspnMessageType
    source_identifier: str | None = None


@dataclass
class StreamConfig(BaseConfig):
    """Configuration for orchestration plugin's message StreamConfig.

    Args:
        group: Inherited from BaseConfig. Registry group in which to store this config.
        default_buffer_mode: Default buffer mode (immediate or sequenced). Defaults to
            sequenced.
        override: If default buffer mode is sequenced, this parameter can be used to
            specify the message types and channels to immedate-stream. Alternatively, if
            default buffer mode is immediate, this parameter specifies the message types
            and channels to buffer. Note that each element in this tuple can provide a
            message type or a type + source ID combination.
    """

    group: str
    default_buffer_mode: BufferMode = BufferMode.SEQUENCED
    override_streams: tuple[Stream, ...] | None = None


IMU_STREAM = Stream(
    group='config/imu_stream',
    message_type=AspnMessageType.ASPN_MEASUREMENT_IMU,
)

# Default stream config. Buffers all message types except IMU.
DEFAULT_STREAM_CONFIG = StreamConfig(
    group='config/stream_config',
    override_streams=(IMU_STREAM,),
)
