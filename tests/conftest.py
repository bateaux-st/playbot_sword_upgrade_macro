"""Shared test fixtures — FakeChatIO, sample data."""

import os
from collections import deque
from typing import Optional

import pytest

from config import AppConfig
from chat_io.protocol import ChatIO
from macro_logger import MacroLogger
from state import AppState
from stats import EnhanceStats
from weapon_catalog import WeaponCatalog


class FakeChatIO(ChatIO):
    """Test double that replays scripted responses."""

    def __init__(self, responses: Optional[list[str]] = None) -> None:
        self._responses: deque[str] = deque(responses or [])
        self.commands_sent: list[str] = []

    def send_command(self, text: str) -> None:
        self.commands_sent.append(text)

    def read_chat_log(self) -> str:
        return self._responses.popleft() if self._responses else ""

    def get_mouse_position(self) -> tuple[int, int]:
        return (500, 500)

    def add_response(self, text: str) -> None:
        self._responses.append(text)

    def add_responses(self, texts: list[str]) -> None:
        self._responses.extend(texts)


@pytest.fixture
def fake_io():
    return FakeChatIO()


@pytest.fixture
def app_config():
    config = AppConfig()
    config.max_action_retry = 1
    config.max_response_wait_retry = 1
    config.command_response_poll_delay = 0
    return config


@pytest.fixture
def app_state():
    return AppState()


@pytest.fixture
def logger(app_state):
    return MacroLogger(app_state)


@pytest.fixture
def stats():
    return EnhanceStats()


@pytest.fixture
def catalog():
    csv_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "weapon_catalog.csv",
    )
    if os.path.exists(csv_path):
        return WeaponCatalog.from_csv(csv_path)
    return WeaponCatalog()


FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def load_fixture(name: str) -> str:
    path = os.path.join(FIXTURES_DIR, name)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()
