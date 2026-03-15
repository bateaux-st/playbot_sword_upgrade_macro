"""All regex-based chat log parsers. Pure functions — no I/O, no state."""
import re
from typing import Callable, Optional
from models import ActionResult, ProfileState, WeaponState

WEAPON_PATTERN = re.compile(r"\[\+(\d+)\]\s*([^\n\r\[]+)")
BOT_PREFIX = "@플레이봇 "
BOT_TAG = "[플레이봇]"


def parse_int(text: str) -> int:
    return int(text.replace(",", ""))


def clean_weapon_name(name: str) -> str:
    name = re.sub(r"\s+", " ", name.strip())
    if "』" in name:
        name = name.split("』", 1)[0].strip()
    if '"' in name:
        name = name.split('"', 1)[0].strip()
    return re.sub(r"\s+", " ", name).strip()


def parse_weapon_text(text: str) -> Optional[WeaponState]:
    matches = WEAPON_PATTERN.findall(text)
    if not matches:
        return None
    level, name = matches[-1]
    return WeaponState(level=int(level), name=clean_weapon_name(name))


def parse_profile_weapon(log: str, label: str) -> Optional[WeaponState]:
    match = re.search(rf"● {label}:\s*(.+)", log)
    if not match:
        return None
    value = match.group(1).strip()
    if value == "없음":
        return None
    return parse_weapon_text(value)


def parse_swap_weapon(
    log: str, icon: str, label: str
) -> Optional[WeaponState]:
    match = re.search(rf"{re.escape(icon)}\s*{label}:\s*(.+)", log)
    if not match:
        return None
    value = match.group(1).strip()
    if value == "없음":
        return None
    return parse_weapon_text(value)


def extract_last_gold(log: str) -> Optional[int]:
    patterns = (
        r"\U0001f4b0(?:현재\s*)?(?:보유\s*)?골드:\s*([\d,]+)\s*G",
        r"남은 골드:\s*([\d,]+)\s*G",
    )
    for pattern in patterns:
        matches = re.findall(pattern, log)
        if matches:
            return parse_int(matches[-1])
    return None


def extract_last_shards(log: str) -> Optional[int]:
    matches = re.findall(
        r"\U0001f320\s*(?:보유\s*)?별의 파편:\s*([\d,]+)개", log
    )
    if matches:
        return parse_int(matches[-1])
    return None


def parse_profile_state(log: str) -> ProfileState:
    return ProfileState(
        equipped=parse_profile_weapon(log, "장착 검"),
        stored=parse_profile_weapon(log, "보관 검"),
        gold=extract_last_gold(log),
        shards=extract_last_shards(log),
    )


def parse_swap_state(log: str) -> ProfileState:
    return ProfileState(
        equipped=parse_swap_weapon(log, "⚔️", "장착"),
        stored=parse_swap_weapon(log, "\U0001f4e6", "보관"),
        gold=extract_last_gold(log),
        shards=extract_last_shards(log),
    )


def parse_enhance_result(
    log: str,
    is_hidden_fn: Callable[[Optional[WeaponState]], bool],
) -> ActionResult:
    result = ActionResult(
        log=log,
        gold=extract_last_gold(log),
        shards=extract_last_shards(log),
    )
    if "강화 중이니 잠깐 기다리도록" in log:
        result.outcome = "busy"
        return result
    if "골드가 부족해" in log:
        result.outcome = "no_gold"
        return result
    if "상급강화가 불가능한" in log:
        result.outcome = "advanced_unavailable"
        result.weapon = parse_weapon_text(log)
        result.is_hidden = is_hidden_fn(result.weapon)
        return result
    if "강화 성공" in log:
        result.outcome = "success"
    elif "강화 유지" in log:
        result.outcome = "maintain"
    elif "강화 파괴" in log:
        result.outcome = "destroy"
    elif "상급강화" in log and "→" in log:
        result.outcome = "advanced_success"
    if "획득 검:" in log:
        result.weapon = parse_weapon_text(log.split("획득 검:")[-1])
    else:
        result.weapon = parse_weapon_text(log)
    result.is_hidden = is_hidden_fn(result.weapon)
    return result


