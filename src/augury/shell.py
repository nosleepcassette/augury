"""Shared terminal rendering and key-handling helpers."""

from __future__ import annotations

import os
import re
import select
import sys
import termios
import time
import tty
from typing import Any

try:
    from rich import box
    from rich.align import Align
    from rich.columns import Columns
    from rich.console import Console, Group
    from rich.markup import escape as rich_escape
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text

    HAS_RICH = True
except Exception:
    HAS_RICH = False

    class _AsciiBox:
        ASCII = None

    box = _AsciiBox()

    class Console:  # type: ignore[no-redef]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self.width = 80

        def print(self, *args: Any, **kwargs: Any) -> None:
            if not args:
                print()
                return
            print(*args)

        def clear(self) -> None:
            os.system("clear")

        def input(self, prompt: str = "") -> str:
            return input(prompt)

    class Text(str):  # type: ignore[no-redef]
        pass

    def rich_escape(value: str) -> str:
        return value

    def Group(*args: Any) -> list[Any]:  # type: ignore[no-redef]
        return list(args)

    class Align:  # type: ignore[no-redef]
        @staticmethod
        def center(renderable: Any, *args: Any, **kwargs: Any) -> Any:
            return renderable

    class Columns(list):  # type: ignore[no-redef]
        def __init__(self, renderables: list[Any], *args: Any, **kwargs: Any) -> None:
            super().__init__(renderables)

    class Panel:  # type: ignore[no-redef]
        def __init__(
            self,
            renderable: Any,
            title: str | None = None,
            subtitle: str | None = None,
            border_style: str | None = None,
            box: Any = None,
            padding: tuple[int, int] | int | None = None,
            expand: bool = True,
        ) -> None:
            self.renderable = renderable
            self.title = title
            self.subtitle = subtitle

        def __str__(self) -> str:
            parts = []
            if self.title:
                parts.append(self.title)
            parts.append(str(self.renderable))
            if self.subtitle:
                parts.append(self.subtitle)
            return "\n".join(parts)

    class Table:  # type: ignore[no-redef]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self.columns: list[str] = []
            self.rows: list[list[str]] = []

        @classmethod
        def grid(cls, *args: Any, **kwargs: Any) -> "Table":
            return cls()

        def add_column(self, header: str, *args: Any, **kwargs: Any) -> None:
            self.columns.append(header)

        def add_row(self, *values: Any, **kwargs: Any) -> None:
            self.rows.append([str(value) for value in values])

        def __str__(self) -> str:
            lines: list[str] = []
            if self.columns:
                lines.append(" | ".join(self.columns))
            for row in self.rows:
                lines.append(" | ".join(row))
            return "\n".join(lines)


AMBER = "#ffb000"
AMBER_SOFT = "#ffd06a"
AMBER_DIM = "#9b6b1f"
STONE = "#cbb489"
INK = "#241707"
PENDING_ESCAPE = False
PENDING_ESCAPE_PREFIX = ""


def strip_markup(text: str) -> str:
    return re.sub(r"\[/?[^\]]+\]", "", str(text)).replace(r"\[", "[").replace(r"\]", "]")


def clear_screen(console: Console) -> None:
    if HAS_RICH:
        console.clear()
    else:
        os.system("clear")


def centered(console: Console, markup: str, plain_text: str | None = None) -> str:
    plain = plain_text if plain_text is not None else strip_markup(markup)
    width = getattr(console, "width", 80) or 80
    padding = max(0, (width - len(plain)) // 2)
    return (" " * padding) + markup


def logo_banner(
    console: Console,
    *,
    logo_lines: list[str] | tuple[str, ...],
    taglines: list[str] | tuple[str, ...],
    subtitle: str = "",
) -> str:
    lines: list[str] = []
    for line in logo_lines:
        lines.append(centered(console, f"[bold {AMBER}]{line}[/]", line))
    lines.append("")
    for index, tagline in enumerate(taglines):
        color = AMBER_SOFT if index == 0 else STONE if index == 1 else AMBER_DIM
        style = "bold" if index == 0 else "dim"
        lines.append(centered(console, f"[{style} {color}]{tagline}[/]", tagline))
    if subtitle:
        lines.append("")
        lines.append(centered(console, f"[dim]{subtitle}[/dim]", subtitle))
    return "\n".join(lines)


def read_key() -> str:
    if not sys.stdin.isatty():
        line = input().strip()
        return line[:1] if line else ""

    def _read_escape_suffix(fd: int, first_timeout: float = 0.15, tail_timeout: float = 0.01) -> str:
        suffix = ""
        deadline = time.monotonic() + first_timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            if not select.select([sys.stdin], [], [], remaining)[0]:
                break
            chunk = os.read(fd, 16).decode(errors="ignore")
            if not chunk:
                break
            suffix += chunk
            deadline = time.monotonic() + tail_timeout
        return suffix

    def _decode_escape_sequence(seq: str) -> str:
        if seq.startswith("[A") or seq.startswith("OA"):
            return "UP"
        if seq.startswith("[B") or seq.startswith("OB"):
            return "DOWN"
        if seq.startswith("[C") or seq.startswith("OC"):
            return "RIGHT"
        if seq.startswith("[D") or seq.startswith("OD"):
            return "LEFT"
        return ""

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        global PENDING_ESCAPE, PENDING_ESCAPE_PREFIX
        if PENDING_ESCAPE_PREFIX:
            seq = PENDING_ESCAPE_PREFIX + ch
            PENDING_ESCAPE_PREFIX = ""
            decoded = _decode_escape_sequence(seq)
            if decoded:
                return decoded
            if seq in {"[", "O"}:
                PENDING_ESCAPE_PREFIX = seq
            return ""
        if PENDING_ESCAPE:
            PENDING_ESCAPE = False
            seq = ch
            if ch in {"[", "O"}:
                seq += _read_escape_suffix(fd, first_timeout=0.05, tail_timeout=0.01)
            decoded = _decode_escape_sequence(seq)
            if decoded:
                return decoded
            if seq in {"[", "O"}:
                PENDING_ESCAPE_PREFIX = seq
            return ""
        if ch == "\x1b":
            suffix = _read_escape_suffix(fd)
            decoded = _decode_escape_sequence(suffix)
            if decoded:
                return decoded
            if not suffix:
                PENDING_ESCAPE = True
            return "ESC"
        if ch == "\x03":
            return "CTRL_C"
        if ch == "\x04":
            return "CTRL_D"
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def terminal_rows(default: int = 24) -> int:
    try:
        return os.get_terminal_size().lines
    except OSError:
        return default


def window_bounds(total: int, cursor: int, page_size: int) -> tuple[int, int]:
    if total <= page_size:
        return 0, total
    start = max(0, min(cursor - (page_size // 2), total - page_size))
    return start, min(total, start + page_size)


__all__ = [
    "AMBER",
    "AMBER_DIM",
    "AMBER_SOFT",
    "Align",
    "Columns",
    "Console",
    "Group",
    "HAS_RICH",
    "INK",
    "Panel",
    "STONE",
    "Table",
    "Text",
    "box",
    "centered",
    "clear_screen",
    "logo_banner",
    "read_key",
    "rich_escape",
    "strip_markup",
    "terminal_rows",
    "window_bounds",
]
