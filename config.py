"""Typed application configuration with JSON persistence."""

import json
from dataclasses import dataclass
from typing import ClassVar, Optional


@dataclass
class AppConfig:
    min_gold_limit: int = 0
    fixed_x: Optional[int] = None
    fixed_y: Optional[int] = None
    drag_offset: int = 550
    max_action_retry: int = 3
    command_response_poll_delay: float = 3.0
    max_response_wait_retry: int = 8
    log_capture_expand_step: int = 140
    max_log_capture_expand_retry: int = 4
    advanced_enhance_start_level: int = 0
    advanced_enhance_shard_cost: int = 10
    log_buffer_size: int = 3000
    max_log_fail: int = 10
    enable_remote_control: bool = False
    remote_poll_interval: float = 5.0

    _KEY_MAP: ClassVar[dict[str, str]] = {
        "MIN_GOLD_LIMIT": "min_gold_limit",
        "FIXED_X": "fixed_x",
        "FIXED_Y": "fixed_y",
        "DRAG_OFFSET": "drag_offset",
        "MAX_ACTION_RETRY": "max_action_retry",
        "COMMAND_RESPONSE_POLL_DELAY": "command_response_poll_delay",
        "MAX_RESPONSE_WAIT_RETRY": "max_response_wait_retry",
        "LOG_CAPTURE_EXPAND_STEP": "log_capture_expand_step",
        "MAX_LOG_CAPTURE_EXPAND_RETRY": "max_log_capture_expand_retry",
        "ADVANCED_ENHANCE_START_LEVEL": "advanced_enhance_start_level",
        "ADVANCED_ENHANCE_SHARD_COST": "advanced_enhance_shard_cost",
        "LOG_BUFFER_SIZE": "log_buffer_size",
        "MAX_LOG_FAIL": "max_log_fail",
        "ENABLE_REMOTE_CONTROL": "enable_remote_control",
        "REMOTE_POLL_INTERVAL": "remote_poll_interval",
    }

    @classmethod
    def load(cls, path: str) -> "AppConfig":
        config = cls()
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return config

        for json_key, field_name in cls._KEY_MAP.items():
            if json_key in data:
                setattr(config, field_name, data[json_key])
        return config

    def save(self, path: str) -> None:
        data = {}
        for json_key, field_name in self._KEY_MAP.items():
            data[json_key] = getattr(self, field_name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