def parse_sell_result(
    log: str,
    is_hidden_fn: Callable[[Optional[WeaponState]], bool],
) -> ActionResult:
    result = ActionResult(
        log=log,
        gold=extract_last_gold(log),
        shards=extract_last_shards(log),
    )
    if "0강" in log and "판매" in log:
        result.outcome = "not_sellable"
    elif "새로운 검 획득:" in log or "획득 검:" in log:
        result.outcome = "sold"
    else:
        result.outcome = "unknown"
    if "새로운 검 획득:" in log:
        result.weapon = parse_weapon_text(log.split("새로운 검 획득:")[-1])
    elif "획득 검:" in log:
        result.weapon = parse_weapon_text(log.split("획득 검:")[-1])
    else:
        result.weapon = parse_weapon_text(log)
    result.is_hidden = is_hidden_fn(result.weapon)
    return result


def build_command_variants(command_text: str) -> list[str]:
    if not command_text:
        return []
    normalized = " ".join(str(command_text).split())
    variants = {normalized}
    if normalized.startswith("/"):
        variants.add(f"{BOT_PREFIX}{normalized[1:]}")
    elif normalized.startswith(BOT_PREFIX):
        variants.add(f"/{normalized[len(BOT_PREFIX):]}")
    return [v for v in variants if v]


def is_waiting_for_command_response(log: str, command_text: str) -> bool:
    if not log or not command_text:
        return False
    variants = build_command_variants(command_text)
    if not variants:
        return False
    last_bot_index = log.rfind(BOT_TAG)
    last_command_index = max(
        (log.rfind(variant) for variant in variants), default=-1
    )
    return last_command_index != -1 and last_command_index > last_bot_index


def is_profile_response(log: str) -> bool:
    return BOT_TAG in log or "● 장착 검:" in log


def is_advanced_enhance_response(log: str) -> bool:
    """상급강화 결과 확인 (중간 대사 제외, 실제 결과만 매칭)."""
    if "상급강화가 불가능한" in log:
        return True
    if "상급강화" in log and "획득 검:" in log:
        return True
    # 일반 강화 결과도 매칭 (폴백)
    return any(m in log for m in ("강화 성공", "강화 유지", "강화 파괴", "골드가 부족해"))


def is_enhance_response(log: str) -> bool:
    markers = (
        "강화 성공",
        "강화 유지",
        "강화 파괴",
        "강화 중이니 잠깐 기다리도록",
        "골드가 부족해",
        "상급강화",
        "상급강화가 불가능한",
    )
    return any(marker in log for marker in markers)


def is_sell_response(log: str) -> bool:
    markers = (
        "〖검판매〗",
        "새로운 검 획득:",
        "0강검은 가치가 없어서 판매할 수없다네.",
        "\U0001f528 대장장이에게 검의 강화를 의뢰하시겠습니까?",
    )
    return any(marker in log for marker in markers)


def is_swap_response(log: str) -> bool:
    return "교체 완료" in log or "⚔️ 장착:" in log or "\U0001f4e6 보관:" in log


def is_fusion_response(log: str) -> bool:
    markers = (
        "합성 성공",
        "합성 실패",
        "전설의 대장장이",
        "합성을 시도하려면",
    )
    return any(marker in log for marker in markers)


def parse_fusion_result(
    log: str,
    is_hidden_fn: Callable[[Optional[WeaponState]], bool],
) -> ActionResult:
    result = ActionResult(
        log=log,
        gold=extract_last_gold(log),
        shards=extract_last_shards(log),
    )
    if "합성 성공" in log:
        result.outcome = "fusion_success"
    elif "합성 실패" in log:
        result.outcome = "fusion_fail"
    else:
        result.outcome = "unknown"
    if "획득 검:" in log:
        result.weapon = parse_weapon_text(log.split("획득 검:")[-1])
    else:
        result.weapon = parse_weapon_text(log)
    result.is_hidden = is_hidden_fn(result.weapon)
    return result
