"""Template-based tarot reading engine for Augury."""

from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from random import SystemRandom
from typing import Any

from . import art as art_module
from .config import get_app_paths

_RNG = SystemRandom()
_READINGS_PATH = get_app_paths().readings_path

_SUIT_ALIASES = {
    "cups": "cups",
    "chalices": "cups",
    "swords": "swords",
    "blades": "swords",
    "wands": "wands",
    "staves": "wands",
    "rods": "wands",
    "batons": "wands",
    "pentacles": "pentacles",
    "coins": "pentacles",
    "disks": "pentacles",
    "discs": "pentacles",
}

_SUIT_ELEMENTS = {
    "wands": "fire",
    "cups": "water",
    "swords": "air",
    "pentacles": "earth",
}

_SUIT_TIPS = {
    "wands": "Wands speak to desire, will, heat, and creative action.",
    "cups": "Cups speak to feeling, intuition, relationship, and receptivity.",
    "swords": "Swords speak to thought, conflict, truth, and discernment.",
    "pentacles": "Pentacles speak to the body, work, craft, money, and material life.",
}

_ELEMENT_TIPS = {
    "fire": "Fire energy pushes toward action, courage, appetite, and expression.",
    "water": "Water energy points to emotion, intuition, memory, and inner tides.",
    "air": "Air energy points to thought, language, analysis, and changing perspective.",
    "earth": "Earth energy points to the practical, embodied, and materially real.",
}

_ELEMENT_MEANINGS = {
    "fire": "The spread is charged with action, urgency, and creative will.",
    "water": "The spread is driven by emotion, intuition, and inner processing.",
    "air": "The spread is shaped by thought, conflict, language, and clarity.",
    "earth": "The spread is grounded in practical realities, resources, and embodiment.",
}

_SUIT_MEANINGS = {
    "wands": "A strong Wands presence makes this reading active, future-facing, and driven by desire.",
    "cups": "A strong Cups presence makes this reading emotional, relational, and intuitive.",
    "swords": "A strong Swords presence makes this reading mental, tense, and concerned with truth or conflict.",
    "pentacles": "A strong Pentacles presence makes this reading practical, grounded, and tied to material conditions.",
}

_NUMBER_MEANINGS = {
    0: "a leap into the unknown",
    1: "beginnings, initiative, and identity",
    2: "duality, balance, and relationship",
    3: "growth, collaboration, and expression",
    4: "structure, stability, and boundaries",
    5: "disruption, friction, and adaptation",
    6: "harmony, reciprocity, and repair",
    7: "reflection, testing, and inward focus",
    8: "power, momentum, and mastery",
    9: "culmination, ripeness, and nearing completion",
    10: "closure, overflow, and transition",
    11: "thresholds, messages, and apprenticeship",
    12: "suspension, waiting, and changed perspective",
    13: "transformation, shedding, and deep change",
    14: "integration, maturity, and command of experience",
    19: "visibility, warmth, and life force",
    20: "reckoning, awakening, and review",
    21: "completion, wholeness, and synthesis",
}

_TRIGRAM_MEANINGS: dict[str, str] = {
    "Heaven": "the Creative — pure yang, strength, the father principle",
    "Earth": "the Receptive — pure yin, yielding, the mother principle",
    "Thunder": "the Arousing — shock and movement, the eldest son",
    "Water": "the Abysmal — danger and depth, the middle son",
    "Mountain": "Keeping Still — rest and restraint, the youngest son",
    "Wind": "the Gentle — penetrating and persistent, the eldest daughter",
    "Fire": "the Clinging — clarity and illumination, the middle daughter",
    "Lake": "the Joyous — openness and expression, the youngest daughter",
}

_ELEMENT_PAIRS: dict[tuple[str, str], str] = {
    ("fire", "water"): "Fire and Water in the same spread create a tension between action and emotion — the drive to move forward meets the pull to feel first.",
    ("water", "fire"): "Fire and Water in the same spread create a tension between action and emotion — the drive to move forward meets the pull to feel first.",
    ("air", "earth"): "Air and Earth together suggest that the thinking and the practical are both in play — ideas seeking ground, or material reality demanding a clearer mental framing.",
    ("earth", "air"): "Air and Earth together suggest that the thinking and the practical are both in play — ideas seeking ground, or material reality demanding a clearer mental framing.",
    ("fire", "earth"): "Fire and Earth together are generative — desire and will meeting practical capacity, the energy to build something real.",
    ("earth", "fire"): "Fire and Earth together are generative — desire and will meeting practical capacity, the energy to build something real.",
    ("water", "air"): "Water and Air together speak to the interior life — emotion and thought in conversation, feeling trying to find its language.",
    ("air", "water"): "Water and Air together speak to the interior life — emotion and thought in conversation, feeling trying to find its language.",
}

_MAJOR_ARCANA_NAMES = {
    "the fool",
    "the magician",
    "the high priestess",
    "the empress",
    "the emperor",
    "the hierophant",
    "the lovers",
    "the chariot",
    "strength",
    "the hermit",
    "wheel of fortune",
    "justice",
    "the hanged man",
    "death",
    "temperance",
    "the devil",
    "the tower",
    "the star",
    "the moon",
    "the sun",
    "judgement",
    "judgment",
    "the world",
}

