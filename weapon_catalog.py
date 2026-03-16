"""Weapon catalog loading and weapon classification."""
import csv
import os
from typing import Optional, Union
from constants import TRASH_WEAPON_KEYWORDS
from models import WeaponState
from parsing import clean_weapon_name

WeaponType = Union[str, tuple[str, ...]]
FALLBACK_HIDDEN_WEAPON_NAMES: frozenset[str] = frozenset(
    {
        "광선검",
        "기타",
        "꽃다발",
        "끝이 뺭툴한 윤",
        "단소",
        "딱딱하게 굳은 지우개 - 지우개",
        "지우개",
        "빗자루",
        "슬리퍼",
        "아이스크림",
        "우산",
        "젖가락",
        "주전자",
        "채찍",
        "칫솔",
        "캔디케인: 만물을 달콤하게 하는 절대 축복 - 캔디케인",
        "캔디케인",
        "하드",
        "핫도그",
        "화살",
    }
)

class WeaponCatalog:
    def __init__(
        self,
        name_type_map: Optional[dict[str, WeaponType]] = None,
    ) -> None:
        self._map: dict[str, WeaponType] = name_type_map or {}

    @classmethod
    def from_csv(cls, csv_path: str) -> "WeaponCatalog":
        name_type_map: dict[str, WeaponType] = {}
        if not os.path.exists(csv_path):
            return cls(name_type_map)
        with open(csv_path, "r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                name = clean_weapon_name(row.get("name", ""))
                if not name:
                    continue
                category = (row.get("category", "") or "").strip()
                is_hidden = (
                    row.get("isHidden", "") or ""
                ).strip().lower() == "true"
                weapon_type = "히든" if is_hidden else category
                if not weapon_type:
                    continue
                existing = name_type_map.get(name)
                if existing is None:
                    name_type_map[name] = weapon_type
                elif isinstance(existing, tuple):
                    if weapon_type not in existing:
                        name_type_map[name] = tuple(
                            sorted(set(existing) | {weapon_type})
                        )
                elif existing != weapon_type:
                    name_type_map[name] = tuple(sorted({existing, weapon_type}))
        return cls(name_type_map)

    def is_hidden(self, name: str) -> bool:
        if not name:
            return False
        cleaned = clean_weapon_name(name)
        weapon_type = self._map.get(cleaned)
        if weapon_type is not None:
            if isinstance(weapon_type, str):
                return weapon_type == "히든"
            return "히든" in weapon_type
        if self._map:
            return False
        if cleaned in FALLBACK_HIDDEN_WEAPON_NAMES:
            return True
        if " - " in cleaned:
            suffix = cleaned.split(" - ")[-1].strip()
            if suffix in FALLBACK_HIDDEN_WEAPON_NAMES:
                return True
        return any(
            hidden_name in cleaned
            for hidden_name in FALLBACK_HIDDEN_WEAPON_NAMES
        )

    def is_trash(self, name: str) -> bool:
        if not name:
            return False
        return any(keyword in name for keyword in TRASH_WEAPON_KEYWORDS)

    def is_hidden_candidate(self, weapon: Optional[WeaponState]) -> bool:
        return bool(weapon and weapon.name and self.is_hidden(weapon.name))

    def can_sell(self, weapon: Optional[WeaponState]) -> bool:
        return bool(
            weapon and weapon.level is not None and weapon.level > 0
        )

    def is_target_reached(
        self,
        weapon: Optional[WeaponState],
        target_level: int,
        log: str = "",
    ) -> bool:
        return (
            weapon is not None
            and weapon.level is not None
            and weapon.level >= target_level
        )
