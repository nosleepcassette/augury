# Augury I Ching Integration Spec

## Goal

Add a full I Ching application to Augury that:

1. Feels native inside Augury's existing Rich/TTY-driven CLI and TUI.
2. Can also run as a fully standalone app with the same visual language and command patterns.
3. Does not wreck backward compatibility for current tarot users and scripts.

This should be a first-class sibling to tarot, not a special-case plugin screen.

## Product Shape

### Inside Augury

- `augury` remains the umbrella binary.
- Tarot continues to work with today's command surface.
- I Ching is added as a new system with its own TUI flow, browser, history, and CLI commands.

Recommended command shape:

```bash
augury read --spread three-card --query "..."     # existing tarot alias stays
augury daily                                      # existing tarot alias stays
augury card "The Fool"                            # existing tarot alias stays

augury tarot read --spread three-card --query "..."
augury tarot daily
augury tarot card "The Fool"

augury iching cast --method coins --query "..."
augury iching daily
augury iching hexagram 24
augury iching history --limit 20
```

### Standalone

Expose a standalone launcher that opens directly into the I Ching app:

```bash
iching cast --method coins --query "What is shifting?"
iching daily
iching hexagram 24
iching history
iching configure
iching paths
```

Implementation-wise, `iching` should be a thin launcher into the same package, not a separate repo or second codebase.

## Design Principles

### 1. Share shell infrastructure, not domain logic

Augury currently mixes shell code and tarot code in `src/augury/cli.py`. For this project, extract only the clearly shared parts:

- console/theme setup
- screen clearing and banners
- key handling
- windowing/paging helpers
- menu/table/panel helpers
- config/path helpers
- launcher installation

Keep tarot interpretation and I Ching interpretation separate.

### 2. Do not force a fake universal oracle model

Tarot has spreads, cards, reversals, suit analysis, and custom spreads.
I Ching has casting methods, hexagrams, changing lines, relating hexagrams, trigrams, and line texts.

The clean abstraction is:

- shared app shell
- per-system engines
- per-system renderers
- per-system history payloads with a small shared envelope

Not:

- one giant generic `Reading` object full of nullable tarot/I Ching fields

### 3. Preserve current tarot UX by default

Current `augury` users should not lose:

- `augury read`
- `augury daily`
- `augury card`
- current menu-driven tarot TUI

The new system should be additive first, then generalized internally.

## Recommended Architecture

## Package Layout

Recommended target layout:

```text
src/augury/
  __main__.py
  cli.py
  config.py
  shell.py
  systems/
    __init__.py
    tarot/
      __init__.py
      app.py
      cli.py
      engine.py
      data.py
      art.py
      discord.py
    iching/
      __init__.py
      app.py
      cli.py
      engine.py
      data.py
      art.py
```

Backward-compatibility shims can stay at the top level for now:

- `src/augury/cards.py` -> re-export from `systems.tarot.data`
- `src/augury/engine.py` -> re-export from `systems.tarot.engine`
- `src/augury/art.py` -> re-export from `systems.tarot.art`
- `src/augury/discord.py` -> re-export from `systems.tarot.discord`

That lets the refactor land without breaking current imports immediately.

## Shared Shell Layer

Move these out of the current top-level tarot CLI into shared modules:

- Rich setup and fallback console classes
- palette constants
- `_clear_screen`
- `_banner`
- `_centered`
- `_read_key`
- `_window_bounds`
- terminal sizing helpers
- generic list/detail/history rendering helpers where useful

Avoid over-abstracting the screen system. A few reusable helpers are enough.

## System Modules

Each system should own:

- domain data
- draw/cast engine
- system-specific preferences
- browser/detail screens
- history serialization/deserialization
- CLI subcommands
- TUI main menu

That gives tarot and I Ching equal status.

## TUI Integration

## Recommended UX

### `augury`

Keep the current tarot-first experience, but add an explicit route into I Ching.

Recommended main menu evolution:

- `New Reading`
- `Daily Card`
- `Card Browser`
- `Reading History`
- `Custom Spreads`
- `I Ching`
- `Preferences`
- `Quit`

Selecting `I Ching` enters the I Ching system menu.

This is less disruptive than inserting a mandatory top-level system chooser in front of existing users.

### `iching`

Open directly into an I Ching main menu with the same presentation style:

- `New Cast`
- `Daily Hexagram`
- `Hexagram Browser`
- `Consultation History`
- `Casting Methods`
- `Preferences`
- `Quit`

## I Ching Screens

### Main Menu

Mirror the Augury tarot menu structure and keyboard behavior.

### New Cast

Flow:

