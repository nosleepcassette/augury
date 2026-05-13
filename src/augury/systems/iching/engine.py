"""Casting engine, history, and JSON serialization for the I Ching system."""

from __future__ import annotations

import hashlib
import json
import random
import re
from dataclasses import asdict, dataclass, is_dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from random import SystemRandom
from typing import Any

from ...config import DEFAULT_ICHING_PREFS, get_app_paths
from .data import Hexagram, get_hexagram_by_binary, get_hexagram_by_number, hexagram_to_json

_RNG = SystemRandom()
_CONSULTATIONS_PATH = get_app_paths().iching_readings_path
_METHODS = {
    "three-coin-yarrow": {
        "name": "Three Coins (Yarrow Weights)",
        "description": "A coin-style cast that preserves yarrow-stalk line probabilities.",
        "weights": {6: 1, 7: 5, 8: 7, 9: 3},
    }
}


@dataclass(slots=True, frozen=True)
class CastLine:
    line_number: int
    value: int
    polarity: str
    changing: bool


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


def _normalize_method(method: str | None) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", str(method or "").strip().lower()).strip("-")
    if value in {"three-coins", "coins", "yarrow", "three-coin-yarrow"}:
        return "three-coin-yarrow"
    return str(DEFAULT_ICHING_PREFS["default_method"])


def method_specs() -> list[dict[str, Any]]:
    return [
        {"slug": slug, **spec}
        for slug, spec in _METHODS.items()
    ]


def method_name(method: str) -> str:
    slug = _normalize_method(method)
    return str(_METHODS[slug]["name"])


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
    return value


def _line_from_value(value: int, line_number: int) -> CastLine:
    if value not in {6, 7, 8, 9}:
        raise ValueError(f"Unexpected line value: {value}")
    polarity = "yang" if value in {7, 9} else "yin"
    return CastLine(
        line_number=line_number,
        value=value,
        polarity=polarity,
        changing=value in {6, 9},
    )


def _weighted_choice(rng: random.Random, weights: dict[int, int]) -> int:
    total = sum(weights.values())
    pick = rng.randint(1, total)
    cursor = 0
    for value, weight in sorted(weights.items()):
        cursor += weight
        if pick <= cursor:
            return value
    return max(weights)


def _line_value_for_relating(line: CastLine) -> int:
    if line.value == 6:
        return 7
    if line.value == 9:
        return 8
    return line.value


def _binary_top_to_bottom(lines: list[CastLine], *, relating: bool = False) -> str:
    values = []
    for line in reversed(lines):
        value = _line_value_for_relating(line) if relating else line.value
        values.append("1" if value in {7, 9} else "0")
    return "".join(values)


def cast_lines(method: str = "three-coin-yarrow", rng: random.Random | None = None) -> list[CastLine]:
    slug = _normalize_method(method)
    weights = dict(_METHODS[slug]["weights"])
    active_rng = rng or _RNG
    return [
        _line_from_value(_weighted_choice(active_rng, weights), index)
        for index in range(1, 7)
    ]


def _first_sentence(text: str) -> str:
    cleaned = " ".join(str(text).split())
    if not cleaned:
        return ""
    match = re.search(r"(?<=[.!?])\s", cleaned)
    if not match:
        return cleaned
    return cleaned[: match.start()].strip()


_TRIGRAM_MEANINGS: dict[str, str] = {
    "Heaven": "the Creative — pure yang, strength, sky, the father principle",
    "Earth": "the Receptive — pure yin, yielding, vast and open, the mother principle",
    "Thunder": "the Arousing — shock and sudden movement, the eldest son, spring energy",
    "Water": "the Abysmal — danger, depth, the coursing stream, the middle son",
    "Mountain": "Keeping Still — rest, the boundary, the youngest son",
    "Wind": "the Gentle — penetrating persistence, wood, the eldest daughter",
    "Fire": "the Clinging — clarity and illumination, the sun, the middle daughter",
    "Lake": "the Joyous — openness, joy, the mouth, the youngest daughter",
}


def _excerpt(text: str, sentences: int = 2) -> str:
    """Return the first N sentences from a block of Wilhelm commentary."""
    cleaned = " ".join(str(text).split())
    if not cleaned:
        return ""
    parts = re.split(r"(?<=[.!?])\s+", cleaned)
    return " ".join(parts[:sentences]).strip()


def _trigram_sentence(hexagram: "Hexagram") -> str:
    lower = hexagram.lower_trigram
    upper = hexagram.upper_trigram
    lower_meaning = _TRIGRAM_MEANINGS.get(lower, lower)
    upper_meaning = _TRIGRAM_MEANINGS.get(upper, upper)
    if lower == upper:
        return (
            f"Both trigrams are {lower} ({lower_meaning}). "
            f"The doubling intensifies this quality — it fills the entire structure of the hexagram."
        )
    return (
        f"The lower trigram is {lower} ({lower_meaning}); "
        f"the upper trigram is {upper} ({upper_meaning}). "
        f"What arises from below meets what governs from above."
    )


