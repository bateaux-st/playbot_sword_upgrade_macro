"""Tests for remote_control.RemoteCommandPoller."""

import threading
import time

import pytest

from constants import REMOTE_CMD_PAUSE, REMOTE_CMD_RESUME, REMOTE_CMD_STOP
from remote_control import RemoteCommandPoller
from state import AppState
from tests.conftest import FakeChatIO


class TestGetNewPortion:
    def test_empty_old_log(self):
        assert RemoteCommandPoller._get_new_portion("new text", "") == "new text"

    def test_identical_logs(self):
        log = "some chat log"
        assert RemoteCommandPoller._get_new_portion(log, log) == ""

    def test_appended_text(self):
        old = "message1\nmessage2"
        new = "message1\nmessage2\nmessage3"
        assert "message3" in RemoteCommandPoller._get_new_portion(new, old)

    def test_scrolled_window(self):
        old = "msg1\nmsg2\nmsg3"
        new = "msg2\nmsg3\nmsg4"
        portion = RemoteCommandPoller._get_new_portion(new, old)
        assert "msg4" in portion

    def test_completely_different(self):
        old = "completely old"
        new = "completely new"
        assert RemoteCommandPoller._get_new_portion(new, old) == new


class TestHandleCommand:
    def test_pause_when_not_paused(self):
        state = AppState()
        callback_called = []
        poller = RemoteCommandPoller(
            FakeChatIO(), state,
            on_pause=lambda: callback_called.append("pause"),
        )
        poller._handle_command(REMOTE_CMD_PAUSE)
        assert state.paused is True
        assert callback_called == ["pause"]

    def test_pause_when_already_paused(self):
        state = AppState()
        state.toggle_pause()  # already paused
        callback_called = []
        poller = RemoteCommandPoller(
            FakeChatIO(), state,
            on_pause=lambda: callback_called.append("pause"),
        )
        poller._handle_command(REMOTE_CMD_PAUSE)
        assert state.paused is True  # still paused, not toggled
        assert callback_called == []

    def test_resume_when_paused(self):
        state = AppState()
        state.toggle_pause()  # paused
        callback_called = []
        poller = RemoteCommandPoller(
            FakeChatIO(), state,
            on_resume=lambda: callback_called.append("resume"),
        )
        poller._handle_command(REMOTE_CMD_RESUME)
        assert state.paused is False
        assert callback_called == ["resume"]

    def test_resume_when_not_paused(self):
        state = AppState()
        callback_called = []
        poller = RemoteCommandPoller(
            FakeChatIO(), state,
            on_resume=lambda: callback_called.append("resume"),
        )
        poller._handle_command(REMOTE_CMD_RESUME)
        assert state.paused is False  # still not paused
        assert callback_called == []

    def test_stop(self):
        state = AppState()
        callback_called = []
        poller = RemoteCommandPoller(
            FakeChatIO(), state,
            on_stop=lambda: callback_called.append("stop"),
        )
        poller._handle_command(REMOTE_CMD_STOP)
        assert state.restart_requested is True
        assert callback_called == ["stop"]


class TestPollerLifecycle:
    def test_start_stop(self):
        io = FakeChatIO(["some log"])
        state = AppState()
        poller = RemoteCommandPoller(io, state, poll_interval=0.1)
        poller.start()
        assert poller._thread is not None
        assert poller._thread.is_alive()
        poller.stop()
        assert poller._thread is None

    def test_detects_pause_command_via_last_log(self):
        """Not paused: poller reads last_log to detect #일시정지."""
        io = FakeChatIO()
        state = AppState()
        paused_event = threading.Event()

        poller = RemoteCommandPoller(
            io, state,
            poll_interval=0.1,
            on_pause=lambda: paused_event.set(),
        )

        poller.start()
        time.sleep(0.15)
        # Simulate main thread updating last_log
        io.set_last_log(f"[오후 3:00] 사용자: {REMOTE_CMD_PAUSE}")
        assert paused_event.wait(timeout=3.0)
        assert state.paused is True
        poller.stop()

    def test_detects_resume_when_paused(self):
        """Paused via remote: poller does actual read to detect #재개."""
        io = FakeChatIO()
        state = AppState()
        state.toggle_pause(remote=True)  # start paused via remote
        resumed_event = threading.Event()

        poller = RemoteCommandPoller(
            io, state,
            poll_interval=0.1,
            on_resume=lambda: resumed_event.set(),
        )

        io.add_response(f"[오후 3:00] 사용자: {REMOTE_CMD_RESUME}")

        poller.start()
        assert resumed_event.wait(timeout=3.0)
        assert state.paused is False
        poller.stop()

    def test_deduplication(self):
        """Same last_log should not trigger command twice."""
        io = FakeChatIO()
        state = AppState()
        pause_count = []

        poller = RemoteCommandPoller(
            io, state,
            poll_interval=0.1,
            on_pause=lambda: pause_count.append(1),
        )

        log_with_cmd = f"[오후 3:00] 사용자: {REMOTE_CMD_PAUSE}"
        io.set_last_log(log_with_cmd)

        poller.start()
        time.sleep(0.5)
        poller.stop()

        assert len(pause_count) == 1

    def test_sends_confirmation_on_pause(self):
        """Pausing sends [매크로] 일시정지됨 to chat."""
        io = FakeChatIO()
        state = AppState()
        poller = RemoteCommandPoller(io, state, poll_interval=0.1)

        io.set_last_log(f"[오후 3:00] 사용자: {REMOTE_CMD_PAUSE}")
        poller.start()
        time.sleep(0.5)
        poller.stop()

        assert "[매크로] 일시정지됨" in io.texts_sent
