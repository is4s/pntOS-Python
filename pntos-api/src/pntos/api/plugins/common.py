from dataclasses import dataclass
from enum import Enum
from typing import Callable, List, Optional, Protocol

from aspn23.aspn_base import AspnBase
from aspn23.type_timestamp import TypeTimestamp
from numpy import float64
from numpy.typing import NDArray


@dataclass
class Message:
    wrapped_message: AspnBase
    source_identifier: str


EstimateWithCovarianceType = Enum(
    "EstimateWithCovarianceType", ["PNTOS_EWC_GENERIC", "PNTOS_EWC_ATTITUDE_QUAT"]
)


@dataclass
class EstimateWithCovariance:
    type: EstimateWithCovarianceType
    estimate: NDArray[float64]


PluginTypes = Enum(
    "PluginTypes",
    [
        "PNTOS_UNDEFINED_PLUGIN",
        "PNTOS_CONTROLLER_PLUGIN",
        "PNTOS_FUSION_PLUGIN",
        "PNTOS_FUSION_STRATEGY_PLUGIN",
        "PNTOS_PLATFORM_INTEGRATION_PLUGIN",
        "PNTOS_INITIALIZATION_PLUGIN",
        "PNTOS_DATABASE_PLUGIN",
        "PNTOS_TRANSPORT_PLUGIN",
        "PNTOS_UI_PLUGIN",
        "PNTOS_ORCHESTRATION_PLUGIN",
        "PNTOS_ORCHESTRATION_STRATEGY_PLUGIN",
        "PNTOS_REGISTRY_PLUGIN",
        "PNTOS_INERTIAL_PLUGIN",
        "PNTOS_STATE_MODELING_PLUGIN",
        "PNTOS_LOGGING_PLUGIN",
        "PNTOS_UTILITY_PLUGIN",
        "PNTOS_PREPROCESSOR_PLUGIN",
    ],
)


FusionType = Enum(
    "FusionType",
    [
        "PNTOS_FUSION_STANDARD_MODEL",
        "PNTOS_FUSION_SAMPLED_MODEL",
        "PNTOS_FUSION_TIME_DELAYED_MODEL",
        "PNTOS_FUSION_STANDARD_COMPILED_MODEL",
    ],
)

LoggingLevel = Enum(
    "LoggingLevel",
    [
        "PNTOS_LOG_LEVEL_ERROR",
        "PNTOS_LOG_LEVEL_WARN",
        "PNTOS_LOG_LEVEL_INFO",
        "PNTOS_LOG_LEVEL_DEBUG",
    ],
)


KeyValueStoreDataFormat = Enum(
    "KeyValueStoreDataFormat", ["PNTOS_KV_STORE_INI", "PNTOS_KV_STORE_UNSPECIFIED"]
)


class KeyValueStore(Protocol):
    def get_key_array(self) -> List[str]:
        pass

    def has_key(self, key: str) -> bool:
        pass

    def get_str(self, key: str) -> Optional[str]:
        pass

    def get_str_array(self, key: str) -> List[str]:
        pass

    def get_int(self, key: str) -> int:
        pass

    def get_bool(self, key: str) -> bool:
        pass

    def get_double(self, key: str) -> float:
        pass

    def get_double_array(self, key: str) -> NDArray[float64]:
        pass

    def get_message(self, key: str) -> Optional[Message]:
        pass

    def get_raw(self, key: Optional[str]) -> Optional[bytes]:
        pass

    def set_str(self, key: str, value: str) -> None:
        pass

    def set_str_array(self, key: str, value: List[str]) -> None:
        pass

    def set_int(self, key: str, value: int) -> None:
        pass

    def set_bool(self, key: str, value: bool) -> None:
        pass

    def set_double(self, key: str, value: float) -> None:
        pass

    def set_double_array(self, key: str, value: NDArray[float64]) -> None:
        pass

    def set_message(self, key: str, value: Optional[Message]) -> None:
        pass

    def set_raw(self, key: Optional[str], bytes: bytes) -> None:
        pass

    def remove_key(self, key: str) -> bool:
        pass

    def batch_end(self) -> None:
        pass

    def batch_restart(self) -> None:
        pass

    def request_notify(
        self,
        key: Optional[str],
        callback: Callable[[str, List[str], "KeyValueStore"], int],
    ) -> bool:
        pass

    def remove_notify(
        self,
        key: Optional[str],
        callback: Callable[[str, List[str], "KeyValueStore"], int],
    ) -> bool:
        pass

    def set_permanent(self, permanent: bool) -> bool:
        pass

    data_format: KeyValueStoreDataFormat


class Registry(Protocol):
    def batch_start(self, group: str) -> KeyValueStore:
        pass

    def get_group_array(self) -> List[str]:
        pass

    def has_group(self, group: str) -> bool:
        pass

    def request_notify_new_group(self, callback: Callable[[str], None]) -> bool:
        pass


class Mediator(Protocol):
    def get_filter_description_list(self) -> List[str]:
        pass

    def request_solutions(
        self, solution_times: List[TypeTimestamp], filter_description: Optional[str]
    ) -> List[Message]:
        pass

    def process_pntos_message(self, message: Message) -> None:
        pass

    def broadcast_aspn_message(
        self,
        message: Message,
        transport: Optional[str],
        destination_identifier: Optional[str],
    ) -> None:
        pass

    def log_message(self, level: LoggingLevel, message: str) -> None:
        pass

    registry: Registry


class CommonPlugin(Protocol):
    def init_plugin(
        self, plugin_resources_location: Optional[str], mediator: Optional[Mediator]
    ) -> None:
        pass

    def shutdown_plugin(self) -> None:
        pass

    identifier: str
