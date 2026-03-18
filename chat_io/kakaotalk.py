"""Concrete ChatIO implementation using pyautogui + pyperclip."""

import ctypes
import ctypes.wintypes
import threading
import time

import pyautogui
import pyperclip

from config import AppConfig
from state import AppState
from chat_io.protocol import ChatIO

_user32 = ctypes.windll.user32
_GA_ROOT = 2
_KAKAOTALK_HEADER_HEIGHT = 110  # 타이틀바 + 프로필 영역


def _get_window_top(x: int, y: int) -> int:
    """입력 좌표가 속한 윈도우의 상단 Y좌표를 반환한다."""
    point = ctypes.wintypes.POINT(x, y)
    hwnd = _user32.WindowFromPoint(point)
    if hwnd:
        hwnd = _user32.GetAncestor(hwnd, _GA_ROOT)
    if not hwnd:
        return 0
    rect = ctypes.wintypes.RECT()
    _user32.GetWindowRect(hwnd, ctypes.byref(rect))
    return rect.top


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
        self._window_top = _get_window_top(input_x, input_y) + _KAKAOTALK_HEADER_HEIGHT
        self._io_lock = threading.Lock()
        self._last_log: str = ""

    def send_command(self, text: str) -> None:
        self._state.check_interrupts()
        with self._io_lock:
            self._send_command_impl(text)

    def _send_command_impl(self, text: str) -> None:
        pyautogui.click(self._input_x, self._input_y)
        pyautogui.hotkey("ctrl", "a")
        time.sleep(0.05)
        pyautogui.press("backspace")

        # @플레이봇 멘션 + 커맨드 2단계 입력
        if text.startswith("@플레이봇 "):
            mention = "@플레이봇"
            cmd = text[len("@플레이봇 "):]
            self._paste_text(mention)
            time.sleep(0.2)
            pyautogui.press("enter")  # 멘션 자동완성 선택
            time.sleep(0.15)
            self._paste_text(cmd)
            time.sleep(0.1)
            pyautogui.press("enter")  # 전송
            time.sleep(0.05)
            pyautogui.press("enter")
        else:
            self._paste_text(text)
            time.sleep(0.1)
            pyautogui.press("enter")
            time.sleep(0.05)
            pyautogui.press("enter")

    def _paste_text(self, text: str) -> None:
        """클립보드를 통해 텍스트를 붙여넣는다."""
        pyperclip.copy("")
        for _ in range(5):
            pyperclip.copy(text)
            time.sleep(0.05)
            current_clip = pyperclip.paste().strip()
            if current_clip and len(current_clip) > max(len(text) + 8, 40):
                pyperclip.copy("")
                continue
            if current_clip == text:
                time.sleep(0.05)
                pyautogui.hotkey("ctrl", "v")
                return

    def read_chat_log(self) -> str:
        self._state.check_interrupts()
        with self._io_lock:
            return self._read_chat_log_impl()

    def read_chat_log_no_interrupt(self) -> str:
        """Read chat log without checking interrupts. For background poller."""
        with self._io_lock:
            return self._read_chat_log_impl()

    def _read_chat_log_impl(self) -> str:
        last_log = ""

        for attempt in range(self._config.max_log_capture_expand_retry + 1):
            adjusted_start_y = max(
                self._window_top,
                self._log_start_y
                - (attempt * self._config.log_capture_expand_step),
            )
            pyperclip.copy("")
            log = self._drag_copy(adjusted_start_y)
            last_log = log

            if log.strip():
                self._last_log = log[-self._config.log_buffer_size :]
                return self._last_log

            if attempt < self._config.max_log_capture_expand_retry:
                time.sleep(0.1)
                continue
            break

        return last_log[-self._config.log_buffer_size :] if last_log else ""

    @property
    def last_log(self) -> str:
        return self._last_log

    def send_text_no_interrupt(self, text: str) -> None:
        """Send plain text without checking interrupts. For poller use."""
        with self._io_lock:
            pyautogui.click(self._input_x, self._input_y)
            self._paste_text(text)
            time.sleep(0.1)
            pyautogui.press("enter")

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