_BUILTIN_SPREADS = {
    "single": {
        "name": "Single Card",
        "positions": ["Card"],
    },
    "three-card": {
        "name": "Three Card",
        "positions": ["Past", "Present", "Future"],
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
    },
    "relationship": {
        "name": "Relationship",
        "positions": ["You", "Them", "The Connection", "Challenge", "Potential"],
    },
    "career": {
        "name": "Career",
        "positions": ["Current Path", "Obstacle", "Hidden Factor", "Action", "Outcome"],
    },
    "yes-no": {
        "name": "Yes/No",
        "positions": ["Answer"],
    },
    "elemental": {
        "name": "Elemental",
        "positions": ["Fire (Drive)", "Water (Emotion)", "Air (Mind)", "Earth (Material)"],
    },
    "horseshoe": {
        "name": "Horseshoe",
        "positions": ["Past", "Present", "Hidden Influences", "Obstacles", "External Forces", "Advice", "Outcome"],
    },
    "shadow-work": {
        "name": "Shadow Work",
        "positions": ["The Pattern", "The Root", "What Is Hidden", "The Gift Within It", "The Path Forward"],
    },
    "star": {
        "name": "Star",
        "positions": ["Present Situation", "What Crosses You", "What Crowns You", "Foundation", "Recent Past", "Near Future", "Your Role", "External Influences", "Hopes & Fears", "Where This Leads"],
    },
    "soul-path": {
        "name": "Soul Path",
        "positions": ["Where You Came From", "What You Carry", "Your Core Gift", "Your Challenge", "Your Next Step"],
    },
    "new-moon-intention": {
        "name": "New Moon Intention",
        "positions": ["What I Am Releasing", "What I Am Calling In", "What Supports This", "The Action Step", "The Blessing"],
    },
    "relationship-deep": {
        "name": "Relationship Deep",
        "positions": ["Your Energy", "Their Energy", "The Bond", "What Strengthens", "What Challenges", "Hidden Dynamic", "Guidance"],
    },
}

_POSITION_CONTEXTS = {
    "card": "This names the core energy at the center of the reading.",
    "past": "This points to influences that have already shaped the situation.",
    "present": "This describes the energy active around you now.",
    "future": "This suggests where the pattern is heading if it continues.",
    "challenge": "This shows the tension, obstacle, or lesson pressing hardest.",
    "above": "This reflects conscious hopes, ideals, or what you are aiming toward.",
    "below": "This reflects the root system under the situation: instinct, history, or the unconscious.",
    "advice": "This shows the clearest attitude or move to work with.",
    "external": "This points to outside conditions, other people, or the surrounding field.",
    "hopes-fears": "This reveals what is desired and feared at the same time.",
    "outcome": "This shows the likely result if nothing fundamental changes.",
    "you": "This reflects your current stance, tone, or role in the dynamic.",
    "them": "This reflects the other person's energy or position in the dynamic.",
    "the-connection": "This describes the bond, pattern, or chemistry between the parties.",
    "potential": "This shows what the situation could become with conscious effort.",
    "current-path": "This shows the course you are presently walking.",
    "obstacle": "This reveals the resistance, delay, or practical snag in the way.",
    "hidden-factor": "This points to something important that is easy to miss.",
    "action": "This shows the move most likely to shift the pattern.",
    "answer": "This gives the most direct response the spread can offer.",
    "fire-drive": "This position focuses on motivation, will, and what wants expression.",
    "water-emotion": "This position focuses on the emotional undertow and what the heart is carrying.",
    "air-mind": "This position focuses on thought, perspective, and mental framing.",
    "earth-material": "This position focuses on the concrete, practical, and embodied side of the matter.",
    "hidden-influences": "This reveals forces at work beneath the surface that are shaping the situation.",
    "external-forces": "This shows the conditions, people, or energies coming from outside.",
    "the-pattern": "This identifies the recurring dynamic or behavior that is calling for attention.",
    "the-root": "This points to the origin or deep cause underneath the pattern.",
    "what-is-hidden": "This surfaces what has been out of awareness or actively avoided.",
    "the-gift-within-it": "This reveals what strength, insight, or resource lives inside the difficulty.",
    "the-path-forward": "This shows the direction of integration and what becomes possible on the other side.",
    "what-crosses-you": "This names the tension, friction, or opposing force working against the situation.",
    "what-crowns-you": "This reflects the highest potential or clearest possible outcome in view.",
    "foundation": "This points to the deeper ground the situation is rooted in.",
    "recent-past": "This shows what has just concluded or is still in the process of completing.",
    "near-future": "This indicates what is approaching and beginning to take form.",
    "your-role": "This names the part you are playing — consciously or not — in how this unfolds.",
    "where-this-leads": "This suggests the longer arc and where the energy wants to land.",
    "where-you-came-from": "This points to the formative experience, lineage, or history that shaped the soul's starting point.",
    "what-you-carry": "This names the gifts, wounds, or patterns brought into this life from the past.",
    "your-core-gift": "This identifies the essential quality or capacity that is yours to express.",
    "your-challenge": "This names the difficulty that is also the growing edge — the place where the gift is tested.",
    "your-next-step": "This shows the most aligned movement forward at this moment in the path.",
    "what-i-am-releasing": "This names what is ready to be let go — what no longer serves the new cycle.",
    "what-i-am-calling-in": "This holds the seed of what wants to grow and be invited into being.",
    "what-supports-this": "This reveals the resource, energy, or ally that backs the intention.",
    "the-action-step": "This shows the concrete or symbolic move that anchors the intention in the world.",
    "the-blessing": "This names the grace, opening, or gift that accompanies the new beginning.",
    "their-energy": "This reflects the other person's current state, stance, or energy in relation to the dynamic.",
    "the-bond": "This describes the nature, quality, and pattern of the connection itself.",
    "what-strengthens": "This shows what feeds and sustains the best in this relationship.",
    "what-challenges": "This names the friction, gap, or growth edge between the two people.",
    "hidden-dynamic": "This surfaces what is operating beneath the surface in the connection.",
    "guidance": "This offers the clearest direction for how to move within this relationship.",
}


