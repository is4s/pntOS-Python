from dataclasses import dataclass

from .BaseConfig import BaseConfig


@dataclass
class DownsamplerConfig(BaseConfig):
    channels_to_downsample: list[str]
    """
    A list of channels to downsample
    """

    downsampling_factors: list[int]
    """
    List of downsampling factors to apply to the channels
    """

    group: str
