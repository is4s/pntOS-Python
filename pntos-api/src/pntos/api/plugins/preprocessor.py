from typing import List, Optional, Protocol

from .common import CommonPlugin, Message


class Preprocessor(Protocol):
    def process_pntos_message(self, message: Message) -> List[Message]:
        pass


class PreprocessorPlugin(CommonPlugin, Protocol):
    preprocessor_identifiers: List[str]

    def new_preprocessor(
        self, preprocessor_index: int, config_group: Optional[str]
    ) -> Preprocessor:
        pass