@dataclass
class DrawnCard:
    card: Any
    position_name: str
    reversed: bool


@dataclass
class Reading:
    spread_name: str
    query: str | None
    drawn_cards: list[DrawnCard]
    timestamp: datetime
    interpretation: str


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(text).strip().lower()).strip("-")


def _ensure_sentence(text: str) -> str:
    text = str(text).strip()
    if not text:
        return ""
    if text[-1] not in ".!?":
        return text + "."
    return text


def _first_present(value: Any, *names: str, default: Any = None) -> Any:
    if isinstance(value, dict):
        lowered = {str(key).lower(): key for key in value.keys()}
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
                lowered_key = lowered.get(candidate.lower())
                if lowered_key is not None and value[lowered_key] is not None:
                    return value[lowered_key]
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


def _listify(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        if "\n" in value:
            parts = value.splitlines()
        elif ";" in value:
            parts = value.split(";")
        elif "," in value:
            parts = value.split(",")
        else:
            parts = [value]
        return [part.strip() for part in parts if part.strip()]
    return [str(value).strip()]


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
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if hasattr(value, "__dict__"):
        return _json_safe(
            {
                key: item
                for key, item in vars(value).items()
                if not key.startswith("_")
            }
        )
    return repr(value)


def _card_name(card: Any) -> str:
    return str(_first_present(card, "name", "title", "card_name", default="Unknown Card"))


def _card_arcana(card: Any) -> str:
    arcana = _first_present(card, "arcana", "type", "card_type", default="")
    if arcana:
        text = str(arcana).strip().lower()
        if "major" in text:
            return "major"
        if "minor" in text:
            return "minor"
    return "major" if _card_name(card).strip().lower() in _MAJOR_ARCANA_NAMES else "minor"


def _card_suit(card: Any) -> str | None:
    suit = _first_present(card, "suit", "suite", default=None)
    if not suit:
        return None
    return _SUIT_ALIASES.get(str(suit).strip().lower())


def _card_number(card: Any) -> int | None:
    value = _first_present(card, "number", "rank_number", "index", "num", default=None)
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        digits = re.search(r"-?\d+", value)
        if digits:
            return int(digits.group(0))
    rank = _first_present(card, "rank", "value", "face", default=None)
    if isinstance(rank, int):
        return rank
    if rank is None:
        name = _card_name(card).lower()
        rank = name.split(" of ", 1)[0]
    if isinstance(rank, str):
        mapping = {
            "ace": 1,
            "two": 2,
            "three": 3,
            "four": 4,
            "five": 5,
            "six": 6,
            "seven": 7,
            "eight": 8,
            "nine": 9,
            "ten": 10,
            "page": 11,
            "knight": 12,
            "queen": 13,
            "king": 14,
        }
        lowered = rank.strip().lower()
        if lowered in mapping:
            return mapping[lowered]
    numerology = _first_present(card, "numerology", default=None)
    if isinstance(numerology, int):
        return numerology
    if isinstance(numerology, str):
        digits = re.search(r"-?\d+", numerology)
        if digits:
            return int(digits.group(0))
    return None


def _card_element(card: Any) -> str | None:
    raw = _first_present(card, "element", "elements", default=None)
    for value in _listify(raw):
        lowered = value.lower()
        if lowered in _ELEMENT_MEANINGS:
            return lowered
    suit = _card_suit(card)
    if suit:
        return _SUIT_ELEMENTS.get(suit)
    return None


def _card_keywords(card: Any, reversed_card: bool) -> list[str]:
    if reversed_card:
        keywords = _first_present(
            card,
            "reversed_keywords",
            "keywords_reversed",
            "rev_keywords",
            default=None,
        )
        if keywords:
            return _listify(keywords)
    if not reversed_card:
        keywords = _first_present(
            card,
            "upright_keywords",
            "keywords_upright",
            default=None,
        )
        if keywords:
            return _listify(keywords)
    return _listify(_first_present(card, "keywords", default=None))


def _card_meaning(card: Any, reversed_card: bool) -> str:
    if reversed_card:
        reversed_meaning = _first_present(
            card,
            "reversed_meaning",
            "meaning_reversed",
            "reversed",
            default=None,
        )
        if reversed_meaning:
            return _ensure_sentence(reversed_meaning)

    upright_meaning = _first_present(
        card,
        "upright_meaning",
        "meaning_upright",
        "meaning",
        "description",
        default="",
    )
    upright_text = _ensure_sentence(upright_meaning)
    if reversed_card:
        if upright_text:
            return (
                upright_text
                + " Reversed, this energy can turn inward, arrive unevenly, or show up as blockage or delay."
            )
        return "Reversed, this energy tends to show up as blockage, delay, inversion, or internal pressure."
    return upright_text or "This card points to a meaningful theme even if the database entry is sparse."


def _card_tips(card: Any) -> list[str]:
    return _listify(_first_present(card, "educational_tips", "tips", default=None))


def _card_related(card: Any) -> list[str]:
    return [item.lower() for item in _listify(_first_present(card, "related_cards", "related", default=None))]


def _card_astrology_sentence(card: Any) -> str:
    astro = _first_present(card, "astrology", default=None)
    if not astro:
        return ""
    return f"Astrologically, this card carries the signature of {astro}, bringing that planetary and sign energy directly into this position."


def _card_numerology_sentence(card: Any) -> str:
    raw = _first_present(card, "numerology", default=None)
    if not raw:
        return ""
    text = str(raw).strip()
    if " / " in text:
        num_part, desc = text.split(" / ", 1)
        num_part = num_part.strip()
        desc = desc.strip()
        return f"The number {num_part} here is the numerological signature of this card — the energy of {desc}."
    return f"Numerologically: {text}."


def _card_educational_tip(card: Any) -> str:
    tip = _first_present(card, "educational_tip", default=None)
    if not tip:
        return ""
    return _ensure_sentence(str(tip).strip())


def _related_in_reading_sentence(card: Any, names_in_reading: set[str]) -> str:
    related = [n for n in _card_related(card) if n in names_in_reading]
    if not related:
        return ""
    related_str = ", ".join(sorted(n.title() for n in related))
    count = len(related)
    verb = "appears" if count == 1 else "appear"
    return (
        f"{related_str} {verb} elsewhere in this reading — a traditional pairing with "
        f"{_card_name(card)} that deepens and reinforces what this position is saying."
    )


def _serialize_card(card: Any) -> dict[str, Any]:
    base = _json_safe(card)
    if not isinstance(base, dict):
        base = {"name": _card_name(card), "value": base}

    serialized = dict(base)
    serialized.setdefault("name", _card_name(card))
    serialized.setdefault("arcana", _card_arcana(card))
    serialized.setdefault("suit", _card_suit(card))
    serialized.setdefault("number", _card_number(card))
    serialized.setdefault("element", _card_element(card))
    serialized.setdefault("upright_keywords", _card_keywords(card, False))
    serialized.setdefault("reversed_keywords", _card_keywords(card, True))
    serialized.setdefault("upright_meaning", _card_meaning(card, False))
    serialized.setdefault("reversed_meaning", _card_meaning(card, True))
    serialized.setdefault("art", _card_art(card))
    return serialized


def _card_art(card: Any) -> str:
    existing = _first_present(card, "art", default=None)
    if isinstance(existing, str) and existing.strip():
        return existing

    name = _card_name(card)
    suit = _card_suit(card)
    number = _card_number(card)
    try:
        if _card_arcana(card) == "major":
            return art_module.get_card_art(name)
        if suit and number:
            return art_module.get_suit_art(suit, number)
    except Exception:
        pass
    return str(art_module.CARD_BACK)


def _load_augury_cards_module() -> Any:
    try:
        from . import cards
    except Exception as exc:  # pragma: no cover - fatal only on broken installs
        raise RuntimeError("Could not import augury.cards.") from exc
    return cards


def _coerce_card_collection(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, dict):
        if "cards" in value and isinstance(value["cards"], (list, tuple)):
            return list(value["cards"])
        return list(value.values())
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return []


def _get_deck() -> list[Any]:
    module = _load_augury_cards_module()

    for attribute in ("CARDS", "DECK", "ALL_CARDS", "CARD_DATABASE", "RIDER_WAITE_CARDS"):
        cards = _coerce_card_collection(getattr(module, attribute, None))
        if cards:
            return cards

    for factory_name in ("get_deck", "get_cards", "load_cards"):
        factory = getattr(module, factory_name, None)
        if callable(factory):
            cards = _coerce_card_collection(factory())
            if cards:
                return cards

    raise RuntimeError("augury.cards did not expose a recognizable deck export.")


def _coerce_spread_record(record: Any) -> tuple[str, list[str]] | None:
    if isinstance(record, dict):
        name = record.get("name") or record.get("slug")
        positions = record.get("positions")
    else:
        name = _first_present(record, "name", "slug", default=None)
        positions = _first_present(record, "positions", default=None)

    if not name or not positions:
        return None
    return str(name), [str(position) for position in positions]


def _resolve_spread(spread_name: str) -> tuple[str, list[str]]:
    normalized = _normalize(spread_name)

    for slug, spread in _BUILTIN_SPREADS.items():
        aliases = {
            slug,
            _normalize(slug),
            _normalize(spread["name"]),
        }
        if normalized in aliases:
            return spread["name"], list(spread["positions"])

    module = _load_augury_cards_module()
    for attribute in ("BUILTIN_SPREADS", "SPREADS", "ALL_SPREADS"):
        spread_list = getattr(module, attribute, None)
        if spread_list is None:
            continue
        if isinstance(spread_list, dict):
            spread_iter = spread_list.values()
        else:
            spread_iter = spread_list
        for record in spread_iter:
            coerced = _coerce_spread_record(record)
            if not coerced:
                continue
            name, positions = coerced
            if normalized in {_normalize(name), _normalize(str(_first_present(record, "slug", default=name)))}:
                return name, positions

    valid_spreads = sorted(spread["name"] for spread in _BUILTIN_SPREADS.values())
    raise ValueError(f"Unknown spread '{spread_name}'. Valid built-ins: {', '.join(valid_spreads)}")


def _position_context(position_name: str) -> str:
    key = _normalize(position_name)
    return _POSITION_CONTEXTS.get(key, f"This position frames how {position_name.lower()} shapes the reading.")


def _major_minor_ratio(cards: list[DrawnCard]) -> dict[str, int]:
    major = sum(1 for drawn in cards if _card_arcana(drawn.card) == "major")
    return {"major": major, "minor": len(cards) - major}


def _number_pattern_data(cards: list[DrawnCard]) -> dict[str, Any]:
    numbers = [number for number in (_card_number(drawn.card) for drawn in cards) if number is not None]
    counts = Counter(numbers)
    repeats = {str(number): count for number, count in counts.items() if count > 1}

    sequence = False
    if len(numbers) >= 3:
        ordered = sorted(set(numbers))
        run = 1
        for index in range(1, len(ordered)):
            if ordered[index] == ordered[index - 1] + 1:
                run += 1
                if run >= 3:
                    sequence = True
                    break
            else:
                run = 1

    return {
        "numbers": numbers,
        "repeats": repeats,
        "sequence": sequence,
    }


def analyze_patterns(reading: Reading) -> dict[str, Any]:
    suit_counts = Counter()
    element_counts = Counter()

    for drawn in reading.drawn_cards:
        suit = _card_suit(drawn.card)
        if suit:
            suit_counts[suit] += 1

        element = _card_element(drawn.card)
        if element:
            element_counts[element] += 1

    elemental_balance = {element: element_counts.get(element, 0) for element in ("fire", "water", "air", "earth")}
    for element, count in element_counts.items():
        if element not in elemental_balance:
            elemental_balance[element] = count

    ratio = _major_minor_ratio(reading.drawn_cards)
    number_patterns = _number_pattern_data(reading.drawn_cards)

    return {
        "suit_distribution": dict(sorted(suit_counts.items())),
        "major_minor_ratio": ratio,
        "number_patterns": number_patterns,
        "elemental_balance": elemental_balance,
        "reversal_count": sum(1 for drawn in reading.drawn_cards if drawn.reversed),
        "dominant_suit": max(suit_counts, key=suit_counts.get) if suit_counts else None,
        "dominant_element": max(element_counts, key=element_counts.get) if element_counts else None,
    }


def _pattern_sentences(reading: Reading) -> list[str]:
    analysis = analyze_patterns(reading)
    sentences: list[str] = []

    dominant_suit = analysis.get("dominant_suit")
    if dominant_suit:
        sentences.append(_SUIT_MEANINGS[dominant_suit])

    ratio = analysis["major_minor_ratio"]
    if ratio["major"] and ratio["major"] >= ratio["minor"]:
        sentences.append("The number of Major Arcana cards suggests this is touching a larger life lesson, not just a passing mood.")
    elif ratio["major"]:
        sentences.append("The Major Arcana presence shows that at least part of this situation carries deeper significance.")

    repeats = analysis["number_patterns"]["repeats"]
    if repeats:
        repeated = sorted(repeats.items(), key=lambda item: (-item[1], int(item[0])))
        number, count = repeated[0]
        number_value = int(number)
        meaning = _NUMBER_MEANINGS.get(number_value, "a repeating structural theme in the reading")
        sentences.append(
            f"The repeated number {number} appears {count} times, emphasizing {meaning}."
        )

    if analysis["number_patterns"]["sequence"]:
        sentences.append("There is a numerical sequence in the draw, which often points to movement, process, or a step-by-step unfolding.")

    dominant_element = analysis.get("dominant_element")
    if dominant_element and dominant_element in _ELEMENT_MEANINGS:
        sentences.append(_ELEMENT_MEANINGS[dominant_element])

    reversal_count = analysis["reversal_count"]
    if reversal_count:
        if reversal_count == len(reading.drawn_cards):
            sentences.append("Every card arrived reversed, so the reading leans toward inward pressure, delay, or hidden process.")
        elif reversal_count >= max(2, len(reading.drawn_cards) // 2):
            sentences.append("Several cards arrived reversed, suggesting the issue may be working itself out internally before it shows clearly on the surface.")

    return sentences


def _interpret_drawn_card(drawn: DrawnCard, names_in_reading: set[str] | None = None) -> str:
    card = drawn.card
    name = _card_name(card)
    orientation = "reversed" if drawn.reversed else "upright"
    parts: list[str] = []

    # Position + card + orientation header
    parts.append(
        f"In the {drawn.position_name} position, {name} appears {orientation}. "
        f"{_position_context(drawn.position_name)}"
    )

    # Primary meaning
    meaning = _card_meaning(card, drawn.reversed)
    if meaning:
        parts.append(meaning)

    # Keywords
    keywords = _card_keywords(card, drawn.reversed)
    if keywords:
        parts.append(f"The active keywords here are {', '.join(keywords[:5])}.")

    # Astrology ruler
    astro_s = _card_astrology_sentence(card)
    if astro_s:
        parts.append(astro_s)

    # Numerology
    num_s = _card_numerology_sentence(card)
    if num_s:
        parts.append(num_s)

    # Major Arcana elevation
    if _card_arcana(card) == "major":
        parts.append(
            "As a Major Arcana card, this is not background texture — it marks a significant theme, "
            "a turning point, or an archetypal force active in your life right now."
        )

    # Educational tip (if distinctive)
    tip = _card_educational_tip(card)
    if tip:
        parts.append(tip)

    # Related cards in reading
    if names_in_reading:
        related_s = _related_in_reading_sentence(card, names_in_reading)
        if related_s:
            parts.append(related_s)

    return " ".join(parts).strip()


def _elemental_tension_sentences(reading: Reading) -> list[str]:
    """Note elemental pairings between adjacent cards in the spread."""
    sentences: list[str] = []
    seen: set[tuple[str, str]] = set()
    cards = reading.drawn_cards
    for i in range(len(cards) - 1):
        el1 = _card_element(cards[i].card)
        el2 = _card_element(cards[i + 1].card)
        if el1 and el2 and el1 != el2:
            pair = tuple(sorted([el1, el2]))
            if pair not in seen:
                seen.add(pair)  # type: ignore[arg-type]
                msg = _ELEMENT_PAIRS.get((el1, el2)) or _ELEMENT_PAIRS.get((el2, el1))
                if msg:
                    sentences.append(msg)
    return sentences


def _closing_synthesis(reading: Reading) -> str:
    """Generate a closing integrative paragraph from the spread patterns."""
    analysis = analyze_patterns(reading)
    parts: list[str] = []

    n = len(reading.drawn_cards)
    reversal_count = analysis["reversal_count"]
    ratio = analysis["major_minor_ratio"]
    dominant_element = analysis.get("dominant_element")
    dominant_suit = analysis.get("dominant_suit")

    # Reversal framing
    if reversal_count == n:
        parts.append(
            "Every card in this reading arrived reversed. The work described here is largely internal — "
            "pressure building beneath the surface, energy that has not yet found its outward form."
        )
    elif reversal_count >= max(2, n // 2):
        parts.append(
            f"{reversal_count} of {n} cards arrived reversed, suggesting this situation is processing "
            "inwardly before it becomes fully visible or actionable."
        )
    elif reversal_count == 0 and n >= 3:
        parts.append(
            "All cards arrived upright — the energies described here are expressed and accessible, "
            "not hidden or blocked."
        )

    # Major arcana weight
    if ratio["major"] >= 3:
        parts.append(
            f"With {ratio['major']} Major Arcana cards present, this reading is touching something larger "
            "than immediate circumstances — a life theme, a defining moment, or an archetypal pattern "
            "that wants your full attention."
        )
    elif ratio["major"] == 0 and n >= 4:
        parts.append(
            "The absence of Major Arcana means this reading is squarely in the practical, everyday register — "
            "the situation is workable and the resolution lies in concrete action and choice."
        )

    # Dominant element close
    if dominant_element:
        element_closes = {
            "fire": "Trust what you want. The energy here is real and the forward movement is available.",
            "water": "Let yourself feel what you actually feel. The insight this reading points to lives in the emotional body, not in thinking it through.",
            "air": "Clarity is possible, but it requires cutting through rather than circling. The answer you seek is a decision.",
            "earth": "This is about what you actually do, not what you intend. The practical path is the spiritual path here.",
        }
        close = element_closes.get(dominant_element)
        if close:
            parts.append(close)

    return " ".join(parts).strip()


def interpret_reading(reading: Reading) -> str:
    sections: list[str] = []
    names_in_reading = {_card_name(drawn.card).lower() for drawn in reading.drawn_cards}

    # Opening
    if reading.query:
        sections.append(
            f'You asked: "{reading.query}". '
            f"The {reading.spread_name} spread — {len(reading.drawn_cards)} position"
            + ("s" if len(reading.drawn_cards) != 1 else "")
            + " — holds that question."
        )
    else:
        sections.append(
            f"The {reading.spread_name} spread opens across {len(reading.drawn_cards)} position"
            + ("s." if len(reading.drawn_cards) != 1 else ".")
        )

    # Card-by-card
    for drawn in reading.drawn_cards:
        sections.append(_interpret_drawn_card(drawn, names_in_reading))

    # Pattern analysis
    pattern_sentences = _pattern_sentences(reading)
    tension_sentences = _elemental_tension_sentences(reading)
    all_pattern = pattern_sentences + tension_sentences
    if all_pattern:
        sections.append("Looking at the spread as a whole: " + " ".join(all_pattern))

    # Yes/No direct answer
    if reading.spread_name.lower() in ("yes/no", "yes-no") and reading.drawn_cards:
        answer_card = reading.drawn_cards[0]
        leaning = "not yet — the energy is present but meeting resistance" if answer_card.reversed else "yes, and with real momentum behind it"
        sections.append(f"As a direct answer to your question, this reading leans {leaning}.")

    # Closing synthesis
    close = _closing_synthesis(reading)
    if close:
        sections.append(close)

    return "\n\n".join(section.strip() for section in sections if section.strip())


# Trigram-to-tarot-element mapping for cross-system synthesis
_TRIGRAM_ELEMENTS: dict[str, str] = {
    "Heaven": "air",
    "Wind": "air",
    "Fire": "fire",
    "Thunder": "fire",
    "Water": "water",
    "Lake": "water",
    "Earth": "earth",
    "Mountain": "earth",
}


def synthesize_combined(reading: "Reading", consultation: Any) -> str:
    """Generate a 2-3 sentence cross-system synthesis from a combined tarot + I Ching reading."""
    analysis = analyze_patterns(reading)
    dominant_element = analysis.get("dominant_element")
    primary = consultation.primary_hexagram

    parts: list[str] = []

    # Check if tarot dominant element aligns with hexagram trigrams
    lower_element = _TRIGRAM_ELEMENTS.get(primary.lower_trigram)
    upper_element = _TRIGRAM_ELEMENTS.get(primary.upper_trigram)
    trigram_elements = {e for e in (lower_element, upper_element) if e}

    if dominant_element and dominant_element in trigram_elements:
        trigram_name = primary.upper_trigram if upper_element == dominant_element else primary.lower_trigram
        parts.append(
            f"Both systems converge on {dominant_element}: the tarot cards lean heavily toward this element, "
            f"and the I Ching echoes it through the {trigram_name} trigram. "
            f"When two oracles point the same direction, the message is hard to ignore."
        )
    elif dominant_element:
        hex_energy = primary.lower_trigram if primary.lower_trigram else primary.upper_trigram
        parts.append(
            f"The tarot draws toward {dominant_element}, while the I Ching's {hex_energy} trigram carries a different current. "
            f"These two systems aren't saying the same thing — hold both, and notice where they diverge."
        )

    # Note if both systems suggest transition or stability
    has_changing = bool(consultation.changing_lines)
    reversal_count = analysis.get("reversal_count", 0)
    total_cards = len(reading.drawn_cards) if reading.drawn_cards else 1

    if has_changing and reversal_count > 0:
        parts.append(
            f"The reversed cards and the changing lines both suggest active friction — something is resisting or shifting. "
            f"This is not a stable moment; it is asking for a decision."
        )
    elif not has_changing and reversal_count == 0:
        parts.append(
            "Neither system shows movement — no changing lines, no reversed cards. "
            "This reading describes a condition in full force, not a turning point."
        )

    return " ".join(parts).strip()


def generate_educational_tips(reading: Reading) -> list[str]:
    tips: list[str] = []
    seen: set[str] = set()
    analysis = analyze_patterns(reading)
    names_in_reading = {_card_name(drawn.card).lower() for drawn in reading.drawn_cards}

    def add_tip(text: str) -> None:
        cleaned = _ensure_sentence(text)
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            tips.append(cleaned)

    for drawn in reading.drawn_cards:
        for tip in _card_tips(drawn.card):
            add_tip(tip)

        related = [name for name in _card_related(drawn.card) if name in names_in_reading]
        if related:
            related_text = ", ".join(sorted({name.title() for name in related}))
            add_tip(f"{_card_name(drawn.card)} is traditionally worth comparing with {related_text} when those cards appear together.")

    if analysis["major_minor_ratio"]["major"]:
        add_tip("Major Arcana cards usually point to larger life lessons or turning points, while Minor Arcana cards describe the texture of day-to-day life around them.")

    dominant_suit = analysis.get("dominant_suit")
    if dominant_suit:
        add_tip(_SUIT_TIPS[dominant_suit])

    dominant_element = analysis.get("dominant_element")
    if dominant_element and dominant_element in _ELEMENT_TIPS:
        add_tip(_ELEMENT_TIPS[dominant_element])

    repeats = analysis["number_patterns"]["repeats"]
    for number in sorted(repeats, key=int):
        meaning = _NUMBER_MEANINGS.get(int(number))
        if meaning:
            add_tip(f"In tarot numerology, {number} often relates to {meaning}.")
            break

    return tips[:6]


def _resolve_card_by_name(name: str, deck: list[Any]) -> Any:
    """Find a card in the deck by name, with fuzzy matching.

    Accepts formats like:
    - "Two of Swords"
    - "two of swords"
    - "2 of swords"
    - "The High Priestess"
    - "high priestess"
    - "page of cups"
    """
    target = name.strip().lower()

    # Direct match
    for card in deck:
        if _card_name(card).strip().lower() == target:
            return card

    # Match without leading "the"
    target_no_the = target.removeprefix("the ")
    for card in deck:
        card_name = _card_name(card).strip().lower()
        if card_name.removeprefix("the ") == target_no_the:
            return card

    # Number word to digit substitution ("two of swords" -> "2 of swords")
    word_to_digit = {
        "ace": "1", "one": "1",
        "two": "2", "three": "3", "four": "4", "five": "5",
        "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10",
        "page": "11", "knight": "12", "queen": "13", "king": "14",
    }
    words = target.split()
    digit_target = " ".join(word_to_digit.get(w, w) for w in words)
    if digit_target != target:
        for card in deck:
            card_name = _card_name(card).strip().lower()
            card_digit = " ".join(word_to_digit.get(w, w) for w in card_name.split())
            if card_digit == digit_target or card_name == digit_target:
                return card

    # Partial match: check if target contains all words of a card name (minus "of", "the")
    stop_words = {"of", "the", "in", "a", "an"}
    target_tokens = {w for w in target.split() if w not in stop_words}
    for card in deck:
        card_tokens = {w for w in _card_name(card).strip().lower().split() if w not in stop_words}
        if target_tokens and target_tokens.issubset(card_tokens):
            return card

    raise ValueError(
        f"Card '{name}' not found in deck. "
        f"Use exact names like 'Two of Swords', 'The High Priestess', or 'Page of Cups'."
    )


def _parse_card_spec(spec: str, deck: list[Any]) -> tuple[Any, bool]:
    """Parse a card specification like 'Two of Swords' or 'Two of Swords rx'.

    Returns (card_object, reversed_bool).
    'rx' suffix marks a card as reversed.
    """
    spec = spec.strip()
    reversed_card = False

    # Check for reversed markers: 'rx', 'reversed', 'rev', '(r)', '(rx)'
    reversed_markers = [" rx", " reversed", " rev", " (r)", " (rx)"]
    for marker in reversed_markers:
        if spec.lower().endswith(marker):
            spec = spec[: -len(marker)].strip()
            reversed_card = True
            break

    card = _resolve_card_by_name(spec, deck)
    return card, reversed_card


def draw_manual_reading(
    spread_name: str,
    card_specs: list[str],
    query: str | None = None,
) -> Reading:
    """Draw a reading from manually specified cards instead of random draw.

    card_specs is a list of card name strings, one per position in the spread.
    Append 'rx' to mark a card reversed: 'Two of Swords rx'.

    Example:
        draw_manual_reading(
            "three-card",
            ["Two of Swords", "Two of Pentacles", "Page of Cups"],
            query="What about this decision?",
        )
    """
    resolved_name, positions = _resolve_spread(spread_name)
    deck = list(_get_deck())

    if len(card_specs) != len(positions):
        raise ValueError(
            f"Spread '{resolved_name}' has {len(positions)} positions, "
            f"but {len(card_specs)} card{'s' if len(card_specs) != 1 else ''} "
            f"were specified. Need exactly {len(positions)} cards."
        )

    drawn_cards = []
    used_names: list[str] = []
    for position_name, spec in zip(positions, card_specs):
        card, reversed_card = _parse_card_spec(spec, deck)
        drawn_cards.append(
            DrawnCard(
                card=card,
                position_name=position_name,
                reversed=reversed_card,
            )
        )
        used_names.append(_card_name(card))

    reading = Reading(
        spread_name=resolved_name,
        query=query,
        drawn_cards=drawn_cards,
        timestamp=datetime.now(timezone.utc),
        interpretation="",
    )
    reading.interpretation = interpret_reading(reading)
    return reading


def draw_reading(spread_name: str, query: str | None = None) -> Reading:
    resolved_name, positions = _resolve_spread(spread_name)
    deck = list(_get_deck())
    if len(deck) < len(positions):
        raise ValueError(
            f"Spread '{resolved_name}' needs {len(positions)} cards, but the imported deck only has {len(deck)}."
        )

    _RNG.shuffle(deck)
    drawn_cards = [
        DrawnCard(
            card=deck[index],
            position_name=position_name,
            reversed=(_RNG.random() < 0.30),
        )
        for index, position_name in enumerate(positions)
    ]

    reading = Reading(
        spread_name=resolved_name,
        query=query,
        drawn_cards=drawn_cards,
        timestamp=datetime.now(timezone.utc),
        interpretation="",
    )
    reading.interpretation = interpret_reading(reading)
    return reading


def reading_to_json(reading: Reading) -> dict[str, Any]:
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
                "card": _serialize_card(drawn.card),
            }
            for drawn in reading.drawn_cards
        ],
        "interpretation": reading.interpretation,
        "analysis": analyze_patterns(reading),
        "educational_tips": generate_educational_tips(reading),
    }


