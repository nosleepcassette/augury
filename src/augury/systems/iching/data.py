"""Data loading and lookup helpers for the I Ching system."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from importlib import resources
from typing import Any


@dataclass(slots=True, frozen=True)
class Hexagram:
    number: int
    name: str
    slug: str
    chinese_name: str
    pinyin: str
    unicode_symbol: str
    binary_top_to_bottom: str
    lower_trigram: str
    upper_trigram: str
    keywords: tuple[str, ...]
    symbolic: str
    judgment_text: str
    judgment_comments: str
    image_text: str
    image_comments: str
    line_texts: tuple[str, ...]
    line_comments: tuple[str, ...]
    educational_tip: str


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(value).strip().lower()).strip("-")


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _binary_string(value: Any) -> str:
    digits = "".join(ch for ch in str(value) if ch in {"0", "1"})
    return digits.zfill(6)


def _dataset_text() -> str:
    data_file = resources.files("augury.systems.iching").joinpath("data/iching_wilhelm_translation.js")
    text = data_file.read_text(encoding="utf-8")
    prefix = "export default "
    if text.startswith(prefix):
        text = text[len(prefix) :]
    return text.rstrip().rstrip(";")


@lru_cache(maxsize=1)
def _raw_dataset() -> dict[str, Any]:
    payload = json.loads(_dataset_text())
    return payload if isinstance(payload, dict) else {}


def _hexagram_name(record: dict[str, Any]) -> str:
    english = _clean_text(record.get("english"))
    if english:
        return english
    judgment = _clean_text(record.get("wilhelm_judgment", {}).get("text"))
    match = re.match(r"([A-Z][A-Z ,'\-]+)", judgment)
    if match:
        return match.group(1).title().replace(" ,", ",")
    return f"Hexagram {int(record.get('hex', 0) or 0)}"


def _keywords(record: dict[str, Any]) -> tuple[str, ...]:
    values = [
        _clean_text(record.get("english")),
        _clean_text(record.get("wilhelm_above", {}).get("alchemical")),
        _clean_text(record.get("wilhelm_below", {}).get("alchemical")),
        _clean_text(record.get("wilhelm_above", {}).get("symbolic")).strip(","),
        _clean_text(record.get("wilhelm_below", {}).get("symbolic")).strip(","),
    ]
    seen: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.append(value)
    return tuple(seen)


def _hexagram_from_record(record: dict[str, Any]) -> Hexagram:
    lines = record.get("wilhelm_lines", {})
    line_texts = tuple(_clean_text(lines.get(str(index), {}).get("text")) for index in range(1, 7))
    line_comments = tuple(_clean_text(lines.get(str(index), {}).get("comments")) for index in range(1, 7))
    lower_trigram = _clean_text(record.get("wilhelm_below", {}).get("alchemical")).title()
    upper_trigram = _clean_text(record.get("wilhelm_above", {}).get("alchemical")).title()
    name = _hexagram_name(record)
    return Hexagram(
        number=int(record.get("hex", 0) or 0),
        name=name,
        slug=_slugify(name),
        chinese_name=_clean_text(record.get("trad_chinese")),
        pinyin=_clean_text(record.get("pinyin")),
        unicode_symbol=_clean_text(record.get("hex_font")),
        binary_top_to_bottom=_binary_string(record.get("binary")),
        lower_trigram=lower_trigram,
        upper_trigram=upper_trigram,
        keywords=_keywords(record),
        symbolic=_clean_text(record.get("wilhelm_symbolic")),
        judgment_text=_clean_text(record.get("wilhelm_judgment", {}).get("text")),
        judgment_comments=_clean_text(record.get("wilhelm_judgment", {}).get("comments")),
        image_text=_clean_text(record.get("wilhelm_image", {}).get("text")),
        image_comments=_clean_text(record.get("wilhelm_image", {}).get("comments")),
        line_texts=line_texts,
        line_comments=line_comments,
        educational_tip=(
            f"Read the hexagram from the bottom line upward. {name} pairs {lower_trigram.lower()} below "
            f"with {upper_trigram.lower()} above."
        ),
    )


@lru_cache(maxsize=1)
def all_hexagrams() -> tuple[Hexagram, ...]:
    records = []
    for key in sorted(_raw_dataset(), key=lambda item: int(item)):
        value = _raw_dataset()[key]
        if isinstance(value, dict):
            records.append(_hexagram_from_record(value))
    return tuple(records)


@lru_cache(maxsize=1)
def _indexes() -> tuple[dict[int, Hexagram], dict[str, Hexagram], dict[str, Hexagram]]:
    by_number: dict[int, Hexagram] = {}
    by_slug: dict[str, Hexagram] = {}
    by_binary: dict[str, Hexagram] = {}
    for hexagram in all_hexagrams():
        by_number[hexagram.number] = hexagram
        by_binary[hexagram.binary_top_to_bottom] = hexagram
        for value in {
            str(hexagram.number),
            hexagram.slug,
            _slugify(hexagram.name),
            _slugify(hexagram.chinese_name),
            _slugify(hexagram.pinyin),
        }:
            if value:
                by_slug[value] = hexagram
    return by_number, by_slug, by_binary


def get_hexagram_by_number(number: int) -> Hexagram:
    by_number, _, _ = _indexes()
    return by_number[int(number)]


def get_hexagram_by_binary(binary_top_to_bottom: str) -> Hexagram:
    _, _, by_binary = _indexes()
    normalized = _binary_string(binary_top_to_bottom)
    return by_binary[normalized]


def lookup_hexagram(value: int | str) -> Hexagram:
    if isinstance(value, int) or str(value).strip().isdigit():
        return get_hexagram_by_number(int(value))
    _, by_slug, _ = _indexes()
    normalized = _slugify(str(value))
    if normalized in by_slug:
        return by_slug[normalized]
    raise KeyError(f"Unknown hexagram: {value}")


def hexagram_to_json(hexagram: Hexagram) -> dict[str, Any]:
    return {
        "number": hexagram.number,
        "name": hexagram.name,
        "slug": hexagram.slug,
        "chinese_name": hexagram.chinese_name,
        "pinyin": hexagram.pinyin,
        "unicode_symbol": hexagram.unicode_symbol,
        "binary_top_to_bottom": hexagram.binary_top_to_bottom,
        "lower_trigram": hexagram.lower_trigram,
        "upper_trigram": hexagram.upper_trigram,
        "keywords": list(hexagram.keywords),
        "symbolic": hexagram.symbolic,
        "judgment": {
            "text": hexagram.judgment_text,
            "comments": hexagram.judgment_comments,
        },
        "image": {
            "text": hexagram.image_text,
            "comments": hexagram.image_comments,
        },
        "lines": [
            {
                "line_number": index,
                "text": hexagram.line_texts[index - 1],
                "comments": hexagram.line_comments[index - 1],
            }
            for index in range(1, 7)
        ],
        "educational_tip": hexagram.educational_tip,
    }


__all__ = [
    "Hexagram",
    "all_hexagrams",
    "get_hexagram_by_binary",
    "get_hexagram_by_number",
    "hexagram_to_json",
    "lookup_hexagram",
]
