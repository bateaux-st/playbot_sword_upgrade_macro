"""Unit tests for EnhanceStats — in-memory accumulation + flush."""

import json
import os

import pytest

from stats import EnhanceStats


class TestEnhanceStatsRecord:
    def test_record_marks_dirty(self):
        stats = EnhanceStats()
        assert stats.dirty is False
        stats.record("normal", 5, 6)
        assert stats.dirty is True

    def test_record_accumulates(self):
        stats = EnhanceStats()
        stats.record("normal", 5, 6)
        stats.record("normal", 5, 6)
        stats.record("normal", 5, 4)

        rows = stats.get_transition_rows("normal")
        assert len(rows) == 2

        success_row = next(r for r in rows if r["end"] == 6)
        assert success_row["count"] == 2
        assert success_row["attempts"] == 3

        fail_row = next(r for r in rows if r["end"] == 4)
        assert fail_row["count"] == 1

    def test_record_invalid_type(self):
        stats = EnhanceStats()
        stats.record("invalid", 5, 6)
        assert stats.dirty is False

    def test_record_none_levels(self):
        stats = EnhanceStats()
        stats.record("normal", None, 6)
        assert stats.dirty is False
        stats.record("normal", 5, None)
        assert stats.dirty is False

    def test_record_advanced(self):
        stats = EnhanceStats()
        stats.record("advanced", 0, 3)
        rows = stats.get_transition_rows("advanced")
        assert len(rows) == 1
        assert rows[0]["start"] == 0
        assert rows[0]["end"] == 3


class TestEnhanceStatsFlush:
    def test_flush_writes_json(self, tmp_path):
        stats_path = str(tmp_path / "stats.json")
        stats = EnhanceStats()
        stats.record("normal", 5, 6)
        stats.record("normal", 5, 4)

        assert stats.flush(stats_path) is True
        assert stats.dirty is False

        with open(stats_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["normal"]["attempts"]["5"] == 2

    def test_flush_skips_when_clean(self, tmp_path):
        stats_path = str(tmp_path / "stats.json")
        stats = EnhanceStats()
        assert stats.flush(stats_path) is True
        assert not os.path.exists(stats_path)


class TestEnhanceStatsLoad:
    def test_load_existing(self, tmp_path):
        stats_path = str(tmp_path / "stats.json")
        data = {
            "version": 1,
            "normal": {
                "attempts": {"5": 10},
                "transitions": {"5": {"6": 7, "4": 3}},
            },
            "advanced": {"attempts": {}, "transitions": {}},
        }
        with open(stats_path, "w") as f:
            json.dump(data, f)

        stats = EnhanceStats.load(stats_path)
        rows = stats.get_transition_rows("normal")
        assert len(rows) == 2

    def test_load_nonexistent(self):
        stats = EnhanceStats.load("/nonexistent/path.json")
        assert stats.get_transition_rows("normal") == []

    def test_load_corrupt(self, tmp_path):
        stats_path = str(tmp_path / "bad.json")
        with open(stats_path, "w") as f:
            f.write("not json")
        stats = EnhanceStats.load(stats_path)
        assert stats.get_transition_rows("normal") == []


class TestFormatReport:
    def test_empty_report(self):
        stats = EnhanceStats()
        report = stats.format_report()
        assert "\uae30\ub85d \uc5c6\uc74c" in report

    def test_report_with_data(self):
        stats = EnhanceStats()
        stats.record("normal", 5, 6)
        stats.record("normal", 5, 4)
        report = stats.format_report()
        assert "+5 \uc2dc\ub3c4: 2\ud68c" in report
        assert "+5 -> +6" in report
        assert "+5 -> +4" in report
