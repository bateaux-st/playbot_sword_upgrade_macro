"""Unified logging with rich TUI — fixed header/footer, scrolling log body."""
import time
from collections import deque
from typing import Optional
from rich.console import Console, Group
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from constants import get_mode_label
from models import WeaponState, describe_weapon, format_metric
from state import AppState
from stats import EnhanceStats

MAX_LOG_LINES = 200


class MacroLogger:
    def __init__(self, state: AppState, stats: Optional["EnhanceStats"] = None) -> None:
        self._state = state
        self._stats = stats
        self._console = Console()
        self._live: Optional[Live] = None
        self._log_lines: deque[str] = deque(maxlen=MAX_LOG_LINES)
        # Header state
        self._mode: str = ""
        self._target_level: int = 0
        self._use_shards: bool = False
        self._auto_sell: bool = False
        self._equipped: Optional[WeaponState] = None
        self._stored: Optional[WeaponState] = None
        self._gold: Optional[int] = None
        self._shards: Optional[int] = None
        self._paused: bool = False
    # ── Public API (unchanged interface) ──

    def status(self, msg: str) -> None:
        line = f"[{time.strftime('%H:%M:%S')}] {msg}"
        self._log_lines.append(line)
        if self._live is not None:
            self._refresh()
        else:
            print(line, flush=True)

    def timeline(self, kind: str, message: str) -> None:
        step = self._state.next_timeline_step()
        self.status(f"[TL{step:03d}] {kind:<8} {message}")

    def reset_session(
        self,
        mode: str,
        target_level: int,
        use_shards: bool,
        auto_sell: bool,
    ) -> None:
        self._state.reset_timeline()
        self._mode = mode
        self._target_level = target_level
        self._use_shards = use_shards
        self._auto_sell = auto_sell
        self._log_lines.clear()
        self.timeline(
            "RESET",
            f"mode={get_mode_label(mode)} target=+{target_level} "
            f"shards={'on' if use_shards else 'off'} "
            f"auto_sell={'on' if auto_sell else 'off'}",
        )
    # ── Header state updates ──

    def update_weapon_state(
        self,
        equipped: Optional[WeaponState] = None,
        stored: Optional[WeaponState] = None,
        gold: Optional[int] = None,
        shards: Optional[int] = None,
    ) -> None:
        if equipped is not None:
            self._equipped = equipped
        if stored is not None:
            self._stored = stored
        if gold is not None:
            self._gold = gold
        if shards is not None:
            self._shards = shards
        if self._live is not None:
            self._refresh()

    def update_pause_state(self, paused: bool) -> None:
        self._paused = paused
        if self._live is not None:
            self._refresh()
    # ── Live display lifecycle ──

    def start_live(self) -> None:
        self._live = Live(
            self._build_layout(),
            console=self._console,
            refresh_per_second=4,
            screen=True,
        )
        self._live.start()

    def stop_live(self) -> None:
        if self._live is not None:
            self._live.stop()
            self._live = None
    # ── Layout building ──

    def _refresh(self) -> None:
        if self._live is not None:
            self._live.update(self._build_layout())

    def _build_layout(self) -> Layout:
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=5),
            Layout(name="body"),
            Layout(name="footer", size=3),
        )
        layout["header"].update(self._build_header())
        if self._stats is not None:
            body = Layout()
            body.split_row(
                Layout(name="log", ratio=3),
                Layout(name="stats", ratio=1, minimum_size=30),
            )
            body["log"].update(self._build_log_panel())
            body["stats"].update(self._build_stats_panel())
            layout["body"].update(body)
        else:
            layout["body"].update(self._build_log_panel())
        layout["footer"].update(self._build_footer())
        return layout

    def _build_header(self) -> Panel:
        table = Table.grid(padding=(0, 2))
        table.add_column(style="bold cyan", min_width=20)
        table.add_column(min_width=30)
        table.add_column(min_width=20)
        mode_label = get_mode_label(self._mode).upper()
        target_str = f"+{self._target_level}"
        opts = []
        if self._use_shards:
            opts.append("파편사용")
        if self._auto_sell:
            opts.append("자동판매")
        opt_str = " | ".join(opts) if opts else ""
        table.add_row(
            f"[bold]{mode_label}[/] → {target_str}",
            f"⚔️ 장착: [yellow]{describe_weapon(self._equipped)}[/]",
            f"💰 골드: [green]{format_metric(self._gold)}[/]G",
        )
        table.add_row(
            opt_str,
            f"📦 보관: [yellow]{describe_weapon(self._stored)}[/]",
            f"🌠 파편: [magenta]{format_metric(self._shards)}[/]개",
        )
        return Panel(table, title="검키우기 v11.0", border_style="blue")

    def _build_log_panel(self) -> Panel:
        visible_lines = list(self._log_lines)
        try:
            height = self._console.height - 10
        except Exception:
            height = 20
        if height < 5:
            height = 20
        display_lines = visible_lines[-height:]
        log_text = Text("\n".join(display_lines)) if display_lines else Text("(대기 중...)", style="dim")
        return Panel(log_text, title="로그", border_style="dim")

    def _build_stats_panel(self) -> Panel:
        if self._stats is None:
            return Panel(Text("(통계 없음)", style="dim"), title="강화 확률", border_style="dim")
        lines: list[str] = []
        for title, mode_key in (("일반", "normal"), ("상급", "advanced")):
            rows = self._stats.get_transition_rows(mode_key)
            if not rows:
                continue
            lines.append(f"[bold]{title}[/]")
            current_start = None
            for row in rows:
                if current_start != row["start"]:
                    current_start = row["start"]
                    lines.append(f" +{current_start} ({row['attempts']:,}회)")
                lines.append(
                    f"  →+{row['end']}: "
                    f"{row['count']:,}/{row['attempts']:,} "
                    f"({row['rate']:.1f}%)"
                )
        if not lines:
            content = Text("(기록 없음)", style="dim")
        else:
            from rich.markup import escape

            content = Text.from_markup("\n".join(lines))
        return Panel(content, title="강화 확률", border_style="dim")

    def _build_footer(self) -> Panel:
        if self._paused:
            status_text = Text("⏸ 일시정지", style="bold yellow")
        else:
            status_text = Text("▶ 실행중", style="bold green")
        footer = Table.grid(padding=(0, 3))
        footer.add_column()
        footer.add_column()
        footer.add_column()
        footer.add_row(
            status_text,
            Text("F8 일시정지/재개", style="dim"),
            Text("F9 메뉴복귀", style="dim"),
        )
        return Panel(footer, border_style="blue")
