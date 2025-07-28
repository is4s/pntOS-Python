from dataclasses import dataclass
from enum import Enum

from .BaseConfig import BaseConfig


class AspnVersion(Enum):
    """
    Available versions for ASPN messages.
    """

    V2 = 0
    """
    ASPN 2.2 Release
    """

    V23 = 1
    """
    ASPN 2023 Release
    """


@dataclass
class LcmTransportConfig(BaseConfig):
    """
    Configuration that dictates the version of ASPN messages broadcasted by the LcmTransportPlugin.
    """

    output_version: AspnVersion
    """
    The version of ASPN messages broadcasted by the LcmTransportPlugin.
    """

    group: str