1. choose casting method
2. enter optional query
3. cast six lines
4. show primary hexagram
5. show changing lines
6. show relating hexagram if present
7. show interpretation and study notes
8. save to history unless disabled

### Daily Hexagram

Single-key flow equivalent to `daily card`.

Needs a product decision:

- random on each invocation
- deterministic per calendar day

### Hexagram Browser

List all 64 hexagrams with:

- number
- name
- lower trigram
- upper trigram
- keywords

Detail view should show:

- hexagram glyph/ASCII lines
- name and number
- lower/upper trigrams
- core text/summary
- line summaries
- derived-study notes

### Consultation History

I Ching history should be separate from tarot history in the UI at first.

An aggregate cross-system history can be added later if wanted.

### Casting Methods

Parallel to tarot's `Custom Spreads`, but domain-correct.

Recommended initial scope:

- built-in methods only
  - three coins
  - yarrow-stalk probabilities
- optional future support for saved casting profiles

Do not try to replicate tarot custom spreads here; the equivalent concept is casting profile, not spread layout.

## I Ching Data Model

## Core Records

Recommended local data model:

```python
@dataclass(slots=True)
class Hexagram:
    number: int
    name: str
    slug: str
    chinese_name: str | None
    unicode_symbol: str | None
    lower_trigram: str
    upper_trigram: str
    keywords: list[str]
    judgment: str
    image: str
    line_texts: list[str]        # line 1..6, bottom to top
    educational_tip: str
```

```python
@dataclass(slots=True)
class CastLine:
    line_number: int             # 1..6, bottom to top
    value: int                   # 6, 7, 8, 9
    polarity: Literal["yin", "yang"]
    changing: bool
```

```python
@dataclass(slots=True)
class Consultation:
    method: str
    query: str | None
    timestamp: datetime
    lines: list[CastLine]
    primary_hexagram: Hexagram
    relating_hexagram: Hexagram | None
    changing_lines: list[int]
    interpretation: str
```

## Engine Behavior

MVP behavior should support:

- primary hexagram derivation from six lines
- changing line detection
- relating hexagram derivation by flipping changing lines
- summary interpretation using:
  - primary hexagram
  - changing lines
  - relating hexagram
  - optional trigram emphasis

Phase-two options:

- nuclear hexagram
- opposite/complementary hexagram
- sequence/pair navigation
- method profiles with weighted probabilities and naming

## Rendering

I Ching needs its own ASCII art, similar in richness to tarot card art.

Recommended rendering primitives:

- solid line: `───────`
- broken line: `── ──`
- changing yin marker
- changing yang marker

Each consultation view should show:

- primary hexagram panel
- relating hexagram panel when present
- changing lines summary
- interpretation panel
- study notes panel

The layout should feel like today's Augury reading view, not like a plain text dump.

## CLI Surface

Recommended I Ching CLI:

```bash
augury iching cast --method coins --query "..."
augury iching cast --json --no-save
augury iching daily --json
augury iching hexagram 24 --json
augury iching history --limit 10 --json
```

Standalone alias:

```bash
iching cast ...
iching daily ...
iching hexagram ...
iching history ...
iching configure ...
iching paths ...
```

Recommended subcommands:

- `cast`
- `daily`
- `hexagram`
- `history`
- `configure`
- `paths`

Optional compatibility alias:

- `read` -> alias for `cast`

## JSON Shape

Recommended payload shape:

```json
{
  "system": "iching",
  "method": "three-coins",
  "query": "What is shifting?",
  "timestamp": "2026-04-03T12:00:00+00:00",
  "lines": [
    {"line_number": 1, "value": 7, "polarity": "yang", "changing": false}
  ],
  "primary_hexagram": {
    "number": 24,
    "name": "Return",
    "lower_trigram": "Thunder",
    "upper_trigram": "Earth"
  },
  "relating_hexagram": {
    "number": 2,
    "name": "Receptive"
  },
  "changing_lines": [2, 5],
  "interpretation": "..."
}
```

Tarot JSON should remain stable. Do not break existing tarot automation just to unify output early.

## Storage and Config

## History

Recommended near-term storage:

- keep current tarot history file intact
- add a new I Ching history file

Suggested paths:

- tarot: existing `readings.jsonl`
- I Ching: `iching_readings.jsonl`

This is lower-risk than forcing a cross-system history schema immediately.

## Preferences

Current `prefs.json` is tarot-shaped.
Recommended direction:

```json
{
  "default_system": "tarot",
  "tarot": {
    "default_spread": "three-card",
    "allow_reversals": true,
    "show_tips": true,
    "history_limit": 50
  },
  "iching": {
    "default_method": "three-coins",
    "show_line_text": true,
    "show_trigrams": true,
    "history_limit": 50,
    "daily_mode": "deterministic"
  }
}
```

