"""Fusion mode — enhance two weapons to +20, then fuse for +21."""

from constants import FUSION_TARGET_LEVEL, MODE_FUSION
from models import describe_weapon, describe_profile_state
from modes.base import BaseMode, register_mode


@register_mode(MODE_FUSION)
class FusionMode(BaseMode):
    def run(self) -> None:
        actions = self._actions
        logger = self._logger

        # ── Step 1: Check current profile ──
        profile = actions.load_profile()
        logger.timeline(
            "STATE", f"fusion start {describe_profile_state(profile)}"
        )

        equipped = profile.equipped
        stored = profile.stored
        stored_ready = actions.is_target_reached(
            stored, FUSION_TARGET_LEVEL
        )

        # ── Step 2: Enhance equipped weapon (A) to +20 ──
        if not actions.is_target_reached(equipped, FUSION_TARGET_LEVEL):
            logger.timeline(
                "DECISION",
                f"enhance equipped to +{FUSION_TARGET_LEVEL}: "
                f"{describe_weapon(equipped)}",
            )
            outcome, equipped = actions.run_target_enhancement(
                FUSION_TARGET_LEVEL,
                current_weapon=equipped,
                allow_advanced=self._params.use_shards,
            )
            if outcome != "target_reached":
                logger.status(f"Stopped: equipped enhancement {outcome}")
                return

        logger.timeline(
            "STATE", f"equipped ready: {describe_weapon(equipped)}"
        )

        if stored_ready:
            # ── Stored weapon already +20 — skip swap/enhance ──
            logger.timeline(
                "STATE",
                f"stored already ready: {describe_weapon(stored)}, "
                f"skipping swap+enhance",
            )
        else:
            # ── Step 3: Swap — put +20 A into storage, equip B ──
            logger.timeline(
                "DECISION", "swap: store equipped, get new weapon"
            )
            swap_state, _ = actions.swap()
            logger.timeline(
                "STATE",
                f"after swap {describe_profile_state(swap_state)}",
            )

            new_equipped = swap_state.equipped

            # ── Step 4: Enhance new equipped weapon (B) to +20 ──
            if not actions.is_target_reached(
                new_equipped, FUSION_TARGET_LEVEL
            ):
                logger.timeline(
                    "DECISION",
                    f"enhance new equipped to +{FUSION_TARGET_LEVEL}: "
                    f"{describe_weapon(new_equipped)}",
                )
                outcome, new_equipped = actions.run_target_enhancement(
                    FUSION_TARGET_LEVEL,
                    current_weapon=new_equipped,
                    allow_advanced=self._params.use_shards,
                )
                if outcome != "target_reached":
                    logger.status(
                        f"Stopped: second weapon enhancement {outcome}"
                    )
                    return

        logger.timeline("STATE", "both weapons at +20, ready for fusion")

        # ── Step 5: Fuse for +21 ──
        logger.timeline("DECISION", "attempting fusion")
        logger.status("Both weapons at +20. Attempting fusion!")
        result = actions.fusion()

        if result.outcome == "fusion_success":
            logger.status(
                f"FUSION SUCCESS! {describe_weapon(result.weapon)}"
            )
        elif result.outcome == "fusion_fail":
            logger.status(
                f"Fusion failed. {describe_weapon(result.weapon)}"
            )
        else:
            logger.status(
                f"Fusion result unknown: {result.outcome}. "
                f"Check chat log."
            )
