"""Thread-safe application state replacing global variables."""

import threading

from models import RestartSignal


class AppState:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._paused: bool = False
        self._paused_remote: bool = False
        self._restart_requested: bool = False
        self._timeline_step: int = 0
        self._unpause_event = threading.Event()
        self._unpause_event.set()  # initially not paused

    @property
    def paused(self) -> bool:
        with self._lock:
            return self._paused

    @property
    def paused_remote(self) -> bool:
        with self._lock:
            return self._paused_remote

    def toggle_pause(self, remote: bool = False) -> bool:
        with self._lock:
            self._paused = not self._paused
            if self._paused:
                self._paused_remote = remote
                self._unpause_event.clear()
            else:
                self._paused_remote = False
                self._unpause_event.set()
            return self._paused

    @property
    def restart_requested(self) -> bool:
        with self._lock:
            return self._restart_requested

    def request_restart(self) -> None:
        with self._lock:
            self._restart_requested = True
            # Unblock any paused wait so restart is detected immediately
            self._unpause_event.set()

    def clear_restart(self) -> None:
        with self._lock:
            self._restart_requested = False
            self._paused = False
            self._paused_remote = False
            self._unpause_event.set()

    @property
    def timeline_step(self) -> int:
        with self._lock:
            return self._timeline_step

    def next_timeline_step(self) -> int:
        with self._lock:
            self._timeline_step += 1
            return self._timeline_step

    def reset_timeline(self) -> None:
        with self._lock:
            self._timeline_step = 0

    def check_interrupts(self) -> None:
        """Raise RestartSignal if restart requested; block while paused."""
        with self._lock:
            if self._restart_requested:
                raise RestartSignal()
            if not self._paused:
                return
        # Wait atomically for unpause or restart (no polling)
        self._unpause_event.wait()
        with self._lock:
            if self._restart_requested:
                raise RestartSignal()
