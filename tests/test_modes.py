"""Unit tests for mode runners with mock ChatIO."""

import pytest

from actions import GameActions
from modes.base import ModeParams, MODE_REGISTRY
from modes.target import TargetMode
from modes.money import MoneyMode
from constants import MODE_TARGET, MODE_HIDDEN, MODE_MONEY
from tests.conftest import FakeChatIO


class TestModeRegistry:
    def test_all_modes_registered(self):
        assert MODE_TARGET in MODE_REGISTRY
        assert MODE_HIDDEN in MODE_REGISTRY
        assert MODE_MONEY in MODE_REGISTRY

    def test_target_mode_class(self):
        assert MODE_REGISTRY[MODE_TARGET] is TargetMode


class TestRunTargetEnhancement:
    def test_already_reached(self, app_config, app_state, logger, stats, catalog):
        io = FakeChatIO([
            "[\ud50c\ub808\uc774\ubd07]\n\u25cf \uc7a5\ucc29 \uac80: [+10] \uac15\ucca0\uc2ec \uac80\n\u25cf \ubcf4\uad00 \uac80: \uc5c6\uc74c\n\U0001f4b0\ubcf4\uc720 \uace8\ub4dc: 5,000 G"
        ])
        actions = GameActions(io, app_config, app_state, logger, catalog, stats)
        outcome, weapon = actions.run_target_enhancement(10)
        assert outcome == "target_reached"
        assert weapon.level == 10

    def test_enhance_to_target(self, app_config, app_state, logger, stats, catalog):
        io = FakeChatIO([
            "[\ud50c\ub808\uc774\ubd07]\n\u25cf \uc7a5\ucc29 \uac80: [+2] \uac15\ucca0\uc2ec \uac80\n\u25cf \ubcf4\uad00 \uac80: \uc5c6\uc74c\n\U0001f4b0\ubcf4\uc720 \uace8\ub4dc: 5,000 G",
            "[\ud50c\ub808\uc774\ubd07] \uac15\ud654 \uc131\uacf5! [+3] \uac15\ucca0\uc2ec \uac80\n\U0001f4b0\ubcf4\uc720 \uace8\ub4dc: 4,500 G",
        ])
        actions = GameActions(io, app_config, app_state, logger, catalog, stats)
        outcome, weapon = actions.run_target_enhancement(3)
        assert outcome == "target_reached"
        assert weapon.level == 3
