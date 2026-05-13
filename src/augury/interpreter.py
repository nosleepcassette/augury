# maps · cassette.help · MIT
"""LLM interpretation layer for augury readings.

Supports Gemini Flash (default), Hermes, and NVIDIA NIM.
Keys are loaded from ~/.env. If unavailable, returns native interpretation.

Engine selection: set AUGURY_INTERPRET_ENGINE to gemini, hermes, nvidia, or nvidia-glm.
"""

from __future__ import annotations

import json
import os
import re
import sys
import threading
import time
from pathlib import Path
from typing import Any

_BRAILLE_FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"


class _Spinner:
    """Non-blocking terminal spinner for long LLM calls."""

    def __init__(self, label: str = "interpreting") -> None:
        self._label = label
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def _run(self) -> None:
        is_tty = getattr(sys.stderr, "isatty", lambda: False)()
        if not is_tty:
            return
        frames = list(_BRAILLE_FRAMES)
        start = time.monotonic()
        i = 0
        while not self._stop.wait(0.1):
            elapsed = int(time.monotonic() - start)
            frame = frames[i % len(frames)]
            sys.stderr.write(f"\r\033[33m{frame}\033[0m {self._label}… {elapsed}s  ")
            sys.stderr.flush()
            i += 1
        sys.stderr.write("\r\033[K")
        sys.stderr.flush()

    def __enter__(self) -> "_Spinner":
        self._thread.start()
        return self

    def __exit__(self, *_: object) -> None:
        self._stop.set()
        self._thread.join(timeout=0.5)

NVIDIA_MODELS = {
    # Verified against NVIDIA NIM supported model docs on 2026-05-13.
    "glm-5": "zai-org/glm-5",
    "glm-5.1": "zai-org/glm-51",
    "llama-70b": "meta/llama-3.1-70b-instruct",
    "nemotron": "nvidia/llama-3.1-nemotron-70b-instruct",
}

_TAROT_SYSTEM_PROMPT = (
    "You are a skilled, thoughtful tarot reader writing for a paying client. "
    "You have been given the full structured data for a tarot reading including card names, "
    "positions, orientations, elemental analysis, astrology rulers, and numerology. "
    "Write a rich 4-6 paragraph interpretation in second person ('you'). "
    "Reference specific cards by name and position. "
    "Note where cards speak to the same theme. "
    "Close with practical guidance. "
    "Do not use clichés or generic platitudes. "
    "Write as if you know what you're talking about."
)

_ICHING_SYSTEM_PROMPT = (
    "You are a scholar and practitioner of the I Ching writing a consultation response for a paying client. "
    "You have been given the full structured data: hexagram number, name, Chinese name, judgment, "
    "judgment commentary, image, image commentary, trigrams, and changing lines with their commentaries. "
    "Write a 3-5 paragraph synthesis in second person that weaves together the Wilhelm text with "
    "practical modern insight. Reference the hexagram name and changing lines specifically."
)

_COMBINED_SYSTEM_PROMPT = (
    "You are synthesizing a divination reading that draws on three systems: tarot, I Ching, and astrology. "
    "Note where all three systems converge on the same theme. "
    "Note where they diverge and what that means. "
    "Close with a clear, grounded statement of what this moment is asking of the person. "
    "Write in second person, 5-7 paragraphs."
)


def _load_env_key(name: str) -> str | None:
    """Load an API key from environment or ~/.env file."""
    value = os.environ.get(name)
    if value:
        return value.strip()
    env_path = Path.home() / ".env"
    if not env_path.exists():
        return None
    try:
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            if key.strip() == name:
                return val.strip().strip('"').strip("'")
    except OSError:
        pass
    return None


def _active_engine() -> str:
    return os.environ.get("AUGURY_INTERPRET_ENGINE", "gemini").lower()


def _call_gemini(system_prompt: str, user_content: str, api_key: str) -> str:
    """Call Gemini Flash via direct REST API."""
    import urllib.request

    model = "gemini-2.5-flash"
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        f"?key={api_key.strip()}"
    )
    body = json.dumps({
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"parts": [{"text": user_content}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 2048},
    }).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with _Spinner("gemini"):
        with urllib.request.urlopen(req, timeout=None) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    candidates = data.get("candidates", [])
    if not candidates:
        raise RuntimeError(f"Gemini returned no candidates: {data}")
    parts = candidates[0].get("content", {}).get("parts", [])
    return "".join(p.get("text", "") for p in parts).strip()


