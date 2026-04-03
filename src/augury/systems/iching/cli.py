"""Standalone and integrated CLI for the I Ching system."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from typing import Any

from ...config import (
    DEFAULT_ICHING_PREFS,
    default_launcher_dir,
    get_app_paths,
    install_cli_launcher,
    load_preferences,
    save_preferences,
)
from ...shell import Console, HAS_RICH
from .app import IChingApp, show_consultation, show_hexagram_detail
from .data import hexagram_to_json, lookup_hexagram
from .engine import (
    cast_consultation,
    consultation_to_json,
    daily_consultation,
    load_consultations,
    method_name,
    save_consultation,
)


def _load_prefs() -> dict[str, Any]:
    prefs = dict(DEFAULT_ICHING_PREFS)
    prefs.update(load_preferences().get("iching", {}))
    return prefs


def _save_prefs(prefs: dict[str, Any]) -> None:
    payload = load_preferences()
    payload["iching"] = dict(prefs)
    save_preferences(payload)


def _emit_json(payload: Any) -> int:
    json.dump(payload, fp=sys.stdout, indent=2, ensure_ascii=True)
    sys.stdout.write("\n")
    return 0


def _paths_payload() -> dict[str, str]:
    paths = get_app_paths()
    return {
        "config_dir": str(paths.config_dir),
        "data_dir": str(paths.data_dir),
        "prefs_path": str(paths.prefs_path),
        "iching_readings_path": str(paths.iching_readings_path),
        "launcher_dir": str(default_launcher_dir()),
    }


def _configuration_payload() -> dict[str, Any]:
    return {
        "paths": _paths_payload(),
        "preferences": _load_prefs(),
    }


def _print_paths(console: Console) -> None:
    for key, value in _paths_payload().items():
        console.print(f"{key}: {value}")


def _bool_prompt(console: Console, label: str, default: bool) -> bool:
    hint = "Y/n" if default else "y/N"
    try:
        response = console.input(f"{label} [{hint}] ")
    except (EOFError, KeyboardInterrupt):
        return default
    normalized = response.strip().lower()
    if not normalized:
        return default
    if normalized in {"y", "yes"}:
        return True
    if normalized in {"n", "no"}:
        return False
    return default


def _run_paths_command(args: argparse.Namespace) -> int:
    payload = _paths_payload()
    if args.json:
        return _emit_json(payload)
    console = Console(highlight=False, force_terminal=True) if HAS_RICH else Console()
    _print_paths(console)
    return 0


def _run_configure_command(args: argparse.Namespace) -> int:
    console = Console(highlight=False, force_terminal=True) if HAS_RICH else Console()
    prefs = _load_prefs()

    if args.print_paths:
        _print_paths(console)
        if args.no_input and not args.install_launcher:
            return 0

    if args.no_input:
        if args.install_launcher:
            install_cli_launcher("iching", "augury.iching", args.launcher_dir)
        if args.json:
            return _emit_json(_configuration_payload())
        return 0

    app = IChingApp()
    prefs["default_method"] = app.choose_method(str(prefs.get("default_method", DEFAULT_ICHING_PREFS["default_method"])))
    prefs["show_trigrams"] = _bool_prompt(console, "Show trigram names in views?", bool(prefs.get("show_trigrams", True)))
    prefs["show_line_text"] = _bool_prompt(console, "Show changing-line text in reading views?", bool(prefs.get("show_line_text", True)))
    history_value = app.prompt("history limit", str(prefs.get("history_limit", DEFAULT_ICHING_PREFS["history_limit"])))
    try:
        prefs["history_limit"] = max(1, int(history_value))
    except Exception:
        pass
    _save_prefs(prefs)

    if _bool_prompt(console, f"Install or refresh the iching launcher in {args.launcher_dir or default_launcher_dir()}?", False):
        target_dir = app.prompt("launcher directory", str(args.launcher_dir or default_launcher_dir()))
        target = install_cli_launcher("iching", "augury.iching", target_dir or None)
        console.print(f"Installed iching at {target}")

    if args.json:
        return _emit_json(_configuration_payload())
    console.print("Configuration saved.")
    return 0


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def _run_cast_command(args: argparse.Namespace) -> int:
    consultation = cast_consultation(method=args.method, query=args.query)
    if not args.no_save:
        save_consultation(consultation)
    payload = consultation_to_json(consultation)
    payload["saved"] = not args.no_save
    payload["saved_to"] = None if args.no_save else str(get_app_paths().iching_readings_path)
    if args.json:
        return _emit_json(payload)
    console = Console(highlight=False, force_terminal=True) if HAS_RICH else Console()
    show_consultation(console, consultation)
    return 0


def _run_daily_command(args: argparse.Namespace) -> int:
    consultation = daily_consultation(_parse_date(args.date), method=args.method)
    if not args.no_save:
        save_consultation(consultation)
    payload = consultation_to_json(consultation)
    payload["saved"] = not args.no_save
    payload["saved_to"] = None if args.no_save else str(get_app_paths().iching_readings_path)
    if args.json:
        return _emit_json(payload)
    console = Console(highlight=False, force_terminal=True) if HAS_RICH else Console()
    show_consultation(console, consultation)
    return 0


def _run_hexagram_command(args: argparse.Namespace) -> int:
    hexagram = lookup_hexagram(" ".join(args.identifier))
    payload = hexagram_to_json(hexagram)
    if args.json:
        return _emit_json(payload)
    console = Console(highlight=False, force_terminal=True) if HAS_RICH else Console()
    show_hexagram_detail(console, hexagram)
    return 0


def _run_history_command(args: argparse.Namespace) -> int:
    limit = max(1, int(args.limit))
    consultations = list(reversed(load_consultations()))[:limit]
    if args.json:
        return _emit_json([consultation_to_json(item) for item in consultations])
    console = Console(highlight=False, force_terminal=True) if HAS_RICH else Console()
    for item in consultations:
        console.print(f"{item.timestamp.date().isoformat()}  {item.primary_hexagram.number} {item.primary_hexagram.name}")
    return 0


def _add_command_parsers(subparsers: Any, *, nested: bool = False) -> None:
    cast_parser = subparsers.add_parser("cast", help="Cast an I Ching consultation")
    cast_parser.add_argument("--method", default=DEFAULT_ICHING_PREFS["default_method"], help="Casting method slug")
    cast_parser.add_argument("--query", default=None, help="Optional consultation prompt")
    cast_parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    cast_parser.add_argument("--no-save", action="store_true", help="Do not persist the consultation")

    daily_parser = subparsers.add_parser("daily", help="Draw the deterministic daily hexagram")
    daily_parser.add_argument("--method", default=DEFAULT_ICHING_PREFS["default_method"], help="Casting method slug")
    daily_parser.add_argument("--date", default=None, help="Override the date in YYYY-MM-DD format")
    daily_parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    daily_parser.add_argument("--no-save", action="store_true", help="Do not persist the consultation")

    hexagram_parser = subparsers.add_parser("hexagram", help="Show a hexagram by number or name")
    hexagram_parser.add_argument("identifier", nargs="+", help="Hexagram number or name")
    hexagram_parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")

    history_parser = subparsers.add_parser("history", help="Show consultation history")
    history_parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    history_parser.add_argument("--limit", type=int, default=25, help="Number of consultations to show")

    if not nested:
        configure_parser = subparsers.add_parser("configure", help="Configure I Ching preferences and launcher install")
        configure_parser.add_argument("--json", action="store_true", help="Emit machine-readable configuration")
        configure_parser.add_argument("--print-paths", action="store_true", help="Print active config and data paths")
        configure_parser.add_argument("--install-launcher", action="store_true", help="Install the iching launcher")
        configure_parser.add_argument("--launcher-dir", default=None, help="Override the launcher directory")
        configure_parser.add_argument("--no-input", action="store_true", help="Do not prompt interactively")

        paths_parser = subparsers.add_parser("paths", help="Show I Ching config and data paths")
        paths_parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")


def add_augury_subparser(subparsers: Any) -> None:
    iching_parser = subparsers.add_parser("iching", help="Launch the I Ching app or run I Ching commands")
    nested = iching_parser.add_subparsers(dest="iching_command")
    _add_command_parsers(nested, nested=True)


def run_augury_args(args: argparse.Namespace) -> int:
    command = getattr(args, "iching_command", None)
    if command == "cast":
        return _run_cast_command(args)
    if command == "daily":
        return _run_daily_command(args)
    if command == "hexagram":
        return _run_hexagram_command(args)
    if command == "history":
        return _run_history_command(args)
    return IChingApp().run()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="iching",
        description="I Ching reader TUI and CLI.",
    )
    subparsers = parser.add_subparsers(dest="command")
    _add_command_parsers(subparsers, nested=False)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "cast":
        return _run_cast_command(args)
    if args.command == "daily":
        return _run_daily_command(args)
    if args.command == "hexagram":
        return _run_hexagram_command(args)
    if args.command == "history":
        return _run_history_command(args)
    if args.command == "configure":
        return _run_configure_command(args)
    if args.command == "paths":
        return _run_paths_command(args)
    return IChingApp().run()


__all__ = [
    "add_augury_subparser",
    "main",
    "run_augury_args",
]
