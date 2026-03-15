"""Base mode class, parameters, and dispatch registry."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Type

from actions import GameActions
from macro_logger import MacroLogger


@dataclass
class ModeParams:
    target_level: int
    use_shards: bool = False


@dataclass
class HiddenModeParams(ModeParams):
    auto_sell: bool = False


MODE_REGISTRY: dict[str, Type["BaseMode"]] = {}


def register_mode(mode_id: str):
    """Decorator to register a mode class in the dispatch table."""
    def decorator(cls: Type["BaseMode"]) -> Type["BaseMode"]:
        MODE_REGISTRY[mode_id] = cls
        return cls
    return decorator


class BaseMode(ABC):
    def __init__(
        self,
        actions: GameActions,
        logger: MacroLogger,
        params: ModeParams,
    ) -> None:
        self._actions = actions
        self._logger = logger
        self._params = params

    @abstractmethod
    def run(self) -> None:
        ...
