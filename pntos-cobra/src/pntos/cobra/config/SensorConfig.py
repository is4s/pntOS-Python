from dataclasses import dataclass

from .BaseConfig import BaseConfig


@dataclass
class SensorConfig(BaseConfig):
    group: str

    lever_arm: tuple[float, float, float]
    orientation: tuple[float, float, float, float]
    source_identifier: str  # e.g. LCM channel name
    destination_identifier: str  # e.g. Measurement Processor `identifier` field
    use_for_alignment: bool
    sensor_name: str
