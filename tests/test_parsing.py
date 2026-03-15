"""Unit tests for parsing module — all pure functions."""

import pytest

from models import WeaponState, ProfileState, ActionResult
from parsing import (
    clean_weapon_name,
    parse_int,
    parse_weapon_text,
    parse_profile_weapon,
    extract_last_gold,
    extract_last_shards,
    parse_profile_state,
    parse_enhance_result,
    parse_sell_result,
    build_command_variants,
    is_waiting_for_command_response,
    is_profile_response,
    is_enhance_response,
    is_sell_response,
    is_swap_response,
    parse_swap_state,
)


class TestParseInt:
    def test_plain_number(self):
        assert parse_int("12345") == 12345

    def test_comma_separated(self):
        assert parse_int("1,234,567") == 1234567

    def test_zero(self):
        assert parse_int("0") == 0


class TestCleanWeaponName:
    def test_basic_trim(self):
        assert clean_weapon_name("  \uac15\ucca0\uc2ec \uac80  ") == "\uac15\ucca0\uc2ec \uac80"

    def test_collapse_whitespace(self):
        assert clean_weapon_name("\uac15\ucca0\uc2ec   \uac80") == "\uac15\ucca0\uc2ec \uac80"

    def test_strip_after_right_bracket(self):
        assert clean_weapon_name("\uc9c4\uc815\ud55c \uad8c\ub2a5\uc774 \uae43\ub4e0 \uac15\ucca0 \uac80\u300f\uc5b4\ucad3\uad6c") == "\uc9c4\uc815\ud55c \uad8c\ub2a5\uc774 \uae43\ub4e0 \uac15\ucca0 \uac80"

    def test_strip_after_quote(self):
        assert clean_weapon_name('\uac80 \uc774\ub984"some extra') == "\uac80 \uc774\ub984"

    def test_empty(self):
        assert clean_weapon_name("") == ""


class TestParseWeaponText:
    def test_basic(self):
        result = parse_weapon_text("[+5] \uac15\ucca0\uc2ec \uac80")
        assert result == WeaponState(level=5, name="\uac15\ucca0\uc2ec \uac80")

    def test_high_level(self):
        result = parse_weapon_text("[+20] \uc6b0\uc8fc \ud0dc\ub3d9\uc758 \uac15\ucca0 \uc12d\ub9ac")
        assert result == WeaponState(level=20, name="\uc6b0\uc8fc \ud0dc\ub3d9\uc758 \uac15\ucca0 \uc12d\ub9ac")

    def test_zero_level(self):
        result = parse_weapon_text("[+0] \ub0a1\uc740 \uac80")
        assert result == WeaponState(level=0, name="\ub0a1\uc740 \uac80")

    def test_no_match(self):
        assert parse_weapon_text("\uc544\ubb34 \ud328\ud134\ub3c4 \uc5c6\ub294 \ud14d\uc2a4\ud2b8") is None

    def test_multiple_matches_returns_last(self):
        text = "[+3] \uccab\ubc88\uc9f8 \uac80\n[+7] \ub450\ubc88\uc9f8 \uac80"
        result = parse_weapon_text(text)
        assert result == WeaponState(level=7, name="\ub450\ubc88\uc9f8 \uac80")


class TestExtractGold:
    def test_current_gold(self):
        assert extract_last_gold("\U0001f4b0\ud604\uc7ac \ubcf4\uc720 \uace8\ub4dc: 1,234,567 G") == 1234567

    def test_remaining_gold(self):
        assert extract_last_gold("\ub0a8\uc740 \uace8\ub4dc: 500 G") == 500

    def test_no_gold(self):
        assert extract_last_gold("\uc544\ubb34 \uc815\ubcf4 \uc5c6\uc74c") is None

    def test_multiple_returns_last(self):
        log = "\U0001f4b0\ubcf4\uc720 \uace8\ub4dc: 100 G\n\U0001f4b0\ubcf4\uc720 \uace8\ub4dc: 200 G"
        assert extract_last_gold(log) == 200


class TestExtractShards:
    def test_with_prefix(self):
        assert extract_last_shards("\U0001f320\ubcf4\uc720 \ubcc4\uc758 \ud30c\ud3b8: 25\uac1c") == 25

    def test_no_shards(self):
        assert extract_last_shards("\uc544\ubb34\uac83\ub3c4 \uc5c6\uc74c") is None


class TestParseProfileState:
    def test_full_profile(self):
        log = (
            "\u25cf \uc7a5\ucc29 \uac80: [+5] \uac15\ucca0\uc2ec \uac80\n"
            "\u25cf \ubcf4\uad00 \uac80: [+3] \ub0a1\uc740 \ub3c4\ub07c\n"
            "\U0001f4b0\ud604\uc7ac \ubcf4\uc720 \uace8\ub4dc: 10,000 G\n"
            "\U0001f320\ubcf4\uc720 \ubcc4\uc758 \ud30c\ud3b8: 5\uac1c"
        )
        state = parse_profile_state(log)
        assert state.equipped == WeaponState(level=5, name="\uac15\ucca0\uc2ec \uac80")
        assert state.stored == WeaponState(level=3, name="\ub0a1\uc740 \ub3c4\ub07c")
        assert state.gold == 10000
        assert state.shards == 5

    def test_no_stored(self):
        log = "\u25cf \uc7a5\ucc29 \uac80: [+1] \uac80\n\u25cf \ubcf4\uad00 \uac80: \uc5c6\uc74c"
        state = parse_profile_state(log)
        assert state.equipped is not None
        assert state.stored is None

    def test_empty_log(self):
        state = parse_profile_state("")
        assert state.equipped is None
        assert state.stored is None
        assert state.gold is None
        assert state.shards is None


