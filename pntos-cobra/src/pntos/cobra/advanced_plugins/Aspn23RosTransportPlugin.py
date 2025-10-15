from threading import Thread
from typing import List

try:
    import rclpy  # type: ignore[import-not-found]
except ImportError as e:
    raise ImportError(
        'Is ROS installed and is its environment sourced? See the ROS usage '
        'tutorial in the documentation.'
    ) from e

try:
    from aspn23_ros_utils import AspnMsg, AspnRosNode  # type: ignore[import-not-found]
except ImportError as e:
    raise ImportError(
        'Is the ASPN-ROS environment sourced? See the ROS usage tutorial in '
        'the documentation.'
    ) from e

import contextlib

from rclpy.executors import (  # type: ignore[import-not-found]
    ExternalShutdownException,
    SingleThreadedExecutor,
)
from rclpy.node import Subscription  # type: ignore[import-not-found]
from rclpy.timer import Timer  # type: ignore[import-not-found]

from pntos.api import LoggingLevel, Mediator, Message, TransportPlugin


class Aspn23RosTransportPlugin(TransportPlugin):
    """An example ROS Transport Plugin for ASPN23 implemented in Python"""

    identifier: str
    aspn_ros_node: AspnRosNode
    mediator: Mediator
    executor: SingleThreadedExecutor
    thread: Thread

    def __init__(self, identifier: str):
        self.identifier = identifier
        self._subs: List[Subscription] = []
        self._topics: List[str] = []
        self._scan_timer: Timer

    def init_plugin(
        self,
        plugin_resources_location: str | None = None,
        mediator: Mediator | None = None,
    ) -> None:
        """
        PntOS plugin initialization function

        This is called by the pntOS system before calling any other function.
        """
        if mediator is not None:
            self.mediator = mediator
        if not rclpy.ok():
            rclpy.init()

        self.executor = SingleThreadedExecutor()
        self.aspn_ros_node = AspnRosNode('aspn23_ros_transport')
        self.executor.add_node(self.aspn_ros_node)

        def execute() -> None:
            with contextlib.suppress(ExternalShutdownException):
                self.executor.spin()

        self.thread = Thread(target=execute)

    def shutdown_plugin(self) -> None:
        """
        PntOS plugin shutdown function

        This is called by the pntOS system when it is done with the plugin.
        """
        self.stop_listening()

        self.executor.shutdown()
        rclpy.try_shutdown()
        self.thread.join()

        self.aspn_ros_node.destroy_node()
        self.mediator.log_message(
            LoggingLevel.INFO, f'Shutdown plugin for {self.identifier}.'
        )

    def _scan_for_topics(self) -> None:
        topic_info = self.aspn_ros_node.get_topic_names_and_types()
        topics = [
            topic
            for topic, msg_types in topic_info
            if 'aspn' in msg_types[0] and 'cobra' not in topic and 'pntos' not in topic
        ]
        for topic in topics:
            if topic in self._topics:
                continue
            self._subs.append(
                self.aspn_ros_node.subscribe_aspn(
                    lambda msg, topic=topic: self.mediator.process_pntos_message(
                        Message(msg, topic),
                    ),
                    topic,
                )
            )
            self._topics.append(topic)
            self.mediator.log_message(
                LoggingLevel.DEBUG, f'Subscribed to ROS topic {topic}.'
            )

    def start_listening(self) -> None:
        """Begin listening for ROS messages"""

        self._scan_timer = self.aspn_ros_node.create_timer(0.01, self._scan_for_topics)
        self.thread.start()
        self.mediator.log_message(LoggingLevel.INFO, 'ROS transport started.')

    def stop_listening(self) -> None:
        """Shut down all ROS subscriptions belonging to this plugin"""
        self._scan_timer.cancel()
        for sub in self._subs:
            self.aspn_ros_node.destroy_subscription(sub)
        self._subs.clear()
        self.mediator.log_message(LoggingLevel.INFO, 'ROS transport stopped.')

    def broadcast_message(
        self, message: Message, channel_name: str | None = None
    ) -> None:
        """Publish a ROS message"""
        if not isinstance(message.wrapped_message, AspnMsg):
            self.mediator.log_message(
                LoggingLevel.ERROR,
                f'Cannot publish message of type {type(message.wrapped_message)} on '
                f'topic {channel_name}.',
            )
            return
        if channel_name is None:
            self.mediator.log_message(
                LoggingLevel.WARN,
                'No channel name specified (required in this implementation).',
            )
            return
        if '-' in channel_name:
            self.mediator.log_message(
                LoggingLevel.WARN,
                f'Channel name {channel_name} has dashes, which are not supported in '
                f'ROS. Replacing with underscores.',
            )
            channel_name = channel_name.replace('-', '_')
        self.aspn_ros_node.publish_aspn(message.wrapped_message, channel_name)
