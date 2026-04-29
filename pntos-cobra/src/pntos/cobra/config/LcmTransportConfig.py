from dataclasses import dataclass, field
from enum import IntEnum

from .BaseConfig import BaseConfig


class AspnVersion(IntEnum):
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
    """Configuration for LcmTransportPlugin.

    Attributes:
        group (str): Inherited from BaseConfig. The registry group in which to store this config.
        output_version (AspnVersion): The version of ASPN messages to output.
        url (str): LCM URL to which the transport should connect. Will subscribe and publish to this address.
        subscribe_to (str): A regex string indicating which channels to which the transport should subscribe.
    """

    group: str = field(default='config/lcm_transport', init=False)
    output_version: AspnVersion
    url: str = 'tcpq://'
    subscribe_to: str = '^((?!pntos).)*$'


@dataclass
class LcmLogTransportConfig(BaseConfig):
    """
    Configuration for LcmLogTransportPlugin, which processes messages from an LCM log.
    """

    group: str = field(default='config/lcm_log_transport', init=False)

    input_file: str
    """
    The path of the LCM log to be processed.
    """

    output_file: str
    """
    The path of the LCM log to which the transport should record messages.

    NOTE: If output_file already exists, it will be overwritten. Thus, it must be different from input_file.
    """

    output_version: AspnVersion
    """
    The version of ASPN messages broadcasted by the LcmLogTransportPlugin.
    """

    channels_to_process: tuple[str, ...] | None = None
    """
    List of channels to process. If None, will process all channels.
    """

    record_input_channels: bool = True
    """
    Flag to control whether input channels are written to the output log.

    NOTE: The default is set to True. When enabled, the output log will contain any sensor or truth channels from the input log that may be required for postprocessing.
    """
