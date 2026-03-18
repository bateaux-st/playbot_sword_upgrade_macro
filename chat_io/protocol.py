"""Abstract I/O port — the seam that makes business logic testable."""

from abc import ABC, abstractmethod


class ChatIO(ABC):
    @abstractmethod
    def send_command(self, text: str) -> None:
        """Type text into the chat input and press Enter."""

    @abstractmethod
    def read_chat_log(self) -> str:
        """Capture current visible chat log text."""

    def read_chat_log_no_interrupt(self) -> str:
        """Read chat log without checking interrupts. For background poller."""
        return self.read_chat_log()

    @property
    def last_log(self) -> str:
        """Return the last successfully read chat log."""
        return ""

    def send_text_no_interrupt(self, text: str) -> None:
        """Send plain text without checking interrupts. For poller use."""

    @abstractmethod
    def get_mouse_position(self) -> tuple[int, int]:
        """Return current (x, y) mouse position."""
