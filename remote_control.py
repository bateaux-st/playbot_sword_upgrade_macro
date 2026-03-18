"""Remote control via KakaoTalk chat commands (#일시정지, #재개, #중단)."""

import threading
from typing import Optional

from chat_io.protocol import ChatIO
from constants import REMOTE_CMD_PAUSE, REMOTE_CMD_RESUME, REMOTE_CMD_STOP
from state import AppState


class RemoteCommandPoller:
    """Daemon thread that polls chat log for remote control commands."""

    def __init__(
        self,
        chat_io: ChatIO,
        state: AppState,
        *,
        poll_interval: float = 5.0,
        on_pause: Optional[callable] = None,
        on_resume: Optional[callable] = None,
        on_stop: Optional[callable] = None,
    ) -> None:
        self._io = chat_io
        self._state = state
        self._poll_interval = poll_interval
        self._on_pause = on_pause
        self._on_resume = on_resume
        self._on_stop = on_stop
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        if self._thread is not None:
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._poll_loop, daemon=True, name="remote-cmd-poller"
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=10.0)
            self._thread = None

    def _poll_loop(self) -> None:
        last_log = ""
        while not self._stop_event.is_set():
            self._stop_event.wait(self._poll_interval)
            if self._stop_event.is_set():
                break

            if self._state.paused_remote:
                # 원격 대기 상태: 직접 드래그-복사로 #재개/#중단 감지
                try:
                    log = self._io.read_chat_log_no_interrupt()
                except Exception:
                    continue
            else:
                # 실행 중 또는 로컬 정지: 메인 스레드 로그 재활용
                log = self._io.last_log

            if log == last_log:
                continue

            new_portion = self._get_new_portion(log, last_log)
            last_log = log

            if not new_portion:
                continue

            for cmd in (REMOTE_CMD_PAUSE, REMOTE_CMD_RESUME, REMOTE_CMD_STOP):
                if cmd in new_portion:
                    self._handle_command(cmd)
                    break  # 한 폴링 사이클에 하나의 커맨드만 처리

    @staticmethod
    def _get_new_portion(new_log: str, old_log: str) -> str:
        """이전 로그와 비교하여 새로 추가된 부분만 반환한다."""
        if not old_log:
            return new_log

        # 이전 로그의 끝부분이 새 로그에서 어디에 있는지 찾기
        # 채팅 로그는 슬라이딩 윈도우이므로 끝부분 매칭
        tail_len = min(len(old_log), 200)
        old_tail = old_log[-tail_len:]
        pos = new_log.find(old_tail)
        if pos >= 0:
            return new_log[pos + tail_len :]

        # 매칭 실패 시 전체 새 로그 반환 (화면이 완전히 바뀜)
        return new_log

    def _handle_command(self, cmd: str) -> None:
        if cmd == REMOTE_CMD_PAUSE:
            if not self._state.paused:
                self._state.toggle_pause(remote=True)
                if self._on_pause:
                    self._on_pause()
                self._io.send_text_no_interrupt("[매크로] 일시정지됨")
        elif cmd == REMOTE_CMD_RESUME:
            if self._state.paused:
                self._state.toggle_pause()
                if self._on_resume:
                    self._on_resume()
                self._io.send_text_no_interrupt("[매크로] 재개됨")
        elif cmd == REMOTE_CMD_STOP:
            if self._on_stop:
                self._on_stop()
            self._io.send_text_no_interrupt("[매크로] 중단됨")
            self._state.request_restart()
