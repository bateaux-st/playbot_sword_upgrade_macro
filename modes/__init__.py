"""Mode runners — import all modes to trigger registration."""

from modes.fusion import FusionMode
from modes.hidden import HiddenMode
from modes.money import MoneyMode
from modes.target import TargetMode
from modes.base import MODE_REGISTRY, ModeParams, HiddenModeParams

__all__ = [
    "MODE_REGISTRY",
    "ModeParams",
    "HiddenModeParams",
    "TargetMode",
    "HiddenMode",
    "MoneyMode",
    "FusionMode",
]
