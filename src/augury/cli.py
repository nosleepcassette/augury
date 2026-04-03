#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import random
import re
import select
import sys
import termios
import time
import tty
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import __version__
from . import art as art_module
from . import cards as cards_module
from . import engine as engine_module
from .config import (
    atomic_json_write as config_atomic_json_write,
    default_discord_helper_path,
    default_launcher_dir,
    get_app_paths,
    install_cli_launchers,
    install_discord_helper,
    load_integrations,
    load_preferences,
    load_json as config_load_json,
    load_system_preferences,
    save_integrations,
    save_system_preferences,
)
from .systems.iching import cli as iching_cli

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


VERSION = __version__
AMBER = "#ffb000"
AMBER_SOFT = "#ffd06a"
AMBER_DIM = "#9b6b1f"
STONE = "#cbb489"
INK = "#241707"
APP_PATHS = get_app_paths()
DATA_DIR = APP_PATHS.data_dir
READINGS_PATH = DATA_DIR / "readings.jsonl"
SPREADS_PATH = APP_PATHS.spreads_path
PREFS_PATH = APP_PATHS.prefs_path
INTEGRATIONS_PATH = APP_PATHS.integrations_path
LOGO_LINES = [
    "8888b.  888  888  .d88b.  888  888 888d888 888  888",
    '    "88b 888  888 d88P"88b 888  888 888P"   888  888',
    ".d888888 888  888 888  888 888  888 888     888  888",
    "888  888 Y88b 888 Y88b 888 Y88b 888 888     Y88b 888",
    '"Y888888  "Y88888  "Y88888  "Y88888 888      "Y88888',
    "                       888                       888",
    "                  Y8b d88P                  Y8b d88P",
    '                   "Y88P"                    "Y88P"',
]
TAGLINES = [
    "tarot terminal",
    "draw, read, remember",
    "amber light, no altars required",
]
DEFAULT_PREFS = {
    "default_spread": "three-card",
    "allow_reversals": True,
    "show_tips": True,
    "history_limit": 50,
}
PENDING_ESCAPE = False
PENDING_ESCAPE_PREFIX = ""
MENU_ITEMS = [
    ("n", "&New Reading", "new_reading"),
    ("d", "&Daily Card", "daily_card"),
    ("c", "&Card Browser", "card_browser"),
    ("h", "Reading &History", "reading_history"),
    ("s", "Custom &Spreads", "manage_custom_spreads"),
    ("p", "&Preferences", "preferences"),
    ("q", "&Quit", None),
]
MENU_HINT = "j/k move  |  enter select  |  hotkeys active"
SYSTEM_MENU_ITEMS = [
    ("t", "&Tarot", "tarot"),
    ("i", "&I Ching", "iching"),
    ("q", "&Quit", None),
]
SYSTEM_MENU_HINT = "j/k move  |  enter select  |  tarot / i ching hotkeys active"
FILTER_OPTIONS = [
    ("all", "All", None),
    ("major", "Major", "major"),
    ("wands", "Wands", "wands"),
    ("cups", "Cups", "cups"),
    ("swords", "Swords", "swords"),
    ("pentacles", "Pentacles", "pentacles"),
]


@dataclass
class StubCard:
    name: str
    number: int
    suit: str | None
    arcana: str
    upright_keywords: list[str]
    reversed_keywords: list[str]
    upright_meaning: str
    reversed_meaning: str
    element: str
    astrology: str
    numerology: str
    related_cards: list[str]
    educational_tip: str


@dataclass
class StubDrawnCard:
    card: Any
    position_name: str
    reversed: bool


@dataclass
class StubReading:
    spread_name: str
    query: str | None
    drawn_cards: list[StubDrawnCard]
    timestamp: datetime
    interpretation: str


STUB_SPREADS = {
    "single": {
        "name": "Single Card",
        "positions": ["Focus"],
        "description": "A single-card draw for an immediate signal.",
    },
    "three-card": {
        "name": "Three Card",
        "positions": ["Past", "Present", "Future"],
        "description": "A three-card line through momentum and direction.",
    },
    "relationship": {
        "name": "Relationship",
        "positions": ["You", "Them", "Connection", "Challenge", "Potential"],
        "description": "A relationship spread with mutual and shared positions.",
    },
    "career": {
        "name": "Career",
        "positions": ["Current Path", "Obstacle", "Opportunity", "Action", "Outcome"],
        "description": "A work-oriented spread with practical direction.",
    },
    "elemental": {
        "name": "Elemental",
        "positions": ["Fire", "Water", "Air", "Earth"],
        "description": "A four-card elemental cross.",
    },
    "yes-no": {
        "name": "Yes / No",
        "positions": ["Signal", "Friction", "Guidance"],
        "description": "Directional clarity without pretending tarot is a switch.",
    },
    "celtic-cross": {
        "name": "Celtic Cross",
        "positions": [
            "Present",
            "Challenge",
            "Past",
            "Future",
            "Above",
            "Below",
            "Advice",
            "External",
            "Hopes/Fears",
            "Outcome",
        ],
        "description": "A classic ten-card spread for larger situations.",
    },
}
STUB_CARDS = [
    StubCard(
        name="The Fool",
        number=0,
        suit=None,
        arcana="major",
        upright_keywords=["beginnings", "trust", "leap"],
        reversed_keywords=["hesitation", "naivete", "risk"],
        upright_meaning="A threshold card that asks for movement, openness, and trust in the new path.",
        reversed_meaning="The leap is still present, but fear or carelessness is distorting it.",
        element="Air",
        astrology="Uranus",
        numerology="0 / pure potential",
        related_cards=["The Magician"],
        educational_tip="The Fool is numbered zero because it can begin any cycle.",
    ),
    StubCard(
        name="The Magician",
        number=1,
        suit=None,
        arcana="major",
        upright_keywords=["skill", "focus", "will"],
        reversed_keywords=["scattered", "trickery", "untapped"],
        upright_meaning="Tools are on the table. The work is to align intention with execution.",
        reversed_meaning="Capacity exists, but it is being diffused, hidden, or handled dishonestly.",
        element="Air",
        astrology="Mercury",
        numerology="1 / initiative",
        related_cards=["The Fool"],
        educational_tip="The Magician connects inspiration to concrete action.",
    ),
    StubCard(
        name="The High Priestess",
        number=2,
        suit=None,
        arcana="major",
        upright_keywords=["intuition", "stillness", "depth"],
        reversed_keywords=["blocked", "secrets", "withdrawal"],
        upright_meaning="Listen beneath the noise. The answer is not loud, but it is present.",
        reversed_meaning="Inner knowing is available but being ignored or obscured.",
        element="Water",
        astrology="Moon",
        numerology="2 / polarity",
        related_cards=["The Moon"],
        educational_tip="This card reads what is unspoken as much as what is said.",
    ),
    StubCard(
        name="The Empress",
        number=3,
        suit=None,
        arcana="major",
        upright_keywords=["growth", "nurture", "abundance"],
        reversed_keywords=["depletion", "stagnation", "overgiving"],
        upright_meaning="Support, creativity, and material growth are available when properly tended.",
        reversed_meaning="What should nourish is strained, delayed, or smothering.",
        element="Earth",
        astrology="Venus",
        numerology="3 / growth",
        related_cards=["Ace of Pentacles"],
        educational_tip="The Empress is about systems that grow under care.",
    ),
    StubCard(
        name="Ace of Wands",
        number=1,
        suit="Wands",
        arcana="minor",
        upright_keywords=["spark", "drive", "start"],
        reversed_keywords=["stall", "delay", "burnout"],
        upright_meaning="A fresh ignition of desire, courage, or creative momentum.",
        reversed_meaning="The fire exists, but it is blocked, scattered, or not yet timed well.",
        element="Fire",
        astrology="Fire",
        numerology="1 / initiation",
        related_cards=["Two of Wands"],
        educational_tip="Aces introduce the raw seed of a suit before it fully takes shape.",
    ),
    StubCard(
        name="Two of Wands",
        number=2,
        suit="Wands",
        arcana="minor",
        upright_keywords=["planning", "range", "choice"],
        reversed_keywords=["fear", "smallness", "indecision"],
        upright_meaning="You can see more than one path. Strategy matters now.",
        reversed_meaning="The horizon is there, but fear is shrinking the field of view.",
        element="Fire",
        astrology="Mars in Aries",
        numerology="2 / duality",
        related_cards=["Ace of Wands"],
        educational_tip="Twos often ask for balance, reflection, or a meaningful choice.",
    ),
    StubCard(
        name="Ace of Cups",
        number=1,
        suit="Cups",
        arcana="minor",
        upright_keywords=["feeling", "opening", "blessing"],
        reversed_keywords=["numbness", "overflow", "guardedness"],
        upright_meaning="Emotional current is arriving fresh and clean. Let it move.",
        reversed_meaning="Feeling is present, but it is either blocked or spilling without a container.",
        element="Water",
        astrology="Water",
        numerology="1 / initiation",
        related_cards=["Two of Cups"],
        educational_tip="Cups speak to feeling, intuition, and relational life.",
    ),
    StubCard(
        name="Two of Cups",
        number=2,
        suit="Cups",
        arcana="minor",
        upright_keywords=["bond", "mutuality", "meeting"],
        reversed_keywords=["distance", "imbalance", "misattunement"],
        upright_meaning="A mutual exchange or mirror dynamic is active.",
        reversed_meaning="Connection is present, but it is not moving evenly or honestly.",
        element="Water",
        astrology="Venus in Cancer",
        numerology="2 / reciprocity",
        related_cards=["Ace of Cups"],
        educational_tip="Twos in Cups emphasize exchange and relational balance.",
    ),
    StubCard(
        name="Three of Swords",
        number=3,
        suit="Swords",
        arcana="minor",
        upright_keywords=["grief", "truth", "cut"],
        reversed_keywords=["release", "repair", "aftershock"],
        upright_meaning="Pain is clarifying something that sentiment could not hide.",
        reversed_meaning="The wound is still real, but healing or release has started.",
        element="Air",
        astrology="Saturn in Libra",
        numerology="3 / expression",
        related_cards=["Justice"],
        educational_tip="Swords deal with thought, truth, language, and conflict.",
    ),
    StubCard(
        name="Six of Pentacles",
        number=6,
        suit="Pentacles",
        arcana="minor",
        upright_keywords=["exchange", "support", "resources"],
        reversed_keywords=["debt", "strings", "imbalance"],
        upright_meaning="Resources are moving. The question is whether the exchange is fair.",
        reversed_meaning="Support has strings attached or is distributed unevenly.",
        element="Earth",
        astrology="Moon in Taurus",
        numerology="6 / reciprocity",
        related_cards=["Ace of Pentacles"],
        educational_tip="Pentacles read the body, money, labor, and material reality.",
    ),
    StubCard(
        name="The Star",
        number=17,
        suit=None,
        arcana="major",
        upright_keywords=["hope", "guidance", "renewal"],
        reversed_keywords=["fatigue", "distance", "doubt"],
        upright_meaning="A calmer, cleaner light is available after disruption.",
        reversed_meaning="Hope has not disappeared, but it feels remote or difficult to trust.",
        element="Air",
        astrology="Aquarius",
        numerology="17 / renewal",
        related_cards=["The Tower"],
        educational_tip="The Star is often the card that follows rupture with gentler reorientation.",
    ),
    StubCard(
        name="The World",
        number=21,
        suit=None,
        arcana="major",
        upright_keywords=["completion", "integration", "wholeness"],
        reversed_keywords=["delay", "unfinished", "loose ends"],
        upright_meaning="A cycle is reaching completion and asks to be integrated fully.",
        reversed_meaning="The arc is almost done, but something still needs closure.",
        element="Earth",
        astrology="Saturn",
        numerology="21 / completion",
        related_cards=["The Fool"],
        educational_tip="The World closes the cycle that The Fool begins.",
    ),
]


