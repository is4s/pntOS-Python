from dataclasses import dataclass

from .BaseConfig import BaseConfig


@dataclass
class UiLogPlottingConfig(BaseConfig):
    """
    Defines the LCM or ROS log file for plotting and the solution and truth PVA channels.
    """

    group: str

    logfile: str
    """
    The name of the LCM or ROS log file to be plotted.
    """

    solution_channel: str
    """
    The PVA solution channel.
    """

    truth_channel: str
    """
    The PVA truth channel.
    """