class TestParseEnhanceResult:
    _always_false = lambda self, w: False
    _always_true = lambda self, w: True

    def test_success(self):
        log = "\uac15\ud654 \uc131\uacf5! [+6] \uac15\ucca0\uc2ec \uac80\n\U0001f4b0\ubcf4\uc720 \uace8\ub4dc: 9,000 G"
        result = parse_enhance_result(log, lambda w: False)
        assert result.outcome == "success"
        assert result.weapon == WeaponState(level=6, name="\uac15\ucca0\uc2ec \uac80")
        assert result.gold == 9000

    def test_maintain(self):
        log = "\uac15\ud654 \uc720\uc9c0 [+5] \uac15\ucca0\uc2ec \uac80"
        result = parse_enhance_result(log, lambda w: False)
        assert result.outcome == "maintain"
        assert result.weapon.level == 5

    def test_destroy(self):
        log = "\uac15\ud654 \ud30c\uad34! \ud68d\ub4dd \uac80: [+0] \ub0a1\uc740 \uac80"
        result = parse_enhance_result(log, lambda w: False)
        assert result.outcome == "destroy"
        assert result.weapon.level == 0

    def test_busy(self):
        log = "\uac15\ud654 \uc911\uc774\ub2c8 \uc7a0\uae50 \uae30\ub2e4\ub9ac\ub3c4\ub85d"
        result = parse_enhance_result(log, lambda w: False)
        assert result.outcome == "busy"

    def test_no_gold(self):
        log = "\uace8\ub4dc\uac00 \ubd80\uc871\ud574"
        result = parse_enhance_result(log, lambda w: False)
        assert result.outcome == "no_gold"

    def test_hidden_callback(self):
        log = "\uac15\ud654 \uc131\uacf5! [+1] \uad11\uc120\uac80"
        result = parse_enhance_result(log, lambda w: w is not None and w.name == "\uad11\uc120\uac80")
        assert result.is_hidden is True


class TestParseSellResult:
    def test_sold(self):
        log = "\uc0c8\ub85c\uc6b4 \uac80 \ud68d\ub4dd: [+0] \ub0a1\uc740 \uac80\n\U0001f4b0\ubcf4\uc720 \uace8\ub4dc: 15,000 G"
        result = parse_sell_result(log, lambda w: False)
        assert result.outcome == "sold"
        assert result.weapon.level == 0
        assert result.gold == 15000

    def test_not_sellable(self):
        log = "0\uac15\uac80\uc740 \uac00\uce58\uac00 \uc5c6\uc5b4\uc11c \ud310\ub9e4\ud560 \uc218\uc5c6\ub2e4\ub124."
        result = parse_sell_result(log, lambda w: False)
        assert result.outcome == "not_sellable"


class TestBuildCommandVariants:
    def test_slash_command(self):
        variants = build_command_variants("/\uac15\ud654")
        assert "/\uac15\ud654" in variants
        assert "@\ud50c\ub808\uc774\ubd07 \uac15\ud654" in variants

    def test_empty(self):
        assert build_command_variants("") == []

    def test_bot_prefix(self):
        variants = build_command_variants("@\ud50c\ub808\uc774\ubd07 \uac15\ud654")
        assert "/\uac15\ud654" in variants
        assert "@\ud50c\ub808\uc774\ubd07 \uac15\ud654" in variants


class TestIsWaitingForResponse:
    def test_command_after_bot(self):
        log = "[\ud50c\ub808\uc774\ubd07] \uc774\uc804 \uc751\ub2f5\n/\uac15\ud654"
        assert is_waiting_for_command_response(log, "/\uac15\ud654") is True

    def test_bot_after_command(self):
        log = "/\uac15\ud654\n[\ud50c\ub808\uc774\ubd07] \uac15\ud654 \uc131\uacf5!"
        assert is_waiting_for_command_response(log, "/\uac15\ud654") is False

    def test_empty(self):
        assert is_waiting_for_command_response("", "/\uac15\ud654") is False


class TestResponseValidators:
    def test_is_profile_response(self):
        assert is_profile_response("[\ud50c\ub808\uc774\ubd07] \ud504\ub85c\ud544") is True
        assert is_profile_response("\u25cf \uc7a5\ucc29 \uac80: [+1] \uac80") is True
        assert is_profile_response("random text") is False

    def test_is_enhance_response(self):
        assert is_enhance_response("\uac15\ud654 \uc131\uacf5!") is True
        assert is_enhance_response("\uac15\ud654 \uc720\uc9c0") is True
        assert is_enhance_response("\uac15\ud654 \ud30c\uad34") is True
        assert is_enhance_response("random") is False

    def test_is_sell_response(self):
        assert is_sell_response("\u3016\uac80\ud310\ub9e4\u3017") is True
        assert is_sell_response("\uc0c8\ub85c\uc6b4 \uac80 \ud68d\ub4dd: [+0] \uac80") is True
        assert is_sell_response("random") is False

    def test_is_swap_response(self):
        assert is_swap_response("\uad50\uccb4 \uc644\ub8cc") is True
        assert is_swap_response("\u2694\ufe0f \uc7a5\ucc29: [+3] \uac80") is True
        assert is_swap_response("random") is False
