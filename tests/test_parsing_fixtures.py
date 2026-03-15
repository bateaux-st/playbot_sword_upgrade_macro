"""Parsing tests using real KakaoTalk message samples from all_messages.txt."""

import pytest

from models import WeaponState, ProfileState
from parsing import (
    parse_enhance_result,
    parse_sell_result,
    parse_profile_state,
    parse_swap_state,
    extract_last_gold,
    extract_last_shards,
    parse_weapon_text,
    is_enhance_response,
    is_sell_response,
    is_profile_response,
    is_swap_response,
)

# ── Real message samples from all_messages.txt ──

ENHANCE_SUCCESS_LOG = """\
@배성태 〖✨강화 성공✨ +8 → +9〗

💬 대장장이: "이건 그냥... 단소가 아니군. 대체 뭘 만든 거냐?"

💸사용 골드: -5,000G
💰남은 골드: 2,248,731G
⚔️획득 검: [+9] 물소리가 파도가 된 단소"""

ENHANCE_MAINTAIN_LOG = """\
@배성태 〖💦강화 유지💦〗

💬 대장장이: "이런, 아직도 쓸만한가? 기묘하군."

『[+8] 침묵의 소리를 내는 단소』의 레벨이 유지되었습니다.

💸사용 골드: -5,000G
💰남은 골드: 2,253,731G"""

ENHANCE_DESTROY_LOG = """\
@배성태 〖💥강화 파괴💥〗

💬 대장장이: "역시 쓰레기는 쓰레기통으로 가는 법이지."

💸사용 골드: -1,000G
💰남은 골드: 3,377,696G

🌠 별의 파편 2개 획득! (199개 → 201개)
『[+6] 날아오르는 먼지의 빗자루』 산산조각 나서, 『[+0] 낡은 검』 지급되었습니다."""

NO_GOLD_LOG = """\
⚔️배틀마스터: "혹시 자네 골드가 부족한가? 배틀에서 이기면 골드를 드린다네. 아니면, 감정사에게 가보게나."
"""

ADVANCED_ENHANCE_LOG = """\
@배성태 〖🌠 상급강화 +0 → +6〗

💬 대장장이: "💬 대장장이: "🙇 ...잠시 묵념하겠네. 내 손에서 역사상 최고의 검이 나왔다는 게 믿기지 않아... 자네는 선택받은 용사가 분명해.""

🌟 사용 파편: -10개
🌠 남은 파편: 199개
⚔️ 획득 검: [+6] 날아오르는 먼지의 빗자루"""

SELL_LOG = """\
@배성태 〖검 판매〗

💬 감정사: '+1 불씨 검'이라... 이름만 들어도 영 시원찮군. 감정 결과, 자네의 '[+1] 불씨 검'은 11G에 판매되었네!

💶획득 골드: +11G
💰현재 보유 골드: 2,258,727G
⚔️새로운 검 획득: [+0] 낡은 검"""

SELL_EXPENSIVE_LOG = """\
@배성태 〖검 판매〗

💬 감정사: "흠... '[+1] 서리 깃든 몽둥이'이라. 음, +1치고는 제법 멋들어진 이름이군. 감정 결과, 자네의 '[+1] 서리 깃든 몽둥이'는 10G에 판매되었네!"

💶획득 골드: +10G
💰현재 보유 골드: 2,258,727G
⚔️새로운 검 획득: [+0] 낡은 몽둥이"""

CANNOT_SELL_LOG = """\
@배성태 💬 감정사: "0강검은 가치가 없어서 판매할 수 없다네. 대장장이에게 가서 검 강화를 먼저 하고 오시게나."
🔨 대장장이에게 검의 강화를 의뢰하시겠습니까?"""

PROFILE_OLD_LOG = """\
[프로필]
● 이름: @배성태
● 도감 ID: 무명의 용사 a951
● 전적: 17승 24패
● 최고 기록: [+14] 라의 태초 신격 검
● 보유 검: [+14] 라의 태초 신격 검

[보유 아이템]
💰골드: 168,462 G
🌠 별의 파편: 28개"""

PROFILE_NEW_LOG = """\
[프로필]
● 이름: @배성태
● 도감 ID: 무명의 용사 a951
● 전적: 53승 70패
● 최고 기록: [+19] 다중우주를 직조하는 생명의 태초 법칙
● 장착 검: [+0] 낡은 몽둥이
● 보관 검: [+19] 다중우주를 직조하는 생명의 태초 법칙

[보유 아이템]
💰골드: 27,529,426 G
🌠 별의 파편: 84개"""

SWAP_LOG = """\
@배성태 〖🔄교체 완료〗

⚔️ 장착: [+19] 다중우주를 직조하는 생명의 태초 법칙
📦 보관: [+0] 낡은 검"""

SWAP_EMPTY_STORAGE_LOG = """\
@배성태 〖🔄교체 완료〗

보관함이 비어있어서 새로운 0강 검이 부여되었습니다.

⚔️ 장착: [+0] 낡은 검
📦 보관: [+19] 다중우주를 직조하는 생명의 태초 법칙"""

_not_hidden = lambda w: False


# ── Tests ──

class TestRealEnhanceSuccess:
    def test_outcome(self):
        result = parse_enhance_result(ENHANCE_SUCCESS_LOG, _not_hidden)
        assert result.outcome == "success"

    def test_weapon(self):
        result = parse_enhance_result(ENHANCE_SUCCESS_LOG, _not_hidden)
        assert result.weapon.level == 9
        assert result.weapon.name == "물소리가 파도가 된 단소"

    def test_gold(self):
        result = parse_enhance_result(ENHANCE_SUCCESS_LOG, _not_hidden)
        assert result.gold == 2248731


