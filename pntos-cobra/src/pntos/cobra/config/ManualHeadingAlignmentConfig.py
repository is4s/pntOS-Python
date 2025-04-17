from dataclasses import dataclass

from .BaseConfig import BaseConfig


@dataclass
class ManualHeadingAlignmentConfig(BaseConfig):
    heading: float
    heading_sigma: float
    group: str
