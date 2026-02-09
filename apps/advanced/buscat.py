#!/usr/bin/env python3

# API imports
import sys

from pntos.api import LoggingLevel

# Import Cobra plugins and config structs
from pntos.cobra import (
    BuscatControllerPlugin,
    LcmLogTransportPlugin,
    StandardLoggingPlugin,
    StandardRegistryPlugin,
)
from pntos.cobra.config import (
    AspnVersion,
    BuscatConfig,
    LcmLogTransportConfig,
)
from pntos_python_datasets import ASPN2_EXAMPLE_LCM_LOG

OUTPUT_LOG = sys.argv[1] if len(sys.argv) > 1 else 'pntos_output.log'

# Config setup
my_config = [
    BuscatConfig(group='buscat', output_transports=('Cobra LCM Log Transport Plugin',)),
    LcmLogTransportConfig(
        group='config/lcm_log_transport',
        output_version=AspnVersion.V23,
        input_file=ASPN2_EXAMPLE_LCM_LOG,
        output_file=OUTPUT_LOG,
    ),
]
# End Config

# Instantiate all of our plugins
controller = BuscatControllerPlugin('Buscat Controller Plugin')
plugins = [
    LcmLogTransportPlugin('Cobra LCM Log Transport Plugin'),
    StandardLoggingPlugin(
        'Cobra Standard Logging Plugin',
        global_log_level=LoggingLevel.INFO,  # Switch to `DEBUG` for more informative log output
    ),
    StandardRegistryPlugin('Cobra Standard Registry Plugin', config=my_config),
]

# Start the controller, and pass it all of the other plugins to use
controller.init_plugin()
controller.take_control(plugins)
