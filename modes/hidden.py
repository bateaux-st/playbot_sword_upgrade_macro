"""Hidden weapon mode — find hidden weapon, enhance, optionally sell+repeat."""

from typing import Optional

from constants import MODE_HIDDEN
from models import WeaponState, describe_weapon
from modes.base import BaseMode, HiddenModeParams, register_mode


@register_mode(MODE_HIDDEN)
class HiddenMode(BaseMode):
    def run(self) -> None:
        actions = self._actions
        logger = self._logger
        weapon = actions.load_weapon()

        while True:
            weapon = self._acquire_hidden(weapon)
            if weapon is None:
                return

            outcome, weapon = actions.run_target_enhancement(
                self._params.target_level,
                current_weapon=weapon,
                stop_on_destroy=True,
                advanced_hidden_only=True,
                allow_advanced=self._params.use_shards,
            )

            if outcome == "destroyed":
                continue
            if outcome != "target_reached":
                return
            if not (
                isinstance(self._params, HiddenModeParams)
                and self._params.auto_sell
            ):
                return

            weapon = actions.ensure_sellable(weapon)
            if weapon is None:
                return
            sell_result = actions.sell()
            weapon = actions.resolve_weapon(sell_result, weapon)

    def _acquire_hidden(
        self, current_weapon: Optional[WeaponState] = None
    ) -> Optional[WeaponState]:
        actions = self._actions
        logger = self._logger

        weapon = current_weapon or actions.load_weapon()
        logger.timeline(
            "STATE",
            f"hidden search start current={describe_weapon(weapon)}",
        )

        while True:
            if actions.is_hidden_candidate(weapon):
                logger.timeline(
                    "STATE",
                    f"hidden acquired={describe_weapon(weapon)}",
                )
                logger.status(
                    f"Hidden weapon found! ({weapon.name[:20]}...)"
                )
                return weapon

            logger.timeline(
                "DECISION",
                f"non-hidden weapon={describe_weapon(weapon)} "
                f"-> sell loop",
            )
            weapon = actions.ensure_sellable(weapon)
            if weapon is None:
                return None

            if actions.is_hidden_candidate(weapon):
                continue

            sell_result = actions.sell()
            weapon = actions.resolve_weapon(sell_result, weapon)
