"""Money farming mode — enhance to target, sell, repeat."""

from constants import MODE_MONEY
from modes.base import BaseMode, register_mode


@register_mode(MODE_MONEY)
class MoneyMode(BaseMode):
    def run(self) -> None:
        actions = self._actions
        weapon = actions.load_weapon()

        while True:
            outcome, weapon = actions.run_target_enhancement(
                self._params.target_level,
                current_weapon=weapon,
            )
            if outcome != "target_reached":
                return

            weapon = actions.ensure_sellable(weapon)
            if weapon is None:
                return
            sell_result = actions.sell()
            weapon = actions.resolve_weapon(sell_result, weapon)
