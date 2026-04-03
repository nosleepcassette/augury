from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHONPATH = str(ROOT / "src")


def _run(*args: str, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    merged_env = dict(os.environ)
    merged_env.update(env)
    merged_env["PYTHONPATH"] = PYTHONPATH
    return subprocess.run(
        [sys.executable, "-m", "augury", *args],
        cwd=ROOT,
        env=merged_env,
        text=True,
        capture_output=True,
        check=True,
    )


def _run_discord(*args: str, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    merged_env = dict(os.environ)
    merged_env.update(env)
    merged_env["PYTHONPATH"] = PYTHONPATH
    return subprocess.run(
        [sys.executable, "-m", "augury.discord", *args],
        cwd=ROOT,
        env=merged_env,
        text=True,
        capture_output=True,
        check=True,
    )


def _run_iching(*args: str, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    merged_env = dict(os.environ)
    merged_env.update(env)
    merged_env["PYTHONPATH"] = PYTHONPATH
    return subprocess.run(
        [sys.executable, "-m", "augury.iching", *args],
        cwd=ROOT,
        env=merged_env,
        text=True,
        capture_output=True,
        check=True,
    )


def test_read_json_no_save(tmp_path: Path) -> None:
    result = _run(
        "read",
        "--json",
        "--no-save",
        "--spread",
        "single",
        "--query",
        "test prompt",
        env={"AUGURY_HOME": str(tmp_path)},
    )
    payload = json.loads(result.stdout)
    assert payload["saved"] is False
    assert payload["saved_to"] is None
    assert payload["spread_name"]
    assert not (tmp_path / "readings.jsonl").exists()


def test_read_json_save_writes_history(tmp_path: Path) -> None:
    result = _run(
        "read",
        "--json",
        "--spread",
        "single",
        "--query",
        "persist me",
        env={"AUGURY_HOME": str(tmp_path)},
    )
    payload = json.loads(result.stdout)
    assert payload["saved"] is True
    assert (tmp_path / "readings.jsonl").exists()
    assert payload["drawn_cards"][0]["art"].strip()
    assert payload["drawn_cards"][0]["card"]["art"].strip()


def test_history_json_preserves_card_art(tmp_path: Path) -> None:
    _run(
        "read",
        "--json",
        "--spread",
        "single",
        "--query",
        "keep the art",
        env={"AUGURY_HOME": str(tmp_path)},
    )
    result = _run(
        "history",
        "--json",
        "--limit",
        "1",
        env={"AUGURY_HOME": str(tmp_path)},
    )
    payload = json.loads(result.stdout)
    assert payload[0]["drawn_cards"][0]["art"].strip()
    assert payload[0]["drawn_cards"][0]["card"]["art"].strip()


def test_paths_command_reports_override(tmp_path: Path) -> None:
    result = _run(
        "paths",
        "--json",
        env={"AUGURY_HOME": str(tmp_path), "AUGURY_BIN_DIR": str(tmp_path / "bin")},
    )
    payload = json.loads(result.stdout)
    assert payload["config_dir"] == str(tmp_path)
    assert payload["data_dir"] == str(tmp_path)
    assert payload["launcher_dir"] == str(tmp_path / "bin")
    assert payload["iching_readings_path"] == str(tmp_path / "iching_readings.jsonl")


def test_configure_installs_discord_helper(tmp_path: Path) -> None:
    helper_path = tmp_path / "bin" / "augury-discord"
    _run(
        "configure",
        "--no-input",
        "--install-discord-helper",
        "--discord-helper-path",
        str(helper_path),
        env={"AUGURY_HOME": str(tmp_path)},
    )
    assert helper_path.exists()
    config_payload = json.loads((tmp_path / "integrations.json").read_text(encoding="utf-8"))
    assert config_payload["discord"]["enabled"] is True
    assert config_payload["discord"]["helper_path"] == str(helper_path)


def test_configure_installs_launchers(tmp_path: Path) -> None:
    launcher_dir = tmp_path / "bin"
    _run(
        "configure",
        "--no-input",
        "--install-launchers",
        "--launcher-dir",
        str(launcher_dir),
        env={"AUGURY_HOME": str(tmp_path)},
    )
    augury_path = launcher_dir / "augury"
    discord_path = launcher_dir / "augury-discord"
    iching_path = launcher_dir / "iching"
    assert augury_path.exists()
    assert discord_path.exists()
    assert iching_path.exists()
    assert '-m augury "$@"' in augury_path.read_text(encoding="utf-8")
    assert '-m augury.discord "$@"' in discord_path.read_text(encoding="utf-8")
    assert '-m augury.iching "$@"' in iching_path.read_text(encoding="utf-8")
    config_payload = json.loads((tmp_path / "integrations.json").read_text(encoding="utf-8"))
    assert config_payload["discord"]["enabled"] is True
    assert config_payload["discord"]["helper_path"] == str(discord_path)


def test_discord_command_formats_card(tmp_path: Path) -> None:
    result = _run_discord("handle", "/tarot card The Fool", env={"AUGURY_HOME": str(tmp_path)})
    assert "**The Fool**" in result.stdout
    assert "Upright:" in result.stdout
    assert "```" in result.stdout


def test_discord_read_includes_card_art(tmp_path: Path) -> None:
    result = _run_discord(
        "read",
        "--spread",
        "single",
        "--query",
        "show the card",
        env={"AUGURY_HOME": str(tmp_path)},
    )
    assert "**Single Card**" in result.stdout
    assert "```" in result.stdout
    assert "Keywords:" in result.stdout


def test_augury_tarot_namespace_matches_top_level_read(tmp_path: Path) -> None:
    result = _run(
        "tarot",
        "read",
        "--json",
        "--no-save",
        "--spread",
        "single",
        "--query",
        "namespaced tarot",
        env={"AUGURY_HOME": str(tmp_path)},
    )
    payload = json.loads(result.stdout)
    assert payload["spread_name"] == "Single Card"
    assert payload["saved"] is False


def test_iching_cast_json_no_save(tmp_path: Path) -> None:
    result = _run(
        "iching",
        "cast",
        "--json",
        "--no-save",
        "--query",
        "What is shifting?",
        env={"AUGURY_HOME": str(tmp_path)},
    )
    payload = json.loads(result.stdout)
    assert payload["system"] == "iching"
    assert payload["saved"] is False
    assert payload["saved_to"] is None
    assert payload["primary_hexagram"]["number"] >= 1
    assert not (tmp_path / "iching_readings.jsonl").exists()


def test_iching_daily_is_deterministic_for_date(tmp_path: Path) -> None:
    first = _run_iching(
        "daily",
        "--json",
        "--no-save",
        "--date",
        "2026-04-03",
        env={"AUGURY_HOME": str(tmp_path)},
    )
    second = _run_iching(
        "daily",
        "--json",
        "--no-save",
        "--date",
        "2026-04-03",
        env={"AUGURY_HOME": str(tmp_path)},
    )
    first_payload = json.loads(first.stdout)
    second_payload = json.loads(second.stdout)
    assert first_payload["primary_hexagram"]["number"] == second_payload["primary_hexagram"]["number"]
    assert first_payload["lines"] == second_payload["lines"]


def test_iching_hexagram_lookup_json(tmp_path: Path) -> None:
    result = _run_iching(
        "hexagram",
        "24",
        "--json",
        env={"AUGURY_HOME": str(tmp_path)},
    )
    payload = json.loads(result.stdout)
    assert payload["number"] == 24
    assert payload["judgment"]["text"]
    assert len(payload["lines"]) == 6


def test_iching_history_json_after_save(tmp_path: Path) -> None:
    _run_iching(
        "cast",
        "--json",
        "--query",
        "persist the consultation",
        env={"AUGURY_HOME": str(tmp_path)},
    )
    result = _run_iching(
        "history",
        "--json",
        "--limit",
        "1",
        env={"AUGURY_HOME": str(tmp_path)},
    )
    payload = json.loads(result.stdout)
    assert payload[0]["system"] == "iching"
    assert (tmp_path / "iching_readings.jsonl").exists()
