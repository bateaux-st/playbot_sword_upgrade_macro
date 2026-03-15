"""Pure data models for the macro."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class WeaponState:
    level: Optional[int] = None
    name: Optional[str] = None


@dataclass
class ProfileState:
    equipped: Optional[WeaponState] = None
    stored: Optional[WeaponState] = None
    gold: Optional[int] = None
    shards: Optional[int] = None


@dataclass
class ActionResult:
    log: str
    outcome: str = "unknown"
    weapon: Optional[WeaponState] = None
    gold: Optional[int] = None
    shards: Optional[int] = None
    is_hidden: Optional[bool] = None


class RestartSignal(Exception):
    """Control-flow signal to return to the main menu."""


def format_metric(value: object) -> str:
    if value is None:
        return "?"
    if isinstance(value, int):
        return f"{value:,}"
    return str(value)


def describe_weapon(weapon: Optional[WeaponState]) -> str:
    if weapon is None:
        return "(unknown)"
    level = f"+{weapon.level}" if weapon.level is not None else "+?"
    name = weapon.name or "(unnamed)"
    return f"{level} {name}"


def describe_profile_state(state: Optional[ProfileState]) -> str:
    if state is None:
        return "(none)"
    return (
        f"equipped={describe_weapon(state.equipped)} "
        f"stored={describe_weapon(state.stored)} "
        f"gold={format_metric(state.gold)} "
        f"shards={format_metric(state.shards)}"
    )


def merge_profile_state(
    base: Optional[ProfileState], patch: Optional[ProfileState]
) -> ProfileState:
    if base is None:
        return patch or ProfileState()
    if patch is None:
        return base
    return ProfileState(
        equipped=patch.equipped or base.equipped,
        stored=patch.stored or base.stored,
        gold=patch.gold if patch.gold is not None else base.gold,
        shards=patch.shards if patch.shards is not None else base.shards,
    )
