from dataclasses import dataclass
from typing import Tuple


@dataclass
class SensorConfig:
    lever_arm: Tuple[float, float, float]
    orientation: Tuple[float, float, float, float]
    source_identifier: str  # e.g. LCM channel name
    destination_identifier: str  # e.g. Measurement Processor `identifier` field
    use_for_alignment: bool
    sensor_name: str
    group: str = "/config/cobra/sensor_config/default"
