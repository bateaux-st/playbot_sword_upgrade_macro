"""Unit tests for AppConfig — load, save, defaults."""

import json
import os
import tempfile

import pytest

from config import AppConfig


class TestAppConfigDefaults:
    def test_default_values(self):
        config = AppConfig()
        assert config.min_gold_limit == 0
        assert config.fixed_x is None


class TestAppConfigLoad:
    def test_load_nonexistent_file(self):
        config = AppConfig.load("/nonexistent/path.json")
        assert config.min_gold_limit == 0  # defaults

    def test_load_valid_file(self, tmp_path):
        config_path = str(tmp_path / "config.json")
        data = {
            "MIN_GOLD_LIMIT": 5000,
        }
        with open(config_path, "w") as f:
            json.dump(data, f)

        config = AppConfig.load(config_path)
        assert config.min_gold_limit == 5000

    def test_load_invalid_json(self, tmp_path):
        config_path = str(tmp_path / "bad.json")
        with open(config_path, "w") as f:
            f.write("not valid json{{{")

        config = AppConfig.load(config_path)
        assert config.min_gold_limit == 0  # defaults


class TestAppConfigSave:
    def test_save_and_load_roundtrip(self, tmp_path):
        config_path = str(tmp_path / "config.json")
        config = AppConfig()
        config.min_gold_limit = 5000
        config.fixed_x = 100

        config.save(config_path)

        loaded = AppConfig.load(config_path)
        assert loaded.min_gold_limit == 5000
        assert loaded.fixed_x == 100

    def test_save_creates_file(self, tmp_path):
        config_path = str(tmp_path / "new_config.json")
        assert not os.path.exists(config_path)

        config = AppConfig()
        config.save(config_path)

        assert os.path.exists(config_path)
        with open(config_path) as f:
            data = json.load(f)
        assert "MIN_GOLD_LIMIT" in data
