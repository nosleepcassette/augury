"""Rich/TTY application for the I Ching system."""

from __future__ import annotations

import sys
from datetime import date
from typing import Any

from ...config import DEFAULT_ICHING_PREFS, load_system_preferences, save_system_preferences
from ...shell import (
    AMBER,
    AMBER_SOFT,
    HAS_RICH,
    STONE,
    Align,
    Columns,
    Console,
    Group,
    Panel,
    Table,
    Text,
    box,
    centered,
    clear_screen,
    logo_banner,
    read_key,
    rich_escape,
    terminal_rows,
    window_bounds,
)
from .data import Hexagram, all_hexagrams
from .engine import (
    Consultation,
    cast_consultation,
    daily_consultation,
    generate_study_tips,
    load_consultations,
    method_name,
    method_specs,
    save_consultation,
)

LOGO_LINES = [
    "8888888 .d8888b. 888    888 8888888 888b    888  .d8888b.",
    "  888  d88P  Y88b888    888   888   8888b   888 d88P  Y88b",
    "  888  888    888888    888   888   88888b  888 888    888",
    "  888  888        888  888    888   888Y88b 888 888",
    "  888  888        8888888     888   888 Y88b888 888  88888",
    "  888  888    888 888  888    888   888  Y88888 888    888",
    "  888  Y88b  d88P 888    888   888   888   Y8888 Y88b  d88P",
    "8888888  Y8888P88 888    888 8888888 888    Y888  Y8888P88",
]
TAGLINES = [
    "book of changes",
    "cast, read, remember",
    "amber light, full text included",
]
MENU_ITEMS = [
    ("n", "&New Cast", "new_cast"),
    ("d", "&Daily Hexagram", "daily_hexagram"),
    ("h", "&Hexagram Browser", "hexagram_browser"),
    ("c", "&Consultation History", "consultation_history"),
    ("m", "Casting &Methods", "casting_methods"),
    ("p", "&Preferences", "preferences"),
    ("q", "&Quit", None),
]
MENU_HINT = "j/k move  |  enter select  |  hotkeys active"


def _load_prefs() -> dict[str, Any]:
    prefs = dict(DEFAULT_ICHING_PREFS)
    prefs.update(load_system_preferences("iching"))
    return prefs


def _save_prefs(prefs: dict[str, Any]) -> None:
    save_system_preferences("iching", prefs)


def _menu_label(template: str, selected: bool) -> tuple[str, str]:
    marker = template.find("&")
    plain = template.replace("&", "")
    if marker == -1 or marker == len(template) - 1:
        return plain, plain
    before = rich_escape(template[:marker])
    key = rich_escape(template[marker + 1])
    after = rich_escape(template[marker + 2 :])
    if selected:
        markup = (
            f"[bold {AMBER_SOFT}]{before}[/]"
            f"[bold underline {AMBER}]{key}[/]"
            f"[bold {AMBER_SOFT}]{after}[/]"
        )
    else:
        markup = f"[{STONE}]{before}[/][underline {AMBER_SOFT}]{key}[/][{STONE}]{after}[/]"
    return markup, plain


def _line_glyph_from_value(value: int, changing: bool) -> str:
    if value in {7, 9}:
        core = "───────"
        return f"{core}  {'9' if changing else '7'}"
    core = "── ──"
    return f"{core}   {'6' if changing else '8'}"


def _render_consultation_lines(lines: list[Any]) -> str:
    rows = []
    for line in reversed(lines):
        rows.append(f"{line.line_number}  {_line_glyph_from_value(int(line.value), bool(line.changing))}")
    return "\n".join(rows)


def _render_hexagram_lines(hexagram: Hexagram) -> str:
    rows = []
    for index, bit in enumerate(hexagram.binary_top_to_bottom, start=1):
        line_number = 7 - index
        value = 7 if bit == "1" else 8
        rows.append(f"{line_number}  {_line_glyph_from_value(value, False)}")
    return "\n".join(rows)