def save_reading(reading: Reading, path: str | Path | None = None) -> None:
    destination = Path(path) if path is not None else _READINGS_PATH
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(reading_to_json(reading), ensure_ascii=True))
        handle.write("\n")


def _deserialize_drawn_card(payload: dict[str, Any]) -> DrawnCard:
    return DrawnCard(
        card=payload.get("card") or {"name": payload.get("name", "Unknown Card")},
        position_name=str(payload["position_name"]),
        reversed=bool(payload["reversed"]),
    )


def load_readings(path: str | Path | None = None) -> list[Reading]:
    source = Path(path) if path is not None else _READINGS_PATH
    if not source.exists():
        return []

    readings: list[Reading] = []
    with source.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                payload = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON in {source} on line {line_number}") from exc

            timestamp_text = payload.get("timestamp")
            if not timestamp_text:
                raise ValueError(f"Missing timestamp in {source} on line {line_number}")

            readings.append(
                Reading(
                    spread_name=str(payload.get("spread_name", "Unknown Spread")),
                    query=payload.get("query"),
                    drawn_cards=[_deserialize_drawn_card(item) for item in payload.get("drawn_cards", [])],
                    timestamp=datetime.fromisoformat(timestamp_text),
                    interpretation=str(payload.get("interpretation", "")),
                )
            )
    return readings


__all__ = [
    "DrawnCard",
    "Reading",
    "analyze_patterns",
    "draw_manual_reading",
    "draw_reading",
    "generate_educational_tips",
    "interpret_reading",
    "load_readings",
    "reading_to_json",
    "save_reading",
]
