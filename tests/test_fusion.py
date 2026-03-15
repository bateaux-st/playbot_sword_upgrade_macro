"""Unit tests for fusion mode — parsing, actions, mode logic."""

import pytest

from actions import GameActions
from constants import MODE_FUSION
from modes.base import MODE_REGISTRY, ModeParams
from parsing import (
    is_fusion_response,
    parse_fusion_result,
)
from tests.conftest import FakeChatIO


# ── Real fusion success message from a friend ──

FUSION_SUCCESS_LOG = """\
@사용자 〖🔥합성 성공〗

🗯️ 전설: "두 개의 별빛이 교차하며 하나의 칼날이 되었다. 쌍둥이의 변주가 21강에서 완벽한 균형을 찾았군. 지금 네 손엔 '선택'이 아니라 '필연'이 쥐어져 있다."

💸 사용 골드: -1,000,000G
🌟 사용 별의 파편: -100개
🗡️ 사용 재료: [+20] 모든 우주의 격노: 만유를 삼키는 종언의 섭리

💰보유 골드: 2,886,265,642G
🌠 보유 별의 파편: 229개
⚔️획득 검: [+21] 쌍둥이자리의 분기검"""

FUSION_INTRO_LOG = """\
✨ 『전설의 대장장이』 가 용사가 건낸 검들을 확인하고 있습니다..."""

_not_hidden = lambda w: False


class TestFusionResponseValidator:
    def test_success_detected(self):
        assert is_fusion_response(FUSION_SUCCESS_LOG) is True

    def test_intro_detected(self):
        assert is_fusion_response(FUSION_INTRO_LOG) is True

    def test_unrelated_not_detected(self):
        assert is_fusion_response("강화 성공!") is False


class TestParseFusionResult:
    def test_success_outcome(self):
        result = parse_fusion_result(FUSION_SUCCESS_LOG, _not_hidden)
        assert result.outcome == "fusion_success"

    def test_success_weapon(self):
        result = parse_fusion_result(FUSION_SUCCESS_LOG, _not_hidden)
        assert result.weapon is not None
        assert result.weapon.level == 21
        assert "분기검" in result.weapon.name

    def test_success_gold(self):
        result = parse_fusion_result(FUSION_SUCCESS_LOG, _not_hidden)
        assert result.gold == 2886265642

    def test_success_shards(self):
        result = parse_fusion_result(FUSION_SUCCESS_LOG, _not_hidden)
        assert result.shards == 229

    def test_unknown_log(self):
        result = parse_fusion_result("아무 관련 없는 메시지", _not_hidden)
        assert result.outcome == "unknown"


class TestFusionModeRegistered:
    def test_registered(self):
        assert MODE_FUSION in MODE_REGISTRY


class TestFusionAction:
    def test_fusion_success(self, app_config, app_state, logger, stats, catalog):
        io = FakeChatIO([FUSION_SUCCESS_LOG])
        actions = GameActions(io, app_config, app_state, logger, catalog, stats)
        result = actions.fusion()
        assert result.outcome == "fusion_success"
        assert result.weapon.level == 21
