"""Target enhancement mode — enhance to target level, then stop."""

from constants import MODE_TARGET
from modes.base import BaseMode, register_mode


@register_mode(MODE_TARGET)
class TargetMode(BaseMode):
    def run(self) -> None:
        self._actions.run_target_enhancement(
            self._params.target_level,
            allow_advanced=self._params.use_shards,
        )
