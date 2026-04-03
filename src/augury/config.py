"""Shared configuration, storage paths, and launcher-install utilities."""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

APP_NAME = "augury"
SYSTEM_BIN_DIR = Path("/usr/local/bin")
DEFAULT_TAROT_PREFS = {
    "default_spread": "three-card",
    "allow_reversals": True,
    "show_tips": True,
    "history_limit": 50,
}
DEFAULT_ICHING_PREFS = {
    "default_method": "three-coin-yarrow",
    "show_trigrams": True,
    "show_line_text": True,
    "history_limit": 50,
    "daily_mode": "deterministic",
}
DEFAULT_APP_PREFS = {
    "tarot": DEFAULT_TAROT_PREFS,
    "iching": DEFAULT_ICHING_PREFS,
}
DEFAULT_INTEGRATIONS = {
    "discord": {
        "enabled": False,
        "helper_path": None,
    }
}


@dataclass(frozen=True)
class AppPaths:
    config_dir: Path
    data_dir: Path
    prefs_path: Path
    spreads_path: Path
    readings_path: Path
    iching_readings_path: Path
    integrations_path: Path


def _default_config_dir() -> Path:
    home = Path.home()
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", home / "AppData" / "Roaming"))
        return base / "Augury"
    if sys.platform == "darwin":
        return home / "Library" / "Application Support" / APP_NAME
    base = Path(os.environ.get("XDG_CONFIG_HOME", home / ".config"))
    return base / APP_NAME


def _default_data_dir() -> Path:
    home = Path.home()
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", home / "AppData" / "Local"))
        return base / "Augury"
    if sys.platform == "darwin":
        return home / "Library" / "Application Support" / APP_NAME
    base = Path(os.environ.get("XDG_DATA_HOME", home / ".local" / "share"))
    return base / APP_NAME


def default_user_bin_dir() -> Path:
    home = Path.home()
    if os.name == "nt":
        return home / "AppData" / "Local" / "Microsoft" / "WindowsApps"
    return Path(os.environ.get("AUGURY_BIN_DIR", home / ".local" / "bin"))


def _has_write_access(path: Path) -> bool:
    candidate = path.expanduser()
    probe = candidate if candidate.exists() else candidate.parent
    return probe.exists() and os.access(probe, os.W_OK | os.X_OK)


def default_launcher_dir() -> Path:
    override = os.environ.get("AUGURY_BIN_DIR")
    if override:
        return Path(override).expanduser()
    if os.name != "nt" and _has_write_access(SYSTEM_BIN_DIR):
        return SYSTEM_BIN_DIR
    return default_user_bin_dir()


def get_app_paths() -> AppPaths:
    app_home = os.environ.get("AUGURY_HOME")
    if app_home:
        config_dir = Path(app_home).expanduser()
        data_dir = config_dir
    else:
        config_dir = Path(os.environ.get("AUGURY_CONFIG_DIR", _default_config_dir())).expanduser()
        data_dir = Path(os.environ.get("AUGURY_DATA_DIR", _default_data_dir())).expanduser()
    return AppPaths(
        config_dir=config_dir,
        data_dir=data_dir,
        prefs_path=config_dir / "prefs.json",
        spreads_path=config_dir / "spreads.json",
        readings_path=data_dir / "readings.jsonl",
        iching_readings_path=data_dir / "iching_readings.jsonl",
        integrations_path=config_dir / "integrations.json",
    )


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def atomic_json_write(path: Path, payload: Any) -> None:
    ensure_parent(path)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    tmp_path.replace(path)


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def load_integrations() -> dict[str, Any]:
    payload = load_json(get_app_paths().integrations_path, {})
    merged = json.loads(json.dumps(DEFAULT_INTEGRATIONS))
    if isinstance(payload, dict):
        for key, value in payload.items():
            if isinstance(value, dict) and isinstance(merged.get(key), dict):
                merged[key].update(value)
            else:
                merged[key] = value
    return merged


def save_integrations(config: dict[str, Any]) -> None:
    atomic_json_write(get_app_paths().integrations_path, config)


def default_discord_helper_path() -> Path:
    if os.name == "nt":
        return default_launcher_dir() / "augury-discord.cmd"
    return default_launcher_dir() / "augury-discord"


def _launcher_filename(script_name: str) -> str:
    if os.name == "nt":
        return f"{script_name}.cmd"
    return script_name


def _launcher_script(module: str) -> str:
    if os.name == "nt":
        return "@echo off\r\n" f"\"{sys.executable}\" -m {module} %*\r\n"
    return "#!/usr/bin/env sh\n" f"exec \"{sys.executable}\" -m {module} \"$@\"\n"


def install_cli_launcher(script_name: str, module: str, bin_dir: str | Path | None = None) -> Path:
    target_dir = Path(bin_dir).expanduser() if bin_dir is not None else default_launcher_dir()
    target = target_dir / _launcher_filename(script_name)
    ensure_parent(target)
    target.write_text(_launcher_script(module), encoding="utf-8")
    if os.name != "nt":
        target.chmod(0o755)
    return target


def install_cli_launchers(bin_dir: str | Path | None = None) -> dict[str, Path]:
    return {
        "augury": install_cli_launcher("augury", "augury", bin_dir),
        "augury-discord": install_cli_launcher("augury-discord", "augury.discord", bin_dir),
        "iching": install_cli_launcher("iching", "augury.iching", bin_dir),
    }


def install_discord_helper(destination: str | Path | None = None) -> Path:
    if destination is None:
        return install_cli_launcher("augury-discord", "augury.discord")
    target = Path(destination).expanduser()
    ensure_parent(target)
    target.write_text(_launcher_script("augury.discord"), encoding="utf-8")
    if os.name != "nt":
        target.chmod(0o755)
    return target


def _merge_defaults(base: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    merged = json.loads(json.dumps(base))
    for key, value in payload.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key].update(value)
        else:
            merged[key] = value
    return merged


def load_preferences() -> dict[str, Any]:
    payload = load_json(get_app_paths().prefs_path, {})
    if not isinstance(payload, dict):
        payload = {}

    if "tarot" not in payload and "iching" not in payload:
        legacy_tarot = {
            key: payload.get(key, value)
            for key, value in DEFAULT_TAROT_PREFS.items()
        }
        payload = {"tarot": legacy_tarot}

    return _merge_defaults(DEFAULT_APP_PREFS, payload)


def save_preferences(config: dict[str, Any]) -> None:
    atomic_json_write(get_app_paths().prefs_path, _merge_defaults(DEFAULT_APP_PREFS, config))


def load_system_preferences(system: str) -> dict[str, Any]:
    prefs = load_preferences()
    section = prefs.get(system, {})
    if not isinstance(section, dict):
        return {}
    return dict(section)


def save_system_preferences(system: str, payload: dict[str, Any]) -> None:
    prefs = load_preferences()
    prefs[system] = dict(payload)
    save_preferences(prefs)
