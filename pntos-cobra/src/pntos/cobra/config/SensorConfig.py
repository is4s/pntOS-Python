from dataclasses import dataclass


@dataclass
class SensorConfig:
    lever_arm: tuple[float, float, float]
    orientation: tuple[float, float, float, float]
    source_identifier: str  # e.g. LCM channel name
    destination_identifier: str  # e.g. Measurement Processor `identifier` field
    use_for_alignment: bool
    sensor_name: str
    group: str = '/config/cobra/sensor_config/default'
