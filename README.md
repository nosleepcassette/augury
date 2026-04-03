# Augury

Augury is a terminal divination suite with a keyboard-driven TUI, a scriptable CLI, and an optional Discord formatter/helper. It currently ships with a tarot system and a full-text I Ching system, and it is designed to expose stable `augury`, `augury-discord`, and `iching` commands on `PATH`, even on systems where `pip` drops console scripts into a version-specific directory.

Created by **cassette, aka maps**  
Homepage: <https://cassette.help>

## Features

- System chooser in `augury` for tarot and I Ching
- Full-screen tarot UI for browsing cards, drawing readings, managing custom spreads, and reviewing history
- Full-screen I Ching UI for casting consultations, browsing all 64 hexagrams, and reviewing consultation history
- CLI commands for tarot via `augury read`, `augury daily`, `augury card`, and namespaced tarot commands via `augury tarot ...`
- Full I Ching CLI via `augury iching ...` and standalone `iching ...`
- JSON output for automation and scripting
- Optional Discord-friendly formatter via `augury-discord`
- Local preferences, custom spreads, and reading history stored in standard user config/data directories

## Installation

Install from a checkout:

```bash
pip install .
```

Then install stable launchers into `/usr/local/bin` by default, or `~/.local/bin` if `/usr/local/bin` is not writable:

```bash
python3 -m augury configure --no-input --install-launchers
```

Or, for a user-local CLI install:

```bash
pipx install .
```

Once installed, the package provides:

- `augury`
- `augury-discord`
- `iching`

The launcher install step above writes small wrapper scripts that execute `python -m augury` and
`python -m augury.discord` with the interpreter Augury was installed under. That keeps the binary
path stable for agents even if `pip` chose a versioned script directory internally.

## Quick Start

Launch the TUI:

```bash
augury
```

Launch the standalone I Ching app:

```bash
iching
```

Draw a reading from the CLI:

```bash
augury read --spread three-card --query "What should I pay attention to this week?"
```

Emit machine-readable JSON without writing to history:

```bash
augury read --json --no-save --spread single --query "release check"
```

Cast an I Ching consultation:

```bash
augury iching cast --query "What is shifting?"
```

Run the deterministic daily hexagram from the standalone CLI:

```bash
iching daily --date 2026-04-03
```

Inspect paths:

```bash
augury paths
```

Run setup and optionally install stable launchers:

```bash
augury configure
```

## Discord Integration

Augury ships with a formatter/parser module for Discord-style tarot commands.

Examples:

```bash
augury-discord handle "/tarot three What should I know?"
augury-discord card "The Fool"
augury-discord read --spread celtic-cross --query "What is the larger pattern?"
```

The `configure` flow can install stable `augury` and `augury-discord` launchers into a shared bin
directory, and now installs `iching` alongside them. It still supports an explicit
`augury-discord` helper path when you need one.

## Storage

By default Augury uses standard per-user config/data locations:

- Linux: `~/.config/augury` and `~/.local/share/augury`
- macOS: `~/Library/Application Support/augury`
- Windows: `%APPDATA%\\Augury` and `%LOCALAPPDATA%\\Augury`

You can override these with:

- `AUGURY_HOME`
- `AUGURY_CONFIG_DIR`
- `AUGURY_DATA_DIR`
- `AUGURY_BIN_DIR`

Tarot history is stored in `readings.jsonl`; I Ching consultations are stored in `iching_readings.jsonl`.

## Development

Run tests:

```bash
PYTHONPATH=src pytest
```

Run from a checkout without installing:

```bash
PYTHONPATH=src python -m augury
```

## TODO

- Replace the current `--interpret` stub with a real optional narrative/LLM mode
- Expand export/import support for readings and custom spreads
- Add data migration tooling from older private/local layouts
- Add broader automated coverage for the full-screen TUI interaction paths
- Package richer Discord integration examples beyond the formatter/helper CLI
- Support alternate decks, themes, and more presentation presets

## License

MIT. See [LICENSE](LICENSE).