def _strip_markup(text: str) -> str:
    return re.sub(r"\[/?[^\]]+\]", "", text).replace(r"\[", "[").replace(r"\]", "]")


def _normalize_slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(value).strip().lower()).strip("-")


def _ensure_data_dir() -> None:
    READINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    PREFS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SPREADS_PATH.parent.mkdir(parents=True, exist_ok=True)


def _atomic_json_write(path: Path, payload: Any) -> None:
    config_atomic_json_write(path, payload)


def _load_json(path: Path, default: Any) -> Any:
    return config_load_json(path, default)


def _load_prefs() -> dict[str, Any]:
    prefs = dict(DEFAULT_PREFS)
    prefs.update(load_system_preferences("tarot"))
    return prefs


def _save_prefs(prefs: dict[str, Any]) -> None:
    save_system_preferences("tarot", prefs)


def _load_custom_spreads() -> list[dict[str, Any]]:
    payload = _load_json(SPREADS_PATH, [])
    spreads: list[dict[str, Any]] = []
    if isinstance(payload, list):
        for item in payload:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", "")).strip()
            positions = item.get("positions")
            if not name or not isinstance(positions, list) or not positions:
                continue
            spreads.append(
                {
                    "name": name,
                    "slug": _normalize_slug(item.get("slug") or name),
                    "positions": [str(position).strip() for position in positions if str(position).strip()],
                    "description": str(item.get("description", "")).strip(),
                    "custom": True,
                }
            )
    return spreads


def _save_custom_spreads(spreads: list[dict[str, Any]]) -> None:
    payload = []
    for spread in spreads:
        payload.append(
            {
                "name": spread["name"],
                "slug": spread["slug"],
                "positions": list(spread["positions"]),
                "description": spread.get("description", ""),
            }
        )
    _atomic_json_write(SPREADS_PATH, payload)


def _first_present(value: Any, *names: str, default: Any = None) -> Any:
    if isinstance(value, dict):
        lowered = {str(key).lower(): key for key in value}
        for name in names:
            candidates = {
                name,
                name.lower(),
                name.replace("-", "_"),
                name.replace("_", "-"),
                name.replace(" ", "_"),
                name.replace(" ", "-"),
            }
            for candidate in candidates:
                if candidate in value and value[candidate] is not None:
                    return value[candidate]
                actual = lowered.get(candidate.lower())
                if actual is not None and value[actual] is not None:
                    return value[actual]
        return default
    for name in names:
        candidates = {
            name,
            name.lower(),
            name.replace("-", "_"),
            name.replace("_", "-"),
            name.replace(" ", "_"),
            name.replace(" ", "-"),
        }
        for candidate in candidates:
            if hasattr(value, candidate):
                attr = getattr(value, candidate)
                if attr is not None:
                    return attr
    return default


def _json_safe(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value):
        return _json_safe(asdict(value))
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "__dict__"):
        return _json_safe(
            {
                key: item
                for key, item in vars(value).items()
                if not key.startswith("_")
            }
        )
    return value


def _get_all_cards() -> list[Any]:
    if cards_module is not None and getattr(cards_module, "ALL_CARDS", None):
        return list(cards_module.ALL_CARDS)
    return list(STUB_CARDS)


def _card_name(card: Any) -> str:
    return str(_first_present(card, "name", default="Unknown Card"))


def _card_arcana(card: Any) -> str:
    return str(_first_present(card, "arcana", default="minor")).lower()


def _card_suit(card: Any) -> str | None:
    suit = _first_present(card, "suit", default=None)
    if suit is None:
        return None
    return str(suit)


def _card_number(card: Any) -> int | None:
    number = _first_present(card, "number", default=None)
    try:
        return None if number is None else int(number)
    except Exception:
        return None


def _card_keywords(card: Any, reversed_card: bool) -> list[str]:
    key = "reversed_keywords" if reversed_card else "upright_keywords"
    value = _first_present(card, key, default=[])
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    return []


def _card_meaning(card: Any, reversed_card: bool) -> str:
    key = "reversed_meaning" if reversed_card else "upright_meaning"
    value = _first_present(card, key, default="")
    return str(value).strip()


def _card_tip(card: Any) -> str:
    return str(_first_present(card, "educational_tip", default="")).strip()


def _card_related(card: Any) -> list[str]:
    related = _first_present(card, "related_cards", default=[])
    if isinstance(related, list):
        return [str(item) for item in related]
    return []


def _card_element(card: Any) -> str:
    return str(_first_present(card, "element", default="")).strip()


def _card_astrology(card: Any) -> str:
    return str(_first_present(card, "astrology", default="")).strip()


def _card_numerology(card: Any) -> str:
    return str(_first_present(card, "numerology", default="")).strip()


def _lookup_card(name: str) -> Any:
    if cards_module is not None and hasattr(cards_module, "get_card_by_name"):
        try:
            return cards_module.get_card_by_name(name)
        except Exception:
            pass

    normalized = _normalize_slug(name)
    cards = _get_all_cards()
    exact = { _normalize_slug(_card_name(card)): card for card in cards }
    if normalized in exact:
        return exact[normalized]

    partial_matches = [card for card in cards if normalized in _normalize_slug(_card_name(card))]
    if len(partial_matches) == 1:
        return partial_matches[0]
    if partial_matches:
        raise KeyError(
            "Multiple cards matched %r: %s"
            % (name, ", ".join(_card_name(card) for card in partial_matches[:5]))
        )
    raise KeyError(f"Unknown tarot card: {name}")


def _spread_record(name: str, positions: list[str], description: str = "", custom: bool = False) -> dict[str, Any]:
    return {
        "name": name,
        "slug": _normalize_slug(name),
        "positions": positions,
        "description": description,
        "custom": custom,
    }


