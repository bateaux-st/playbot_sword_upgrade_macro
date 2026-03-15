"""Composite game actions — I/O + parsing + logging combined."""

import time
from typing import Callable, Optional

from config import AppConfig
from constants import (
    CMD_ADVANCED_ENHANCE,
    CMD_ENHANCE,
    CMD_FUSION,
    CMD_PROFILE,
    CMD_SELL,
    CMD_SWAP,
)
from chat_io.protocol import ChatIO
from macro_logger import MacroLogger
from models import (
    ActionResult,
    ProfileState,
    WeaponState,
    describe_profile_state,
    describe_weapon,
    format_metric,
    merge_profile_state,
)
from parsing import (
    extract_last_gold,
    is_enhance_response,
    is_fusion_response,
    is_profile_response,
    is_sell_response,
    is_swap_response,
    is_waiting_for_command_response,
    parse_enhance_result,
    parse_fusion_result,
    parse_profile_state,
    parse_sell_result,
    parse_swap_state,
)
from state import AppState
from stats import EnhanceStats
from weapon_catalog import WeaponCatalog


class GameActions:
    def __init__(
        self,
        io: ChatIO,
        config: AppConfig,
        state: AppState,
        logger: MacroLogger,
        catalog: WeaponCatalog,
        stats: EnhanceStats,
    ) -> None:
        self._io = io
        self._config = config
        self._state = state
        self._logger = logger
        self._catalog = catalog
        self._stats = stats

    def capture_response(
        self,
        command: str,
        validator: Optional[Callable[[str], bool]] = None,
    ) -> str:
        self._io.send_command(command)
        time.sleep(self._config.command_response_poll_delay)

        last_log = ""
        for _ in range(self._config.max_response_wait_retry):
            log = self._io.read_chat_log()
            last_log = log

            if not log.strip():
                time.sleep(self._config.command_response_poll_delay)
                continue

            if is_waiting_for_command_response(log, command):
                time.sleep(self._config.command_response_poll_delay)
                continue

            if validator is not None and not validator(log):
                time.sleep(self._config.command_response_poll_delay)
                continue

            return log

        return last_log

    def refresh_profile(self) -> tuple[ProfileState, str]:
        last_log = ""
        for _ in range(self._config.max_action_retry):
            log = self.capture_response(
                CMD_PROFILE,
                validator=is_profile_response,
            )
            last_log = log
            if not log.strip():
                continue
            state = parse_profile_state(log)
            if (
                state.equipped
                or state.gold is not None
                or state.shards is not None
            ):
                self._logger.update_weapon_state(
                    equipped=state.equipped,
                    stored=state.stored,
                    gold=state.gold,
                    shards=state.shards,
                )
                return state, log
        return ProfileState(), last_log

    def enhance(
        self, current_weapon: Optional[WeaponState] = None
    ) -> ActionResult:
        return self._run_enhance(
            CMD_ENHANCE, "normal", current_weapon,
        )

    def advanced_enhance(
        self, current_weapon: Optional[WeaponState] = None
    ) -> ActionResult:
        return self._run_enhance(
            CMD_ADVANCED_ENHANCE, "advanced", current_weapon,
        )

    def _run_enhance(
        self,
        command: str,
        stat_type: str,
        current_weapon: Optional[WeaponState],
    ) -> ActionResult:
        start_level = (
            current_weapon.level
            if current_weapon and current_weapon.level is not None
            else None
        )
        last_result = ActionResult(log="")

        for _ in range(self._config.max_action_retry):
            log = self.capture_response(
                command, validator=is_enhance_response
            )
            result = parse_enhance_result(log, self.is_hidden_candidate)
            last_result = result

            if result.outcome == "busy":
                self._logger.status(f"{command} busy -> retry")
                time.sleep(self._config.command_response_poll_delay)
                continue

            if (
                start_level is not None
                and result.weapon
                and result.weapon.level is not None
            ):
                self._stats.record(
                    stat_type, start_level, result.weapon.level
                )

            # Compact log: "+5 → +6 성공" or "+7 파괴 → +0 낡은 몽둥이"
            sl = f"+{start_level}" if start_level is not None else "+?"
            wl = describe_weapon(result.weapon)
            self._logger.status(f"{sl} → {wl} ({result.outcome})")
            self._update_header_from_result(result)
            return result

        return last_result

    def sell(self) -> ActionResult:
        log = self.capture_response(
            CMD_SELL, validator=is_sell_response
        )
        result = parse_sell_result(log, self.is_hidden_candidate)

        if result.weapon is None:
            profile_state, _ = self.refresh_profile()
            result.weapon = profile_state.equipped
            if result.gold is None:
                result.gold = profile_state.gold
            if result.shards is None:
                result.shards = profile_state.shards
            result.is_hidden = self.is_hidden_candidate(result.weapon)

        if result.outcome == "not_sellable" and result.weapon is None:
            result.weapon = WeaponState(level=0, name=None)
            result.is_hidden = False

        self._logger.status(
            f"판매 → {describe_weapon(result.weapon)} "
            f"(+{format_metric(result.gold)}G)"
        )
        self._update_header_from_result(result)
        return result

    def swap(
        self, base_state: Optional[ProfileState] = None
    ) -> tuple[ProfileState, str]:
        log = self.capture_response(
            CMD_SWAP, validator=is_swap_response
        )
        swap_state = parse_swap_state(log)
        if base_state is not None:
            swap_state = merge_profile_state(base_state, swap_state)
        self._logger.status(
            f"교체 → 장착:{describe_weapon(swap_state.equipped)} "
            f"보관:{describe_weapon(swap_state.stored)}"
        )
        self._logger.update_weapon_state(
            equipped=swap_state.equipped,
            stored=swap_state.stored,
            gold=swap_state.gold,
            shards=swap_state.shards,
        )
        return swap_state, log

    def resolve_weapon(
        self,
        result: ActionResult,
        fallback: Optional[WeaponState],
    ) -> WeaponState:
        if result.weapon is not None:
            return result.weapon
        profile_state, _ = self.refresh_profile()
        return profile_state.equipped or fallback

    def fusion(self) -> ActionResult:
        log = self.capture_response(
            CMD_FUSION, validator=is_fusion_response
        )
        result = parse_fusion_result(log, self.is_hidden_candidate)

        if result.weapon is None:
            profile_state, _ = self.refresh_profile()
            result.weapon = profile_state.equipped
            if result.gold is None:
                result.gold = profile_state.gold
            if result.shards is None:
                result.shards = profile_state.shards

        self._logger.status(
            f"합성 → {describe_weapon(result.weapon)} ({result.outcome})"
        )
        self._update_header_from_result(result)
        return result

    def _update_header_from_result(self, result: ActionResult) -> None:
        self._logger.update_weapon_state(
            equipped=result.weapon,
            gold=result.gold,
            shards=result.shards,
        )

    def should_stop(self, result: ActionResult) -> bool:
        if result.outcome == "no_gold":
            self._logger.status("중지: 골드 부족")
            return True
        if self._config.min_gold_limit <= 0:
            return False
        gold = extract_last_gold(result.log)
        if gold is not None and gold <= self._config.min_gold_limit:
            self._logger.status(f"중지: 최소 골드 도달 ({gold:,}G)")
            return True
        return False

    def should_use_advanced(
        self,
        weapon: Optional[WeaponState],
        profile: Optional[ProfileState],
        hidden_only: bool = False,
    ) -> bool:
        if not weapon or weapon.level is None:
            return False
        if weapon.level != self._config.advanced_enhance_start_level:
            return False
        if profile is None or profile.shards is None:
            return False
        if profile.shards < self._config.advanced_enhance_shard_cost:
            return False
        if hidden_only and not self.is_hidden_candidate(weapon):
            return False
        return True

    def is_target_reached(
        self,
        weapon: Optional[WeaponState],
        target_level: int,
        log: str = "",
    ) -> bool:
        return self._catalog.is_target_reached(weapon, target_level, log)

    def is_hidden_candidate(
        self, weapon: Optional[WeaponState]
    ) -> bool:
        return self._catalog.is_hidden_candidate(weapon)

    def can_sell(self, weapon: Optional[WeaponState]) -> bool:
        return self._catalog.can_sell(weapon)

    @property
    def advanced_enhance_start_level(self) -> int:
        return self._config.advanced_enhance_start_level

    def load_profile(self) -> ProfileState:
        state, _ = self.refresh_profile()
        return state

    def load_weapon(self) -> Optional[WeaponState]:
        return self.load_profile().equipped

    def ensure_sellable(
        self, current_weapon: Optional[WeaponState] = None
    ) -> Optional[WeaponState]:
        weapon = current_weapon or self.load_weapon()

        while not self.can_sell(weapon):
            result = self.enhance(current_weapon=weapon)
            if self.should_stop(result):
                return None
            weapon = self.resolve_weapon(result, weapon)

        return weapon

    def run_target_enhancement(
        self,
        target_level: int,
        current_weapon: Optional[WeaponState] = None,
        stop_on_destroy: bool = False,
        advanced_hidden_only: bool = False,
        allow_advanced: bool = True,
    ) -> tuple[str, Optional[WeaponState]]:
        weapon = current_weapon or self.load_weapon()

        if self.is_target_reached(weapon, target_level):
            self._logger.status(
                f"이미 목표 도달 ({describe_weapon(weapon)})"
            )
            return "target_reached", weapon

        while True:
            profile_state = None
            if (
                weapon
                and weapon.level == self.advanced_enhance_start_level
            ):
                profile_state = self.load_profile()
                weapon = profile_state.equipped or weapon

            if allow_advanced and self.should_use_advanced(
                weapon, profile_state, hidden_only=advanced_hidden_only
            ):
                self._logger.status("상급강화 사용 (+0)")
                result = self.advanced_enhance(current_weapon=weapon)
            else:
                result = self.enhance(current_weapon=weapon)

            if self.should_stop(result):
                weapon = self.resolve_weapon(result, weapon)
                return "stopped", weapon

            weapon = self.resolve_weapon(result, weapon)

            if stop_on_destroy and result.outcome == "destroy":
                self._logger.status("파괴 → 재탐색")
                return "destroyed", weapon

            if self.is_target_reached(
                weapon, target_level, result.log
            ):
                self._logger.status(f"목표 달성! [+{target_level}]")
                return "target_reached", weapon
