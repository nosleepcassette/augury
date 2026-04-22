# Augury

Augury is a terminal divination suite with a keyboard-driven TUI, a scriptable CLI, and an optional Discord formatter/helper. It currently ships with a tarot system and a full-text I Ching system, and it is designed to expose stable `augury`, `augury-discord`, and `iching` commands on `PATH`, even on systems where `pip` drops console scripts into a version-specific directory.

Created by **cassette, aka maps**  
Homepage: <https://cassette.help>

```text
 8888b.  888  888  .d88b.  888  888 888d888 888  888
    "88b 888  888 d88P"88b 888  888 888P"   888  888
.d888888 888  888 888  888 888  888 888     888  888
888  888 Y88b 888 Y88b 888 Y88b 888 888     Y88b 888
"Y888888  "Y88888  "Y88888  "Y88888 888      "Y88888
                       888                       888
                  Y8b d88P                  Y8b d88P
                   "Y88P"                    "Y88P"
```

## Augury

Augury is the suite-level shell that ties the whole project together. Running `augury` opens the top-level chooser, shows you the current tarot and I Ching history counts, and lets you jump into tarot, I Ching, or a combined reading from one place. The suite-level commands also live here: `augury combined` for one-query-two-systems work, `augury render` for turning markdown readings into shareable PNG/PDF assets, and `augury configure` / `augury paths` for install and storage management.

In practice, this is the part of the app that makes the whole thing feel coherent instead of like three unrelated scripts. It owns the stable launcher setup, the shared config/data locations, the combined reading flow, and the cross-system ergonomics that keep tarot, I Ching, and rendering under one roof.

## Tarot

```text
.sSSSSSSSSSSSSSs. .sSSSSs.    .sSSSSSSSs. .sSSSSs.    .sSSSSSSSSSSSSSs.
SSSSS S SSS SSSSS S SSSSSSSs. S SSS SSSSS S SSSSSSSs. SSSSS S SSS SSSSS
SSSSS S  SS SSSSS S  SS SSSSS S  SS SSSS' S  SS SSSSS SSSSS S  SS SSSSS
`:S:' S..SS `:S:' S..SSsSSSSS S..SSsSSSa. S..SS SSSSS `:S:' S..SS `:S:'
      S:::S       S:::S SSSSS S:::S SSSSS S:::S SSSSS       S:::S
      S;;;S       S;;;S SSSSS S;;;S SSSSS S;;;S SSSSS       S;;;S
      S%%%S       S%%%S SSSSS S%%%S SSSSS S%%%S SSSSS       S%%%S
      SSSSS       SSSSS SSSSS SSSSS SSSSS SSSSSsSSSSS       SSSSS
```

The tarot side is the card-driven reading app. In the TUI it gives you a spread picker, a card browser with suit/arcana filtering and search, reading history, custom spread management, and tarot-specific preferences like reversals, tips, and history length. In the detail views it drills into correspondences, keywords, meanings, related cards, and study notes, so it works as both a reading tool and a study surface.

From the command line, tarot is also the fastest part of the suite to script: `augury read`, `augury daily`, `augury card`, and `augury tarot ...` cover one-off pulls, daily draws, card lookups, and automation-friendly JSON output.

## I Ching

```text
 o8o                 oooo         o8o
 `"'                 `888         `"'
oooo        .ooooo.   888 .oo.   oooo  ooo. .oo.    .oooooooo
`888       d88' `"Y8  888P"Y88b  `888  `888P"Y88b  888' `88b
 888       888        888   888   888   888   888  888   888
 888       888   .o8  888   888   888   888   888  `88bod8P'
o888o      `Y8bod8P' o888o o888o o888o o888o o888o `8oooooo.
                                                   d"     YD
                                                   "Y88888P'
```

The I Ching side is the full-text consultation app. In the TUI it handles new casts, deterministic daily hexagrams, browsing all 64 hexagrams, consultation history, and preference controls for things like trigram display and line text visibility. The detail screens bring together the line structure, primary and relating hexagrams, Wilhelm/Baynes judgment and image text, and changing-line commentary in one place.

On the CLI side, `augury iching ...` and standalone `iching ...` both expose casting, daily readings, hexagram lookup, configuration, and path inspection, so the system works equally well as a quiet reading space or a scriptable reference tool.

## Features

- System chooser in `augury` for tarot, I Ching, and a combined tarot + I Ching reading
- Full-screen tarot UI for browsing cards, drawing readings, managing custom spreads, and reviewing history
- Full-screen I Ching UI for casting consultations, browsing all 64 hexagrams, and reviewing consultation history
- Built-in I Ching casting model using three coins with yarrow-stalk probabilities
- Combined reading flow that runs one query through both backends, with a tarot-defaults vs. configure-tarot picker
- CLI commands for tarot via `augury read`, `augury daily`, `augury card`, and namespaced tarot commands via `augury tarot ...`
- Full I Ching CLI via `augury iching ...` and standalone `iching ...`
- Combined CLI via `augury combined ...`
- Markdown rendering via `augury render` and `oracle-render`
- Named render font profiles with automatic filename suffixes for non-default styles
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
- `oracle-render`

The launcher install step above writes small wrapper scripts that execute `python -m augury` and
`python -m augury.discord` and `python -m augury.iching` with the interpreter Augury was installed
under. That keeps the binary path stable for agents even if `pip` chose a versioned script
directory internally.

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

Render a markdown reading to PNG/PDF:

```bash
augury render reading.md --single
augury render reading.md --single --font dotmatrix-varduo
```

Run one query through both tarot and I Ching:

```bash
augury combined --query "What am I missing right now?"
```

Run the deterministic daily hexagram from the standalone CLI:

```bash
iching daily --date 2026-04-03
```

Show a specific hexagram:

```bash
iching hexagram 24
```

Inspect I Ching-specific paths:

```bash
iching paths
```

Configure the standalone I Ching app:

```bash
iching configure
```

Render directly through the standalone renderer:

```bash
oracle-render reading.md --single --font "Love Letter Typewriter"
```

Inspect paths:

```bash
augury paths
```

Run setup and optionally install stable launchers:

```bash
augury configure
```

## Rendering

Augury ships with a markdown renderer for turning readings, notes, or exported text into styled PNG/PDF assets.

- `augury render` is the normal entrypoint from the suite.
- `oracle-render` is the direct renderer entrypoint.
- Supported font profiles are `arial`, `loveletter-typewriter`, `naughty-ones`, `pixelfy-sans`, `pokemon-gb`, `press-start-2p`, `dotmatrix-varduo`, and `vt323`.
- The default readable font is `arial`.
- Non-default fonts automatically add a short suffix to the output basename to prevent accidental overwrites, for example `-dmvd` for `dotmatrix-varduo` and `-llt` for `loveletter-typewriter`.

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

I Ching mode ships with the full Wilhelm/Baynes text corpus plus line commentary, and the daily
hexagram is deterministic for a given calendar date.

The combined mode saves to both history files unless `--no-save` is used.

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
