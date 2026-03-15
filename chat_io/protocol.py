"""Abstract I/O port — the seam that makes business logic testable."""

from abc import ABC, abstractmethod


class ChatIO(ABC):
    @abstractmethod
    def send_command(self, text: str) -> None:
        """Type text into the chat input and press Enter."""

    @abstractmethod
    def read_chat_log(self) -> str:
        """Capture current visible chat log text."""

    @abstractmethod
    def get_mouse_position(self) -> tuple[int, int]:
        """Return current (x, y) mouse position."""
