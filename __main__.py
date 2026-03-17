"""Entry point — stdio setup, hotkeys, main loop."""
import io
import sys
import time


def _enable_vt_processing() -> None:
    """콘솔에서 ANSI 이스케이프 시퀀스를 처리하도록 활성화한다."""
    import ctypes
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
    mode = ctypes.c_ulong()
    if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
        mode.value |= 0x0004  # ENABLE_VIRTUAL_TERMINAL_PROCESSING
        kernel32.SetConsoleMode(handle, mode)


def _ensure_console_size(min_cols: int = 120, min_lines: int = 50) -> None:
    """콘솔 크기가 최소값 미만이면 강제로 설정한다."""
    import os
    try:
        size = os.get_terminal_size()
        cols = max(size.columns, min_cols)
        lines = max(size.lines, min_lines)
        if size.columns < min_cols or size.lines < min_lines:
            os.system(f"mode con: cols={cols} lines={lines}")
    except OSError:
        os.system(f"mode con: cols={min_cols} lines={min_lines}")


def setup_stdio() -> None:
    _enable_vt_processing()
    _ensure_console_size()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(
            encoding="utf-8", line_buffering=True, write_through=True
        )
    else:
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer,
            encoding="utf-8",
            line_buffering=True,
            write_through=True,
        )
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(
            encoding="utf-8", line_buffering=True, write_through=True
        )
    else:
        sys.stderr = io.TextIOWrapper(
            sys.stderr.buffer,
            encoding="utf-8",
            line_buffering=True,
            write_through=True,
        )


def main() -> None:
    import pyautogui

    pyautogui.FAILSAFE = True
    setup_stdio()
    import paths
    from actions import GameActions
    from config import AppConfig
    from constants import MODE_FUSION, MODE_HIDDEN, FUSION_TARGET_LEVEL
    from chat_io.kakaotalk import KakaoTalkIO
    from macro_logger import MacroLogger
    from models import RestartSignal
    from modes import MODE_REGISTRY, ModeParams, HiddenModeParams
    from state import AppState
    from stats import EnhanceStats
    from ui.menu import MainMenu
    from weapon_catalog import WeaponCatalog

    config_path = paths.resolve_runtime_path("sword_config.json")
    stats_path = paths.resolve_runtime_path("enhance_stats.json")
    config = AppConfig.load(config_path)
    catalog = WeaponCatalog.from_csv(
        paths.resolve_bundle_path("weapon_catalog.csv")
    )
    stats = EnhanceStats.load(stats_path)
    state = AppState()
    logger = MacroLogger(state, stats=stats)
    menu = MainMenu(config, stats)
    logger.status("✅ 설정 파일 로드 완료")
    # Register hotkeys
    try:
        import keyboard

        keyboard.add_hotkey("F8", lambda: _on_pause(state, logger))
        keyboard.add_hotkey("F9", lambda: _on_restart(state, logger))
        keyboard.add_hotkey("F3", lambda: logger.toggle_stats_tab())
    except Exception as e:
        logger.status(f"단축키 등록 실패: {e}")
    try:
        while True:
            state.clear_restart()
            mode_id = menu.show()
            if mode_id == "settings":
                menu.show_settings(config_path)
                continue
            if mode_id == "stats":
                menu.show_stats()
                continue
            if mode_id == MODE_FUSION:
                target_level = FUSION_TARGET_LEVEL
            else:
                target_level = menu.prompt_target_level()
                if target_level is None:
                    continue
            use_shards = menu.prompt_use_shards()
            if mode_id == MODE_HIDDEN:
                auto_sell = menu.prompt_auto_sell()
                params = HiddenModeParams(
                    target_level=target_level,
                    use_shards=use_shards,
                    auto_sell=auto_sell,
                )
            else:
                params = ModeParams(
                    target_level=target_level,
                    use_shards=use_shards,
                )
            # Resolve coordinates
            if config.fixed_x is not None and config.fixed_y is not None:
                input_x = config.fixed_x
                input_y = config.fixed_y
                logger.status(
                    f"저장된 좌표 사용: ({input_x}, {input_y})"
                )
            else:
                result = menu.capture_input_position()
                if result is None:
                    continue
                input_x, input_y = result
                config.fixed_x = input_x
                config.fixed_y = input_y
                config.save(config_path)
            log_start_y = input_y - config.drag_offset
            chat_io = KakaoTalkIO(
                input_x, input_y, log_start_y, config, state
            )
            actions = GameActions(
                chat_io, config, state, logger, catalog, stats
            )
            logger.reset_session(
                mode_id,
                params.target_level,
                params.use_shards,
                getattr(params, "auto_sell", False),
            )
            logger.start_live()
            try:
                mode_cls = MODE_REGISTRY[mode_id]
                mode_cls(actions, logger, params).run()
            except RestartSignal:
                logger.status("재시작 처리 중...")
                continue
            except Exception as e:
                logger.stop_live()
                import traceback

                print(f"\n에러 발생: {e}")
                traceback.print_exc()
                input("\n엔터를 누르면 메뉴로 돌아갑니다...")
                continue
            finally:
                logger.stop_live()
                stats.flush(stats_path)
            if input("R 입력 시 재시작: ").lower() != "r":
                break
    except KeyboardInterrupt:
        print("\n사용자 종료")
    except Exception as e:
        import traceback

        print(f"\n에러 발생: {e}")
        traceback.print_exc()
        input("\n엔터를 누르면 종료합니다...")
    finally:
        stats.flush(stats_path)


def _on_pause(state: "AppState", logger: "MacroLogger") -> None:
    is_paused = state.toggle_pause()
    logger.update_pause_state(is_paused)
    if is_paused:
        logger.status("⏸ 일시정지됨 (F8을 눌러 재개)")
    else:
        logger.status("▶ 재개")


def _on_restart(state: "AppState", logger: "MacroLogger") -> None:
    if not state.restart_requested:
        logger.status("\U0001f504 재시작 요청! 메뉴로 이동합니다...")
        state.request_restart()
if __name__ == "__main__":
    main()