def _call_hermes(system_prompt: str, user_content: str) -> str:
    """Call Hermes via the local CLI bridge."""
    import shutil
    import subprocess

    hermes_bin = os.environ.get("HERMES_BIN", "hermes")
    if not shutil.which(hermes_bin):
        raise RuntimeError(
            f"Hermes not found at '{hermes_bin}'. Set HERMES_BIN or install hermes on PATH."
        )
    prompt = f"{system_prompt}\n\n{user_content}".strip()
    with _Spinner("hermes"):
        result = subprocess.run(
            [hermes_bin, "--oneshot", prompt],
            capture_output=True,
            text=True,
            timeout=None,
            check=False,
        )
    if result.returncode != 0:
        raise RuntimeError(f"Hermes error: {result.stderr.strip()}")
    return result.stdout.strip()


def _call_nvidia(
    system_prompt: str,
    user_content: str,
    api_key: str,
    model_key: str = "llama-70b",
) -> str:
    """Call NVIDIA NIM via OpenAI-compatible REST endpoint."""
    try:
        from openai import OpenAI  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "openai package not installed. Run: pip install openai"
        ) from exc

    client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=api_key,
    )
    model = os.environ.get("AUGURY_NVIDIA_MODEL") or NVIDIA_MODELS.get(model_key, NVIDIA_MODELS["glm-5"])
    with _Spinner(f"nvidia/{model.split('/')[-1]}"):
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=0.7,
            max_tokens=2048,
        )
    return completion.choices[0].message.content.strip()


def _call_llm(system_prompt: str, user_content: str, engine: str | None = None) -> str | None:
    """Dispatch to active engine. Returns None if no key available."""
    selected = (engine or _active_engine()).lower()
    if selected == "none":
        return None
    if selected == "hermes":
        return _call_hermes(system_prompt, user_content)
    if selected == "nvidia-glm":
        api_key = _load_env_key("NVIDIA_API_KEY")
        if not api_key:
            return None
        return _call_nvidia(system_prompt, user_content, api_key, model_key="glm-5")
    if selected == "nvidia-glm-5.1":
        api_key = _load_env_key("NVIDIA_API_KEY")
        if not api_key:
            return None
        return _call_nvidia(system_prompt, user_content, api_key, model_key="glm-5.1")
    if selected == "nvidia":
        api_key = _load_env_key("NVIDIA_API_KEY")
        if not api_key:
            return None
        return _call_nvidia(system_prompt, user_content, api_key, model_key="llama-70b")
    api_key = _load_env_key("GEMINI_API_KEY")
    if not api_key:
        return None
    return _call_gemini(system_prompt, user_content, api_key)


def _reading_to_prompt(reading_json: dict[str, Any], query: str | None = None) -> str:
    cards = reading_json.get("drawn_cards", [])
    lines: list[str] = []
    if query:
        lines.append(f"Query: {query}")
    lines.append(f"Spread: {reading_json.get('spread_name', 'unknown')}")
    lines.append("")
    for drawn in cards:
        card = drawn.get("card", drawn)
        name = card.get("name", "Unknown")
        position = drawn.get("position_name", "")
        orientation = "reversed" if drawn.get("reversed") else "upright"
        parts = [f"{position}: {name} ({orientation})"]
        if card.get("astrology"):
            parts.append(f"  Astrology: {card['astrology']}")
        if card.get("numerology"):
            parts.append(f"  Numerology: {card['numerology']}")
        if card.get("element"):
            parts.append(f"  Element: {card['element']}")
        keywords = drawn.get("keywords") or card.get("upright_keywords") or card.get("reversed_keywords") or []
        keywords = keywords or card.get("keywords_upright") or card.get("keywords_reversed") or []
        if keywords:
            parts.append(f"  Keywords: {', '.join(keywords[:5])}")
        meaning = drawn.get("meaning")
        if not meaning and drawn.get("reversed"):
            meaning = card.get("reversed_meaning") or card.get("meaning_reversed")
        if not meaning:
            meaning = card.get("upright_meaning") or card.get("meaning_upright")
        if meaning:
            parts.append(f"  Meaning: {meaning}")
        lines.extend(parts)
        lines.append("")
    return "\n".join(lines)


