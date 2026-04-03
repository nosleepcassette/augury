from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from augury import config as config_module


def test_default_launcher_dir_prefers_system_bin(monkeypatch) -> None:
    monkeypatch.delenv("AUGURY_BIN_DIR", raising=False)
    monkeypatch.setattr(config_module, "_has_write_access", lambda path: path == Path("/usr/local/bin"))
    assert config_module.default_launcher_dir() == Path("/usr/local/bin")


def test_default_launcher_dir_falls_back_to_user_bin(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("AUGURY_BIN_DIR", raising=False)
    monkeypatch.setattr(config_module, "_has_write_access", lambda path: False)
    monkeypatch.setattr(config_module, "default_user_bin_dir", lambda: tmp_path / "bin")
    assert config_module.default_launcher_dir() == tmp_path / "bin"


def test_install_cli_launchers_writes_wrappers(tmp_path: Path) -> None:
    launchers = config_module.install_cli_launchers(tmp_path)
    augury_path = launchers["augury"]
    discord_path = launchers["augury-discord"]
    iching_path = launchers["iching"]

    assert augury_path == tmp_path / "augury"
    assert discord_path == tmp_path / "augury-discord"
    assert iching_path == tmp_path / "iching"
    assert augury_path.exists()
    assert discord_path.exists()
    assert iching_path.exists()
    assert '-m augury "$@"' in augury_path.read_text(encoding="utf-8")
    assert '-m augury.discord "$@"' in discord_path.read_text(encoding="utf-8")
    assert '-m augury.iching "$@"' in iching_path.read_text(encoding="utf-8")
