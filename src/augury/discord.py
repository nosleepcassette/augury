"""Discord-ready tarot command formatting and fallback reading logic."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from random import SystemRandom
from typing import Any

_RNG = SystemRandom()
_COMMAND_PREFIXES = ("/tarot", "/augury")
_CANONICAL_SPREADS = {
    "single": "single",
    "three-card": "three-card",
    "celtic-cross": "celtic-cross",
}
_SPREAD_ALIASES = {
    "single": "single",
    "one": "single",
    "draw": "single",
    "daily": "single",
    "three": "three-card",
    "three-card": "three-card",
    "threecard": "three-card",
    "3": "three-card",
    "celtic": "celtic-cross",
    "cross": "celtic-cross",
    "celtic-cross": "celtic-cross",
    "celticcross": "celtic-cross",
}
_SPREAD_LABELS = {
    "single": "Single Card",
    "three-card": "Three Card",
    "celtic-cross": "Celtic Cross",
}
_SPREAD_POSITIONS = {
    "single": ["Card"],
    "three-card": ["Past", "Present", "Future"],
    "celtic-cross": [
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
}
_SUIT_SYMBOLS = {
    "Wands": "!!",
    "Cups": "()",
    "Swords": "<>",
    "Pentacles": "[]",
}
_SUIT_PROFILES = {
    "Wands": {
        "element": "Fire",
        "astrology": "Aries, Leo, Sagittarius",
        "domain": "will, motion, and creative force",
        "upright_keywords": ["drive", "spark", "will", "motion"],
        "reversed_keywords": ["stall", "burnout", "scatter", "delay"],
    },
    "Cups": {
        "element": "Water",
        "astrology": "Cancer, Scorpio, Pisces",
        "domain": "emotion, intuition, and relationship",
        "upright_keywords": ["feeling", "intuition", "bond", "receptivity"],
        "reversed_keywords": ["distance", "flood", "avoidance", "moodiness"],
    },
    "Swords": {
        "element": "Air",
        "astrology": "Gemini, Libra, Aquarius",
        "domain": "thought, truth, and conflict",
        "upright_keywords": ["clarity", "mind", "truth", "decision"],
        "reversed_keywords": ["confusion", "conflict", "avoidance", "overthinking"],
    },
    "Pentacles": {
        "element": "Earth",
        "astrology": "Taurus, Virgo, Capricorn",
        "domain": "work, craft, money, and the body",
        "upright_keywords": ["grounding", "craft", "resource", "stability"],
        "reversed_keywords": ["drag", "scarcity", "delay", "imbalance"],
    },
}
_RANK_PROFILES = {
    "Ace": {
        "number": 1,
        "upright_keywords": ["seed", "opening", "potential", "start"],
        "reversed_keywords": ["block", "hesitation", "waste", "delay"],
        "upright_phrase": "a first opening",
        "reversed_phrase": "an opening that is blocked or mishandled",
        "numerology": "beginnings, initiative, and concentrated potential",
    },
    "Two": {
        "number": 2,
        "upright_keywords": ["balance", "duality", "choice", "reflection"],
        "reversed_keywords": ["stalemate", "drift", "imbalance", "avoidance"],
        "upright_phrase": "an active balancing point",
        "reversed_phrase": "a split that is hard to reconcile",
        "numerology": "duality, exchange, and balancing forces",
    },
    "Three": {
        "number": 3,
        "upright_keywords": ["growth", "expression", "expansion", "support"],
        "reversed_keywords": ["scattered growth", "delay", "friction", "misalignment"],
        "upright_phrase": "the first visible expansion",
        "reversed_phrase": "growth that is uneven or poorly supported",
        "numerology": "growth, expression, and early momentum",
    },
    "Four": {
        "number": 4,
        "upright_keywords": ["structure", "stability", "containment", "rest"],
        "reversed_keywords": ["rigidity", "stagnation", "cracks", "restlessness"],
        "upright_phrase": "a stable structure",
        "reversed_phrase": "a structure that has become rigid or unstable",
        "numerology": "structure, stability, and holding form",
    },
    "Five": {
        "number": 5,
        "upright_keywords": ["friction", "change", "trial", "pressure"],
        "reversed_keywords": ["dragging conflict", "avoidance", "disorder", "fatigue"],
        "upright_phrase": "a test through pressure and change",
        "reversed_phrase": "disruption that keeps looping",
        "numerology": "friction, challenge, and disruptive growth",
    },
    "Six": {
        "number": 6,
        "upright_keywords": ["repair", "reciprocity", "flow", "support"],
        "reversed_keywords": ["imbalance", "one-sidedness", "delay", "regret"],
        "upright_phrase": "a chance to restore balance",
        "reversed_phrase": "repair that is incomplete or uneven",
        "numerology": "repair, reciprocity, and restored movement",
    },
    "Seven": {
        "number": 7,
        "upright_keywords": ["assessment", "resolve", "testing", "strategy"],
        "reversed_keywords": ["doubt", "drift", "mixed signals", "strain"],
        "upright_phrase": "a testing ground for conviction",
        "reversed_phrase": "a test that exposes uncertainty",
        "numerology": "assessment, testing, and inward resolve",
    },
    "Eight": {
        "number": 8,
        "upright_keywords": ["mastery", "momentum", "discipline", "power"],
        "reversed_keywords": ["stuck loops", "constraint", "misfire", "strain"],
        "upright_phrase": "disciplined momentum",
        "reversed_phrase": "energy caught in a hard knot",
        "numerology": "power, motion, and repeated effort",
    },
    "Nine": {
        "number": 9,
        "upright_keywords": ["culmination", "resilience", "maturity", "depth"],
        "reversed_keywords": ["weariness", "overextension", "withdrawal", "delay"],
        "upright_phrase": "the near-completion of a cycle",
        "reversed_phrase": "a cycle nearing completion but under strain",
        "numerology": "ripeness, resilience, and nearing completion",
    },
    "Ten": {
        "number": 10,
        "upright_keywords": ["completion", "weight", "closure", "transition"],
        "reversed_keywords": ["overload", "unfinished business", "drag", "collapse"],
        "upright_phrase": "the full weight of a cycle ending",
        "reversed_phrase": "an ending that resists clean closure",
        "numerology": "completion, excess, and transition",
    },
    "Page": {
        "number": 11,
        "upright_keywords": ["message", "curiosity", "student", "opening"],
        "reversed_keywords": ["immaturity", "misread signal", "delay", "distraction"],
        "upright_phrase": "a message or first embodiment of the suit",
        "reversed_phrase": "a message that is delayed, fuzzy, or immature",
        "numerology": "thresholds, messages, and apprenticeship",
    },
    "Knight": {
        "number": 12,
        "upright_keywords": ["pursuit", "motion", "mission", "charge"],
        "reversed_keywords": ["rashness", "detour", "stall", "imbalance"],
        "upright_phrase": "pursuit in motion",
        "reversed_phrase": "motion that is too forceful or badly aimed",
        "numerology": "pursuit, direction, and active engagement",
    },
    "Queen": {
        "number": 13,
        "upright_keywords": ["mastery", "maturity", "receptivity", "depth"],
        "reversed_keywords": ["distance", "overcontrol", "drain", "imbalance"],
        "upright_phrase": "mature inner command",
        "reversed_phrase": "inner command that has become withholding or strained",
        "numerology": "maturity, embodiment, and inner command",
    },
    "King": {
        "number": 14,
        "upright_keywords": ["authority", "stewardship", "direction", "command"],
        "reversed_keywords": ["control issues", "rigidity", "drift", "misuse"],
        "upright_phrase": "outer command and stewardship",
        "reversed_phrase": "authority that has become rigid, thin, or misapplied",
        "numerology": "command, responsibility, and outer mastery",
    },
}
_MAJOR_DATA = [
    (0, "The Fool", "Air", "Uranus", ["beginnings", "faith", "freedom", "leap"], ["recklessness", "naivete", "drift", "delay"], "A new path opens when you trust the next step.", "The leap is real, but fear or impulsiveness is distorting it."),
    (1, "The Magician", "Air", "Mercury", ["skill", "focus", "will", "manifestation"], ["manipulation", "scatter", "misuse", "static"], "Tools are in reach; focused action can shape the moment.", "Power is present, but it is scattered or being used badly."),
    (2, "The High Priestess", "Water", "Moon", ["intuition", "silence", "mystery", "inner knowing"], ["secrecy", "avoidance", "blocked intuition", "distance"], "Something important is known below the surface before it can be spoken.", "The quiet signal is being ignored, hidden, or distorted."),
    (3, "The Empress", "Earth", "Venus", ["nurture", "growth", "abundance", "body"], ["smothering", "creative block", "drain", "stagnation"], "Growth comes through care, patience, and embodied attention.", "Nurture has gone off balance, or growth is not getting what it needs."),
    (4, "The Emperor", "Fire", "Aries", ["order", "authority", "structure", "boundary"], ["rigidity", "control", "hardness", "instability"], "Structure and leadership matter here; the frame has to hold.", "Control is replacing leadership, or the frame is too brittle."),
    (5, "The Hierophant", "Earth", "Taurus", ["tradition", "teaching", "belief", "initiation"], ["dogma", "rebellion", "stuck ritual", "disconnect"], "The lesson may come through a tradition, teacher, or tested pattern.", "Belief has become rigid, hollow, or disconnected from lived truth."),
    (6, "The Lovers", "Air", "Gemini", ["union", "choice", "alignment", "bond"], ["misalignment", "indecision", "distance", "split"], "A relationship or choice asks for honest alignment with values.", "The bond or choice is strained by mixed motives or poor alignment."),
    (7, "The Chariot", "Water", "Cancer", ["drive", "direction", "discipline", "victory"], ["loss of control", "stall", "scatter", "conflict"], "Momentum builds when opposing forces are harnessed with discipline.", "There is motion, but it is pulling in more than one direction."),
    (8, "Strength", "Fire", "Leo", ["courage", "patience", "heart", "self-command"], ["doubt", "force", "drain", "hesitation"], "Steady courage and gentle self-command win more than brute force.", "Energy is leaking through fear, force, or loss of heart."),
    (9, "The Hermit", "Earth", "Virgo", ["solitude", "wisdom", "search", "inner light"], ["isolation", "withdrawal", "avoidance", "distance"], "The answer clarifies through quiet, study, and honest inward attention.", "Retreat is turning into isolation, or the search has gone cold."),
    (10, "Wheel of Fortune", "Fire", "Jupiter", ["cycle", "change", "fate", "turning"], ["resistance", "bad timing", "stuck cycle", "delay"], "The wheel is turning; timing and larger patterns matter now.", "A cycle is turning anyway, but resistance or poor timing complicates it."),
    (11, "Justice", "Air", "Libra", ["truth", "balance", "accountability", "clarity"], ["bias", "avoidance", "imbalance", "denial"], "Clear seeing and fair consequence bring the situation into balance.", "Truth is being dodged, or balance is skewed by bias or fear."),
    (12, "The Hanged Man", "Water", "Neptune", ["pause", "surrender", "perspective", "waiting"], ["martyrdom", "stall", "resistance", "stuckness"], "Progress comes through surrender, pause, and a changed angle of view.", "The pause is no longer useful because surrender has become stagnation."),
    (13, "Death", "Water", "Scorpio", ["ending", "release", "transformation", "threshold"], ["clinging", "delay", "fear of change", "drag"], "A real ending clears space for a different life to begin.", "Change is still required, but clinging is dragging out the transition."),
    (14, "Temperance", "Fire", "Sagittarius", ["integration", "healing", "balance", "blending"], ["excess", "imbalance", "impatience", "strain"], "Healing happens through measured blending and patient adjustment.", "The mix is off; something needs recalibration, not force."),
    (15, "The Devil", "Earth", "Capricorn", ["attachment", "desire", "shadow", "bondage"], ["release", "denial", "shame", "escalation"], "The reading names a tie that binds through appetite, fear, or shame.", "The bind is weakening, or it is being hidden instead of faced."),
    (16, "The Tower", "Fire", "Mars", ["rupture", "revelation", "shock", "collapse"], ["aftershock", "avoidance", "slow collapse", "fear"], "Something unstable is breaking so the truth can become undeniable.", "The break is underway, but fear or delay is stretching out the impact."),
    (17, "The Star", "Air", "Aquarius", ["hope", "guidance", "renewal", "faith"], ["disillusion", "drain", "distance", "faint signal"], "Hope returns through clarity, trust, and a cleaner signal from ahead.", "The signal is still there, but discouragement is dimming it."),
    (18, "The Moon", "Water", "Pisces", ["dream", "uncertainty", "instinct", "mystery"], ["confusion", "fear", "projection", "fog"], "Not everything can be known yet; instinct and careful observation matter.", "The fog is thickening through projection, fear, or misread signs."),
    (19, "The Sun", "Fire", "Sun", ["clarity", "joy", "vitality", "success"], ["ego", "delay", "dimness", "fatigue"], "Warmth, clarity, and visible life force are available here.", "The light is present, but it is muted by fatigue, ego, or delay."),
    (20, "Judgement", "Fire", "Pluto", ["awakening", "reckoning", "call", "review"], ["avoidance", "self-doubt", "delay", "stuck review"], "A wake-up call asks for honest review and a cleaner next life.", "The call is there, but self-doubt or avoidance is delaying the answer."),
    (21, "The World", "Earth", "Saturn", ["completion", "integration", "wholeness", "arrival"], ["unfinished cycle", "delay", "fragmentation", "restlessness"], "A cycle can resolve into a wider sense of completion and integration.", "Closure is close, but one final piece still needs honest attention."),
]

try:
    from . import art as _AUGURY_ART
except Exception:
    _AUGURY_ART = None

try:
    from . import cards as _AUGURY_CARDS
except Exception:
    _AUGURY_CARDS = None

try:
    from . import engine as _AUGURY_ENGINE
except Exception:
    _AUGURY_ENGINE = None


@dataclass(frozen=True)
class FallbackCard:
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


@dataclass(frozen=True)
class FallbackDrawnCard:
    card: FallbackCard
    position_name: str
    reversed: bool


@dataclass
class FallbackReading:
    spread_name: str
    query: str | None
    drawn_cards: list[FallbackDrawnCard]
    timestamp: datetime
    interpretation: str


def _normalize_name(value: str) -> str:
    normalized = " ".join(str(value or "").replace("-", " ").replace("_", " ").split()).casefold()
    normalized = normalized.replace("judgment", "judgement")
    return normalized


def _strip_command_prefix(text: str) -> str:
    raw = str(text or "").strip()
    lowered = raw.casefold()
    for prefix in _COMMAND_PREFIXES:
        if lowered == prefix:
            return ""
        if lowered.startswith(prefix + " "):
            return raw[len(prefix) :].strip()
    return raw


def _strip_matching_quotes(text: str) -> str:
    value = str(text or "").strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1].strip()
    return value


def _first_present(value: Any, *names: str, default: Any = None) -> Any:
    if isinstance(value, dict):
        lowered = {str(key).casefold(): key for key in value}
        for name in names:
            variants = {
                name,
                name.lower(),
                name.replace("-", "_"),
                name.replace("_", "-"),
                name.replace(" ", "_"),
                name.replace(" ", "-"),
            }
            for variant in variants:
                if variant in value and value[variant] is not None:
                    return value[variant]
                key = lowered.get(variant.casefold())
                if key is not None and value[key] is not None:
                    return value[key]
        return default

    for name in names:
        variants = {
            name,
            name.lower(),
            name.replace("-", "_"),
            name.replace("_", "-"),
            name.replace(" ", "_"),
            name.replace(" ", "-"),
        }
        for variant in variants:
            if hasattr(value, variant):
                result = getattr(value, variant)
                if result is not None:
                    return result
    return default


def _listify(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        parts = re.split(r"[,\n;]+", value)
        return [part.strip() for part in parts if part.strip()]
    if isinstance(value, (list, tuple, set)):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()]


def _ensure_sentence(text: Any) -> str:
    value = str(text or "").strip()
    if not value:
        return ""
    if value[-1] in ".!?":
        return value
    return value + "."


def _make_major_card(
    number: int,
    name: str,
    element: str,
    astrology: str,
    upright_keywords: list[str],
    reversed_keywords: list[str],
    upright_meaning: str,
    reversed_meaning: str,
) -> FallbackCard:
    return FallbackCard(
        name=name,
        number=number,
        suit=None,
        arcana="major",
        upright_keywords=upright_keywords,
        reversed_keywords=reversed_keywords,
        upright_meaning=upright_meaning,
        reversed_meaning=reversed_meaning,
        element=element,
        astrology=astrology,
        numerology=f"{number} / major arcana cycle marker",
        related_cards=[],
        educational_tip=f"{name} is a Major Arcana card, so it usually reads as a headline rather than background texture.",
    )


def _make_minor_card(rank: str, suit: str) -> FallbackCard:
    rank_profile = _RANK_PROFILES[rank]
    suit_profile = _SUIT_PROFILES[suit]
    number = int(rank_profile["number"])
    upright_keywords = list(rank_profile["upright_keywords"]) + list(suit_profile["upright_keywords"][:2])
    reversed_keywords = list(rank_profile["reversed_keywords"]) + list(suit_profile["reversed_keywords"][:2])
    upright_meaning = (
        f"{rank} of {suit} points to {rank_profile['upright_phrase']} in matters of {suit_profile['domain']}."
    )
    reversed_meaning = (
        f"{rank} of {suit} reversed points to {rank_profile['reversed_phrase']} in matters of {suit_profile['domain']}."
    )
    return FallbackCard(
        name=f"{rank} of {suit}",
        number=number,
        suit=suit,
        arcana="minor",
        upright_keywords=upright_keywords,
        reversed_keywords=reversed_keywords,
        upright_meaning=upright_meaning,
        reversed_meaning=reversed_meaning,
        element=str(suit_profile["element"]),
        astrology=str(suit_profile["astrology"]),
        numerology=f"{number} / {rank_profile['numerology']}",
        related_cards=[],
        educational_tip=(
            f"{rank} shows how the number lesson lands in the suit. In {suit}, that means {suit_profile['domain']}."
        ),
    )


def _build_fallback_deck() -> list[FallbackCard]:
    deck = [
        _make_major_card(
            number=number,
            name=name,
            element=element,
            astrology=astrology,
            upright_keywords=upright_keywords,
            reversed_keywords=reversed_keywords,
            upright_meaning=upright_meaning,
            reversed_meaning=reversed_meaning,
        )
        for (
            number,
            name,
            element,
            astrology,
            upright_keywords,
            reversed_keywords,
            upright_meaning,
            reversed_meaning,
        ) in _MAJOR_DATA
    ]
    for suit in ("Wands", "Cups", "Swords", "Pentacles"):
        for rank in (
            "Ace",
            "Two",
            "Three",
            "Four",
            "Five",
            "Six",
            "Seven",
            "Eight",
            "Nine",
            "Ten",
            "Page",
            "Knight",
            "Queen",
            "King",
        ):
            deck.append(_make_minor_card(rank, suit))
    return deck


_FALLBACK_DECK = _build_fallback_deck()
_FALLBACK_CARD_BY_NAME: dict[str, FallbackCard] = {}
for _card in _FALLBACK_DECK:
    _FALLBACK_CARD_BY_NAME[_normalize_name(_card.name)] = _card
    if _card.name.startswith("The "):
        _FALLBACK_CARD_BY_NAME[_normalize_name(_card.name[4:])] = _card


def _card_name(card: Any) -> str:
    return str(_first_present(card, "name", "title", "card_name", default="Unknown Card"))


def _card_arcana(card: Any) -> str:
    arcana = str(_first_present(card, "arcana", "type", "card_type", default="")).strip().lower()
    if "major" in arcana:
        return "major"
    if "minor" in arcana:
        return "minor"
    return "major" if _card_name(card).casefold().startswith("the ") else "minor"


def _card_suit(card: Any) -> str | None:
    suit = _first_present(card, "suit", default=None)
    if suit is None or suit == "":
        return None
    return str(suit)


def _card_number(card: Any) -> int | None:
    number = _first_present(card, "number", "rank_number", default=None)
    if isinstance(number, int):
        return number
    try:
        return int(number)
    except Exception:
        return None


def _card_keywords(card: Any, reversed_card: bool = False) -> list[str]:
    if reversed_card:
        keywords = _first_present(card, "reversed_keywords", default=None)
        if keywords:
            return _listify(keywords)
    keywords = _first_present(card, "upright_keywords", "keywords", default=None)
    return _listify(keywords)


def _card_meaning(card: Any, reversed_card: bool = False) -> str:
    if reversed_card:
        meaning = _first_present(card, "reversed_meaning", "reversed", default=None)
        if meaning:
            return _ensure_sentence(meaning)
    return _ensure_sentence(
        _first_present(card, "upright_meaning", "meaning", "description", default="This card points to a live theme in the spread.")
    )


def _card_payload(card: Any) -> dict[str, Any]:
    return {
        "name": _card_name(card),
        "arcana": _card_arcana(card),
        "suit": _card_suit(card),
        "number": _card_number(card),
        "element": _first_present(card, "element", default=""),
        "astrology": _first_present(card, "astrology", default=""),
        "numerology": _first_present(card, "numerology", default=""),
        "upright_keywords": _card_keywords(card, False),
        "reversed_keywords": _card_keywords(card, True),
        "upright_meaning": _card_meaning(card, False),
        "reversed_meaning": _card_meaning(card, True),
        "educational_tip": _ensure_sentence(_first_present(card, "educational_tip", "tip", default="")),
        "related_cards": _listify(_first_present(card, "related_cards", "related", default=[])),
        "art": _first_present(card, "art", default=""),
    }


def _resolve_spread_name(spread_name: str) -> str:
    normalized = _normalize_name(spread_name).replace(" ", "-")
    canonical = _SPREAD_ALIASES.get(normalized)
    if canonical:
        return canonical
    raise ValueError("Usage: /tarot | /tarot three | /tarot celtic | /tarot card <name>")


def _fallback_get_card_by_name(card_name: str) -> FallbackCard:
    normalized = _normalize_name(card_name)
    try:
        return _FALLBACK_CARD_BY_NAME[normalized]
    except KeyError as exc:
        raise KeyError(f"Unknown tarot card: {card_name}") from exc


def _lookup_card(card_name: str) -> Any:
    cleaned = _strip_matching_quotes(card_name)
    if not cleaned:
        raise KeyError("Unknown tarot card: ")

    if _AUGURY_CARDS is not None and hasattr(_AUGURY_CARDS, "get_card_by_name"):
        try:
            return _AUGURY_CARDS.get_card_by_name(cleaned)
        except Exception:
            pass
    return _fallback_get_card_by_name(cleaned)


def _card_lookup_or_none(card_name: str) -> Any | None:
    try:
        return _lookup_card(card_name)
    except Exception:
        return None


def _fallback_interpretation(reading: FallbackReading) -> str:
    parts: list[str] = []
    if reading.query:
        parts.append(
            f'Question: "{reading.query}". The {reading.spread_name} spread frames it through {len(reading.drawn_cards)} position'
            + ("s." if len(reading.drawn_cards) != 1 else ".")
        )
    else:
        parts.append(
            f"The {reading.spread_name} spread names the active pattern through {len(reading.drawn_cards)} position"
            + ("s." if len(reading.drawn_cards) != 1 else ".")
        )

    for drawn in reading.drawn_cards:
        meaning = _card_meaning(drawn.card, drawn.reversed)
        orientation = "reversed" if drawn.reversed else "upright"
        parts.append(
            f"In *{drawn.position_name}*, **{drawn.card.name}** arrives {orientation}. {meaning}"
        )

    return "\n\n".join(parts)


def _fallback_draw_reading(spread_name: str, query: str | None = None) -> FallbackReading:
    canonical = _resolve_spread_name(spread_name)
    positions = _SPREAD_POSITIONS[canonical]
    deck = list(_FALLBACK_DECK)
    _RNG.shuffle(deck)
    drawn_cards = [
        FallbackDrawnCard(
            card=deck[index],
            position_name=position_name,
            reversed=(_RNG.random() < 0.30),
        )
        for index, position_name in enumerate(positions)
    ]
    reading = FallbackReading(
        spread_name=_SPREAD_LABELS[canonical],
        query=query or None,
        drawn_cards=drawn_cards,
        timestamp=datetime.now(timezone.utc),
        interpretation="",
    )
    reading.interpretation = _fallback_interpretation(reading)
    return reading


def _draw_reading(spread_name: str, query: str | None = None) -> Any:
    canonical = _resolve_spread_name(spread_name)
    if _AUGURY_ENGINE is not None and hasattr(_AUGURY_ENGINE, "draw_reading"):
        try:
            return _AUGURY_ENGINE.draw_reading(canonical, query=query)
        except Exception:
            pass
    return _fallback_draw_reading(canonical, query=query)


def _reading_payload(reading: Any) -> dict[str, Any]:
    if isinstance(reading, dict):
        payload = dict(reading)
    elif _AUGURY_ENGINE is not None and hasattr(_AUGURY_ENGINE, "reading_to_json"):
        try:
            payload = dict(_AUGURY_ENGINE.reading_to_json(reading))
        except Exception:
            payload = {}
    else:
        payload = {}

    if payload.get("drawn_cards"):
        return payload

    raw_drawn_cards = _first_present(reading, "drawn_cards", "cards", default=[]) or []
    drawn_cards = []
    for drawn in raw_drawn_cards:
        card = _first_present(drawn, "card", default=drawn)
        reversed_card = bool(_first_present(drawn, "reversed", default=False))
        card_data = _card_payload(card)
        drawn_cards.append(
            {
                "name": card_data["name"],
                "position_name": str(_first_present(drawn, "position_name", "position", default="Card")),
                "reversed": reversed_card,
                "keywords": card_data["reversed_keywords"] if reversed_card else card_data["upright_keywords"],
                "meaning": card_data["reversed_meaning"] if reversed_card else card_data["upright_meaning"],
                "card": card_data,
            }
        )

    return {
        "spread_name": str(_first_present(reading, "spread_name", default="Tarot Reading")),
        "query": _first_present(reading, "query", default=None),
        "timestamp": _first_present(reading, "timestamp", default=None),
        "drawn_cards": drawn_cards,
        "interpretation": _ensure_sentence(_first_present(reading, "interpretation", default="")),
        "educational_tips": _listify(_first_present(reading, "educational_tips", "tips", default=[])),
    }


def _fallback_art(card_data: dict[str, Any]) -> str:
    name = str(card_data.get("name") or "Unknown Card")
    suit = card_data.get("suit")
    number = card_data.get("number")
    symbol = _SUIT_SYMBOLS.get(str(suit), "*")
    title = name.upper()[:17]
    if suit:
        suit_line = str(suit).upper()[:17]
        mark_line = (" ".join([symbol] * max(1, min(int(number or 1), 4))))[:17]
    else:
        suit_line = "MAJOR ARCANA"
        mark_line = "* * * * *"
    lines = [
        "+-----------------+",
        f"|{title:^17}|",
        "|                 |",
        f"|{suit_line:^17}|",
        "|                 |",
        f"|{mark_line:^17}|",
        "|                 |",
        f"|{str(card_data.get('element') or '')[:17]:^17}|",
        "+-----------------+",
    ]
    return "\n".join(lines)


def _render_card_art(card_data: dict[str, Any]) -> str:
    existing = str(card_data.get("art") or "").strip()
    if existing:
        return existing
    if _AUGURY_ART is not None:
        try:
            if card_data.get("arcana") == "major":
                return str(_AUGURY_ART.get_card_art(card_data["name"]))
            suit = card_data.get("suit")
            number = card_data.get("number")
            if suit and isinstance(number, int):
                return str(_AUGURY_ART.get_suit_art(suit, number))
        except Exception:
            pass
    return _fallback_art(card_data)


def _discord_code_block(text: str) -> str:
    return "```\n" + str(text).rstrip() + "\n```"


def _orientation_label(reversed_card: bool) -> str:
    return "reversed" if reversed_card else "upright"


def format_reading_for_discord(reading: Any) -> str:
    """Format a reading object as Discord markdown."""

    payload = _reading_payload(reading)
    spread_name = str(payload.get("spread_name") or "Tarot Reading")
    query = str(payload.get("query") or "").strip()
    interpretation = str(payload.get("interpretation") or "").strip()
    tips = _listify(payload.get("educational_tips"))

    sections = [f"**{spread_name}**"]
    if query:
        sections.append(f"Question: {query}")

    for drawn in payload.get("drawn_cards", []):
        card_data = drawn.get("card") if isinstance(drawn, dict) else None
        if not isinstance(card_data, dict):
            card_data = _card_payload(_first_present(drawn, "card", default=drawn))
        position_name = str(_first_present(drawn, "position_name", "position", default="Card"))
        reversed_card = bool(_first_present(drawn, "reversed", default=False))
        keywords = _listify(_first_present(drawn, "keywords", default=card_data.get("upright_keywords", [])))
        header = f"*{position_name}* - **{card_data['name']}** ({_orientation_label(reversed_card)})"
        card_block = [header, _discord_code_block(_render_card_art(card_data))]
        if keywords:
            card_block.append("Keywords: " + ", ".join(keywords[:4]))
        sections.append("\n".join(card_block))

    if interpretation:
        sections.append("**Interpretation**\n" + interpretation)
    if tips:
        sections.append("**Tips**\n" + "\n".join(f"- {tip}" for tip in tips[:3]))

    return "\n\n".join(section for section in sections if section.strip())


def format_card_info_for_discord(card_name: str) -> str:
    """Format a single tarot card lookup for Discord."""

    try:
        card = _lookup_card(card_name)
    except Exception:
        return f'Unknown tarot card: "{card_name}". Try `/tarot card The Fool`.'

    card_data = _card_payload(card)
    lines = [f"**{card_data['name']}**"]

    meta_parts = []
    if card_data["arcana"] == "major":
        meta_parts.append("Major Arcana")
    else:
        meta_parts.append("Minor Arcana")
    if card_data.get("suit"):
        meta_parts.append(str(card_data["suit"]))
    if card_data.get("element"):
        meta_parts.append(str(card_data["element"]))
    if card_data.get("astrology"):
        meta_parts.append(str(card_data["astrology"]))
    if meta_parts:
        lines.append(" | ".join(meta_parts))

    lines.append(_discord_code_block(_render_card_art(card_data)))

    upright_keywords = _listify(card_data.get("upright_keywords"))
    reversed_keywords = _listify(card_data.get("reversed_keywords"))
    if upright_keywords:
        lines.append("Upright keywords: " + ", ".join(upright_keywords[:6]))
    lines.append("Upright: " + _ensure_sentence(card_data.get("upright_meaning")))
    if reversed_keywords:
        lines.append("Reversed keywords: " + ", ".join(reversed_keywords[:6]))
    lines.append("Reversed: " + _ensure_sentence(card_data.get("reversed_meaning")))

    tip = _ensure_sentence(card_data.get("educational_tip"))
    if tip:
        lines.append("Tip: " + tip)

    related = _listify(card_data.get("related_cards"))
    if related:
        lines.append("Related: " + ", ".join(related[:4]))

    return "\n\n".join(line for line in lines if line.strip())


def _extract_spread_and_query(text: str) -> tuple[str, str]:
    stripped = text.strip()
    lowered = stripped.casefold()
    if lowered.startswith("celtic cross"):
        return "celtic-cross", stripped[len("celtic cross") :].strip()
    token, _, rest = stripped.partition(" ")
    canonical = _SPREAD_ALIASES.get(token.replace("_", "-").replace(" ", "-"), "")
    if canonical:
        return canonical, rest.strip()
    return "", stripped


def handle_tarot_command(args: str) -> str:
    """Parse /tarot or /augury style input and return Discord-ready text."""

    body = _strip_command_prefix(args)
    stripped = body.strip()

    if not stripped:
        return format_reading_for_discord(_draw_reading("single"))

    lowered = stripped.casefold()
    if lowered == "card":
        return "Usage: /tarot card <name>"
    if lowered.startswith("card "):
        return format_card_info_for_discord(_strip_matching_quotes(stripped[5:].strip()))

    spread_name, remainder = _extract_spread_and_query(stripped)
    if spread_name:
        query = remainder or None
        return format_reading_for_discord(_draw_reading(spread_name, query=query))

    direct_card = _card_lookup_or_none(stripped)
    if direct_card is not None:
        return format_card_info_for_discord(_card_name(direct_card))

    return format_reading_for_discord(_draw_reading("single", query=stripped))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="augury-discord",
        description="Discord-ready formatter and command parser for Augury.",
    )
    subparsers = parser.add_subparsers(dest="command")

    handle_parser = subparsers.add_parser("handle", help="Parse a /tarot or /augury command string")
    handle_parser.add_argument("text", nargs="*", help="Command text to parse")

    card_parser = subparsers.add_parser("card", help="Format a card lookup for Discord")
    card_parser.add_argument("name", nargs="+", help="Card name")

    read_parser = subparsers.add_parser("read", help="Format a tarot reading for Discord")
    read_parser.add_argument("--spread", default="single", help="Spread name or alias")
    read_parser.add_argument("--query", default=None, help="Optional reading prompt")
    return parser


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] not in {"handle", "card", "read", "-h", "--help"}:
        print(handle_tarot_command(" ".join(argv).strip()))
        return 0

    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "card":
        print(format_card_info_for_discord(" ".join(args.name)))
        return 0
    if args.command == "read":
        print(format_reading_for_discord(_draw_reading(args.spread, query=args.query)))
        return 0
    if args.command == "handle":
        text = " ".join(args.text).strip()
        if not text and not sys.stdin.isatty():
            text = sys.stdin.read().strip()
        print(handle_tarot_command(text))
        return 0
    if not sys.stdin.isatty():
        print(handle_tarot_command(sys.stdin.read().strip()))
        return 0

    parser.print_help()
    return 0


__all__ = [
    "handle_tarot_command",
    "format_card_info_for_discord",
    "format_reading_for_discord",
    "main",
]


if __name__ == "__main__":
    raise SystemExit(main())