def _render_hexagram_summary_panel(
    hexagram: Hexagram,
    lines_rendered: str,
    title: str,
    subtitle: str = "",
    *,
    show_trigrams: bool = True,
) -> Panel:
    meta = Table.grid(padding=(0, 1))
    meta.add_column(style=AMBER_SOFT)
    meta.add_column(style=STONE)
    meta.add_row("Number", str(hexagram.number))
    meta.add_row("Name", hexagram.name)
    meta.add_row("Chinese", hexagram.chinese_name or "-")
    if show_trigrams:
        meta.add_row("Trigrams", f"{hexagram.upper_trigram} over {hexagram.lower_trigram}")
    meta.add_row("Keywords", ", ".join(hexagram.keywords[:4]) or "-")
    content = Group(
        Align.center(Text(lines_rendered, style=AMBER_SOFT)),
        Text("", style=STONE),
        meta,
    )
    return Panel(content, title=title, subtitle=subtitle, border_style=AMBER, box=box.ASCII)


def _timestamp_text(consultation: Consultation) -> str:
    stamp = consultation.timestamp
    if getattr(stamp, "tzinfo", None) is not None:
        stamp = stamp.astimezone()
    return stamp.strftime("%Y-%m-%d %H:%M")


def _summary_hexagrams(consultation: Consultation) -> str:
    primary = f"{consultation.primary_hexagram.number} {consultation.primary_hexagram.name}"
    if consultation.relating_hexagram is None:
        return primary
    return f"{primary} -> {consultation.relating_hexagram.number} {consultation.relating_hexagram.name}"


def show_hexagram_detail(console: Console, hexagram: Hexagram, *, show_trigrams: bool = True, show_line_text: bool = True) -> None:
    clear_screen(console)
    console.print(logo_banner(console, logo_lines=LOGO_LINES, taglines=TAGLINES, subtitle=f"hexagram  ·  {hexagram.number} {hexagram.name}"))
    console.print("")
    if HAS_RICH:
        summary = _render_hexagram_summary_panel(
            hexagram,
            _render_hexagram_lines(hexagram),
            title=f"{hexagram.number} · {hexagram.name}",
            subtitle=hexagram.unicode_symbol or "",
            show_trigrams=show_trigrams,
        )
        console.print(summary)
        console.print(
            Panel(
                Group(
                    Text(hexagram.symbolic, style=STONE),
                    Text("", style=STONE),
                    Text("Judgment", style=f"bold {AMBER}"),
                    Text(hexagram.judgment_text, style=STONE),
                    Text(hexagram.judgment_comments, style=STONE),
                    Text("", style=STONE),
                    Text("Image", style=f"bold {AMBER}"),
                    Text(hexagram.image_text, style=STONE),
                    Text(hexagram.image_comments, style=STONE),
                ),
                title="Core Text",
                border_style=AMBER,
                box=box.ASCII,
                padding=(1, 2),
            )
        )
        if show_line_text:
            line_rows = Table(show_header=True, header_style=f"bold {AMBER}", box=box.ASCII, padding=(0, 1))
            line_rows.add_column("Line", style=AMBER_SOFT, width=6)
            line_rows.add_column("Text", style=STONE)
            line_rows.add_column("Comments", style=STONE)
            for line_number in range(1, 7):
                line_rows.add_row(
                    str(line_number),
                    hexagram.line_texts[line_number - 1] or "-",
                    hexagram.line_comments[line_number - 1] or "-",
                )
            console.print(Panel(line_rows, title="Changing Lines", border_style=AMBER, box=box.ASCII))
    else:
        console.print(_render_hexagram_lines(hexagram))
        console.print(hexagram.judgment_text)
        console.print(hexagram.image_text)
    console.print("")
    console.print("[dim]enter to return[/dim]" if HAS_RICH else "enter to return")
    try:
        console.input("")
    except (EOFError, KeyboardInterrupt):
        return


