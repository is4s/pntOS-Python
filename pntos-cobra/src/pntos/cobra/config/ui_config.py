from dataclasses import dataclass, field

from .BaseConfig import BaseConfig


@dataclass
class UiLogPlottingConfig(BaseConfig):
    """
    Defines the LCM or ROS log file for plotting and the solution and truth PVA channels.
    """

    group: str = field(default='config/ui_logfile_plotting', init=False)

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


@dataclass
class ExperimentalCobraUiConfig(BaseConfig):
    """Configuration for CobraUiPlugin."""

    group: str  # Inherited field
    static_folder: str = 'pntos-cobra/src/pntos/cobra/standard_plugins/ui/_static/dist'
    """
    Path to static folder to serve. Any uploaded files will be saved in
    ``{static_folder}/uploads/``. Additionally, any files in this directory will be
    available to the web interface - do not put sensitive data here.
    """
    cors_allowed_origins: tuple[str, ...] = (
        'http://localhost:5000',
        'http://127.0.0.1:5000',
    )
    """
    CORS allowed origins for WebSocket connections.
    Examples: ['http://localhost:3000', 'https://example.com']
    """
    host: str = 'localhost'
    """Host address to bind the web server to."""
    port: int = 5000
    """Port to run the web server on."""
    send_throttle: int = 30
    """Maximum number of registry updates to send to the front-end every second."""