def _iching_synthesis(consultation: "Consultation") -> str:
    primary = consultation.primary_hexagram
    parts: list[str] = []
    if not consultation.changing_lines:
        parts.append(
            f"Hexagram {primary.number} stands still and complete. "
            "This is not a moment of transition but of being squarely inside a condition — "
            "the oracle is asking you to understand it fully before moving."
        )
    elif len(consultation.changing_lines) == 6:
        parts.append(
            "All six lines are in motion. A total transformation is underway — "
            "the situation described by the primary hexagram is already giving way entirely "
            "to what the relating hexagram holds."
        )
    elif len(consultation.changing_lines) == 1:
        line_num = consultation.changing_lines[0]
        parts.append(
            f"A single changing line at position {line_num} carries the sharpest practical instruction. "
            "The rest of the hexagram provides the context; that line provides the specific message."
        )
    else:
        count = len(consultation.changing_lines)
        parts.append(
            f"{count} lines in motion describe an active transition. "
            "The overall direction is more important here than any single line — "
            "read the relating hexagram as the destination, not just a footnote."
        )
    if primary.keywords:
        kw = ", ".join(primary.keywords[:3])
        parts.append(f"The essential qualities of this hexagram: {kw}.")
    return " ".join(parts).strip()


def interpret_consultation(consultation: Consultation) -> str:
    primary = consultation.primary_hexagram
    parts: list[str] = []

    symbol = primary.unicode_symbol or ""
    hex_name = f"Hexagram {primary.number}, {primary.name}"
    if primary.chinese_name and primary.pinyin:
        hex_name += f" ({primary.chinese_name} / {primary.pinyin})"
    symbol_str = f" {symbol}" if symbol else ""

    if consultation.query:
        parts.append(
            f'You brought the question: "{consultation.query}". '
            f"The cast yields {hex_name}{symbol_str}."
        )
    else:
        parts.append(f"The cast yields {hex_name}{symbol_str}.")

    if primary.symbolic:
        symbolic_excerpt = _excerpt(primary.symbolic, sentences=3)
        if symbolic_excerpt:
            parts.append(symbolic_excerpt)

    if primary.judgment_text:
        judgment_body = primary.judgment_text.strip()
        judgment_comment = _excerpt(primary.judgment_comments, sentences=2)
        if judgment_comment:
            parts.append(f"The Judgment reads: {judgment_body}\n{judgment_comment}")
        else:
            parts.append(f"The Judgment reads: {judgment_body}")

    if primary.image_text:
        image_body = " ".join(primary.image_text.split())
        image_comment = _excerpt(primary.image_comments, sentences=2)
        if image_comment:
            parts.append(f"The Image: {image_body}\n{image_comment}")
        else:
            parts.append(f"The Image: {image_body}")

    trigram_s = _trigram_sentence(primary)
    if trigram_s:
        parts.append(trigram_s)

    if consultation.changing_lines:
        line_numbers_str = ", ".join(str(n) for n in consultation.changing_lines)
        parts.append(
            f"Changing lines appear at position{'s' if len(consultation.changing_lines) > 1 else ''} "
            f"{line_numbers_str}. The answer is in motion — this is not a static condition."
        )
        for number in consultation.changing_lines:
            line_text = primary.line_texts[number - 1].strip()
            line_comment = _excerpt(primary.line_comments[number - 1], sentences=3)
            entry = f"Line {number}: {line_text}"
            if line_comment:
                entry += f"\n{line_comment}"
            parts.append(entry)

        if consultation.relating_hexagram is not None:
            relating = consultation.relating_hexagram
            relating_symbol = relating.unicode_symbol or ""
            rel_name = f"Hexagram {relating.number}, {relating.name}"
            if relating.chinese_name and relating.pinyin:
                rel_name += f" ({relating.chinese_name} / {relating.pinyin})"
            parts.append(
                f"This movement tends toward {rel_name}{' ' + relating_symbol if relating_symbol else ''}.\n"
                f"{relating.judgment_text}\n"
                + _excerpt(relating.judgment_comments, sentences=2)
            )
    else:
        parts.append(
            "No lines are changing. The primary hexagram stands as the complete answer — "
            "a stable condition to be understood and worked with rather than a transition to be navigated. "
            "Spend time with the Judgment and the Image before looking for movement."
        )

    synthesis = _iching_synthesis(consultation)
    if synthesis:
        parts.append(synthesis)

    return "\n\n".join(part.strip() for part in parts if part.strip())