Migration rule:

- if old flat tarot prefs are present, wrap them into `prefs["tarot"]`
- preserve existing defaults automatically

## Paths

Extend `AppPaths` carefully. Either:

1. add explicit system paths, or
2. add a generic `systems_dir`

Pragmatic recommendation:

- explicit paths first
- generalize only if a third system is added later

## Standalone Packaging

Add a new console script:

- `iching = "augury.systems.iching.cli:standalone_main"`

Also update launcher installation so `configure` can install:

- `augury`
- `augury-discord`
- `iching`

If you want a shared stable launcher strategy, keep the same wrapper-script pattern already used by Augury.

## Discord

I Ching support in Discord is optional for the first delivery unless you want parity immediately.

Recommended scope split:

- MVP: local CLI + TUI + standalone launcher
- phase two: `/iching` formatting via `augury-discord`

## Migration and Compatibility

## Must Preserve

- current `augury` entrypoint
- current tarot commands
- current tarot history loading
- current tarot tests
- current launcher install behavior

## Safe Refactor Strategy

1. extract shared shell helpers
2. move tarot internals behind compatibility shims
3. add I Ching as a sibling system
4. add standalone `iching`
5. expand config and tests

Do not start by rewriting the whole app into a generic framework.

## Build Plan

## Phase 1. Shell Extraction

Files:

- `src/augury/cli.py`
- new `src/augury/shell.py`

Tasks:

- move theme, key handling, banners, centering, paging, and console bootstrap into shared helpers
- keep current behavior identical
- keep tarot tests green

## Phase 2. Tarot Isolation Without Behavior Change

Files:

- new `src/augury/systems/tarot/*`
- compatibility shims in existing top-level modules

Tasks:

- move tarot-specific data, art, engine, and TUI handlers into a tarot namespace
- leave `augury read`, `daily`, `card`, `history` behavior unchanged
- keep existing import paths alive with re-exports

## Phase 3. I Ching Data and Engine

Files:

- new `src/augury/systems/iching/data.py`
- new `src/augury/systems/iching/engine.py`
- new `src/augury/systems/iching/art.py`

Tasks:

- add 64 hexagram dataset
- implement casting methods
- implement primary/relating derivation
- implement JSON serialization and history persistence
- implement study-note generation

## Phase 4. I Ching CLI

Files:

- new `src/augury/systems/iching/cli.py`
- `pyproject.toml`
- `setup.py`

Tasks:

- add `augury iching ...`
- add standalone `iching`
- add `configure` support for installing `iching`
- add `paths` support for I Ching storage locations

## Phase 5. I Ching TUI

Files:

- new `src/augury/systems/iching/app.py`
- `src/augury/cli.py`

Tasks:

- add I Ching main menu
- add new cast flow
- add daily hexagram
- add hexagram browser
- add I Ching history view
- wire Augury main menu entry into I Ching

## Phase 6. Config Migration

Files:

- `src/augury/config.py`
- tests

Tasks:

- move prefs to namespaced structure with migration
- add I Ching history/config paths
- preserve old flat tarot prefs

## Phase 7. Tests and Docs

Files:

- `tests/test_cli.py`
- new `tests/test_iching_cli.py`
- `README.md`

Tasks:

- add JSON tests for cast/daily/hexagram/history
- add history persistence tests
- add launcher install tests for `iching`
- document the standalone and integrated flows

## Key Risks

- The main risk is over-abstraction. Tarot and I Ching are similar at the shell level but different in structure.
- Translation/licensing choices for I Ching text can block the data layer.
- A mandatory system chooser could make `augury` feel worse for existing tarot usage.
- If history is generalized too early, the refactor becomes much larger than the feature.

## Recommendation

Build this as a sibling system inside Augury with a shared shell layer and a standalone launcher.

That means:

- preserve the current tarot UX
- refactor only the reusable shell pieces
- keep domain engines separate
- add `augury iching ...` and `iching ...`
- keep history separate at first

This is the cleanest path that satisfies both "integrated into Augury" and "fully standalone" without turning the codebase into an overdesigned framework.

## Open Questions

1. Which translation or text corpus should ship for the 64 hexagrams and line texts?
   - This affects licensing, tone, and how much source text can be embedded locally.
2. Which casting methods do you want in MVP?
   - three coins only
   - three coins + yarrow probabilities
   - more than that
3. Should `augury` remain tarot-first, or should launch-with-no-subcommand open a system chooser?
4. Should daily hexagram be deterministic per day or freshly cast every run?
5. Is Discord support in scope for the first implementation, or can that wait for phase two?
6. What should the standalone binary be called?
   - `iching`
   - `augury-iching`
   - something branded differently
