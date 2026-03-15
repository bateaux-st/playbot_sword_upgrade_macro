"""Console menu rendering and input handling."""
from typing import Optional
from config import AppConfig
from constants import MODE_FUSION, MODE_HIDDEN, MODE_MONEY, MODE_TARGET
from stats import EnhanceStats


class MainMenu:
    def __init__(self, config: AppConfig, stats: EnhanceStats) -> None:
        self._config = config
        self._stats = stats

    def show(self) -> str:
        while True:
            cfg = self._config
            pos_str = (
                f"({cfg.fixed_x}, {cfg.fixed_y})"
                if cfg.fixed_x is not None
                else "미설정"
            )
            print("\n" * 3)
            print("=== 카카오톡 검키우기 v11.0 ===")
            print(f"   [자산] 최소 골드: {cfg.min_gold_limit:,}G")
            print(f"   [좌표] 입력창: {pos_str}")
            print("---------------------------------------")
            print("1. 모든 검 강화")
            print("2. 히든 검 강화")
            print("3. 단순 돈벌기")
            print("4. 21강 만들기")
            print("---------------------------------------")
            print("8. 누적 강화 확률 보기")
            print("9. 옵션 설정")
            print("=======================================")
            try:
                sel = input("선택: ").strip()
            except EOFError:
                raise KeyboardInterrupt
            if sel == "9":
                return "settings"
            if sel == "8":
                return "stats"
            if sel in {MODE_TARGET, MODE_HIDDEN, MODE_MONEY, MODE_FUSION}:
                return sel
            print("잘못된 입력")

    def show_settings(self, config_path: str) -> None:
        cfg = self._config
        while True:
            pos_str = (
                f"({cfg.fixed_x}, {cfg.fixed_y})"
                if cfg.fixed_x is not None
                else "미설정"
            )
            print("\n[옵션 설정]")
            print(f"1. 최소 골드 ({cfg.min_gold_limit}G)")
            print(f"2. 좌표 설정 ({pos_str})")
            print("3. 좌표 초기화")
            print("4. 뒤로 가기")
            opt = input("변경할 번호: ").strip()
            if opt == "1":
                try:
                    cfg.min_gold_limit = int(input("값: "))
                    cfg.save(config_path)
                except (ValueError, OSError):
                    pass
            elif opt == "2":
                result = self.capture_input_position()
                if result is not None:
                    cfg.fixed_x, cfg.fixed_y = result
                    cfg.save(config_path)
                    print(f"  저장 완료: ({cfg.fixed_x}, {cfg.fixed_y})")
            elif opt == "3":
                cfg.fixed_x = None
                cfg.fixed_y = None
                cfg.save(config_path)
                print("  좌표 초기화됨")
            elif opt in {"4", ""}:
                break

    def show_stats(self) -> None:
        print(self._stats.format_report())
        input("\n 엔터를 누르면 메뉴로 돌아갑니다...")

    @staticmethod
    def capture_input_position() -> Optional[tuple[int, int]]:
        import time
        import keyboard as kb
        import pyautogui

        print("[좌표 설정] 마우스를 입력창으로 이동하세요 (엔터: 확정 / ESC: 취소)")
        # 이전 키 입력 무시
        while kb.is_pressed("enter") or kb.is_pressed("esc"):
            time.sleep(0.05)

        while True:
            x, y = pyautogui.position()
            print(f"\r  현재 위치: ({x}, {y})     ", end="", flush=True)
            if kb.is_pressed("enter"):
                print(f"\n  확정: ({x}, {y})")
                return x, y
            if kb.is_pressed("esc"):
                print("\n  취소됨")
                return None
            time.sleep(0.05)

    @staticmethod
    def prompt_target_level() -> Optional[int]:
        raw = input("\n몇 강까지?: ").strip()
        if not raw or not raw.isdigit():
            print("잘못된 입력입니다. 이전 단계로 돌아갑니다.")
            return None
        value = int(raw)
        if value <= 0:
            print("잘못된 입력입니다. 이전 단계로 돌아갑니다.")
            return None
        return value

    @staticmethod
    def prompt_use_shards() -> bool:
        choice = input("별의 파편 사용? (y/N): ").strip().lower()
        return choice in {"y", "yes"}

    @staticmethod
    def prompt_auto_sell() -> bool:
        print("1. 목표 달성 시 멈춤")
        print("2. 판매 후 다시 뽑기(무한)")
        return input("선택: ").strip() == "2"
