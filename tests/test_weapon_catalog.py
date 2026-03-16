"""Unit tests for weapon catalog — hidden/trash detection, CSV loading."""

import os
import pytest

from models import WeaponState
from weapon_catalog import WeaponCatalog, FALLBACK_HIDDEN_WEAPON_NAMES


class TestWeaponCatalogFromCSV:
    def test_load_real_csv_has_entries(self, catalog):
        # CSV has full weapon names, not short names
        # When map is loaded, short fallback names are NOT used
        assert len(catalog._map) > 0

    def test_load_real_csv_normal_weapon(self, catalog):
        assert catalog.is_hidden("\uac15\ucca0\uc2ec \uac80") is False

    def test_load_real_csv_finds_hidden_entries(self, catalog):
        # At least some hidden weapons exist in the CSV
        hidden_count = sum(
            1
            for v in catalog._map.values()
            if v == "\ud788\ub4e0" or (isinstance(v, tuple) and "\ud788\ub4e0" in v)
        )
        assert hidden_count > 0

    def test_empty_catalog_uses_fallback(self):
        empty_catalog = WeaponCatalog()
        assert empty_catalog.is_hidden("\uad11\uc120\uac80") is True
        assert empty_catalog.is_hidden("\uac15\ucca0\uc2ec \uac80") is False

    def test_nonexistent_csv(self):
        catalog = WeaponCatalog.from_csv("/nonexistent/path.csv")
        # Falls back to empty map -> uses fallback set
        assert catalog.is_hidden("\uad11\uc120\uac80") is True


class TestIsHiddenFallback:
    """Test hidden detection with empty catalog (fallback mode)."""

    def test_known_hidden_weapons(self):
        catalog = WeaponCatalog()
        hidden_names = ["\uad11\uc120\uac80", "\uae30\ud0c0", "\uc6b0\uc0b0", "\uc2ac\ub9ac\ud37c", "\uce94\ub514\ucf00\uc778"]
        for name in hidden_names:
            assert catalog.is_hidden(name) is True, f"{name} should be hidden"

    def test_known_normal_weapons(self):
        catalog = WeaponCatalog()
        assert catalog.is_hidden("\uac15\ucca0\uc2ec \uac80") is False

    def test_empty_name(self):
        catalog = WeaponCatalog()
        assert catalog.is_hidden("") is False

    def test_hidden_with_suffix(self):
        catalog = WeaponCatalog()
        assert catalog.is_hidden("\ub531\ub531\ud558\uac8c \uad73\uc740 \uc9c0\uc6b0\uac1c - \uc9c0\uc6b0\uac1c") is True


class TestIsHiddenCSV:
    """Test hidden detection with CSV-loaded catalog (exact match mode)."""

    def test_csv_normal_weapon_not_hidden(self, catalog):
        assert catalog.is_hidden("\uac15\ucca0\uc2ec \uac80") is False
        assert catalog.is_hidden("\ub0a1\uc740 \uac80") is False

    def test_csv_unknown_name_not_hidden(self, catalog):
        # With CSV loaded, unknown names are NOT hidden (no fallback)
        assert catalog.is_hidden("\uc644\uc804\ud788 \uc5c6\ub294 \ubb34\uae30 \uc774\ub984") is False

    def test_csv_short_fallback_name_not_matched(self, catalog):
        # Short fallback names like "\uad11\uc120\uac80" don't match CSV entries
        # because CSV has full names like "\ube5b\uc774 \uae43\ub4e0 \ucd08\uc6d4\uc801 \uad11\uc120\uac80"
        # This is correct: exact match only when CSV is loaded
        assert catalog.is_hidden("\uad11\uc120\uac80") is False


class TestIsTrash:
    def test_trash_weapons_by_keyword(self):
        # is_trash uses keyword matching, works regardless of catalog
        catalog = WeaponCatalog()
        assert catalog.is_trash("\ub0a1\uc740 \uac80") is True
        assert catalog.is_trash("\ub0a1\uc740 \ubabd\ub465\uc774") is True
        assert catalog.is_trash("\ub0a1\uc740 \ub3c4\ub07c") is True
        assert catalog.is_trash("\ub0a1\uc740 \ub9dd\uce58") is True

    def test_non_trash(self, catalog):
        assert catalog.is_trash("\uac15\ucca0\uc2ec \uac80") is False

    def test_empty(self, catalog):
        assert catalog.is_trash("") is False


class TestHiddenCandidate:
    def test_hidden_weapon_state_fallback(self):
        catalog = WeaponCatalog()
        weapon = WeaponState(level=5, name="\uad11\uc120\uac80")
        assert catalog.is_hidden_candidate(weapon) is True

    def test_normal_weapon_state(self, catalog):
        weapon = WeaponState(level=5, name="\uac15\ucca0\uc2ec \uac80")
        assert catalog.is_hidden_candidate(weapon) is False

    def test_none_weapon(self, catalog):
        assert catalog.is_hidden_candidate(None) is False

    def test_no_name(self, catalog):
        weapon = WeaponState(level=5, name=None)
        assert catalog.is_hidden_candidate(weapon) is False


class TestCanSell:
    def test_sellable(self, catalog):
        assert catalog.can_sell(WeaponState(level=1, name="\uac80")) is True
        assert catalog.can_sell(WeaponState(level=20, name="\uac80")) is True

    def test_not_sellable_zero(self, catalog):
        assert catalog.can_sell(WeaponState(level=0, name="\uac80")) is False

    def test_not_sellable_none(self, catalog):
        assert catalog.can_sell(None) is False
        assert catalog.can_sell(WeaponState(level=None, name="\uac80")) is False


class TestTargetReached:
    def test_reached_by_level(self, catalog):
        weapon = WeaponState(level=10, name="\uac80")
        assert catalog.is_target_reached(weapon, 10) is True
        assert catalog.is_target_reached(weapon, 5) is True

    def test_not_reached(self, catalog):
        weapon = WeaponState(level=5, name="\uac80")
        assert catalog.is_target_reached(weapon, 10) is False

    def test_log_ignored(self, catalog):
        """로그에 [+10]이 있어도 weapon.level이 미달이면 False."""
        weapon = WeaponState(level=3, name="\uac80")
        assert catalog.is_target_reached(weapon, 10, "[+10] \uac80") is False

    def test_none_weapon(self, catalog):
        assert catalog.is_target_reached(None, 10) is False
