"""Concrete ChatIO implementation using pyautogui + pyperclip."""

import time

import pyautogui
import pyperclip

from config import AppConfig
from state import AppState
from chat_io.protocol import ChatIO


class KakaoTalkIO(ChatIO):
    def __init__(
        self,
        input_x: int,
        input_y: int,
        log_start_y: int,
        config: AppConfig,
        state: AppState,
    ) -> None:
        self._input_x = input_x
        self._input_y = input_y
        self._log_start_y = log_start_y
        self._config = config
        self._state = state

    def send_command(self, text: str) -> None:
        self._state.check_interrupts()

        pyautogui.click(self._input_x, self._input_y)
        pyautogui.hotkey("ctrl", "a")
        time.sleep(0.05)
        pyautogui.press("backspace")

        pyperclip.copy("")

        for _ in range(5):
            self._state.check_interrupts()
            pyperclip.copy(text)
            time.sleep(0.05)

            current_clip = pyperclip.paste().strip()
            if current_clip and len(current_clip) > max(len(text) + 8, 40):
                pyperclip.copy("")
                continue

            if current_clip == text:
                time.sleep(0.05)
                pyautogui.hotkey("ctrl", "v")
                time.sleep(0.1)
                pyautogui.press("enter")
                time.sleep(0.05)
                pyautogui.press("enter")
                return

    def read_chat_log(self) -> str:
        self._state.check_interrupts()

        previous_clipboard = pyperclip.paste()
        last_log = ""

        for attempt in range(self._config.max_log_capture_expand_retry + 1):
            adjusted_start_y = max(
                0,
                self._log_start_y
                - (attempt * self._config.log_capture_expand_step),
            )
            log = self._drag_copy(adjusted_start_y)
            last_log = log

            if log.strip() and log != previous_clipboard:
                return log[-self._config.log_buffer_size :]

            if attempt < self._config.max_log_capture_expand_retry and (
                not log.strip() or log == previous_clipboard
            ):
                time.sleep(0.1)
                continue
            break

        return last_log[-self._config.log_buffer_size :] if last_log else ""

    def get_mouse_position(self) -> tuple[int, int]:
        return pyautogui.position()

    def _drag_copy(self, start_y: int) -> str:
        pyautogui.moveTo(self._input_x, start_y)
        pyautogui.mouseDown()
        time.sleep(0.1)
        pyautogui.moveTo(self._input_x, self._input_y, duration=0.4)
        time.sleep(0.1)
        pyautogui.mouseUp()

        pyautogui.hotkey("ctrl", "c")
        pyautogui.click(self._input_x, self._input_y)
        return pyperclip.paste()