def _consultation_to_prompt(consultation_json: dict[str, Any], query: str | None = None) -> str:
    primary = consultation_json.get("primary_hexagram", {})
    relating = consultation_json.get("relating_hexagram")
    changing = consultation_json.get("changing_lines", [])
    lines: list[str] = []
    if query:
        lines.append(f"Query: {query}")
    lines.append(
        f"Hexagram {primary.get('number')}: {primary.get('name')} "
        f"({primary.get('chinese_name', '')} / {primary.get('pinyin', '')})"
    )
    lines.append(f"Lower trigram: {primary.get('lower_trigram', '')}  Upper: {primary.get('upper_trigram', '')}")
    if primary.get("symbolic"):
        lines.append(f"Symbolic: {primary['symbolic'][:300]}")
    judgment = primary.get("judgment", {})
    if judgment.get("text"):
        lines.append(f"Judgment: {judgment['text']}")
    if judgment.get("comments"):
        lines.append(f"Judgment commentary: {judgment['comments'][:400]}")
    image = primary.get("image", {})
    if image.get("text"):
        lines.append(f"Image: {image['text']}")
    if image.get("comments"):
        lines.append(f"Image commentary: {image['comments'][:400]}")
    if changing:
        lines.append(f"\nChanging lines: {', '.join(str(n) for n in changing)}")
        line_texts = primary.get("line_texts", [])
        line_comments = primary.get("line_comments", [])
        for n in changing:
            idx = n - 1
            lt = line_texts[idx] if idx < len(line_texts) else ""
            lc = line_comments[idx] if idx < len(line_comments) else ""
            lines.append(f"  Line {n}: {lt}")
            if lc:
                lines.append(f"    Commentary: {lc[:300]}")
    if relating:
        lines.append(
            f"\nRelating hexagram: {relating.get('number')}: {relating.get('name')} "
            f"({relating.get('chinese_name', '')} / {relating.get('pinyin', '')})"
        )
        rel_judgment = relating.get("judgment", {})
        if rel_judgment.get("text"):
            lines.append(f"Relating judgment: {rel_judgment['text']}")
    return "\n".join(lines)


def interpret_tarot(reading_json: dict[str, Any], query: str | None = None, engine: str | None = None) -> str | None:
    """LLM interpretation of a tarot reading. Returns None if no key available."""
    user_content = _reading_to_prompt(reading_json, query)
    return _call_llm(_TAROT_SYSTEM_PROMPT, user_content, engine=engine)


def interpret_iching(consultation_json: dict[str, Any], query: str | None = None, engine: str | None = None) -> str | None:
    """LLM interpretation of an I Ching consultation. Returns None if no key available."""
    user_content = _consultation_to_prompt(consultation_json, query)
    return _call_llm(_ICHING_SYSTEM_PROMPT, user_content, engine=engine)


def interpret_combined(
    tarot_json: dict[str, Any],
    iching_json: dict[str, Any],
    astro_text: str | None = None,
    query: str | None = None,
    engine: str | None = None,
) -> str | None:
    """LLM synthesis of tarot + I Ching + optional astrology. Returns None if no key available."""
    parts: list[str] = []
    if query:
        parts.append(f"Query: {query}\n")
    parts.append("=== TAROT ===")
    parts.append(_reading_to_prompt(tarot_json, query=None))
    parts.append("=== I CHING ===")
    parts.append(_consultation_to_prompt(iching_json, query=None))
    if astro_text:
        parts.append("=== ASTROLOGY ===")
        parts.append(astro_text)
    user_content = "\n".join(parts)
    return _call_llm(_COMBINED_SYSTEM_PROMPT, user_content, engine=engine)


__all__ = [
    "interpret_combined",
    "interpret_iching",
    "interpret_tarot",
]
