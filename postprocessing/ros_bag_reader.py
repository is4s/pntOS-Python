from collections import defaultdict
from dataclasses import dataclass, field

from aspn23 import MeasurementImu, MeasurementPositionVelocityAttitude

try:
    from aspn23_ros_utils import AspnMsg, from_ros_map  # type: ignore[import]
    from rclpy.serialization import deserialize_message  # type: ignore[import]
    from rosbag2_py import (  # type: ignore[import]
        ConverterOptions,
        SequentialReader,
        StorageOptions,
    )
    from rosidl_runtime_py.utilities import get_message  # type: ignore[import]
except ImportError as e:
    raise ImportError(
        'Is ROS installed and the ASPN-ROS environment sourced? See the ROS '
        'usage tutorial in the documentation.'
    ) from e


@dataclass
class TopicData:
    decode_class_name: str = ''
    data: list[AspnMsg] = field(default_factory=list)


class RosBagReader:
    DECODE_CLASS_NAME_MAP = {
        MeasurementImu: 'imu',
        MeasurementPositionVelocityAttitude: 'positionvelocityattitude',
    }

    def __init__(self, bagfile: str):
        if bagfile.endswith('.db3'):
            storage_id = 'sqlite3'
        elif bagfile.endswith('.mcap'):
            storage_id = 'mcap'
        else:
            raise ValueError(f'Invalid bagfile: {bagfile}.')

        storage_options = StorageOptions(uri=bagfile, storage_id=storage_id)
        converter_options = ConverterOptions(
            input_serialization_format='cdr', output_serialization_format='cdr'
        )

        self.reader = SequentialReader()
        self.reader.open(storage_options, converter_options)
        self.type_map = {
            topic.name: topic.type for topic in self.reader.get_all_topics_and_types()
        }

    def harvest_topics(self, topics: list[str]) -> dict[str, TopicData]:
        out = defaultdict(TopicData)
        while self.reader.has_next():
            topic, data, _ = self.reader.read_next()
            if topic not in topics:
                continue
            ros_msg_type = get_message(self.type_map[topic])
            ros_msg = deserialize_message(data, ros_msg_type)
            aspn_msg = from_ros_map[ros_msg_type](ros_msg)
            out[topic].decode_class_name = self.DECODE_CLASS_NAME_MAP[type(aspn_msg)]
            out[topic].data.append(aspn_msg)
        return out
