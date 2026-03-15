"""Unit tests for GameActions with mock ChatIO."""

import pytest

from actions import GameActions
from models import WeaponState, ProfileState, ActionResult
from tests.conftest import FakeChatIO


@pytest.fixture
def make_actions(app_config, app_state, logger, stats, catalog):
    def factory(responses=None):
        io = FakeChatIO(responses or [])
        return GameActions(io, app_config, app_state, logger, catalog, stats), io
    return factory


class TestCaptureResponse:
    def test_returns_log_on_valid_response(self, make_actions):
        actions, io = make_actions(
            ["[\ud50c\ub808\uc774\ubd07] \uac15\ud654 \uc131\uacf5! [+6] \uac15\ucca0\uc2ec \uac80"]
        )
        log = actions.capture_response("/\uac15\ud654")
        assert "\uac15\ud654 \uc131\uacf5" in log
        assert io.commands_sent == ["/\uac15\ud654"]

    def test_returns_empty_on_no_response(self, make_actions):
        actions, io = make_actions([])
        log = actions.capture_response("/\uac15\ud654")
        assert log == ""


class TestEnhance:
    def test_enhance_success(self, make_actions):
        actions, io = make_actions(
            ["[\ud50c\ub808\uc774\ubd07] \uac15\ud654 \uc131\uacf5! [+6] \uac15\ucca0\uc2ec \uac80\n\U0001f4b0\ubcf4\uc720 \uace8\ub4dc: 9,000 G"]
        )
        result = actions.enhance(WeaponState(level=5, name="\uac15\ucca0\uc2ec \uac80"))
        assert result.outcome == "success"
        assert result.weapon.level == 6

    def test_enhance_no_gold(self, make_actions):
        actions, io = make_actions(["\uace8\ub4dc\uac00 \ubd80\uc871\ud574"])
        result = actions.enhance(WeaponState(level=5, name="\uac80"))
        assert result.outcome == "no_gold"


class TestSell:
    def test_sell_success(self, make_actions):
        actions, io = make_actions([
            "\u3016\uac80\ud310\ub9e4\u3017\n\uc0c8\ub85c\uc6b4 \uac80 \ud68d\ub4dd: [+0] \ub0a1\uc740 \uac80\n\U0001f4b0\ubcf4\uc720 \uace8\ub4dc: 15,000 G"
        ])
        result = actions.sell()
        assert result.outcome == "sold"
        assert result.weapon.level == 0
        assert result.gold == 15000


class TestShouldStop:
    def test_no_gold_stops(self, make_actions):
        actions, _ = make_actions()
        result = ActionResult(log="", outcome="no_gold")
        assert actions.should_stop(result) is True

    def test_normal_continues(self, make_actions):
        actions, _ = make_actions()
        result = ActionResult(log="", outcome="success")
        assert actions.should_stop(result) is False


class TestShouldUseAdvanced:
    def test_at_start_level_with_shards(self, make_actions):
        actions, _ = make_actions()
        weapon = WeaponState(level=0, name="\uad11\uc120\uac80")
        profile = ProfileState(shards=20)
        assert actions.should_use_advanced(weapon, profile) is True

    def test_wrong_level(self, make_actions):
        actions, _ = make_actions()
        weapon = WeaponState(level=5, name="\uac80")
        profile = ProfileState(shards=20)
        assert actions.should_use_advanced(weapon, profile) is False

    def test_no_shards(self, make_actions):
        actions, _ = make_actions()
        weapon = WeaponState(level=0, name="\uac80")
        profile = ProfileState(shards=0)
        assert actions.should_use_advanced(weapon, profile) is False

    def test_hidden_only_filter(self, make_actions):
        actions, _ = make_actions()
        weapon = WeaponState(level=0, name="\uac15\ucca0\uc2ec \uac80")
        profile = ProfileState(shards=20)
        assert actions.should_use_advanced(weapon, profile, hidden_only=True) is False
