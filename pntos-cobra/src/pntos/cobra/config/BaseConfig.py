from dataclasses import dataclass
from typing import Protocol


@dataclass
class BaseConfig(Protocol):
    group: str
