from abc import ABC
from dataclasses import dataclass


@dataclass
class BaseConfig(ABC):
    """
    A basic config that all other configs should inherit from.
    """

    group: str
    """
    A user-defined config group name, corresponding to a group in the registry.

    When a config object is stored in the registry, this field determines
    which group in the registry the object's fields will be stored in.
    """
