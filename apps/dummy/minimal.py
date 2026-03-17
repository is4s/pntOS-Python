#!/usr/bin/env python3

# Import Cobra plugins and config structs
from pntos.cobra import (
    DummyControllerPlugin,
    DummyOrchestrationPlugin,
    DummyTransportPlugin,
)

# Instantiate all of our plugins
controller = DummyControllerPlugin('Cobra Dummy Controller Plugin')
plugins = [
    DummyTransportPlugin('Cobra Dummy Transport Plugin'),
    DummyOrchestrationPlugin('Cobra Dummy Orchestration Plugin'),
]

# Start the controller
controller.init_plugin()

# Give the controller control, and pass it the list of other plugins
controller.take_control(plugins)