def generate_study_tips(consultation: Consultation) -> list[str]:
    primary = consultation.primary_hexagram
    tips = [
        primary.educational_tip,
        f"The lower trigram is {primary.lower_trigram}; the upper trigram is {primary.upper_trigram}.",
        "In I Ching work, changing lines are read from the primary hexagram before the relating hexagram.",
    ]
    if not consultation.changing_lines:
        tips.append("With no changing lines, spend more time with the primary Judgment and Image before looking for secondary structure.")
    elif len(consultation.changing_lines) == 1:
        tips.append("With one changing line, that single line often carries the sharpest practical instruction.")
    else:
        tips.append("With multiple changing lines, the answer usually describes an active transition rather than a static condition.")
    return tips[:6]


def cast_consultation(
    method: str = "three-coin-yarrow",
    query: str | None = None,
    *,
    rng: random.Random | None = None,
    timestamp: datetime | None = None,
) -> Consultation:
    slug = _normalize_method(method)
    lines = cast_lines(slug, rng=rng)
    primary = get_hexagram_by_binary(_binary_top_to_bottom(lines))
    changing_lines = [line.line_number for line in lines if line.changing]
    relating = get_hexagram_by_binary(_binary_top_to_bottom(lines, relating=True)) if changing_lines else None
    consultation = Consultation(
        method=slug,
        query=query,
        timestamp=timestamp or datetime.now(timezone.utc),
        lines=lines,
        primary_hexagram=primary,
        relating_hexagram=relating,
        changing_lines=changing_lines,
        interpretation="",
    )
    consultation.interpretation = interpret_consultation(consultation)
    return consultation


def daily_consultation(
    target_date: date | None = None,
    *,
    method: str = "three-coin-yarrow",
) -> Consultation:
    active_date = target_date or date.today()
    seed_text = f"iching-daily:{active_date.isoformat()}:{_normalize_method(method)}"
    seed = int(hashlib.sha256(seed_text.encode("utf-8")).hexdigest(), 16)
    rng = random.Random(seed)
    return cast_consultation(
        method=method,
        query=f"Daily guidance for {active_date.isoformat()}",
        rng=rng,
        timestamp=datetime.combine(active_date, datetime.min.time(), tzinfo=timezone.utc),
    )


def consultation_to_json(consultation: Consultation) -> dict[str, Any]:
    return {
        "system": "iching",
        "method": consultation.method,
        "method_name": method_name(consultation.method),
        "query": consultation.query,
        "timestamp": consultation.timestamp.isoformat(),
        "lines": [_json_safe(line) for line in consultation.lines],
        "primary_hexagram": hexagram_to_json(consultation.primary_hexagram),
        "relating_hexagram": None if consultation.relating_hexagram is None else hexagram_to_json(consultation.relating_hexagram),
        "changing_lines": list(consultation.changing_lines),
        "interpretation": consultation.interpretation,
        "study_tips": generate_study_tips(consultation),
    }


def save_consultation(consultation: Consultation, path: str | Path | None = None) -> None:
    destination = Path(path) if path is not None else _CONSULTATIONS_PATH
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(consultation_to_json(consultation), ensure_ascii=True))
        handle.write("\n")


def _deserialize_line(payload: dict[str, Any]) -> CastLine:
    return CastLine(
        line_number=int(payload["line_number"]),
        value=int(payload["value"]),
        polarity=str(payload["polarity"]),
        changing=bool(payload["changing"]),
    )


def load_consultations(path: str | Path | None = None) -> list[Consultation]:
    source = Path(path) if path is not None else _CONSULTATIONS_PATH
    if not source.exists():
        return []

    consultations: list[Consultation] = []
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

            primary_payload = payload.get("primary_hexagram") or {}
            relating_payload = payload.get("relating_hexagram") or None
            primary = get_hexagram_by_number(int(primary_payload.get("number", 0)))
            relating = None
            if isinstance(relating_payload, dict) and relating_payload.get("number") is not None:
                relating = get_hexagram_by_number(int(relating_payload["number"]))

            consultations.append(
                Consultation(
                    method=str(payload.get("method", DEFAULT_ICHING_PREFS["default_method"])),
                    query=payload.get("query"),
                    timestamp=datetime.fromisoformat(timestamp_text),
                    lines=[_deserialize_line(item) for item in payload.get("lines", [])],
                    primary_hexagram=primary,
                    relating_hexagram=relating,
                    changing_lines=[int(item) for item in payload.get("changing_lines", [])],
                    interpretation=str(payload.get("interpretation", "")),
                )
            )
    return consultations


__all__ = [
    "CastLine",
    "Consultation",
    "cast_consultation",
    "consultation_to_json",
    "daily_consultation",
    "generate_study_tips",
    "interpret_consultation",
    "load_consultations",
    "method_name",
    "method_specs",
    "save_consultation",
]