def _builtin_spreads() -> list[dict[str, Any]]:
    if cards_module is not None and getattr(cards_module, "SPREADS", None):
        spreads: list[dict[str, Any]] = []
        for key, spread in cards_module.SPREADS.items():
            if not isinstance(spread, dict):
                continue
            name = str(spread.get("name") or key).strip()
            positions = [str(item) for item in spread.get("positions", [])]
            if not name or not positions:
                continue
            spreads.append(
                {
                    "name": name,
                    "slug": _normalize_slug(spread.get("slug") or key),
                    "positions": positions,
                    "description": str(spread.get("description", "")).strip(),
                    "custom": False,
                }
            )
        if spreads:
            return spreads
    return [
        _spread_record(record["name"], list(record["positions"]), record.get("description", ""), False)
        for record in STUB_SPREADS.values()
    ]


def _all_spreads(custom_spreads: list[dict[str, Any]]) -> list[dict[str, Any]]:
    combined: list[dict[str, Any]] = []
    seen: set[str] = set()
    for spread in _builtin_spreads() + custom_spreads:
        slug = _normalize_slug(spread["slug"])
        if slug in seen:
            continue
        copy = dict(spread)
        copy["slug"] = slug
        combined.append(copy)
        seen.add(slug)
    return combined


def _resolve_spread(name: str, custom_spreads: list[dict[str, Any]]) -> dict[str, Any]:
    normalized = _normalize_slug(name)
    for spread in _all_spreads(custom_spreads):
        if normalized in {
            _normalize_slug(spread["slug"]),
            _normalize_slug(spread["name"]),
        }:
            return spread
    valid = ", ".join(spread["slug"] for spread in _all_spreads(custom_spreads))
    raise ValueError(f"Unknown spread '{name}'. Available spreads: {valid}")


def _reading_classes() -> tuple[type[Any], type[Any]]:
    drawn_cls = getattr(engine_module, "DrawnCard", StubDrawnCard) if engine_module else StubDrawnCard
    reading_cls = getattr(engine_module, "Reading", StubReading) if engine_module else StubReading
    return drawn_cls, reading_cls


def _fallback_patterns(reading: Any) -> dict[str, Any]:
    suit_distribution: dict[str, int] = {}
    reversal_count = 0
    major = 0
    numbers: list[int] = []
    for drawn in getattr(reading, "drawn_cards", []):
        suit = _card_suit(drawn.card)
        if suit:
            suit_distribution[suit] = suit_distribution.get(suit, 0) + 1
        if getattr(drawn, "reversed", False):
            reversal_count += 1
        if _card_arcana(drawn.card) == "major":
            major += 1
        number = _card_number(drawn.card)
        if number is not None:
            numbers.append(number)
    repeats: dict[str, int] = {}
    for number in sorted(set(numbers)):
        count = numbers.count(number)
        if count > 1:
            repeats[str(number)] = count
    dominant_suit = None
    if suit_distribution:
        dominant_suit = sorted(suit_distribution.items(), key=lambda item: (-item[1], item[0]))[0][0]
    return {
        "suit_distribution": suit_distribution,
        "major_minor_ratio": {"major": major, "minor": len(getattr(reading, "drawn_cards", [])) - major},
        "number_patterns": {"numbers": numbers, "repeats": repeats, "sequence": False},
        "elemental_balance": {},
        "reversal_count": reversal_count,
        "dominant_suit": dominant_suit,
        "dominant_element": None,
    }


def _fallback_interpretation(reading: Any) -> str:
    sections: list[str] = []
    if getattr(reading, "query", None):
        sections.append(f'Question: "{reading.query}".')
    sections.append(
        f"The {reading.spread_name} spread drew {len(getattr(reading, 'drawn_cards', []))} card"
        + ("s." if len(getattr(reading, "drawn_cards", [])) != 1 else ".")
    )
    for drawn in getattr(reading, "drawn_cards", []):
        orientation = "reversed" if getattr(drawn, "reversed", False) else "upright"
        sections.append(
            f"{_card_name(drawn.card)} in {drawn.position_name} appears {orientation}. {_card_meaning(drawn.card, getattr(drawn, 'reversed', False))}"
        )
    analysis = _fallback_patterns(reading)
    if analysis["dominant_suit"]:
        sections.append(f"Dominant suit: {analysis['dominant_suit']}.")
    return "\n\n".join(section for section in sections if section.strip())


def _fallback_tips(reading: Any) -> list[str]:
    tips: list[str] = []
    for drawn in getattr(reading, "drawn_cards", []):
        tip = _card_tip(drawn.card)
        if tip and tip not in tips:
            tips.append(tip)
    return tips[:5]


def _fallback_reading_to_json(reading: Any) -> dict[str, Any]:
    def _fallback_card_payload(card: Any) -> dict[str, Any]:
        payload = _json_safe(card)
        if isinstance(payload, dict):
            payload["art"] = _card_art(card)
            return payload
        return {
            "name": _card_name(card),
            "number": _card_number(card),
            "suit": _card_suit(card),
            "arcana": _card_arcana(card),
            "art": _card_art(card),
        }

    return {
        "spread_name": reading.spread_name,
        "query": reading.query,
        "timestamp": reading.timestamp.isoformat(),
        "drawn_cards": [
            {
                "name": _card_name(drawn.card),
                "arcana": _card_arcana(drawn.card),
                "suit": _card_suit(drawn.card),
                "number": _card_number(drawn.card),
                "element": _card_element(drawn.card),
                "position_name": drawn.position_name,
                "reversed": drawn.reversed,
                "art": _card_art(drawn.card),
                "keywords": _card_keywords(drawn.card, drawn.reversed),
                "meaning": _card_meaning(drawn.card, drawn.reversed),
                "card": _fallback_card_payload(drawn.card),
            }
            for drawn in reading.drawn_cards
        ],
        "interpretation": reading.interpretation,
        "analysis": _fallback_patterns(reading),
        "educational_tips": _fallback_tips(reading),
    }


def _analyze_patterns(reading: Any) -> dict[str, Any]:
    if engine_module is not None and hasattr(engine_module, "analyze_patterns"):
        try:
            return engine_module.analyze_patterns(reading)
        except Exception:
            pass
    return _fallback_patterns(reading)


def _interpret_reading(reading: Any) -> str:
    if engine_module is not None and hasattr(engine_module, "interpret_reading"):
        try:
            return engine_module.interpret_reading(reading)
        except Exception:
            pass
    return _fallback_interpretation(reading)


def _generate_tips(reading: Any) -> list[str]:
    if engine_module is not None and hasattr(engine_module, "generate_educational_tips"):
        try:
            return engine_module.generate_educational_tips(reading)
        except Exception:
            pass
    return _fallback_tips(reading)


def _reading_to_json(reading: Any) -> dict[str, Any]:
    if engine_module is not None and hasattr(engine_module, "reading_to_json"):
        try:
            return engine_module.reading_to_json(reading)
        except Exception:
            pass
    return _fallback_reading_to_json(reading)


def _save_reading(reading: Any) -> None:
    if engine_module is not None and hasattr(engine_module, "save_reading"):
        try:
            engine_module.save_reading(reading, READINGS_PATH)
            return
        except Exception:
            pass
    _ensure_data_dir()
    with READINGS_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(_reading_to_json(reading), ensure_ascii=True))
        handle.write("\n")


def _load_readings() -> list[Any]:
    if engine_module is not None and hasattr(engine_module, "load_readings"):
        try:
            return list(engine_module.load_readings(READINGS_PATH))
        except Exception:
            pass
    if not READINGS_PATH.exists():
        return []
    readings: list[Any] = []
    drawn_cls, reading_cls = _reading_classes()
    with READINGS_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            drawn_cards = []
            for item in payload.get("drawn_cards", []):
                drawn_cards.append(
                    drawn_cls(
                        card=item.get("card") or {"name": item.get("name", "Unknown Card")},
                        position_name=str(item.get("position_name", "Card")),
                        reversed=bool(item.get("reversed", False)),
                    )
                )
            timestamp_text = payload.get("timestamp") or datetime.now(timezone.utc).isoformat()
            readings.append(
                reading_cls(
                    spread_name=str(payload.get("spread_name", "Unknown Spread")),
                    query=payload.get("query"),
                    drawn_cards=drawn_cards,
                    timestamp=datetime.fromisoformat(timestamp_text),
                    interpretation=str(payload.get("interpretation", "")),
                )
            )
    return readings


