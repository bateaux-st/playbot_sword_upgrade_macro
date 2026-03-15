"""Enhancement statistics — in-memory accumulation, batch flush."""
import json
import os
from typing import Optional

ENHANCE_STATS_VERSION = 1


def _default_stats() -> dict:
    return {
        "version": ENHANCE_STATS_VERSION,
        "normal": {"attempts": {}, "transitions": {}},
        "advanced": {"attempts": {}, "transitions": {}},
    }


def _normalize(data: object) -> dict:
    stats = _default_stats()
    if not isinstance(data, dict):
        return stats
    stats["version"] = data.get("version", ENHANCE_STATS_VERSION)
    for mode_key in ("normal", "advanced"):
        mode_data = data.get(mode_key, {})
        if not isinstance(mode_data, dict):
            continue
        attempts = mode_data.get("attempts", {})
        transitions = mode_data.get("transitions", {})
        if isinstance(attempts, dict):
            stats[mode_key]["attempts"] = {
                str(k): int(v) for k, v in attempts.items()
            }
        if isinstance(transitions, dict):
            normalized: dict[str, dict[str, int]] = {}
            for start_level, end_map in transitions.items():
                if not isinstance(end_map, dict):
                    continue
                normalized[str(start_level)] = {
                    str(end_level): int(count)
                    for end_level, count in end_map.items()
                }
            stats[mode_key]["transitions"] = normalized
    return stats


class EnhanceStats:
    def __init__(self) -> None:
        self._data: dict = _default_stats()
        self._dirty: bool = False

    @classmethod
    def load(cls, path: str) -> "EnhanceStats":
        instance = cls()
        try:
            with open(path, "r", encoding="utf-8") as handle:
                instance._data = _normalize(json.load(handle))
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            pass
        return instance

    def record(
        self,
        stat_type: str,
        start_level: Optional[int],
        end_level: Optional[int],
    ) -> None:
        if stat_type not in {"normal", "advanced"}:
            return
        if start_level is None or end_level is None:
            return
        mode_stats = self._data[stat_type]
        start_key = str(start_level)
        end_key = str(end_level)
        mode_stats["attempts"][start_key] = (
            mode_stats["attempts"].get(start_key, 0) + 1
        )
        transition_counts = mode_stats["transitions"].setdefault(
            start_key, {}
        )
        transition_counts[end_key] = transition_counts.get(end_key, 0) + 1
        self._dirty = True

    def flush(self, path: str) -> bool:
        if not self._dirty:
            return True
        try:
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(self._data, handle, ensure_ascii=False, indent=2)
            self._dirty = False
            return True
        except OSError:
            return False

    @property
    def dirty(self) -> bool:
        return self._dirty

    def get_transition_rows(self, mode_key: str) -> list[dict]:
        mode_stats = self._data.get(mode_key, {})
        attempts = mode_stats.get("attempts", {})
        transitions = mode_stats.get("transitions", {})
        rows: list[dict] = []
        def sort_key(value: str) -> object:
            try:
                return int(value)
            except (TypeError, ValueError):
                return value
        for start_key in sorted(attempts.keys(), key=sort_key):
            total_attempts = attempts.get(start_key, 0)
            if total_attempts <= 0:
                continue
            end_counts = transitions.get(start_key, {})
            for end_key in sorted(end_counts.keys(), key=sort_key):
                count = end_counts[end_key]
                rate = (count / total_attempts) * 100 if total_attempts else 0.0
                rows.append(
                    {
                        "start": int(start_key),
                        "end": int(end_key),
                        "count": count,
                        "attempts": total_attempts,
                        "rate": rate,
                    }
                )
        return rows

    def format_report(self) -> str:
        lines = ["\n=== 누적 강화 확률 ==="]
        for title, mode_key in (
            ("일반 강화", "normal"),
            ("상급강화", "advanced"),
        ):
            rows = self.get_transition_rows(mode_key)
            lines.append(f"\n[{title}]")
            if not rows:
                lines.append("기록 없음")
                continue
            current_start = None
            for row in rows:
                if current_start != row["start"]:
                    current_start = row["start"]
                    lines.append(
                        f"+{current_start} 시도: {row['attempts']:,}회"
                    )
                lines.append(
                    f"  +{row['start']} -> +{row['end']}: "
                    f"{row['count']:,}/{row['attempts']:,} ({row['rate']:.2f}%)"
                )
        return "\n".join(lines)
