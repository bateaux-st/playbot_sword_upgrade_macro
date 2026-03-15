"""Unit tests for AppState — thread-safe pause/restart/timeline."""

import threading
import time

import pytest

from models import RestartSignal
from state import AppState


class TestAppStatePause:
    def test_initial_not_paused(self):
        state = AppState()
        assert state.paused is False

    def test_toggle_pause(self):
        state = AppState()
        result = state.toggle_pause()
        assert result is True
        assert state.paused is True

        result = state.toggle_pause()
        assert result is False
        assert state.paused is False


class TestAppStateRestart:
    def test_initial_not_requested(self):
        state = AppState()
        assert state.restart_requested is False

    def test_request_restart(self):
        state = AppState()
        state.request_restart()
        assert state.restart_requested is True

    def test_clear_restart(self):
        state = AppState()
        state.request_restart()
        state.toggle_pause()
        state.clear_restart()
        assert state.restart_requested is False
        assert state.paused is False


class TestAppStateTimeline:
    def test_initial_step_zero(self):
        state = AppState()
        assert state.timeline_step == 0

    def test_next_increments(self):
        state = AppState()
        assert state.next_timeline_step() == 1
        assert state.next_timeline_step() == 2
        assert state.next_timeline_step() == 3

    def test_reset_timeline(self):
        state = AppState()
        state.next_timeline_step()
        state.next_timeline_step()
        state.reset_timeline()
        assert state.timeline_step == 0


class TestCheckInterrupts:
    def test_raises_on_restart(self):
        state = AppState()
        state.request_restart()
        with pytest.raises(RestartSignal):
            state.check_interrupts()

    def test_passes_when_clear(self):
        state = AppState()
        state.check_interrupts()  # should not raise

    def test_blocks_while_paused_then_resumes(self):
        state = AppState()
        state.toggle_pause()
        resumed = threading.Event()

        def check_and_signal():
            state.check_interrupts()
            resumed.set()

        t = threading.Thread(target=check_and_signal, daemon=True)
        t.start()

        time.sleep(0.2)
        assert not resumed.is_set()

        state.toggle_pause()  # unpause
        resumed.wait(timeout=2.0)
        assert resumed.is_set()


class TestThreadSafety:
    def test_concurrent_toggle(self):
        state = AppState()
        toggle_count = 100

        def toggle_many():
            for _ in range(toggle_count):
                state.toggle_pause()

        threads = [threading.Thread(target=toggle_many) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # After even number of toggles per thread, should be False
        # 4 threads * 100 toggles = 400 total toggles (even)
        assert state.paused is False

    def test_concurrent_timeline(self):
        state = AppState()
        increment_count = 100

        def increment_many():
            for _ in range(increment_count):
                state.next_timeline_step()

        threads = [threading.Thread(target=increment_many) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert state.timeline_step == 400