def _card_art(card: Any) -> str:
    existing = _first_present(card, "art", default=None)
    if isinstance(existing, str) and existing.strip():
        return existing
    name = _card_name(card)
    suit = _card_suit(card)
    number = _card_number(card)
    if art_module is not None:
        try:
            if _card_arcana(card) == "major" and hasattr(art_module, "get_card_art"):
                return art_module.get_card_art(name)
            if suit and number and hasattr(art_module, "get_suit_art"):
                return art_module.get_suit_art(suit, number)
        except Exception:
            pass
        if hasattr(art_module, "CARD_BACK"):
            return str(art_module.CARD_BACK)
    title = name[:15].center(17)
    lines = [
        "+-----------------+",
        f"|{title}|",
        "|                 |",
        "|      .---.      |",
        "|     /     \\     |",
        "|     \\_____/     |",
        "|                 |",
        f"| {(_card_suit(card) or 'major')[:13].center(13)} |",
        "|                 |",
        "|     cassette    |",
        "|                 |",
        "|                 |",
        f"| {str(_card_number(card) or '').rjust(2)}              |",
        "+-----------------+",
    ]
    return "\n".join(lines[:15])


def _draw_reading(spread: dict[str, Any], query: str | None, prefs: dict[str, Any]) -> Any:
    cards = _get_all_cards()
    needed = len(spread["positions"])
    if len(cards) < needed:
        raise ValueError(f"Spread {spread['name']} needs {needed} cards, but only {len(cards)} are available.")

    rng = random.SystemRandom()
    selected_cards = rng.sample(cards, needed)
    drawn_cls, reading_cls = _reading_classes()
    drawn_cards = []
    for index, position in enumerate(spread["positions"]):
        drawn_cards.append(
            drawn_cls(
                card=selected_cards[index],
                position_name=str(position),
                reversed=bool(prefs.get("allow_reversals", True) and rng.random() < 0.30),
            )
        )

    reading = reading_cls(
        spread_name=spread["name"],
        query=query,
        drawn_cards=drawn_cards,
        timestamp=datetime.now(timezone.utc),
        interpretation="",
    )
    reading.interpretation = _interpret_reading(reading)
    return reading


def _card_payload(card: Any) -> dict[str, Any]:
    payload = _json_safe(card)
    if isinstance(payload, dict):
        payload["art"] = _card_art(card)
        return payload
    return {
        "name": _card_name(card),
        "number": _card_number(card),
        "suit": _card_suit(card),
        "arcana": _card_arcana(card),
        "keywords": _card_keywords(card, False),
        "art": _card_art(card),
    }


def _timestamp_text(reading: Any) -> str:
    timestamp = getattr(reading, "timestamp", None)
    if isinstance(timestamp, datetime):
        return timestamp.astimezone().strftime("%Y-%m-%d %H:%M")
    return str(timestamp or "")


def _summary_cards(reading: Any) -> str:
    names = [_card_name(drawn.card) for drawn in getattr(reading, "drawn_cards", [])]
    if len(names) <= 3:
        return ", ".join(names)
    return ", ".join(names[:3]) + f" +{len(names) - 3}"


def _interpret_stub_note() -> dict[str, Any]:
    return {
        "requested": True,
        "status": "stub",
        "message": "--interpret is reserved for later LLM narrative mode; showing template output now.",
    }


def _clear_screen(console: Console) -> None:
    if HAS_RICH:
        console.clear()
    else:
        os.system("clear")


