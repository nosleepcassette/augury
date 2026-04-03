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


def _interpret_drawn_card(drawn: DrawnCard) -> str:
    card = drawn.card
    name = _card_name(card)
    orientation = "reversed" if drawn.reversed else "upright"
    meaning = _card_meaning(card, drawn.reversed)
    keywords = _card_keywords(card, drawn.reversed)
    keyword_sentence = ""
    if keywords:
        keyword_sentence = f" Keywords here include {', '.join(keywords[:4])}."

    major_sentence = ""
    if _card_arcana(card) == "major":
        major_sentence = " Because it is Major Arcana, it reads less like background noise and more like a headline."

    return (
        f"In the {drawn.position_name} position, {_card_name(card)} appears {orientation}. "
        f"{_position_context(drawn.position_name)} "
        f"{meaning}{keyword_sentence}{major_sentence}"
    ).strip()


def interpret_reading(reading: Reading) -> str:
    sections: list[str] = []

    if reading.query:
        sections.append(
            f'You asked about "{reading.query}". The {reading.spread_name} spread frames that question through {len(reading.drawn_cards)} position'
            + ("s." if len(reading.drawn_cards) != 1 else ".")
        )
    else:
        sections.append(
            f"The {reading.spread_name} spread reveals the present pattern through {len(reading.drawn_cards)} position"
            + ("s." if len(reading.drawn_cards) != 1 else ".")
        )

    sections.extend(_interpret_drawn_card(drawn) for drawn in reading.drawn_cards)

    pattern_sentences = _pattern_sentences(reading)
    if pattern_sentences:
        sections.append("Pattern-wise, " + " ".join(pattern_sentences))

    if reading.spread_name.lower() == "yes/no" and reading.drawn_cards:
        answer_card = reading.drawn_cards[0]
        leaning = "not yet" if answer_card.reversed else "yes, with momentum"
        sections.append(f"As a direct answer, the reading leans {leaning}.")

    return "\n\n".join(section.strip() for section in sections if section.strip())


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
    "draw_reading",
    "generate_educational_tips",
    "interpret_reading",
    "load_readings",
    "reading_to_json",
    "save_reading",
]
