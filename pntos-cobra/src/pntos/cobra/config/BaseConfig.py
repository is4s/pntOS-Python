from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@runtime_checkable
@dataclass
class BaseConfig(Protocol):
    group: str