def _centered(console: Console, markup: str, plain_text: str | None = None) -> str:
    plain = plain_text if plain_text is not None else _strip_markup(markup)
    width = getattr(console, "width", 80) or 80
    padding = max(0, (width - len(plain)) // 2)
    return (" " * padding) + markup


def _banner(console: Console, subtitle: str = "") -> str:
    lines = []
    for line in LOGO_LINES:
        lines.append(_centered(console, f"[bold {AMBER}]{line}[/]", line))
    lines.append("")
    for index, tagline in enumerate(TAGLINES):
        color = AMBER_SOFT if index == 0 else STONE if index == 1 else AMBER_DIM
        style = "bold" if index == 0 else "dim"
        lines.append(_centered(console, f"[{style} {color}]{tagline}[/]", tagline))
    if subtitle:
        lines.append("")
        lines.append(_centered(console, f"[dim]{subtitle}[/dim]", subtitle))
    return "\n".join(lines)


def _read_key() -> str:
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


def _menu_label(template: str, selected: bool) -> tuple[str, str]:
    marker = template.find("&")
    plain = template.replace("&", "")
    if marker == -1 or marker == len(template) - 1:
        return plain, plain
    before = rich_escape(template[:marker])
    key = rich_escape(template[marker + 1])
    after = rich_escape(template[marker + 2:])
    if selected:
        markup = (
            f"[bold {AMBER_SOFT}]{before}[/]"
            f"[bold underline {AMBER}]{key}[/]"
            f"[bold {AMBER_SOFT}]{after}[/]"
        )
    else:
        markup = (
            f"[{STONE}]{before}[/]"
            f"[underline {AMBER_SOFT}]{key}[/]"
            f"[{STONE}]{after}[/]"
        )
    return markup, plain


def _render_card_panel(drawn: Any) -> Panel | str:
    art_text = _card_art(drawn.card)
    orientation = "REVERSED" if drawn.reversed else "UPRIGHT"
    keywords = ", ".join(_card_keywords(drawn.card, drawn.reversed)[:4])
    element = _card_element(drawn.card)
    astrology = _card_astrology(drawn.card)
    if not HAS_RICH:
        return (
            f"{_card_name(drawn.card)} [{orientation}] ({drawn.position_name})\n"
            f"{art_text}\n"
            f"{keywords}\n{element} | {astrology}"
        )
    title = f"{_card_name(drawn.card)}"
    subtitle = f"{drawn.position_name}  |  {orientation}"
    content = Group(
        Align.center(Text(art_text, style=AMBER_SOFT)),
        Text(keywords or " ", style=AMBER_SOFT),
        Text(f"{element}  |  {astrology}" if (element or astrology) else " ", style="dim"),
    )
    return Panel(
        content,
        title=title,
        subtitle=subtitle,
        border_style=AMBER,
        box=box.ASCII,
        padding=(0, 1),
        expand=True,
    )


def _render_patterns_table(reading: Any) -> Table | str:
    analysis = _analyze_patterns(reading)
    suit_distribution = analysis.get("suit_distribution", {})
    ratio = analysis.get("major_minor_ratio", {})
    if not HAS_RICH:
        return (
            f"major {ratio.get('major', 0)}  minor {ratio.get('minor', 0)}\n"
            f"suits: {json.dumps(suit_distribution, ensure_ascii=True)}\n"
            f"reversals: {analysis.get('reversal_count', 0)}"
        )
    table = Table.grid(padding=(0, 2))
    table.add_column(style=AMBER_SOFT)
    table.add_column(style=STONE)
    table.add_row("Major / Minor", f"{ratio.get('major', 0)} / {ratio.get('minor', 0)}")
    table.add_row("Reversals", str(analysis.get("reversal_count", 0)))
    table.add_row("Dominant Suit", str(analysis.get("dominant_suit") or "-"))
    table.add_row("Dominant Element", str(analysis.get("dominant_element") or "-"))
    if suit_distribution:
        table.add_row(
            "Suit Spread",
            ", ".join(f"{name}:{count}" for name, count in suit_distribution.items()),
        )
    repeats = analysis.get("number_patterns", {}).get("repeats", {})
    if repeats:
        table.add_row(
            "Number Repeats",
            ", ".join(f"{number}x{count}" for number, count in repeats.items()),
        )
    return table


def _terminal_rows(default: int = 24) -> int:
    try:
        return os.get_terminal_size().lines
    except OSError:
        return default


def _window_bounds(total: int, cursor: int, page_size: int) -> tuple[int, int]:
    if total <= page_size:
        return 0, total
    start = max(0, min(cursor - (page_size // 2), total - page_size))
    return start, min(total, start + page_size)


def _show_card_detail(console: Console, card: Any) -> None:
    _clear_screen(console)
    console.print(_banner(console, f"card detail  ·  {_card_name(card)}"))
    console.print("")
    if HAS_RICH:
        left = Panel(
            Align.center(Text(_card_art(card), style=AMBER_SOFT)),
            title=_card_name(card),
            border_style=AMBER,
            box=box.ASCII,
        )
        info = Table.grid(padding=(0, 1))
        info.add_column(style=AMBER_SOFT)
        info.add_column(style=STONE)
        info.add_row("Arcana", _card_arcana(card).title())
        info.add_row("Suit", str(_card_suit(card) or "-"))
        info.add_row("Number", str(_card_number(card) if _card_number(card) is not None else "-"))
        info.add_row("Element", _card_element(card) or "-")
        info.add_row("Astrology", _card_astrology(card) or "-")
        info.add_row("Numerology", _card_numerology(card) or "-")
        details = Panel(info, title="Correspondences", border_style=AMBER, box=box.ASCII)
        console.print(Columns([left, details], expand=True, equal=True))
        console.print("")
        console.print(
            Panel(
                Group(
                    Text("Upright", style=f"bold {AMBER}"),
                    Text(_card_meaning(card, False), style=STONE),
                    Text("", style=STONE),
                    Text("Reversed", style=f"bold {AMBER}"),
                    Text(_card_meaning(card, True), style=STONE),
                ),
                title="Meanings",
                border_style=AMBER,
                box=box.ASCII,
            )
        )
        keywords = Table.grid(padding=(0, 2))
        keywords.add_column(style=AMBER_SOFT)
        keywords.add_column(style=STONE)
        keywords.add_row("Upright Keywords", ", ".join(_card_keywords(card, False)) or "-")
        keywords.add_row("Reversed Keywords", ", ".join(_card_keywords(card, True)) or "-")
        keywords.add_row("Related", ", ".join(_card_related(card)) or "-")
        keywords.add_row("Tip", _card_tip(card) or "-")
        console.print(Panel(keywords, title="Study Notes", border_style=AMBER, box=box.ASCII))
    else:
        console.print(_card_art(card))
        console.print(_card_meaning(card, False))
        console.print(_card_meaning(card, True))
        console.print(_card_tip(card))
    console.print("")
    console.print("[dim]enter to return[/dim]" if HAS_RICH else "enter to return")
    try:
        console.input("")
    except (EOFError, KeyboardInterrupt):
        return


def _show_reading(console: Console, reading: Any, title: str = "reading") -> None:
    _clear_screen(console)
    subtitle = f"{reading.spread_name}  ·  {_timestamp_text(reading)}"
    console.print(_banner(console, subtitle))
    console.print("")
    if HAS_RICH:
        panels = [_render_card_panel(drawn) for drawn in reading.drawn_cards]
        console.print(Columns(panels, expand=True, equal=True))
        console.print("")
        console.print(
            Panel(
                Text(reading.interpretation or "(no interpretation)", style=STONE),
                title="Interpretation",
                border_style=AMBER,
                box=box.ASCII,
                padding=(1, 2),
            )
        )
        console.print(
            Panel(
                _render_patterns_table(reading),
                title="Patterns",
                border_style=AMBER,
                box=box.ASCII,
                padding=(0, 1),
            )
        )
        tips = _generate_tips(reading)
        console.print(
            Panel(
                Group(*[Text(f"- {tip}", style=STONE) for tip in tips] or [Text("(no tips)", style="dim")]),
                title="Educational Tips",
                border_style=AMBER,
                box=box.ASCII,
                padding=(0, 1),
            )
        )
    else:
        console.print(title)
        console.print(reading.interpretation)
        for drawn in reading.drawn_cards:
            console.print(_render_card_panel(drawn))
    console.print("")
    console.print("[dim]enter to return[/dim]" if HAS_RICH else "enter to return")
    try:
        console.input("")
    except (EOFError, KeyboardInterrupt):
        return


class AuguryApp:
    def __init__(self) -> None:
        self.console = Console(highlight=False, force_terminal=True) if HAS_RICH else Console()
        self.prefs = _load_prefs()
        self.custom_spread_defs = _load_custom_spreads()

    def refresh(self) -> None:
        self.prefs = _load_prefs()
        self.custom_spread_defs = _load_custom_spreads()

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
        readings = _load_readings()
        spreads = _all_spreads(self.custom_spread_defs)
        subtitle = (
            f"v{VERSION}  ·  deck {len(_get_all_cards())}  ·  readings {len(readings)}  ·  spreads {len(spreads)}"
        )
        _clear_screen(self.console)
        self.console.print(_banner(self.console, subtitle))
        self.console.print("")
        if HAS_RICH:
            stats = Table.grid(padding=(0, 3))
            stats.add_column(style=AMBER_SOFT)
            stats.add_column(style=STONE)
            stats.add_row("Default Spread", str(self.prefs.get("default_spread", "three-card")))
            stats.add_row("Reversals", "on" if self.prefs.get("allow_reversals", True) else "off")
            stats.add_row("Tips", "on" if self.prefs.get("show_tips", True) else "off")
            self.console.print(
                Align.center(
                    Panel(
                        stats,
                        title="Current State",
                        border_style=AMBER,
                        box=box.ASCII,
                        padding=(0, 2),
                        expand=False,
                    )
                )
            )
            self.console.print("")
        label_width = max(len(item[1].replace("&", "")) for item in MENU_ITEMS)
        for index, (_hotkey, label, _action) in enumerate(MENU_ITEMS):
            styled, plain = _menu_label(label, index == selected)
            padding = " " * (label_width - len(plain))
            if index == selected:
                markup = f"[bold {AMBER}]>===<[/]  {styled}{padding}"
                raw = f">===<  {plain}{padding}"
            else:
                markup = f"[{AMBER_DIM}].....[/]  {styled}{padding}"
                raw = f".....  {plain}{padding}"
            self.console.print(_centered(self.console, markup, raw))
        self.console.print("")
        self.console.print(_centered(self.console, f"[dim]{MENU_HINT}[/dim]", MENU_HINT))

    def run(self) -> int:
        if not sys.stdin.isatty():
            return self.run_fallback_menu()
        selected = 0
        while True:
            self.draw_main_menu(selected)
            key = _read_key()
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
        while True:
            self.draw_main_menu(0)
            self.console.print("")
            choice = self.prompt("choice [n/d/c/h/s/p/q]", "q").lower()
            mapping = {item[0]: item[2] for item in MENU_ITEMS}
            action = mapping.get(choice)
            if action is None:
                return 0
            getattr(self, action)()

    def choose_spread(self, initial: str | None = None) -> dict[str, Any] | None:
        spreads = _all_spreads(self.custom_spread_defs)
        index = 0
        if initial:
            normalized = _normalize_slug(initial)
            for spread_index, spread in enumerate(spreads):
                if spread["slug"] == normalized or _normalize_slug(spread["name"]) == normalized:
                    index = spread_index
                    break
        if not sys.stdin.isatty():
            self.console.print("")
            for number, spread in enumerate(spreads, start=1):
                self.console.print(f"{number:2}. {spread['name']} ({len(spread['positions'])})")
            choice = self.prompt("spread number", str(index + 1))
            try:
                return spreads[max(0, min(len(spreads) - 1, int(choice) - 1))]
            except Exception:
                return spreads[index]
        while True:
            _clear_screen(self.console)
            spread = spreads[index]
            self.console.print(_banner(self.console, "choose spread"))
            self.console.print("")
            if HAS_RICH:
                table = Table(show_header=True, header_style=f"bold {AMBER}", box=box.ASCII, padding=(0, 1))
                table.add_column("#", style="dim", width=4)
                table.add_column("spread", style=AMBER_SOFT, min_width=18)
                table.add_column("cards", style=STONE, width=6)
                table.add_column("description", style=STONE)
                for row_index, item in enumerate(spreads, start=1):
                    style = f"bold {AMBER}" if row_index - 1 == index else ""
                    table.add_row(str(row_index), item["name"], str(len(item["positions"])), item.get("description", ""), style=style)
                self.console.print(table)
            else:
                for row_index, item in enumerate(spreads, start=1):
                    cursor = ">" if row_index - 1 == index else " "
                    self.console.print(f"{cursor} {row_index:2}. {item['name']} ({len(item['positions'])})")
            self.console.print("")
            self.console.print("[dim]j/k move  enter choose  q cancel[/dim]" if HAS_RICH else "j/k move, enter choose, q cancel")
            key = _read_key()
            if key in ("UP", "k"):
                index = (index - 1) % len(spreads)
            elif key in ("DOWN", "j"):
                index = (index + 1) % len(spreads)
            elif key in ("\r", "\n"):
                return spreads[index]
            elif key == "q":
                return None
            elif key in ("CTRL_C", "CTRL_D"):
                return None

    def new_reading(self) -> None:
        spread = self.choose_spread(self.prefs.get("default_spread", "three-card"))
        if spread is None:
            return
        query = self.prompt("query", "")
        reading = _draw_reading(spread, query or None, self.prefs)
        _save_reading(reading)
        _show_reading(self.console, reading, "new reading")

    def daily_card(self) -> None:
        query = f"Daily guidance for {datetime.now().date().isoformat()}"
        spread = _resolve_spread("single", self.custom_spread_defs)
        reading = _draw_reading(spread, query, self.prefs)
        _save_reading(reading)
        _show_reading(self.console, reading, "daily card")

    def card_browser(self) -> None:
        cards = _get_all_cards()
        filter_index = 0
        cursor = 0
        search_query = ""
        while True:
            filtered = []
            filter_slug = FILTER_OPTIONS[filter_index][2]
            for card in cards:
                if filter_slug == "major" and _card_arcana(card) != "major":
                    continue
                if filter_slug and filter_slug != "major":
                    if _normalize_slug(_card_suit(card) or "") != filter_slug:
                        continue
                if search_query:
                    haystack = " ".join(
                        [
                            _card_name(card),
                            _card_suit(card) or "",
                            " ".join(_card_keywords(card, False)),
                            " ".join(_card_keywords(card, True)),
                        ]
                    ).lower()
                    if search_query.lower() not in haystack:
                        continue
                filtered.append(card)
            if not filtered:
                cursor = 0
            else:
                cursor = max(0, min(cursor, len(filtered) - 1))
            page_size = max(8, _terminal_rows() - 14)
            start, end = _window_bounds(len(filtered), cursor, page_size)
            page_cards = filtered[start:end]
            _clear_screen(self.console)
            subtitle = f"filter {FILTER_OPTIONS[filter_index][1]}  |  matches {len(filtered)}"
            self.console.print(_banner(self.console, subtitle))
            self.console.print("")
            if HAS_RICH:
                table = Table(show_header=True, header_style=f"bold {AMBER}", box=box.ASCII, padding=(0, 1))
                table.add_column("#", style="dim", width=4)
                table.add_column("card", style=AMBER_SOFT)
                table.add_column("arcana", style=STONE, width=8)
                table.add_column("suit", style=STONE, width=12)
                table.add_column("keywords", style=STONE)
                for absolute_index, card in enumerate(page_cards, start=start):
                    style = f"bold {AMBER}" if absolute_index == cursor else ""
                    table.add_row(
                        str(absolute_index + 1),
                        _card_name(card),
                        _card_arcana(card),
                        str(_card_suit(card) or "-"),
                        ", ".join(_card_keywords(card, False)[:3]),
                        style=style,
                    )
                self.console.print(table)
            else:
                for absolute_index, card in enumerate(page_cards, start=start):
                    cursor_mark = ">" if absolute_index == cursor else " "
                    self.console.print(f"{cursor_mark} {absolute_index + 1:2}. {_card_name(card)}")
            if filtered and len(filtered) > len(page_cards):
                self.console.print("")
                self.console.print(
                    f"[dim]showing {start + 1}-{end} of {len(filtered)}[/dim]"
                    if HAS_RICH
                    else f"showing {start + 1}-{end} of {len(filtered)}"
                )
            self.console.print("")
            self.console.print(
                "[dim]j/k move  f cycle filter  / search  enter view  q back[/dim]"
                if HAS_RICH
                else "j/k move, f cycle filter, / search, enter view, q back"
            )
            key = _read_key()
            if key in ("UP", "k") and filtered:
                cursor = (cursor - 1) % len(filtered)
            elif key in ("DOWN", "j") and filtered:
                cursor = (cursor + 1) % len(filtered)
            elif key == "f":
                filter_index = (filter_index + 1) % len(FILTER_OPTIONS)
                cursor = 0
            elif key == "/":
                search_query = self.prompt("search", search_query)
            elif key in ("\r", "\n") and filtered:
                _show_card_detail(self.console, filtered[cursor])
            elif key == "q":
                return
            elif key in ("CTRL_C", "CTRL_D"):
                return

    def reading_history(self) -> None:
        readings = list(reversed(_load_readings()))
        if not readings:
            _clear_screen(self.console)
            self.console.print(_banner(self.console, "reading history"))
            self.console.print("")
            self.notice("No readings saved yet.")
            self.pause()
            return
        limit = max(1, int(self.prefs.get("history_limit", 50)))
        readings = readings[:limit]
        cursor = 0
        while True:
            page_size = max(8, _terminal_rows() - 14)
            start, end = _window_bounds(len(readings), cursor, page_size)
            page_readings = readings[start:end]
            _clear_screen(self.console)
            self.console.print(_banner(self.console, f"reading history  |  showing {len(readings)}"))
            self.console.print("")
            if HAS_RICH:
                table = Table(show_header=True, header_style=f"bold {AMBER}", box=box.ASCII, padding=(0, 1))
                table.add_column("#", style="dim", width=4)
                table.add_column("when", style=STONE, width=18)
                table.add_column("spread", style=AMBER_SOFT, width=18)
                table.add_column("cards", style=STONE)
                table.add_column("query", style=STONE)
                for absolute_index, reading in enumerate(page_readings, start=start):
                    style = f"bold {AMBER}" if absolute_index == cursor else ""
                    table.add_row(
                        str(absolute_index + 1),
                        _timestamp_text(reading),
                        reading.spread_name,
                        _summary_cards(reading),
                        str(reading.query or "-"),
                        style=style,
                    )
                self.console.print(table)
            else:
                for absolute_index, reading in enumerate(page_readings, start=start):
                    cursor_mark = ">" if absolute_index == cursor else " "
                    self.console.print(f"{cursor_mark} {absolute_index + 1:2}. {_timestamp_text(reading)}  {reading.spread_name}")
            if len(readings) > len(page_readings):
                self.console.print("")
                self.console.print(
                    f"[dim]showing {start + 1}-{end} of {len(readings)}[/dim]"
                    if HAS_RICH
                    else f"showing {start + 1}-{end} of {len(readings)}"
                )
            self.console.print("")
            self.console.print("[dim]j/k move  enter view  q back[/dim]" if HAS_RICH else "j/k move, enter view, q back")
            key = _read_key()
            if key in ("UP", "k"):
                cursor = (cursor - 1) % len(readings)
            elif key in ("DOWN", "j"):
                cursor = (cursor + 1) % len(readings)
            elif key in ("\r", "\n"):
                _show_reading(self.console, readings[cursor], "reading history")
            elif key == "q":
                return
            elif key in ("CTRL_C", "CTRL_D"):
                return

    def manage_custom_spreads(self) -> None:
        while True:
            self.refresh()
            _clear_screen(self.console)
            self.console.print(_banner(self.console, "custom spreads"))
            self.console.print("")
            spreads = self.custom_spread_defs
            if HAS_RICH:
                table = Table(show_header=True, header_style=f"bold {AMBER}", box=box.ASCII, padding=(0, 1))
                table.add_column("#", style="dim", width=4)
                table.add_column("name", style=AMBER_SOFT)
                table.add_column("positions", style=STONE)
                table.add_column("description", style=STONE)
                for index, spread in enumerate(spreads, start=1):
                    table.add_row(
                        str(index),
                        spread["name"],
                        ", ".join(spread["positions"]),
                        spread.get("description", ""),
                    )
                self.console.print(table)
            else:
                for index, spread in enumerate(spreads, start=1):
                    self.console.print(f"{index:2}. {spread['name']} -> {', '.join(spread['positions'])}")
            self.console.print("")
            self.console.print(
                "[dim]a add  d delete  v view  q back[/dim]" if HAS_RICH else "a add, d delete, v view, q back"
            )
            key = _read_key()
            if key == "a":
                name = self.prompt("spread name", "")
                if not name:
                    continue
                positions_raw = self.prompt("positions (comma-separated)", "")
                positions = [item.strip() for item in positions_raw.split(",") if item.strip()]
                if not positions:
                    self.notice("Need at least one position.", "red")
                    self.pause()
                    continue
                description = self.prompt("description", "")
                spread = {
                    "name": name,
                    "slug": _normalize_slug(name),
                    "positions": positions,
                    "description": description,
                    "custom": True,
                }
                spreads.append(spread)
                _save_custom_spreads(spreads)
            elif key == "d":
                if not spreads:
                    continue
                choice = self.prompt("delete spread #", "")
                if not choice:
                    continue
                try:
                    index = int(choice) - 1
                    if index < 0 or index >= len(spreads):
                        raise ValueError
                except Exception:
                    self.notice("Invalid spread number.", "red")
                    self.pause()
                    continue
                confirm = self.prompt(f"delete {spreads[index]['name']}? [y/N]", "n").lower()
                if confirm == "y":
                    del spreads[index]
                    _save_custom_spreads(spreads)
            elif key == "v":
                if not spreads:
                    continue
                choice = self.prompt("view spread #", "")
                try:
                    index = int(choice) - 1
                    spread = spreads[index]
                except Exception:
                    continue
                _clear_screen(self.console)
                self.console.print(_banner(self.console, spread["name"]))
                self.console.print("")
                self.console.print(
                    Panel(
                        "\n".join(f"{idx}. {position}" for idx, position in enumerate(spread["positions"], start=1)),
                        title="Positions",
                        border_style=AMBER,
                        box=box.ASCII,
                    )
                )
                if spread.get("description"):
                    self.console.print(
                        Panel(spread["description"], title="Description", border_style=AMBER, box=box.ASCII)
                    )
                self.pause()
            elif key == "q":
                return
            elif key in ("CTRL_C", "CTRL_D"):
                return

    def preferences(self) -> None:
        options = [
            ("default_spread", "Default Spread"),
            ("allow_reversals", "Allow Reversals"),
            ("show_tips", "Show Tips"),
            ("history_limit", "History Limit"),
        ]
        cursor = 0
        while True:
            self.refresh()
            _clear_screen(self.console)
            self.console.print(_banner(self.console, "preferences"))
            self.console.print("")
            if HAS_RICH:
                table = Table(show_header=True, header_style=f"bold {AMBER}", box=box.ASCII, padding=(0, 1))
                table.add_column("#", style="dim", width=4)
                table.add_column("setting", style=AMBER_SOFT)
                table.add_column("value", style=STONE)
                for index, (key, label) in enumerate(options, start=1):
                    style = f"bold {AMBER}" if index - 1 == cursor else ""
                    value = self.prefs.get(key)
                    table.add_row(str(index), label, str(value), style=style)
                self.console.print(table)
            else:
                for index, (key, label) in enumerate(options, start=1):
                    cursor_mark = ">" if index - 1 == cursor else " "
                    self.console.print(f"{cursor_mark} {index:2}. {label}: {self.prefs.get(key)}")
            self.console.print("")
            self.console.print(
                "[dim]j/k move  enter edit/toggle  q back[/dim]" if HAS_RICH else "j/k move, enter edit, q back"
            )
            key = _read_key()
            if key in ("UP", "k"):
                cursor = (cursor - 1) % len(options)
            elif key in ("DOWN", "j"):
                cursor = (cursor + 1) % len(options)
            elif key in ("\r", "\n"):
                pref_key, label = options[cursor]
                if pref_key in {"allow_reversals", "show_tips"}:
                    self.prefs[pref_key] = not bool(self.prefs.get(pref_key, False))
                elif pref_key == "history_limit":
                    value = self.prompt(label, str(self.prefs.get(pref_key, 50)))
                    try:
                        self.prefs[pref_key] = max(1, int(value))
                    except Exception:
                        pass
                elif pref_key == "default_spread":
                    spread = self.choose_spread(str(self.prefs.get(pref_key, "three-card")))
                    if spread:
                        self.prefs[pref_key] = spread["slug"]
                _save_prefs(self.prefs)
            elif key == "q":
                return
            elif key in ("CTRL_C", "CTRL_D"):
                return


class SystemChooserApp:
    def __init__(self) -> None:
        self.console = Console(highlight=False, force_terminal=True) if HAS_RICH else Console()

    def draw_main_menu(self, selected: int) -> None:
        from .systems.iching.engine import load_consultations

        tarot_readings = _load_readings()
        iching_consultations = load_consultations()
        subtitle = (
            f"v{VERSION}  ·  tarot {len(tarot_readings)} readings  ·  i ching {len(iching_consultations)} consultations"
        )
        _clear_screen(self.console)
        self.console.print(_banner(self.console, subtitle))
        self.console.print("")
        if HAS_RICH:
            stats = Table.grid(padding=(0, 3))
            stats.add_column(style=AMBER_SOFT)
            stats.add_column(style=STONE)
            stats.add_row("Tarot Deck", str(len(_get_all_cards())))
            stats.add_row("I Ching Text", "64 hexagrams")
            stats.add_row("Launch", "choose a system below")
            self.console.print(
                Align.center(
                    Panel(
                        stats,
                        title="Systems",
                        border_style=AMBER,
                        box=box.ASCII,
                        padding=(0, 2),
                        expand=False,
                    )
                )
            )
            self.console.print("")
        label_width = max(len(item[1].replace("&", "")) for item in SYSTEM_MENU_ITEMS)
        for index, (_hotkey, label, _action) in enumerate(SYSTEM_MENU_ITEMS):
            styled, plain = _menu_label(label, index == selected)
            padding = " " * (label_width - len(plain))
            if index == selected:
                markup = f"[bold {AMBER}]>===<[/]  {styled}{padding}"
                raw = f">===<  {plain}{padding}"
            else:
                markup = f"[{AMBER_DIM}].....[/]  {styled}{padding}"
                raw = f".....  {plain}{padding}"
            self.console.print(_centered(self.console, markup, raw))
        self.console.print("")
        self.console.print(_centered(self.console, f"[dim]{SYSTEM_MENU_HINT}[/dim]", SYSTEM_MENU_HINT))

    def _launch(self, action: str | None) -> int:
        if action == "tarot":
            AuguryApp().run()
            return 0
        if action == "iching":
            from .systems.iching.app import IChingApp

            IChingApp().run()
            return 0
        return 0

    def run(self) -> int:
        if not sys.stdin.isatty():
            return self.run_fallback_menu()
        selected = 0
        while True:
            self.draw_main_menu(selected)
            key = _read_key()
            if key in ("UP", "k"):
                selected = (selected - 1) % len(SYSTEM_MENU_ITEMS)
                continue
            if key in ("DOWN", "j"):
                selected = (selected + 1) % len(SYSTEM_MENU_ITEMS)
                continue
            if key in ("\r", "\n", " "):
                action = SYSTEM_MENU_ITEMS[selected][2]
                if action is None:
                    return 0
                self._launch(action)
                continue
            if key in ("CTRL_C", "CTRL_D"):
                return 0
            for index, (hotkey, _label, action) in enumerate(SYSTEM_MENU_ITEMS):
                if key.lower() != hotkey:
                    continue
                selected = index
                if action is None:
                    return 0
                self._launch(action)
                break

    def run_fallback_menu(self) -> int:
        mapping = {item[0]: item[2] for item in SYSTEM_MENU_ITEMS}
        while True:
            self.draw_main_menu(0)
            self.console.print("")
            choice = self.console.input("choice [t/i/q] ").strip().lower()
            action = mapping.get(choice)
            if action is None:
                return 0
            self._launch(action)


def _emit_json(payload: Any) -> int:
    json.dump(payload, sys.stdout, indent=2, ensure_ascii=True)
    sys.stdout.write("\n")
    return 0


def _human_card(console: Console, card: Any) -> int:
    _show_card_detail(console, card)
    return 0


def _human_history(console: Console, limit: int) -> int:
    readings = list(reversed(_load_readings()))[:limit]
    if not readings:
        console.print("No readings saved.")
        return 0
    if HAS_RICH:
        table = Table(show_header=True, header_style=f"bold {AMBER}", box=box.ASCII)
        table.add_column("When", style=STONE)
        table.add_column("Spread", style=AMBER_SOFT)
        table.add_column("Cards", style=STONE)
        table.add_column("Query", style=STONE)
        for reading in readings:
            table.add_row(_timestamp_text(reading), reading.spread_name, _summary_cards(reading), str(reading.query or "-"))
        console.print(table)
    else:
        for reading in readings:
            console.print(f"{_timestamp_text(reading)}  {reading.spread_name}  {_summary_cards(reading)}")
    return 0


def _apply_interpret_stub(payload: dict[str, Any], interpret: bool) -> dict[str, Any]:
    if interpret:
        payload["interpret_mode"] = _interpret_stub_note()
    return payload


def _bool_prompt(console: Console, label: str, default: bool) -> bool:
    default_hint = "Y/n" if default else "y/N"
    try:
        response = console.input(f"{label} [{default_hint}] ")
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


def _paths_payload() -> dict[str, str]:
    return {
        "config_dir": str(APP_PATHS.config_dir),
        "data_dir": str(APP_PATHS.data_dir),
        "prefs_path": str(PREFS_PATH),
        "spreads_path": str(SPREADS_PATH),
        "readings_path": str(READINGS_PATH),
        "iching_readings_path": str(APP_PATHS.iching_readings_path),
        "integrations_path": str(INTEGRATIONS_PATH),
        "launcher_dir": str(default_launcher_dir()),
    }


def _configuration_payload() -> dict[str, Any]:
    return {
        "paths": _paths_payload(),
        "preferences": load_preferences(),
        "integrations": load_integrations(),
    }


def _print_paths(console: Console) -> None:
    payload = _paths_payload()
    for key, value in payload.items():
        console.print(f"{key}: {value}")


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
    integrations = load_integrations()

    if args.print_paths:
        _print_paths(console)
        if args.no_input and not args.install_discord_helper:
            return 0

    if args.no_input:
        if args.install_launchers:
            launchers = install_cli_launchers(args.launcher_dir)
            integrations.setdefault("discord", {})
            integrations["discord"]["enabled"] = True
            integrations["discord"]["helper_path"] = str(launchers["augury-discord"])
            save_integrations(integrations)
        if args.install_discord_helper:
            helper_path = install_discord_helper(args.discord_helper_path)
            integrations.setdefault("discord", {})
            integrations["discord"]["enabled"] = True
            integrations["discord"]["helper_path"] = str(helper_path)
            save_integrations(integrations)
        if args.json:
            return _emit_json(_configuration_payload())
        return 0

    console.print("Augury setup")
    console.print("")
    _print_paths(console)
    console.print("")

    app = AuguryApp()
    if _bool_prompt(console, "Change the default spread?", True):
        spread = app.choose_spread(str(prefs.get("default_spread", "three-card")))
        if spread:
            prefs["default_spread"] = spread["slug"]

    prefs["allow_reversals"] = _bool_prompt(
        console,
        "Allow reversed cards?",
        bool(prefs.get("allow_reversals", True)),
    )
    prefs["show_tips"] = _bool_prompt(
        console,
        "Show educational tips in the TUI?",
        bool(prefs.get("show_tips", True)),
    )
    history_value = app.prompt("history limit", str(prefs.get("history_limit", 50)))
    try:
        prefs["history_limit"] = max(1, int(history_value))
    except Exception:
        pass
    _save_prefs(prefs)

    launcher_dir = args.launcher_dir or str(default_launcher_dir())
    should_install_launchers = _bool_prompt(
        console,
        f"Install or refresh PATH launchers in {launcher_dir}?",
        bool(integrations.get("discord", {}).get("enabled", False)),
    )
    if should_install_launchers:
        target_dir = app.prompt("launcher directory", str(launcher_dir))
        launchers = install_cli_launchers(target_dir or None)
        integrations.setdefault("discord", {})
        integrations["discord"]["enabled"] = True
        integrations["discord"]["helper_path"] = str(launchers["augury-discord"])
        save_integrations(integrations)
        console.print(f"Installed augury at {launchers['augury']}")
        console.print(f"Installed augury-discord at {launchers['augury-discord']}")
        console.print(f"Installed iching at {launchers['iching']}")
    else:
        integrations.setdefault("discord", {})
        integrations["discord"].setdefault("enabled", False)
        integrations["discord"].setdefault("helper_path", None)
        save_integrations(integrations)

    if args.json:
        return _emit_json(_configuration_payload())
    console.print("")
    console.print("Configuration saved.")
    return 0


def _run_read_command(args: argparse.Namespace) -> int:
    prefs = _load_prefs()
    custom_spreads = _load_custom_spreads()
    spread = _resolve_spread(args.spread or str(prefs.get("default_spread", "three-card")), custom_spreads)
    reading = _draw_reading(spread, args.query, prefs)
    if not args.no_save:
        _save_reading(reading)
    payload = _apply_interpret_stub(_reading_to_json(reading), args.interpret)
    payload["saved"] = not args.no_save
    payload["saved_to"] = None if args.no_save else str(READINGS_PATH)
    if args.json:
        return _emit_json(payload)
    console = Console(highlight=False, force_terminal=True) if HAS_RICH else Console()
    if args.interpret:
        console.print(f"[bold {AMBER}]LLM mode stub:[/] using template interpretation only." if HAS_RICH else "LLM mode stub: using template interpretation only.")
    _show_reading(console, reading, "reading")
    return 0


def _run_daily_command(args: argparse.Namespace) -> int:
    prefs = _load_prefs()
    custom_spreads = _load_custom_spreads()
    spread = _resolve_spread("single", custom_spreads)
    reading = _draw_reading(spread, f"Daily guidance for {datetime.now().date().isoformat()}", prefs)
    if not args.no_save:
        _save_reading(reading)
    payload = _apply_interpret_stub(_reading_to_json(reading), args.interpret)
    payload["saved"] = not args.no_save
    payload["saved_to"] = None if args.no_save else str(READINGS_PATH)
    if args.json:
        return _emit_json(payload)
    console = Console(highlight=False, force_terminal=True) if HAS_RICH else Console()
    if args.interpret:
        console.print(f"[bold {AMBER}]LLM mode stub:[/] using template interpretation only." if HAS_RICH else "LLM mode stub: using template interpretation only.")
    _show_reading(console, reading, "daily card")
    return 0


def _run_card_command(args: argparse.Namespace) -> int:
    name = " ".join(args.name)
    card = _lookup_card(name)
    payload = _card_payload(card)
    if args.json:
        return _emit_json(payload)
    console = Console(highlight=False, force_terminal=True) if HAS_RICH else Console()
    return _human_card(console, card)


def _run_history_command(args: argparse.Namespace) -> int:
    limit = max(1, int(args.limit))
    readings = list(reversed(_load_readings()))[:limit]
    if args.json:
        payload = [_reading_to_json(reading) for reading in readings]
        return _emit_json(payload)
    console = Console(highlight=False, force_terminal=True) if HAS_RICH else Console()
    return _human_history(console, limit)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="augury",
        description="Augury divination suite with tarot and I Ching interfaces.",
    )
    subparsers = parser.add_subparsers(dest="command")

    read_parser = subparsers.add_parser("read", help="Draw a reading")
    read_parser.add_argument("--spread", default=None, help="Spread name or slug")
    read_parser.add_argument("--query", default=None, help="Question or reading prompt")
    read_parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    read_parser.add_argument("--interpret", action="store_true", help="LLM narrative mode stub")
    read_parser.add_argument("--no-save", action="store_true", help="Do not persist the reading to history")

    daily_parser = subparsers.add_parser("daily", help="Draw the daily card")
    daily_parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    daily_parser.add_argument("--interpret", action="store_true", help="LLM narrative mode stub")
    daily_parser.add_argument("--no-save", action="store_true", help="Do not persist the reading to history")

    card_parser = subparsers.add_parser("card", help="Show a card")
    card_parser.add_argument("name", nargs="+", help="Card name")
    card_parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")

    history_parser = subparsers.add_parser("history", help="Show reading history")
    history_parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    history_parser.add_argument("--limit", type=int, default=25, help="Number of readings to show")

    configure_parser = subparsers.add_parser("configure", help="Run setup and optional integration install")
    configure_parser.add_argument("--json", action="store_true", help="Emit machine-readable configuration")
    configure_parser.add_argument("--print-paths", action="store_true", help="Print active config and data paths")
    configure_parser.add_argument("--install-launchers", action="store_true", help="Install augury, augury-discord, and iching into a stable bin directory")
    configure_parser.add_argument("--launcher-dir", default=None, help="Override the launcher install directory")
    configure_parser.add_argument("--install-discord-helper", action="store_true", help="Install the Discord helper launcher")
    configure_parser.add_argument("--discord-helper-path", default=None, help="Override the helper launcher path")
    configure_parser.add_argument("--no-input", action="store_true", help="Do not prompt interactively")

    paths_parser = subparsers.add_parser("paths", help="Show Augury config and data paths")
    paths_parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")

    tarot_parser = subparsers.add_parser("tarot", help="Launch the tarot app or run tarot commands")
    tarot_subparsers = tarot_parser.add_subparsers(dest="tarot_command")

    tarot_read_parser = tarot_subparsers.add_parser("read", help="Draw a tarot reading")
    tarot_read_parser.add_argument("--spread", default=None, help="Spread name or slug")
    tarot_read_parser.add_argument("--query", default=None, help="Question or reading prompt")
    tarot_read_parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    tarot_read_parser.add_argument("--interpret", action="store_true", help="LLM narrative mode stub")
    tarot_read_parser.add_argument("--no-save", action="store_true", help="Do not persist the reading to history")

    tarot_daily_parser = tarot_subparsers.add_parser("daily", help="Draw the daily card")
    tarot_daily_parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    tarot_daily_parser.add_argument("--interpret", action="store_true", help="LLM narrative mode stub")
    tarot_daily_parser.add_argument("--no-save", action="store_true", help="Do not persist the reading to history")

    tarot_card_parser = tarot_subparsers.add_parser("card", help="Show a tarot card")
    tarot_card_parser.add_argument("name", nargs="+", help="Card name")
    tarot_card_parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")

    tarot_history_parser = tarot_subparsers.add_parser("history", help="Show tarot reading history")
    tarot_history_parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    tarot_history_parser.add_argument("--limit", type=int, default=25, help="Number of readings to show")

    iching_cli.add_augury_subparser(subparsers)
    return parser


def main(argv: list[str] | None = None) -> int:
    _ensure_data_dir()
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "read":
        return _run_read_command(args)
    if args.command == "daily":
        return _run_daily_command(args)
    if args.command == "card":
        return _run_card_command(args)
    if args.command == "history":
        return _run_history_command(args)
    if args.command == "configure":
        return _run_configure_command(args)
    if args.command == "paths":
        return _run_paths_command(args)
    if args.command == "tarot":
        if args.tarot_command == "read":
            return _run_read_command(args)
        if args.tarot_command == "daily":
            return _run_daily_command(args)
        if args.tarot_command == "card":
            return _run_card_command(args)
        if args.tarot_command == "history":
            return _run_history_command(args)
        return AuguryApp().run()
    if args.command == "iching":
        return iching_cli.run_augury_args(args)
    return SystemChooserApp().run()


if __name__ == "__main__":
    raise SystemExit(main())
