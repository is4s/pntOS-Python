#!/usr/bin/env python3
import asyncio

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


# Set up a function to run the plugins with a non-blocking timer
async def run_cobra() -> None:
    # pass the controller all of the other plugins to use
    controller.take_control(plugins)
    await asyncio.sleep(5)


# Let the plugins run and clean up when done/interrupted
try:
    asyncio.run(run_cobra())
except KeyboardInterrupt:
    pass
finally:
    controller.shutdown_plugin()