def show_consultation(
    console: Console,
    consultation: Consultation,
    *,
    show_trigrams: bool = True,
    show_line_text: bool = True,
) -> None:
    clear_screen(console)
    subtitle = f"{consultation.primary_hexagram.number} {consultation.primary_hexagram.name}  ·  {_timestamp_text(consultation)}"
    console.print(logo_banner(console, logo_lines=LOGO_LINES, taglines=TAGLINES, subtitle=subtitle))
    console.print("")
    if HAS_RICH:
        panels = [
            _render_hexagram_summary_panel(
                consultation.primary_hexagram,
                _render_consultation_lines(consultation.lines),
                title="Primary Hexagram",
                subtitle=consultation.primary_hexagram.unicode_symbol or "",
                show_trigrams=show_trigrams,
            )
        ]
        if consultation.relating_hexagram is not None:
            panels.append(
                _render_hexagram_summary_panel(
                    consultation.relating_hexagram,
                    _render_hexagram_lines(consultation.relating_hexagram),
                    title="Relating Hexagram",
                    subtitle=consultation.relating_hexagram.unicode_symbol or "",
                    show_trigrams=show_trigrams,
                )
            )
        console.print(Columns(panels, expand=True, equal=True))
        console.print(
            Panel(
                Text(consultation.interpretation, style=STONE),
                title=f"Interpretation  ·  {method_name(consultation.method)}",
                border_style=AMBER,
                box=box.ASCII,
                padding=(1, 2),
            )
        )
        if consultation.changing_lines and show_line_text:
            line_table = Table(show_header=True, header_style=f"bold {AMBER}", box=box.ASCII, padding=(0, 1))
            line_table.add_column("Line", style=AMBER_SOFT, width=6)
            line_table.add_column("Text", style=STONE)
            line_table.add_column("Comments", style=STONE)
            for number in consultation.changing_lines:
                line_table.add_row(
                    str(number),
                    consultation.primary_hexagram.line_texts[number - 1] or "-",
                    consultation.primary_hexagram.line_comments[number - 1] or "-",
                )
            console.print(Panel(line_table, title="Changing Lines", border_style=AMBER, box=box.ASCII))
        tips = Group(*[Text(f"- {tip}", style=STONE) for tip in generate_study_tips(consultation)])
        console.print(Panel(tips, title="Study Notes", border_style=AMBER, box=box.ASCII))
    else:
        console.print(consultation.interpretation)
    console.print("")
    console.print("[dim]enter to return[/dim]" if HAS_RICH else "enter to return")
    try:
        console.input("")
    except (EOFError, KeyboardInterrupt):
        return


