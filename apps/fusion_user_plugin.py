# Grab the plugins we want off the shelf

from threading import Thread
from time import sleep

from aspn23.measurement_position import MeasurementPosition
from pntos.api import TransportPlugin
from pntos.api.plugins.common import Mediator, Message
from pntos.cobra import (
    SimpleControllerPlugin,
    SimpleOrchestrationPlugin,
    SimpleRegistryPlugin,
)
from pntos.cobra.config import AlignmentConfig, ImuConfig, SensorConfig

# Set up configuration parameters

my_config = [
    ImuConfig(
        accel_bias_sigma=(0.0098, 0.0098, 0.0098),
        accel_bias_tau=(3600.0, 3600.0, 3600.0),
        accel_rw_sigma=(0.001, 0.001, 0.001),
        gyro_bias_sigma=(1.234e-6, 1.234e-6, 1.234e-6),
        gyro_bias_tau=(3600.0, 3600.0, 3600.0),
        gyro_rw_sigma=(0.001, 0.001, 0.001),
    ),
    AlignmentConfig(
        initialPosCov=(9.0, 9.0, 9.0),
        initialVelCov=(0.1, 0.1, 0.1),
        initialTiltCov=(0.01, 0.01, 0.01),
        initialAccelBiasCov=(9.604e-5, 9.604e-5, 9.604e-5),
        initialGyroBiasCov=(2.3504074e-11, 2.3504074e-11, 2.3504074e-11),
    ),
    SensorConfig(
        lever_arm=(0.0, 0.0, 0.0),
        orientation=(0.0, 0.0, 0.0, 0.0),
        source_identifier="lcm://cobranav/novatel",
        destination_identifier="gps_measurement_processor",
        use_for_alignment=True,
        sensor_name="novatel",
    ),
]

# Define our own transport plugin


class MyTransportPlugin(TransportPlugin):
    def init_plugin(
        self, plugin_resources_location: str | None, mediator: Mediator | None
    ) -> None:
        assert mediator is not None
        # Save off the mediator to send messages to the system later
        self.mediator = mediator

    def shutdown_plugin(self) -> None:
        pass

    def start_listening(self) -> None:
        self.listening = True
        Thread(target=listen_for_messages).start()

    def stop_listening(self) -> None:
        self.listening = False

    def broadcast_message(self, message: Message, channel_name: str | None) -> None:
        pass

    mediator: Mediator
    listening: bool
    identifier: str = "my_transport_plugin"


def listen_for_messages(my_plugin: MyTransportPlugin):
    sleep(0.1)
    if my_plugin.listening:
        # Create a new ASPN measurement
        aspn_msg = MeasurementPosition(...)  # noqa: F841

        # Send a new ASPN message we've received to the system
        my_plugin.mediator.process_pntos_message(
            Message(aspn_msg, source_identifier="channel_foo")
        )


# Create all of our plugins

controller = SimpleControllerPlugin(identifier="my_controller")
orchestration = SimpleOrchestrationPlugin(identifier="my_orchestration")
registry = SimpleRegistryPlugin(identifier="my_registry", config=my_config)
custom_transport = MyTransportPlugin()

# Start the controller, and pass it all of the other plugins to use

controller.init_plugin(None, None)
controller.take_control([orchestration, registry, custom_transport], [], None)