class TestRealEnhanceMaintain:
    def test_outcome(self):
        result = parse_enhance_result(ENHANCE_MAINTAIN_LOG, _not_hidden)
        assert result.outcome == "maintain"

    def test_weapon_level_preserved(self):
        result = parse_enhance_result(ENHANCE_MAINTAIN_LOG, _not_hidden)
        assert result.weapon.level == 8

    def test_gold(self):
        result = parse_enhance_result(ENHANCE_MAINTAIN_LOG, _not_hidden)
        assert result.gold == 2253731


class TestRealEnhanceDestroy:
    def test_outcome(self):
        result = parse_enhance_result(ENHANCE_DESTROY_LOG, _not_hidden)
        assert result.outcome == "destroy"

    def test_replacement_weapon(self):
        result = parse_enhance_result(ENHANCE_DESTROY_LOG, _not_hidden)
        assert result.weapon.level == 0
        assert result.weapon.name == "낡은 검"

    def test_gold(self):
        result = parse_enhance_result(ENHANCE_DESTROY_LOG, _not_hidden)
        assert result.gold == 3377696


class TestRealAdvancedEnhance:
    def test_outcome(self):
        result = parse_enhance_result(ADVANCED_ENHANCE_LOG, _not_hidden)
        assert result.outcome == "advanced_success"

    def test_weapon(self):
        result = parse_enhance_result(ADVANCED_ENHANCE_LOG, _not_hidden)
        assert result.weapon.level == 6
        assert "빗자루" in result.weapon.name


class TestRealSell:
    def test_sold_outcome(self):
        result = parse_sell_result(SELL_LOG, _not_hidden)
        assert result.outcome == "sold"

    def test_new_weapon(self):
        result = parse_sell_result(SELL_LOG, _not_hidden)
        assert result.weapon.level == 0
        assert result.weapon.name == "낡은 검"

    def test_gold(self):
        result = parse_sell_result(SELL_LOG, _not_hidden)
        assert result.gold == 2258727

    def test_sell_with_different_weapon(self):
        result = parse_sell_result(SELL_EXPENSIVE_LOG, _not_hidden)
        assert result.outcome == "sold"
        assert result.weapon.level == 0
        assert "몽둥이" in result.weapon.name

    def test_cannot_sell(self):
        result = parse_sell_result(CANNOT_SELL_LOG, _not_hidden)
        assert result.outcome == "not_sellable"


class TestRealProfileOld:
    def test_gold(self):
        state = parse_profile_state(PROFILE_OLD_LOG)
        assert state.gold == 168462

    def test_shards(self):
        state = parse_profile_state(PROFILE_OLD_LOG)
        assert state.shards == 28

    def test_no_equipped_stored_labels(self):
        # Old format uses "보유 검" not "장착 검"/"보관 검"
        state = parse_profile_state(PROFILE_OLD_LOG)
        assert state.equipped is None
        assert state.stored is None


class TestRealProfileNew:
    def test_equipped(self):
        state = parse_profile_state(PROFILE_NEW_LOG)
        assert state.equipped.level == 0
        assert "몽둥이" in state.equipped.name

    def test_stored(self):
        state = parse_profile_state(PROFILE_NEW_LOG)
        assert state.stored.level == 19

    def test_gold(self):
        state = parse_profile_state(PROFILE_NEW_LOG)
        assert state.gold == 27529426

    def test_shards(self):
        state = parse_profile_state(PROFILE_NEW_LOG)
        assert state.shards == 84


class TestRealSwap:
    def test_equipped(self):
        state = parse_swap_state(SWAP_LOG)
        assert state.equipped.level == 19

    def test_stored(self):
        state = parse_swap_state(SWAP_LOG)
        assert state.stored.level == 0
        assert state.stored.name == "낡은 검"

    def test_empty_storage_swap(self):
        state = parse_swap_state(SWAP_EMPTY_STORAGE_LOG)
        assert state.equipped.level == 0
        assert state.stored.level == 19


class TestRealResponseValidators:
    def test_enhance_success_detected(self):
        assert is_enhance_response(ENHANCE_SUCCESS_LOG) is True

    def test_enhance_maintain_detected(self):
        assert is_enhance_response(ENHANCE_MAINTAIN_LOG) is True

    def test_enhance_destroy_detected(self):
        assert is_enhance_response(ENHANCE_DESTROY_LOG) is True

    def test_advanced_enhance_detected(self):
        assert is_enhance_response(ADVANCED_ENHANCE_LOG) is True

    def test_sell_detected(self):
        assert is_sell_response(SELL_LOG) is True

    def test_cannot_sell_detected(self):
        assert is_sell_response(CANNOT_SELL_LOG) is True

    def test_profile_detected(self):
        assert is_profile_response(PROFILE_NEW_LOG) is True

    def test_swap_detected(self):
        assert is_swap_response(SWAP_LOG) is True

    def test_swap_empty_storage_detected(self):
        assert is_swap_response(SWAP_EMPTY_STORAGE_LOG) is True


class TestRealGoldExtraction:
    def test_from_enhance(self):
        assert extract_last_gold(ENHANCE_SUCCESS_LOG) == 2248731

    def test_from_sell(self):
        assert extract_last_gold(SELL_LOG) == 2258727

    def test_from_profile(self):
        assert extract_last_gold(PROFILE_NEW_LOG) == 27529426

    def test_from_destroy(self):
        assert extract_last_gold(ENHANCE_DESTROY_LOG) == 3377696


class TestRealShardsExtraction:
    def test_from_profile(self):
        assert extract_last_shards(PROFILE_NEW_LOG) == 84

    def test_from_profile_old(self):
        assert extract_last_shards(PROFILE_OLD_LOG) == 28