class IChingApp:
    def __init__(self) -> None:
        self.console = Console(highlight=False, force_terminal=True) if HAS_RICH else Console()
        self.prefs = _load_prefs()

    def refresh(self) -> None:
        self.prefs = _load_prefs()

    def prompt(self, label: str, default: str = "") -> str:
        prompt = f"[bold {AMBER}]{label}[/] "
        if default:
            prompt += f"[dim](default: {default})[/] "
        try:
            value = self.console.input(prompt if HAS_RICH else f"{label} ")
        except (EOFError, KeyboardInterrupt):
            return ""
        value = value.strip()
        return value if value else default

    def notice(self, text: str, color: str = AMBER_SOFT) -> None:
        if HAS_RICH:
            self.console.print(f"[{color}]{rich_escape(text)}[/]")
        else:
            self.console.print(text)

    def pause(self, text: str = "enter to continue") -> None:
        try:
            self.console.input(f"[dim]{text}[/] " if HAS_RICH else f"{text} ")
        except (EOFError, KeyboardInterrupt):
            return

    def draw_main_menu(self, selected: int) -> None:
        self.refresh()
        consultations = load_consultations()
        subtitle = (
            f"method {method_name(str(self.prefs.get('default_method', DEFAULT_ICHING_PREFS['default_method'])))}"
            f"  ·  consultations {len(consultations)}  ·  hexagrams {len(all_hexagrams())}"
        )
        clear_screen(self.console)
        self.console.print(logo_banner(self.console, logo_lines=LOGO_LINES, taglines=TAGLINES, subtitle=subtitle))
        self.console.print("")
        if HAS_RICH:
            stats = Table.grid(padding=(0, 3))
            stats.add_column(style=AMBER_SOFT)
            stats.add_column(style=STONE)
            stats.add_row("Default Method", method_name(str(self.prefs.get("default_method", DEFAULT_ICHING_PREFS["default_method"]))))
            stats.add_row("Show Trigrams", "on" if self.prefs.get("show_trigrams", True) else "off")
            stats.add_row("Show Line Text", "on" if self.prefs.get("show_line_text", True) else "off")
            self.console.print(Align.center(Panel(stats, title="Current State", border_style=AMBER, box=box.ASCII, padding=(0, 2), expand=False)))
            self.console.print("")
        label_width = max(len(item[1].replace("&", "")) for item in MENU_ITEMS)
        for index, (_hotkey, label, _action) in enumerate(MENU_ITEMS):
            styled, plain = _menu_label(label, index == selected)
            padding = " " * (label_width - len(plain))
            if index == selected:
                markup = f"[bold {AMBER}]>===<[/]  {styled}{padding}"
                raw = f">===<  {plain}{padding}"
            else:
                markup = f"[dim]{'.' * 5}[/]  {styled}{padding}"
                raw = f".....  {plain}{padding}"
            self.console.print(centered(self.console, markup, raw))
        self.console.print("")
        self.console.print(centered(self.console, f"[dim]{MENU_HINT}[/dim]", MENU_HINT))

    def run(self) -> int:
        if not sys.stdin.isatty():
            return self.run_fallback_menu()
        selected = 0
        while True:
            self.draw_main_menu(selected)
            key = read_key()
            if key in ("UP", "k"):
                selected = (selected - 1) % len(MENU_ITEMS)
                continue
            if key in ("DOWN", "j"):
                selected = (selected + 1) % len(MENU_ITEMS)
                continue
            if key in ("\r", "\n", " "):
                action = MENU_ITEMS[selected][2]
                if action is None:
                    return 0
                getattr(self, action)()
                continue
            if key in ("CTRL_C", "CTRL_D"):
                return 0
            for index, (hotkey, _label, action) in enumerate(MENU_ITEMS):
                if key.lower() != hotkey:
                    continue
                selected = index
                if action is None:
                    return 0
                getattr(self, action)()
                break

    def run_fallback_menu(self) -> int:
        mapping = {item[0]: item[2] for item in MENU_ITEMS}
        while True:
            self.draw_main_menu(0)
            self.console.print("")
            choice = self.prompt("choice [n/d/h/c/m/p/q]", "q").lower()
            action = mapping.get(choice)
            if action is None:
                return 0
            getattr(self, action)()

    def choose_method(self, initial: str | None = None) -> str:
        methods = method_specs()
        index = 0
        if initial:
            for method_index, method in enumerate(methods):
                if method["slug"] == initial:
                    index = method_index
                    break
        if not sys.stdin.isatty():
            self.console.print("")
            for number, method in enumerate(methods, start=1):
                self.console.print(f"{number:2}. {method['name']}")
            choice = self.prompt("method number", str(index + 1))
            try:
                return str(methods[max(0, min(len(methods) - 1, int(choice) - 1))]["slug"])
            except Exception:
                return str(methods[index]["slug"])
        while True:
            clear_screen(self.console)
            method = methods[index]
            self.console.print(logo_banner(self.console, logo_lines=LOGO_LINES, taglines=TAGLINES, subtitle="choose method"))
            self.console.print("")
            table = Table(show_header=True, header_style=f"bold {AMBER}", box=box.ASCII, padding=(0, 1))
            table.add_column("#", style="dim", width=4)
            table.add_column("method", style=AMBER_SOFT)
            table.add_column("description", style=STONE)
            for row_index, item in enumerate(methods, start=1):
                style = f"bold {AMBER}" if row_index - 1 == index else ""
                table.add_row(str(row_index), item["name"], item["description"], style=style)
            self.console.print(table)
            self.console.print("")
            self.console.print(Panel(method["description"], title="Current Method", border_style=AMBER, box=box.ASCII))
            self.console.print("")
            self.console.print("[dim]j/k move  enter choose  q cancel[/dim]")
            key = read_key()
            if key in ("UP", "k"):
                index = (index - 1) % len(methods)
            elif key in ("DOWN", "j"):
                index = (index + 1) % len(methods)
            elif key in ("\r", "\n"):
                return str(methods[index]["slug"])
            elif key in {"q", "CTRL_C", "CTRL_D"}:
                return str(methods[index]["slug"])

    def new_cast(self) -> None:
        method = self.choose_method(str(self.prefs.get("default_method", DEFAULT_ICHING_PREFS["default_method"])))
        query = self.prompt("query", "")
        consultation = cast_consultation(method=method, query=query or None)
        save_consultation(consultation)
        show_consultation(
            self.console,
            consultation,
            show_trigrams=bool(self.prefs.get("show_trigrams", True)),
            show_line_text=bool(self.prefs.get("show_line_text", True)),
        )

    def daily_hexagram(self) -> None:
        consultation = daily_consultation(date.today(), method=str(self.prefs.get("default_method", DEFAULT_ICHING_PREFS["default_method"])))
        save_consultation(consultation)
        show_consultation(
            self.console,
            consultation,
            show_trigrams=bool(self.prefs.get("show_trigrams", True)),
            show_line_text=bool(self.prefs.get("show_line_text", True)),
        )

    def hexagram_browser(self) -> None:
        items = list(all_hexagrams())
        cursor = 0
        search_query = ""
        while True:
            filtered = []
            for hexagram in items:
                haystack = " ".join(
                    [
                        str(hexagram.number),
                        hexagram.name,
                        hexagram.chinese_name,
                        hexagram.pinyin,
                        hexagram.lower_trigram,
                        hexagram.upper_trigram,
                        " ".join(hexagram.keywords),
                    ]
                ).lower()
                if search_query and search_query.lower() not in haystack:
                    continue
                filtered.append(hexagram)
            cursor = 0 if not filtered else max(0, min(cursor, len(filtered) - 1))
            page_size = max(8, terminal_rows() - 14)
            start, end = window_bounds(len(filtered), cursor, page_size)
            page_items = filtered[start:end]
            clear_screen(self.console)
            self.console.print(logo_banner(self.console, logo_lines=LOGO_LINES, taglines=TAGLINES, subtitle=f"hexagram browser  |  matches {len(filtered)}"))
            self.console.print("")
            table = Table(show_header=True, header_style=f"bold {AMBER}", box=box.ASCII, padding=(0, 1))
            table.add_column("#", style="dim", width=4)
            table.add_column("hexagram", style=AMBER_SOFT)
            table.add_column("trigrams", style=STONE)
            table.add_column("keywords", style=STONE)
            for absolute_index, item in enumerate(page_items, start=start):
                style = f"bold {AMBER}" if absolute_index == cursor else ""
                table.add_row(
                    str(item.number),
                    item.name,
                    f"{item.upper_trigram} / {item.lower_trigram}",
                    ", ".join(item.keywords[:3]),
                    style=style,
                )
            self.console.print(table)
            self.console.print("")
            self.console.print("[dim]j/k move  / search  enter view  q back[/dim]")
            key = read_key()
            if key in ("UP", "k") and filtered:
                cursor = (cursor - 1) % len(filtered)
            elif key in ("DOWN", "j") and filtered:
                cursor = (cursor + 1) % len(filtered)
            elif key == "/":
                search_query = self.prompt("search", search_query)
            elif key in ("\r", "\n") and filtered:
                show_hexagram_detail(
                    self.console,
                    filtered[cursor],
                    show_trigrams=bool(self.prefs.get("show_trigrams", True)),
                    show_line_text=bool(self.prefs.get("show_line_text", True)),
                )
            elif key in {"q", "CTRL_C", "CTRL_D"}:
                return

    def consultation_history(self) -> None:
        consultations = list(reversed(load_consultations()))
        if not consultations:
            clear_screen(self.console)
            self.console.print(logo_banner(self.console, logo_lines=LOGO_LINES, taglines=TAGLINES, subtitle="consultation history"))
            self.console.print("")
            self.notice("No consultations saved yet.")
            self.pause()
            return
        limit = max(1, int(self.prefs.get("history_limit", DEFAULT_ICHING_PREFS["history_limit"])))
        consultations = consultations[:limit]
        cursor = 0
        while True:
            page_size = max(8, terminal_rows() - 14)
            start, end = window_bounds(len(consultations), cursor, page_size)
            page_items = consultations[start:end]
            clear_screen(self.console)
            self.console.print(logo_banner(self.console, logo_lines=LOGO_LINES, taglines=TAGLINES, subtitle=f"consultation history  |  showing {len(consultations)}"))
            self.console.print("")
            table = Table(show_header=True, header_style=f"bold {AMBER}", box=box.ASCII, padding=(0, 1))
            table.add_column("#", style="dim", width=4)
            table.add_column("when", style=STONE, width=18)
            table.add_column("result", style=AMBER_SOFT)
            table.add_column("query", style=STONE)
            for absolute_index, item in enumerate(page_items, start=start):
                style = f"bold {AMBER}" if absolute_index == cursor else ""
                table.add_row(
                    str(absolute_index + 1),
                    _timestamp_text(item),
                    _summary_hexagrams(item),
                    str(item.query or "-"),
                    style=style,
                )
            self.console.print(table)
            self.console.print("")
            self.console.print("[dim]j/k move  enter view  q back[/dim]")
            key = read_key()
            if key in ("UP", "k"):
                cursor = (cursor - 1) % len(consultations)
            elif key in ("DOWN", "j"):
                cursor = (cursor + 1) % len(consultations)
            elif key in ("\r", "\n"):
                show_consultation(
                    self.console,
                    consultations[cursor],
                    show_trigrams=bool(self.prefs.get("show_trigrams", True)),
                    show_line_text=bool(self.prefs.get("show_line_text", True)),
                )
            elif key in {"q", "CTRL_C", "CTRL_D"}:
                return

    def casting_methods(self) -> None:
        clear_screen(self.console)
        self.console.print(logo_banner(self.console, logo_lines=LOGO_LINES, taglines=TAGLINES, subtitle="casting methods"))
        self.console.print("")
        table = Table(show_header=True, header_style=f"bold {AMBER}", box=box.ASCII, padding=(0, 1))
        table.add_column("method", style=AMBER_SOFT)
        table.add_column("description", style=STONE)
        table.add_column("line odds", style=STONE)
        for item in method_specs():
            table.add_row(
                item["name"],
                item["description"],
                "6:1  7:5  8:7  9:3",
            )
        self.console.print(table)
        self.console.print("")
        self.pause()

    def preferences(self) -> None:
        options = [
            ("default_method", "Default Method"),
            ("show_trigrams", "Show Trigrams"),
            ("show_line_text", "Show Line Text"),
            ("history_limit", "History Limit"),
        ]
        cursor = 0
        while True:
            self.refresh()
            clear_screen(self.console)
            self.console.print(logo_banner(self.console, logo_lines=LOGO_LINES, taglines=TAGLINES, subtitle="preferences"))
            self.console.print("")
            table = Table(show_header=True, header_style=f"bold {AMBER}", box=box.ASCII, padding=(0, 1))
            table.add_column("#", style="dim", width=4)
            table.add_column("setting", style=AMBER_SOFT)
            table.add_column("value", style=STONE)
            for index, (key, label) in enumerate(options, start=1):
                style = f"bold {AMBER}" if index - 1 == cursor else ""
                table.add_row(str(index), label, str(self.prefs.get(key)), style=style)
            self.console.print(table)
            self.console.print("")
            self.console.print("[dim]j/k move  enter edit/toggle  q back[/dim]")
            key = read_key()
            if key in ("UP", "k"):
                cursor = (cursor - 1) % len(options)
            elif key in ("DOWN", "j"):
                cursor = (cursor + 1) % len(options)
            elif key in ("\r", "\n"):
                pref_key, label = options[cursor]
                if pref_key in {"show_trigrams", "show_line_text"}:
                    self.prefs[pref_key] = not bool(self.prefs.get(pref_key, False))
                elif pref_key == "history_limit":
                    value = self.prompt(label, str(self.prefs.get(pref_key, DEFAULT_ICHING_PREFS["history_limit"])))
                    try:
                        self.prefs[pref_key] = max(1, int(value))
                    except Exception:
                        pass
                elif pref_key == "default_method":
                    self.prefs[pref_key] = self.choose_method(str(self.prefs.get(pref_key, DEFAULT_ICHING_PREFS["default_method"])))
                _save_prefs(self.prefs)
            elif key in {"q", "CTRL_C", "CTRL_D"}:
                return


__all__ = [
    "IChingApp",
    "show_consultation",
    "show_hexagram_detail",
]
