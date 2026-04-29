#!/usr/bin/env python3
# maps · cassette.help · MIT
# oracle-render — render augury/divination markdown into styled editorial PNG/PDF
from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError as exc:
    raise SystemExit(
        "Pillow is required. Run: pip3 install Pillow\n"
        f"Original error: {exc}"
    )


# -----------------------------
# Theme — dark amber phosphor
# -----------------------------
BG          = (10, 7, 3)
PANEL       = (22, 15, 7)
PANEL_ALT   = (30, 21, 10)
TEXT        = (230, 178, 80)
TEXT_MUTED  = (170, 128, 50)
TEXT_ACCENT = (247, 200, 100)
RULE        = (80, 56, 20)
RULE_LIGHT  = (55, 38, 14)

LONG_WIDTH        = 1100
LONG_OUTER_MARGIN = 48
LONG_INNER_MARGIN = 130
STORY_SIZE  = (1080, 1920)
POST_SIZE   = (1080, 1080)
PNG_DPI     = (150, 150)

_FONT_OVERRIDE_ENV = "ORACLE_RENDER_FONT_PATH"
_FONT_NAME_ENV = "ORACLE_RENDER_FONT"
_FONT_OVERRIDE_PATH = os.environ.get(_FONT_OVERRIDE_ENV, "").strip()
DEFAULT_FONT_PROFILE_KEY = "arial"


@dataclass(frozen=True)
class FontProfile:
    label: str
    body: Tuple[str, ...]
    bold: Tuple[str, ...] = ()
    italic: Tuple[str, ...] = ()
    bold_italic: Tuple[str, ...] = ()
    mono: Tuple[str, ...] = ()


def _dedupe_paths(paths: Sequence[str]) -> Tuple[str, ...]:
    candidates: list[str] = []
    for path in paths:
        if path and path not in candidates:
            candidates.append(path)
    return tuple(candidates)


def _with_font_override(paths: Sequence[str]) -> Tuple[str, ...]:
    candidates: list[str] = []
    if _FONT_OVERRIDE_PATH and os.path.exists(_FONT_OVERRIDE_PATH):
        candidates.append(_FONT_OVERRIDE_PATH)
    for path in paths:
        if path and path not in candidates:
            candidates.append(path)
    return tuple(candidates)


GENERIC_FONT_CANDIDATES_BODY = (
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/Library/Fonts/Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
)
GENERIC_FONT_CANDIDATES_BOLD = (
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
)
GENERIC_FONT_CANDIDATES_ITALIC = (
    "/System/Library/Fonts/Supplemental/Arial Italic.ttf",
    "/Library/Fonts/Arial Italic.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf",
)
GENERIC_FONT_CANDIDATES_BOLD_ITALIC = (
    "/System/Library/Fonts/Supplemental/Arial Bold Italic.ttf",
    "/Library/Fonts/Arial Bold Italic.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf",
)
GENERIC_FONT_CANDIDATES_MONO = (
    "/Users/maps/Library/Fonts/SGr-IosevkaTerm-Regular.ttc",
    "/System/Library/Fonts/Supplemental/Menlo.ttc",
    "/System/Library/Fonts/Supplemental/Courier New.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
)

FONT_PROFILES = {
    "arial": FontProfile(
        label="Arial",
        body=("/System/Library/Fonts/Supplemental/Arial.ttf",),
        bold=("/System/Library/Fonts/Supplemental/Arial Bold.ttf",),
        italic=("/System/Library/Fonts/Supplemental/Arial Italic.ttf",),
        bold_italic=("/System/Library/Fonts/Supplemental/Arial Bold Italic.ttf",),
        mono=("/System/Library/Fonts/Supplemental/Arial.ttf",),
    ),
    "loveletter-typewriter": FontProfile(
        label="Love Letter Typewriter",
        body=("/Users/maps/Library/Fonts/LoveLetterTypewriter.ttf",),
        mono=("/Users/maps/Library/Fonts/LoveLetterTypewriter.ttf",),
    ),
    "naughty-ones": FontProfile(
        label="Naughty Ones",
        body=("/Users/maps/Library/Fonts/naughty-ones-amiga.otf",),
        mono=("/Users/maps/Library/Fonts/naughty-ones-amiga.otf",),
    ),
    "pixelfy-sans": FontProfile(
        label="Pixelify Sans",
        body=("/Users/maps/Library/Fonts/PixelifySans-VariableFont_wght.ttf",),
        mono=("/Users/maps/Library/Fonts/PixelifySans-VariableFont_wght.ttf",),
    ),
    "pokemon-gb": FontProfile(
        label="Pokemon GB",
        body=("/Users/maps/Library/Fonts/PokemonGb-RAeo.ttf",),
        mono=("/Users/maps/Library/Fonts/PokemonGb-RAeo.ttf",),
    ),
    "press-start-2p": FontProfile(
        label="Press Start 2P",
        body=("/Users/maps/Library/Fonts/PressStart2P-Regular.ttf",),
        mono=("/Users/maps/Library/Fonts/PressStart2P-Regular.ttf",),
    ),
    "dotmatrix-varduo": FontProfile(
        label="DotMatrix VarDuo",
        body=("/Users/maps/Library/Fonts/DotMatrixVarDuo-Regular.otf",),
        bold=("/Users/maps/Library/Fonts/DotMatrixVarDuo-Bold.otf",),
        italic=("/Users/maps/Library/Fonts/DotMatrixVarDuo-Italic.otf",),
        bold_italic=("/Users/maps/Library/Fonts/DotMatrixVarDuo-BoldItalic.otf",),
        mono=("/Users/maps/Library/Fonts/DotMatrixVarDuo-Regular.otf",),
    ),
    "vt323": FontProfile(
        label="VT323",
        body=("/Users/maps/Library/Fonts/VT323-Regular.ttf",),
        mono=("/Users/maps/Library/Fonts/VT323-Regular.ttf",),
    ),
}

FONT_ALIASES = {
    "default": DEFAULT_FONT_PROFILE_KEY,
    "normal": DEFAULT_FONT_PROFILE_KEY,
    "loveletter": "loveletter-typewriter",
    "love-letter-typewriter": "loveletter-typewriter",
    "naughty": "naughty-ones",
    "pixelfy": "pixelfy-sans",
    "pixelify": "pixelfy-sans",
    "pixelify-sans": "pixelfy-sans",
    "pokemon": "pokemon-gb",
    "press-start": "press-start-2p",
    "dotmatrix": "dotmatrix-varduo",
}

FONT_OUTPUT_SUFFIXES = {
    "loveletter-typewriter": "llt",
    "naughty-ones": "no",
    "pixelfy-sans": "pfs",
    "pokemon-gb": "pgb",
    "press-start-2p": "ps2p",
    "dotmatrix-varduo": "dmvd",
    "vt323": "vt323",
}


def _normalize_font_name(name: str) -> str:
    return re.sub(r"-+", "-", name.strip().lower().replace("_", "-").replace(" ", "-"))


def resolve_font_profile_name(name: Optional[str]) -> str:
    raw_name = name or os.environ.get(_FONT_NAME_ENV, "") or DEFAULT_FONT_PROFILE_KEY
    normalized = _normalize_font_name(raw_name)
    resolved = FONT_ALIASES.get(normalized, normalized)
    if resolved not in FONT_PROFILES:
        choices = ", ".join(sorted(FONT_PROFILES))
        raise ValueError(f"Unknown font '{raw_name}'. Choose one of: {choices}")
    return resolved


def font_choices_help() -> str:
    return ", ".join(sorted(FONT_PROFILES))


def font_output_suffix(font_name: str) -> Optional[str]:
    resolved = resolve_font_profile_name(font_name)
    if resolved == DEFAULT_FONT_PROFILE_KEY:
        return None
    return FONT_OUTPUT_SUFFIXES.get(resolved, resolved)


def base_name_for_font(base_name: str, font_name: str) -> str:
    suffix = font_output_suffix(font_name)
    if not suffix:
        return base_name
    if base_name.endswith(f"-{suffix}"):
        return base_name
    return f"{base_name}-{suffix}"


def _profile_candidates(style: str, font_name: str) -> Tuple[str, ...]:
    profile = FONT_PROFILES[resolve_font_profile_name(font_name)]
    fallback_map = {
        "body": GENERIC_FONT_CANDIDATES_BODY,
        "bold": GENERIC_FONT_CANDIDATES_BOLD,
        "italic": GENERIC_FONT_CANDIDATES_ITALIC,
        "bold_italic": GENERIC_FONT_CANDIDATES_BOLD_ITALIC,
        "mono": GENERIC_FONT_CANDIDATES_MONO,
    }
    primary_map = {
        "body": profile.body,
        "bold": profile.bold or profile.body,
        "italic": profile.italic or profile.body,
        "bold_italic": profile.bold_italic or profile.italic or profile.bold or profile.body,
        "mono": profile.mono or profile.body,
    }
    return _with_font_override(_dedupe_paths(primary_map[style] + fallback_map[style]))


FONT_CANDIDATES_UNICODE_CJK = [
    # Keep Unicode fallback separate from the user-facing text font.
    # Markdown apps do automatic font fallback for missing glyphs; Pillow does not.
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/Library/Fonts/Arial Unicode.ttf",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/STHeiti Light.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/Songti.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
]
FONT_CANDIDATES_UNICODE_SYMBOLS = [
    "/System/Library/Fonts/Apple Symbols.ttf",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/Library/Fonts/Arial Unicode.ttf",
    "/System/Library/Fonts/STIXTwoMath.otf",
]

_GLYPH_BYTES_CACHE: dict[tuple[str, int, str], bytes] = {}


def _glyph_bytes(font: ImageFont.ImageFont, ch: str) -> bytes:
    font_id = str(getattr(font, "path", f"<font:{id(font)}>"))
    font_size = int(getattr(font, "size", 0))
    key = (font_id, font_size, ch)
    cached = _GLYPH_BYTES_CACHE.get(key)
    if cached is not None:
        return cached
    glyph = bytes(font.getmask(ch))
    _GLYPH_BYTES_CACHE[key] = glyph
    return glyph


def _font_has_glyph(font: ImageFont.ImageFont, ch: str) -> bool:
    if ch == "\ufffd":
        return True
    return _glyph_bytes(font, ch) != _glyph_bytes(font, "\ufffd")

# Unicode ranges that need the fallback font (CJK, hexagrams, trigrams, etc.)
_UNICODE_RANGES = [
    (0x4E00, 0x9FFF),   # CJK unified ideographs
    (0x3000, 0x303F),   # CJK punctuation
    (0x3040, 0x30FF),   # Hiragana + Katakana
    (0x3400, 0x4DBF),   # CJK extension A
    (0xFF00, 0xFFEF),   # Halfwidth/fullwidth forms
]
_I_CHING_SYMBOL_RANGES = [
    (0x2630, 0x2637),   # trigrams ☰-☷
    (0x4DC0, 0x4DFF),   # I Ching hexagrams ䷀-䷿
]


def _char_needs_unicode_font(ch: str) -> bool:
    cp = ord(ch)
    return any(lo <= cp <= hi for lo, hi in _UNICODE_RANGES + _I_CHING_SYMBOL_RANGES)


def _text_has_unicode(text: str) -> bool:
    return any(_char_needs_unicode_font(c) for c in text)


def load_font(size: int, candidates: Sequence[str]) -> ImageFont.ImageFont:
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size=size)
            except Exception:
                continue
    return ImageFont.load_default()


def load_font_family(size: int, candidates: Sequence[str]) -> Tuple[ImageFont.ImageFont, ...]:
    loaded: list[ImageFont.ImageFont] = []
    seen: set[str] = set()
    for path in candidates:
        if not path or path in seen or not os.path.exists(path):
            continue
        try:
            loaded.append(ImageFont.truetype(path, size=size))
            seen.add(path)
        except Exception:
            continue
    if loaded:
        return tuple(loaded)
    return (ImageFont.load_default(),)


# -----------------------------
# Inline markup
# -----------------------------
@dataclass
class TextRun:
    text: str
    bold: bool = False
    italic: bool = False


def parse_inline_markup(text: str) -> List[TextRun]:
    """Split text into TextRuns preserving **bold**, *italic*, ***bold-italic***."""
    runs: List[TextRun] = []
    pat = re.compile(r'\*\*\*(.+?)\*\*\*|\*\*(.+?)\*\*|\*(.+?)\*', re.DOTALL)
    last = 0
    for m in pat.finditer(text):
        if m.start() > last:
            plain = text[last:m.start()]
            if plain:
                runs.append(TextRun(text=plain))
        if m.group(1) is not None:
            runs.append(TextRun(text=m.group(1), bold=True, italic=True))
        elif m.group(2) is not None:
            runs.append(TextRun(text=m.group(2), bold=True))
        elif m.group(3) is not None:
            runs.append(TextRun(text=m.group(3), italic=True))
        last = m.end()
    if last < len(text):
        tail = text[last:]
        if tail:
            runs.append(TextRun(text=tail))
    return runs or [TextRun(text=text)]


# -----------------------------
# Markdown parsing
# -----------------------------
@dataclass
class RawBlock:
    kind: str
    level: int = 0
    text: str = ""
    lines: List[str] = field(default_factory=list)
    rows: List[List[str]] = field(default_factory=list)


@dataclass
class RenderBlock:
    kind: str
    text: str = ""          # may contain **bold** / *italic* markers for paragraph/bullet
    lines: List[str] = field(default_factory=list)
    rows: List[List[str]] = field(default_factory=list)
    level: int = 0


def strip_inline_md(text: str, *, keep_emphasis: bool = False) -> str:
    """Strip markdown inline syntax. keep_emphasis preserves **bold** and *italic*."""
    text = text.replace("\t", "    ")
    text = re.sub(r"!\[([^\]]*)\]\(([^\)]*)\)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\(([^\)]*)\)", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    if not keep_emphasis:
        text = re.sub(r"\*\*\*([^*]+)\*\*\*", r"\1", text)
        text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
        text = re.sub(r"__([^_]+)__", r"\1", text)
        text = re.sub(r"\*([^*]+)\*", r"\1", text)
        text = re.sub(r"_([^_]+)_", r"\1", text)
    text = text.replace("&nbsp;", " ")
    text = text.replace("[ ]", "☐")
    text = text.replace("[x]", "☑")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _preprocess_text(text: str) -> str:
    """Convert plain-text conventions (====, ----) to markdown before parsing."""
    lines = text.split('\n')
    result: List[str] = []
    i = 0
    def clean_line(value: str) -> str:
        return re.sub(r"^(?:\s*\d+\|\s*)+", "", value)

    while i < len(lines):
        line = clean_line(lines[i])
        if re.match(r'^={8,}\s*$', line):
            if (i + 2 < len(lines)
                    and clean_line(lines[i + 1]).strip()
                    and re.match(r'^={8,}\s*$', clean_line(lines[i + 2]))):
                result.append(f'## {clean_line(lines[i + 1]).strip()}')
                i += 3
                continue
            else:
                result.append('---')
        elif re.match(r'^-{10,}\s*$', line):
            result.append('---')
        else:
            result.append(line)
        i += 1
    return '\n'.join(result)


def _split_markdown_table_row(row: str) -> List[str]:
    """Split one markdown table row, respecting escaped pipe characters."""
    row = row.strip()
    if row.startswith("|"):
        row = row[1:]
    if row.endswith("|"):
        row = row[:-1]
    return [
        strip_inline_md(cell.replace(r"\|", "|").strip())
        for cell in re.split(r"(?<!\\)\|", row)
    ]


def _is_table_separator_row(row: Sequence[str]) -> bool:
    """Return True for markdown separator rows like --- or :---:."""
    return bool(row) and all(
        re.fullmatch(r":?\s*-{3,}\s*:?", cell.strip()) for cell in row
    )


def _normalize_table_rows(rows: Sequence[Sequence[str]]) -> List[List[str]]:
    """Clean table rows into an even rectangular grid for rendering."""
    cleaned: List[List[str]] = []
    for row in rows:
        cells = [re.sub(r"\s+", " ", str(cell)).strip() for cell in row]
        if not cells or _is_table_separator_row(cells):
            continue
        cleaned.append(cells)

    if not cleaned:
        return []

    ncols = max(len(row) for row in cleaned)
    padded = [row + [""] * (ncols - len(row)) for row in cleaned]
    keep_cols = [
        ci for ci in range(ncols)
        if any(row[ci].strip() for row in padded)
    ]
    if not keep_cols:
        return []
    return [[row[ci] for ci in keep_cols] for row in padded]


def parse_markdown(md_text: str) -> List[RawBlock]:
    lines = md_text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    blocks: List[RawBlock] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        if stripped.startswith("```"):
            fence = stripped[:3]
            i += 1
            code_lines: List[str] = []
            while i < len(lines) and not lines[i].strip().startswith(fence):
                code_lines.append(lines[i].rstrip("\n"))
                i += 1
            if i < len(lines):
                i += 1
            blocks.append(RawBlock(kind="code", lines=code_lines))
            continue

        heading_match = re.match(r"^(#{1,6})\s+(.*)$", line)
        if heading_match:
            level = len(heading_match.group(1))
            text = strip_inline_md(heading_match.group(2))  # headings: strip emphasis
            blocks.append(RawBlock(kind="heading", level=level, text=text))
            i += 1
            continue

        if re.match(r"^\s*([-*_])\1{2,}\s*$", line):
            blocks.append(RawBlock(kind="rule"))
            i += 1
            continue

        if stripped.startswith("|"):
            table_lines: List[str] = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i].strip())
                i += 1
            rows = _normalize_table_rows(
                _split_markdown_table_row(tbl) for tbl in table_lines
            )
            if rows:
                blocks.append(RawBlock(kind="table", rows=rows))
            continue

        bullet_match = re.match(r"^\s*([-*+])\s+(.*)$", line)
        numbered_match = re.match(r"^\s*(\d+)\.\s+(.*)$", line)
        checkbox_match = re.match(r"^\s*[-*+]\s+\[( |x|X)\]\s+(.*)$", line)
        if bullet_match or numbered_match or checkbox_match:
            items: List[str] = []
            while i < len(lines):
                current = lines[i]
                cb = re.match(r"^\s*[-*+]\s+\[( |x|X)\]\s+(.*)$", current)
                bl = re.match(r"^\s*([-*+])\s+(.*)$", current)
                nm = re.match(r"^\s*(\d+)\.\s+(.*)$", current)
                if cb:
                    prefix = "☑ " if cb.group(1).lower() == "x" else "☐ "
                    items.append(prefix + strip_inline_md(cb.group(2), keep_emphasis=True))
                    i += 1
                    continue
                if nm:
                    items.append(f"{nm.group(1)}. " + strip_inline_md(nm.group(2), keep_emphasis=True))
                    i += 1
                    continue
                if bl:
                    items.append("• " + strip_inline_md(bl.group(2), keep_emphasis=True))
                    i += 1
                    continue
                break
            blocks.append(RawBlock(kind="list", lines=items))
            continue

        para_lines = [stripped]
        i += 1
        while i < len(lines):
            nxt = lines[i].strip()
            if not nxt:
                break
            if nxt.startswith("#") or nxt.startswith("|") or nxt.startswith("```"):
                break
            if re.match(r"^\s*([-*+])\s+", lines[i]) or re.match(r"^\s*\d+\.\s+", lines[i]):
                break
            if re.match(r"^\s*([-*_])\1{2,}\s*$", lines[i]):
                break
            para_lines.append(nxt)
            i += 1
        # Keep emphasis markers in paragraphs
        blocks.append(RawBlock(kind="paragraph",
                               text=strip_inline_md(" ".join(para_lines), keep_emphasis=True)))

    return blocks


def compile_blocks(raw_blocks: Sequence[RawBlock]) -> List[RenderBlock]:
    compiled: List[RenderBlock] = []
    for block in raw_blocks:
        if block.kind == "heading":
            compiled.append(RenderBlock(kind="heading", text=block.text, level=block.level))
        elif block.kind == "paragraph":
            compiled.append(RenderBlock(kind="paragraph", text=block.text))
        elif block.kind == "list":
            for item in block.lines:
                compiled.append(RenderBlock(kind="bullet", text=item))
        elif block.kind == "rule":
            compiled.append(RenderBlock(kind="rule"))
        elif block.kind == "code":
            if block.lines:
                compiled.append(RenderBlock(kind="code",
                    lines=[ln.rstrip() for ln in block.lines if ln.strip() != ""] or [""]))
        elif block.kind == "table":
            if block.rows:
                compiled.append(RenderBlock(kind="table", rows=block.rows))
    return compiled


# -----------------------------
# Canvas spec and fonts
# -----------------------------
@dataclass
class CanvasSpec:
    width: int
    height: Optional[int]
    outer_margin: int
    inner_margin_x: int
    top_margin: int
    bottom_margin: int
    title_size: int
    h2_size: int
    h3_size: int
    body_size: int
    bullet_size: int
    mono_size: int
    meta_size: int
    panel_radius: int
    rule_width: int
    mode_name: str

    @property
    def content_width(self) -> int:
        return self.width - 2 * self.inner_margin_x


def make_spec(mode: str) -> CanvasSpec:
    if mode == "single":
        return CanvasSpec(
            width=LONG_WIDTH, height=None,
            outer_margin=LONG_OUTER_MARGIN, inner_margin_x=LONG_INNER_MARGIN,
            top_margin=120, bottom_margin=120,
            title_size=58, h2_size=44, h3_size=34,
            body_size=30, bullet_size=29, mono_size=24, meta_size=26,
            panel_radius=24, rule_width=1, mode_name=mode,
        )
    if mode == "story":
        return CanvasSpec(
            width=STORY_SIZE[0], height=STORY_SIZE[1],
            outer_margin=40, inner_margin_x=80,
            top_margin=100, bottom_margin=100,
            title_size=52, h2_size=40, h3_size=32,
            body_size=28, bullet_size=27, mono_size=22, meta_size=24,
            panel_radius=20, rule_width=1, mode_name=mode,
        )
    if mode == "post":
        return CanvasSpec(
            width=POST_SIZE[0], height=POST_SIZE[1],
            outer_margin=36, inner_margin_x=72,
            top_margin=80, bottom_margin=80,
            title_size=44, h2_size=34, h3_size=28,
            body_size=24, bullet_size=23, mono_size=18, meta_size=20,
            panel_radius=16, rule_width=1, mode_name=mode,
        )
    raise ValueError(f"Unknown mode: {mode}")


@dataclass
class Fonts:
    title: ImageFont.ImageFont
    h2: ImageFont.ImageFont
    h3: ImageFont.ImageFont
    body: ImageFont.ImageFont
    body_bold: ImageFont.ImageFont
    body_italic: ImageFont.ImageFont
    body_bold_italic: ImageFont.ImageFont
    bullet: ImageFont.ImageFont
    mono: ImageFont.ImageFont
    meta: ImageFont.ImageFont
    table_body: ImageFont.ImageFont
    unicode_cjk_fallbacks: Tuple[ImageFont.ImageFont, ...]
    unicode_symbol_fallbacks: Tuple[ImageFont.ImageFont, ...]


def make_fonts(spec: CanvasSpec, font_name: str) -> Fonts:
    return Fonts(
        title=load_font(spec.title_size, _profile_candidates("bold", font_name)),
        h2=load_font(spec.h2_size, _profile_candidates("bold", font_name)),
        h3=load_font(spec.h3_size, _profile_candidates("bold", font_name)),
        body=load_font(spec.body_size, _profile_candidates("body", font_name)),
        body_bold=load_font(spec.body_size, _profile_candidates("bold", font_name)),
        body_italic=load_font(spec.body_size, _profile_candidates("italic", font_name)),
        body_bold_italic=load_font(spec.body_size, _profile_candidates("bold_italic", font_name)),
        bullet=load_font(spec.bullet_size, _profile_candidates("body", font_name)),
        mono=load_font(spec.mono_size, _profile_candidates("mono", font_name)),
        meta=load_font(spec.meta_size, _profile_candidates("bold", font_name)),
        table_body=load_font(spec.meta_size, _profile_candidates("body", font_name)),
        unicode_cjk_fallbacks=load_font_family(spec.body_size, FONT_CANDIDATES_UNICODE_CJK),
        unicode_symbol_fallbacks=load_font_family(spec.body_size, FONT_CANDIDATES_UNICODE_SYMBOLS),
    )


# -----------------------------
# Font/metrics helpers
# -----------------------------
def line_height(font: ImageFont.ImageFont, extra: int = 0) -> int:
    bbox = font.getbbox("Ag")
    return (bbox[3] - bbox[1]) + extra


def _run_font(run: TextRun, fonts: Fonts) -> ImageFont.ImageFont:
    if run.bold and run.italic:
        return fonts.body_bold_italic
    if run.bold:
        return fonts.body_bold
    if run.italic:
        return fonts.body_italic
    return fonts.body


def _measure_run(draw: ImageDraw.ImageDraw, run: TextRun, fonts: Fonts) -> int:
    if not run.text:
        return 0
    font = _run_font(run, fonts)
    return draw.textbbox((0, 0), run.text, font=font)[2]


def _space_w(draw: ImageDraw.ImageDraw, fonts: Fonts) -> int:
    return draw.textbbox((0, 0), " ", font=fonts.body)[2]


# -----------------------------
# Inline word-wrap with markup
# -----------------------------
def _split_words_with_style(text: str) -> List[Tuple[str, bool, bool]]:
    """Return list of (word, bold, italic) from markup text."""
    runs = parse_inline_markup(text)
    words: List[Tuple[str, bool, bool]] = []
    for run in runs:
        parts = run.text.split(" ")
        for j, part in enumerate(parts):
            if part:
                words.append((part, run.bold, run.italic))
            if j < len(parts) - 1 and (words or True):
                words.append((" ", run.bold, run.italic))
    # Collapse space tokens
    result: List[Tuple[str, bool, bool]] = []
    for w, b, it in words:
        if w == " ":
            if result and result[-1][0] != "\x00":  # sentinel
                result.append(("\x00", b, it))  # space marker
        else:
            result.append((w, b, it))
    return result


def _merge_word_runs(word_list: List[Tuple[str, bool, bool]]) -> List[TextRun]:
    """Merge adjacent same-style words into TextRuns."""
    if not word_list:
        return []
    runs: List[TextRun] = []
    cur_t, cur_b, cur_i = word_list[0]
    for w, b, i in word_list[1:]:
        if b == cur_b and i == cur_i:
            cur_t += " " + w
        else:
            runs.append(TextRun(text=cur_t, bold=cur_b, italic=cur_i))
            cur_t, cur_b, cur_i = w, b, i
    runs.append(TextRun(text=cur_t, bold=cur_b, italic=cur_i))
    return runs


def wrap_inline(draw: ImageDraw.ImageDraw, text: str, fonts: Fonts,
                width: int) -> List[List[TextRun]]:
    """Word-wrap text (with inline markup) to fit width. Returns list of lines."""
    if not text.strip():
        return [[TextRun(text="")]]

    raw_words = _split_words_with_style(text)
    sp_w = _space_w(draw, fonts)

    lines: List[List[TextRun]] = []
    current: List[Tuple[str, bool, bool]] = []
    current_w = 0

    for token in raw_words:
        word, bold, italic = token
        if word == "\x00":  # space between words
            continue
        run = TextRun(text=word, bold=bold, italic=italic)
        w = _measure_run(draw, run, fonts)

        if current and current_w + sp_w + w > width:
            lines.append(_merge_word_runs(current))
            current = [(word, bold, italic)]
            current_w = w
        else:
            if current:
                current_w += sp_w
            current.append((word, bold, italic))
            current_w += w

    if current:
        lines.append(_merge_word_runs(current))
    return lines or [[TextRun(text="")]]


def _count_inline_lines(draw: ImageDraw.ImageDraw, text: str, fonts: Fonts, width: int) -> int:
    """Return line count for text wrapped to width (for height measurement)."""
    plain = re.sub(r'\*+([^*]+)\*+', r'\1', text)
    words = plain.split()
    if not words:
        return 1
    lines, current_w = 1, 0
    sp_w = _space_w(draw, fonts)
    for word in words:
        w = draw.textbbox((0, 0), word, font=fonts.body)[2]
        if current_w and current_w + sp_w + w > width:
            lines += 1
            current_w = w
        else:
            current_w = (current_w + sp_w + w) if current_w else w
    return lines


# -----------------------------
# Inline rendering
# -----------------------------
def _fallback_fonts_for_char(fonts: Fonts, ch: str) -> Tuple[ImageFont.ImageFont, ...]:
    cp = ord(ch)
    if any(lo <= cp <= hi for lo, hi in _I_CHING_SYMBOL_RANGES):
        return fonts.unicode_symbol_fallbacks + fonts.unicode_cjk_fallbacks
    if any(lo <= cp <= hi for lo, hi in _UNICODE_RANGES):
        return fonts.unicode_cjk_fallbacks + fonts.unicode_symbol_fallbacks
    return fonts.unicode_symbol_fallbacks + fonts.unicode_cjk_fallbacks


def _pick_font_for_char(primary_font: ImageFont.ImageFont, fonts: Fonts, ch: str) -> ImageFont.ImageFont:
    if _font_has_glyph(primary_font, ch):
        return primary_font
    for fallback_font in _fallback_fonts_for_char(fonts, ch):
        if _font_has_glyph(fallback_font, ch):
            return fallback_font
    return primary_font


def _render_run_text(draw: ImageDraw.ImageDraw, x: int, y: int,
                     text: str, font: ImageFont.ImageFont,
                     fonts: Fonts,
                     fill: Tuple[int, int, int]) -> int:
    """Render text char-by-char with unicode fallback. Returns new x."""
    if not _text_has_unicode(text) and all(_font_has_glyph(font, ch) for ch in text):
        draw.text((x, y), text, font=font, fill=fill)
        return x + draw.textbbox((0, 0), text, font=font)[2]
    for ch in text:
        f = _pick_font_for_char(font, fonts, ch)
        draw.text((x, y), ch, font=f, fill=fill)
        x += draw.textbbox((0, 0), ch, font=f)[2]
    return x


def _render_inline_line(draw: ImageDraw.ImageDraw, fonts: Fonts,
                         x: int, y: int, runs: List[TextRun],
                         fill: Tuple[int, int, int],
                         justify_width: Optional[int] = None) -> None:
    """Render one line of TextRuns. justify_width enables full justification."""
    if not runs:
        return
    sp_w = _space_w(draw, fonts)
    n_gaps = len(runs) - 1

    if justify_width is not None and n_gaps > 0:
        total_text = sum(_measure_run(draw, r, fonts) for r in runs)
        extra = justify_width - total_text
        sp_w = sp_w + extra // n_gaps
        remainder = extra - (extra // n_gaps) * n_gaps
    else:
        remainder = 0

    cx = x
    for i, run in enumerate(runs):
        font = _run_font(run, fonts)
        cx = _render_run_text(draw, cx, y, run.text, font, fonts, fill)
        if i < n_gaps:
            cx += sp_w + (1 if i < remainder else 0)


def draw_inline_lines(draw: ImageDraw.ImageDraw, spec: CanvasSpec, fonts: Fonts,
                       y: int, text: str, fill: Tuple[int, int, int],
                       gap: int, x_offset: int = 0,
                       justify: bool = True) -> int:
    """Draw paragraph text with inline markup and full justification."""
    x = spec.inner_margin_x + x_offset
    cw = spec.content_width - x_offset
    line_groups = wrap_inline(draw, text, fonts, cw)
    lh = line_height(fonts.body)

    for i, runs in enumerate(line_groups):
        is_last = (i == len(line_groups) - 1)
        jw = cw if (justify and not is_last and len(runs) > 1) else None
        _render_inline_line(draw, fonts, x, y, runs, fill, justify_width=jw)
        y += lh + gap
    if line_groups:
        y -= gap
    return y


def draw_centered_lines(draw: ImageDraw.ImageDraw, spec: CanvasSpec, y: int,
                         lines: Sequence[str], font: ImageFont.ImageFont,
                         fill: Tuple[int, int, int], gap: int) -> int:
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        x = (spec.width - (bbox[2] - bbox[0])) // 2
        draw.text((x, y), line, font=font, fill=fill)
        y += line_height(font) + gap
    if lines:
        y -= gap
    return y


def centered_lines_height(font: ImageFont.ImageFont, count: int, gap: int) -> int:
    if count <= 0:
        return 0
    return (line_height(font) * count) + (gap * (count - 1))


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont,
              width: int) -> List[str]:
    """Plain text word-wrap (for headings, table cells, etc.)."""
    words = text.split()
    if not words:
        return [""]
    lines: List[str] = []
    current = ""
    for word in words:
        trial = (current + " " + word).strip()
        if draw.textbbox((0, 0), trial, font=font)[2] <= width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


# -----------------------------
# Canvas
# -----------------------------
def make_base_canvas(spec: CanvasSpec, *, height: int) -> Tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (spec.width, height), BG)
    draw = ImageDraw.Draw(img)
    for y in range(0, height, 4):
        base = 10 + (y % 8)
        draw.line((0, y, spec.width, y), fill=(base, base // 2, 0))
    draw.rounded_rectangle(
        (spec.outer_margin, spec.outer_margin,
         spec.width - spec.outer_margin, height - spec.outer_margin),
        radius=spec.panel_radius,
        fill=PANEL,
        outline=RULE,
        width=spec.rule_width,
    )
    return img, draw


# -----------------------------
# Table rendering
# -----------------------------
def _measure_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> int:
    return draw.textbbox((0, 0), text, font=font)[2]


def _table_body_font(fonts: Fonts, ncols: int) -> ImageFont.ImageFont:
    return fonts.table_body if ncols >= 4 else fonts.body


def _table_cell_padding(ncols: int) -> Tuple[int, int, int]:
    """Return horizontal padding, vertical padding, line gap for table cells."""
    if ncols >= 5:
        return 8, 7, 3
    if ncols >= 4:
        return 10, 8, 4
    return 12, 10, 5


def _fit_widths_to_available(widths: List[int], available: int) -> List[int]:
    if not widths:
        return []
    floor = max(1, min(36, available // len(widths)))
    total = sum(widths)
    if total == available:
        return widths
    if total <= 0:
        base = available // len(widths)
        result = [base for _ in widths]
    else:
        scale = available / total
        result = [max(floor, int(round(width * scale))) for width in widths]

    diff = available - sum(result)
    while diff != 0 and result:
        changed = False
        for idx in reversed(range(len(result))):
            if diff == 0:
                break
            step = 1 if diff > 0 else -1
            if step > 0 or result[idx] > floor:
                result[idx] += step
                diff -= step
                changed = True
        if not changed:
            break
    return result


def _calc_col_widths(draw: ImageDraw.ImageDraw, spec: CanvasSpec, fonts: Fonts,
                     rows: List[List[str]]) -> List[int]:
    rows = _normalize_table_rows(rows)
    if not rows:
        return []
    ncols = max(len(r) for r in rows)
    cell_pad_h, _, _ = _table_cell_padding(ncols)
    available = spec.content_width
    if ncols == 1:
        return [available]

    body_font = _table_body_font(fonts, ncols)
    min_widths: List[int] = []
    desired_widths: List[int] = []
    for ci in range(ncols):
        longest_word = 0
        desired = 0
        for ri, row in enumerate(rows):
            font = fonts.meta if ri == 0 else body_font
            cell = row[ci] if ci < len(row) else ""
            txt = cell.upper() if ri == 0 else cell
            words = txt.split() or [txt]
            for word in words:
                longest_word = max(longest_word, _measure_text(draw, word, font))
            desired = max(desired, _measure_text(draw, txt, font))
        min_widths.append(max(42, longest_word + cell_pad_h * 2 + 4))
        desired_widths.append(max(min_widths[-1], desired + cell_pad_h * 2 + 4))

    if sum(min_widths) >= available:
        return _fit_widths_to_available(min_widths, available)

    widths = min_widths[:]
    remaining = available - sum(widths)
    extra_needs = [max(0, desired_widths[i] - min_widths[i]) for i in range(ncols)]
    extra_total = sum(extra_needs)
    if extra_total:
        for ci, need in enumerate(extra_needs):
            take = min(remaining, int(round(remaining * need / extra_total)))
            widths[ci] += take
        diff = available - sum(widths)
        for ci in sorted(range(ncols), key=lambda i: extra_needs[i], reverse=True):
            if diff == 0:
                break
            widths[ci] += 1 if diff > 0 else -1
            diff += -1 if diff > 0 else 1
    else:
        widths = [width + remaining // ncols for width in widths]
        widths[-1] += available - sum(widths)

    return _fit_widths_to_available(widths, available)


def _table_row_height(draw: ImageDraw.ImageDraw, fonts: Fonts, row: List[str],
                      col_widths: List[int], is_header: bool,
                      cell_pad_h: int, cell_pad_v: int, line_gap: int) -> int:
    ncols = len(col_widths)
    font = fonts.meta if is_header else _table_body_font(fonts, ncols)
    row_h = line_height(font)
    for ci in range(ncols):
        cell = row[ci] if ci < len(row) else ""
        cw = col_widths[ci]
        txt = cell.upper() if is_header else cell
        lines = wrap_text(draw, txt, font, max(20, cw - cell_pad_h * 2))
        h = centered_lines_height(font, len(lines), line_gap)
        row_h = max(row_h, h)
    return row_h + cell_pad_v * 2


def _table_row_heights(draw: ImageDraw.ImageDraw, fonts: Fonts,
                       rows: List[List[str]], col_widths: List[int]) -> List[int]:
    ncols = len(col_widths)
    cell_pad_h, cell_pad_v, line_gap = _table_cell_padding(ncols)
    return [
        _table_row_height(draw, fonts, row, col_widths, ri == 0,
                          cell_pad_h, cell_pad_v, line_gap)
        for ri, row in enumerate(rows)
    ]


def _measure_row_h(draw: ImageDraw.ImageDraw, fonts: Fonts, row: List[str],
                   col_widths: List[int], is_header: bool,
                   cell_pad_h: int, cell_pad_v: int) -> int:
    _, _, line_gap = _table_cell_padding(len(col_widths))
    return _table_row_height(draw, fonts, row, col_widths, is_header,
                             cell_pad_h, cell_pad_v, line_gap)


def measure_table(draw: ImageDraw.ImageDraw, spec: CanvasSpec, fonts: Fonts,
                  rows: List[List[str]]) -> int:
    rows = _normalize_table_rows(rows)
    if not rows:
        return 0
    col_widths = _calc_col_widths(draw, spec, fonts, rows)
    total = 2
    for ri, row_h in enumerate(_table_row_heights(draw, fonts, rows, col_widths)):
        total += row_h
        if ri < len(rows) - 1:
            total += 1
    return total


def draw_table(draw: ImageDraw.ImageDraw, spec: CanvasSpec, fonts: Fonts,
               y: int, rows: List[List[str]]) -> int:
    rows = _normalize_table_rows(rows)
    if not rows:
        return y
    ncols = max(len(r) for r in rows)
    col_widths = _calc_col_widths(draw, spec, fonts, rows)
    left = spec.inner_margin_x
    right = left + sum(col_widths)
    cell_pad_h, cell_pad_v, line_gap = _table_cell_padding(ncols)

    table_height = measure_table(draw, spec, fonts, rows)
    draw.rounded_rectangle((left, y, right, y + table_height),
                           radius=8, fill=PANEL, outline=RULE, width=1)

    yy = y + 1
    for ri, row in enumerate(rows):
        is_header = ri == 0
        font = fonts.meta if is_header else _table_body_font(fonts, ncols)
        row_h = _table_row_height(
            draw, fonts, row, col_widths, is_header, cell_pad_h, cell_pad_v, line_gap
        )
        row_bg = PANEL_ALT if is_header else ((18, 12, 5) if ri % 2 == 1 else PANEL)
        draw.rectangle((left + 1, yy, right - 1, yy + row_h - 1), fill=row_bg)

        cx = left
        for ci in range(ncols):
            cell = row[ci] if ci < len(row) else ""
            cw = col_widths[ci]
            txt = cell.upper() if is_header else cell
            fill = TEXT_ACCENT if is_header else TEXT
            lines = wrap_text(draw, txt, font, max(20, cw - cell_pad_h * 2))
            ty = yy + cell_pad_v
            for ln in lines:
                draw.text((cx + cell_pad_h, ty), ln, font=font, fill=fill)
                ty += line_height(font) + line_gap
            cx += cw
            if ci < ncols - 1:
                draw.line((cx, yy, cx, yy + row_h), fill=RULE_LIGHT, width=1)

        yy += row_h
        if ri < len(rows) - 1:
            draw.line((left + 1, yy, right - 1, yy), fill=RULE_LIGHT, width=1)
            yy += 1

    return y + table_height


def split_table_to_fit(draw: ImageDraw.ImageDraw, spec: CanvasSpec, fonts: Fonts,
                       block: RenderBlock, available: int) -> Tuple[Optional[RenderBlock], Optional[RenderBlock]]:
    """Split a tall table by rows, repeating the header on the continuation."""
    rows = _normalize_table_rows(block.rows)
    if not rows:
        return None, None
    if available <= 0:
        return None, RenderBlock(kind="table", rows=rows)
    if measure_table(draw, spec, fonts, rows) <= available:
        return RenderBlock(kind="table", rows=rows), None

    col_widths = _calc_col_widths(draw, spec, fonts, rows)
    row_heights = _table_row_heights(draw, fonts, rows, col_widths)
    header = rows[0]
    body = rows[1:]
    if not body:
        return None, RenderBlock(kind="table", rows=rows)

    used = 2 + row_heights[0]
    fit_count = 0
    for offset, row_h in enumerate(row_heights[1:]):
        add = 1 + row_h
        if used + add > available:
            break
        used += add
        fit_count = offset + 1

    if fit_count <= 0:
        return None, RenderBlock(kind="table", rows=rows)

    head_rows = [header] + body[:fit_count]
    tail_body = body[fit_count:]
    first = RenderBlock(kind="table", rows=head_rows)
    rest = RenderBlock(kind="table", rows=[header] + tail_body) if tail_body else None
    return first, rest


# -----------------------------
# Block height measurement
# -----------------------------
def block_height(draw: ImageDraw.ImageDraw, spec: CanvasSpec, fonts: Fonts,
                 block: RenderBlock) -> int:
    if block.kind == "heading":
        font = fonts.title if block.level <= 1 else (fonts.h2 if block.level == 2 else fonts.h3)
        text = block.text.upper() if block.level <= 2 else block.text
        lines = wrap_text(draw, text, font, spec.content_width)
        h = centered_lines_height(font, len(lines), 10)
        if block.level <= 2:
            h += 20 + 16 + 4
        return h
    if block.kind == "paragraph":
        n = _count_inline_lines(draw, block.text, fonts, spec.content_width)
        return centered_lines_height(fonts.body, n, 10)
    if block.kind == "bullet":
        n = _count_inline_lines(draw, block.text, fonts, spec.content_width - 28)
        return centered_lines_height(fonts.bullet, n, 8)
    if block.kind == "code":
        lines = block.lines or [""]
        return 20 + centered_lines_height(fonts.mono, len(lines), 7) + 20
    if block.kind == "rule":
        return 20
    if block.kind == "table":
        return measure_table(draw, spec, fonts, block.rows)
    raise ValueError(f"Unsupported block kind: {block.kind}")


def block_spacing_after(prev: Optional[RenderBlock], current: RenderBlock,
                         spec: CanvasSpec) -> int:
    if prev is None:
        return 0
    if current.kind == "heading":
        return 44 if spec.mode_name != "post" else 28
    if prev.kind == "heading" and current.kind in {"paragraph", "bullet", "table", "code"}:
        return 20 if spec.mode_name != "post" else 14
    if current.kind == "rule" or prev.kind == "rule":
        return 28
    if current.kind == "table" or prev.kind == "table":
        return 24
    if current.kind == "bullet" and prev.kind == "bullet":
        return 8
    return 20 if spec.mode_name != "post" else 12


def split_block_to_fit(draw: ImageDraw.ImageDraw, spec: CanvasSpec, fonts: Fonts,
                        block: RenderBlock, available: int) -> Tuple[Optional[RenderBlock], Optional[RenderBlock]]:
    if available <= 0:
        return None, block
    lh = line_height(fonts.body)
    if block.kind in ("paragraph", "bullet"):
        gap = 10 if block.kind == "paragraph" else 8
        cw = spec.content_width if block.kind == "paragraph" else spec.content_width - 28
        max_lines = (available + gap) // (lh + gap)
        line_groups = wrap_inline(draw, block.text, fonts, cw)
        if max_lines >= len(line_groups):
            return block, None
        if max_lines == 0:
            return None, block

        # Reconstruct split text preserving inline markup. wrap_inline gives us
        # the visual line groupings; we use them only to count how many rendered
        # words fit, then rebuild markdown emphasis from the original styled runs.
        words_in_head = sum(
            len(run.text.split())
            for runs in line_groups[:max_lines]
            for run in runs
        )
        styled_words: List[Tuple[str, bool, bool]] = []
        for run in parse_inline_markup(block.text):
            styled_words.extend((word, run.bold, run.italic) for word in run.text.split())

        def serialize(tokens: List[Tuple[str, bool, bool]]) -> str:
            parts: List[str] = []
            current_words: List[str] = []
            current_style: Optional[Tuple[bool, bool]] = None

            def flush() -> None:
                nonlocal current_words, current_style
                if not current_words or current_style is None:
                    return
                segment = " ".join(current_words)
                bold, italic = current_style
                if bold and italic:
                    parts.append(f"***{segment}***")
                elif bold:
                    parts.append(f"**{segment}**")
                elif italic:
                    parts.append(f"*{segment}*")
                else:
                    parts.append(segment)
                current_words = []

            for word, bold, italic in tokens:
                style = (bold, italic)
                if current_style is not None and style != current_style:
                    flush()
                current_style = style
                current_words.append(word)
            flush()
            return " ".join(parts)

        head_raw = serialize(styled_words[:words_in_head])
        tail_raw = serialize(styled_words[words_in_head:])
        first = RenderBlock(kind=block.kind, text=head_raw)
        rest = RenderBlock(kind=block.kind, text=tail_raw) if tail_raw.strip() else None
        return first, rest
    if block.kind == "table":
        return split_table_to_fit(draw, spec, fonts, block, available)
    if block.kind in ("heading", "rule", "code"):
        return (block, None) if block_height(draw, spec, fonts, block) <= available else (None, block)
    return None, block


# -----------------------------
# Block rendering
# -----------------------------
def render_block(draw: ImageDraw.ImageDraw, spec: CanvasSpec, fonts: Fonts,
                 y: int, block: RenderBlock) -> int:
    rx1 = spec.inner_margin_x
    rx2 = spec.width - spec.inner_margin_x

    if block.kind == "heading":
        font = fonts.title if block.level <= 1 else (fonts.h2 if block.level == 2 else fonts.h3)
        if block.level <= 2:
            text = block.text.upper()
            lines = wrap_text(draw, text, font, spec.content_width)
            draw.line((rx1, y + 2, rx2, y + 2), fill=RULE, width=2)
            y += 20
            y = draw_centered_lines(draw, spec, y, lines, font, TEXT_ACCENT, 8)
            y += 16
            draw.line((rx1, y, rx2, y), fill=RULE, width=2)
            return y
        else:
            lines = wrap_text(draw, block.text, font, spec.content_width)
            x = spec.inner_margin_x
            for ln in lines:
                draw.text((x, y), ln, font=font, fill=TEXT_ACCENT)
                y += line_height(font) + 8
            if lines:
                y -= 8
            return y

    if block.kind == "paragraph":
        return draw_inline_lines(draw, spec, fonts, y, block.text, TEXT, 10, justify=True)

    if block.kind == "bullet":
        return draw_inline_lines(draw, spec, fonts, y, block.text, TEXT_MUTED, 8,
                                  x_offset=16, justify=False)

    if block.kind == "code":
        lines = block.lines or []
        h = block_height(draw, spec, fonts, block)
        draw.rounded_rectangle((rx1, y, rx2, y + h), radius=10, fill=PANEL_ALT, outline=RULE, width=1)
        ty = y + 20
        for ln in lines:
            # Unicode-aware mono rendering
            _render_run_text(draw, rx1 + 20, ty, ln, fonts.mono, fonts, TEXT_MUTED)
            ty += line_height(fonts.mono) + 7
        return y + h

    if block.kind == "rule":
        draw.line((rx1, y + 10, rx2, y + 10), fill=RULE, width=1)
        return y + 20

    if block.kind == "table":
        return draw_table(draw, spec, fonts, y, block.rows)

    raise ValueError(f"Unsupported block kind: {block.kind}")


# -----------------------------
# Long single render + PDF
# -----------------------------
def measure_total_height(blocks: Sequence[RenderBlock], spec: CanvasSpec, fonts: Fonts) -> int:
    temp_img = Image.new("RGB", (spec.width, 1000), BG)
    draw = ImageDraw.Draw(temp_img)
    y = spec.top_margin
    prev: Optional[RenderBlock] = None
    for block in blocks:
        y += block_spacing_after(prev, block, spec)
        y += block_height(draw, spec, fonts, block)
        prev = block
    return y + spec.bottom_margin


def render_single(
    blocks: Sequence[RenderBlock], out_base: Path, font_name: str, pdf: bool = True
) -> Tuple[Path, Optional[Path]]:
    spec = make_spec("single")
    fonts = make_fonts(spec, font_name)
    height = measure_total_height(blocks, spec, fonts)
    img, draw = make_base_canvas(spec, height=height)

    y = spec.top_margin
    prev: Optional[RenderBlock] = None
    for block in blocks:
        y += block_spacing_after(prev, block, spec)
        y = render_block(draw, spec, fonts, y, block)
        prev = block

    png_path = out_base.with_suffix(".png")
    img.save(png_path, "PNG", dpi=PNG_DPI)
    if pdf:
        pdf_path = out_base.with_suffix(".pdf")
        save_long_image_as_pdf(img, pdf_path)
        return png_path, pdf_path
    return png_path, None


def save_long_image_as_pdf(img: Image.Image, pdf_path: Path, page_height_px: int = 2200) -> None:
    slices: List[Image.Image] = []
    y = 0
    while y < img.height:
        crop = img.crop((0, y, img.width, min(y + page_height_px, img.height))).convert("RGB")
        slices.append(crop)
        y += page_height_px
    if not slices:
        raise ValueError("No image slices available for PDF output")
    first, rest = slices[0], slices[1:]
    first.save(pdf_path, "PDF", save_all=True, append_images=rest, resolution=150.0)


# -----------------------------
# Pagination for story/post
# -----------------------------
def paginate_blocks(blocks: Sequence[RenderBlock], mode: str, font_name: str) -> List[List[RenderBlock]]:
    spec = make_spec(mode)
    fonts = make_fonts(spec, font_name)
    temp_img = Image.new("RGB", (spec.width, spec.height or 2000), BG)
    draw = ImageDraw.Draw(temp_img)

    pages: List[List[RenderBlock]] = []
    current: List[RenderBlock] = []
    used = spec.top_margin
    prev: Optional[RenderBlock] = None
    queue: List[RenderBlock] = list(blocks)

    while queue:
        block = queue.pop(0)
        space_before = block_spacing_after(prev, block, spec)
        need = space_before + block_height(draw, spec, fonts, block)
        max_height = (spec.height or 0) - spec.bottom_margin

        if used + need <= max_height:
            current.append(block)
            used += need
            prev = block
            continue

        available = max_height - used - space_before
        head, tail = split_block_to_fit(draw, spec, fonts, block, available)
        if head is not None and head != block:
            current.append(head)
            pages.append(current)
            current = []
            prev = None
            used = spec.top_margin
            if tail is not None:
                queue.insert(0, tail)
            continue

        if current:
            pages.append(current)
            current = []
            prev = None
            used = spec.top_margin
            queue.insert(0, block)
            continue

        current.append(block)
        pages.append(current)
        current = []
        prev = None
        used = spec.top_margin

    if current:
        pages.append(current)
    return pages


def render_pages(blocks: Sequence[RenderBlock], mode: str, output_dir: Path,
                 basename: str, font_name: str) -> List[Path]:
    spec = make_spec(mode)
    fonts = make_fonts(spec, font_name)
    pages = paginate_blocks(blocks, mode, font_name)
    output_dir.mkdir(parents=True, exist_ok=True)
    rendered: List[Path] = []

    for idx, page_blocks in enumerate(pages, start=1):
        img, draw = _render_page_image(spec, fonts, page_blocks)
        suffix = "story" if mode == "story" else "post"
        out_path = output_dir / f"{basename}-{suffix}-{idx:02d}.png"
        img.save(out_path, "PNG", dpi=PNG_DPI)
        rendered.append(out_path)

    return rendered


# -----------------------------
# CLI
# -----------------------------
def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def path_stem_safe(path: Path) -> str:
    stem = path.stem.strip().lower()
    stem = re.sub(r"[^a-z0-9]+", "-", stem)
    stem = re.sub(r"-+", "-", stem).strip("-")
    return stem or "render"


def read_text_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8-sig")


def _list_fonts() -> None:
    """Print available font profiles with resolved paths."""
    print("Available font profiles:\n")
    alias_map: dict[str, list[str]] = {}
    for alias, target in FONT_ALIASES.items():
        if target not in alias_map:
            alias_map[target] = []
        alias_map[target].append(alias)
    for key in sorted(FONT_PROFILES):
        profile = FONT_PROFILES[key]
        aliases = alias_map.get(key, [])
        alias_str = f"  aliases: {', '.join(sorted(aliases))}" if aliases else ""
        print(f"  {key}  ({profile.label}){alias_str}")
        for style_name, paths in [
            ("body", profile.body),
            ("bold", profile.bold),
            ("italic", profile.italic),
            ("bold_italic", profile.bold_italic),
            ("mono", profile.mono),
        ]:
            if not paths:
                continue
            exists = [p for p in paths if os.path.exists(p)]
            status = "OK" if exists else "MISSING"
            print(f"    {style_name}: {status}  {paths[0]}")
        print()
    print(f"Default: {DEFAULT_FONT_PROFILE_KEY}")
    print(f"Env override: {_FONT_NAME_ENV}=<name>  {_FONT_OVERRIDE_ENV}=<path>")


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Render markdown into a dark amber styled long PNG/PDF and optional story/post slides."
    )
    p.add_argument("input", nargs="?", default=None, help="Path to input markdown file (omit with --font to list fonts)")
    p.add_argument("-o", "--output-dir", default="./render.out", help="Output directory")
    p.add_argument("--base-name", default=None, help="Base output name")
    p.add_argument(
        "--font",
        default=os.environ.get(_FONT_NAME_ENV, DEFAULT_FONT_PROFILE_KEY),
        help=f"Font profile for main text (default: {DEFAULT_FONT_PROFILE_KEY}; options: {font_choices_help()})",
    )
    p.add_argument("--single", action="store_true", help="Render one long PNG and PDF")
    p.add_argument("--stories", action="store_true", help="Render 1080x1920 story slides")
    p.add_argument("--posts", action="store_true", help="Render 1080x1080 post slides")
    p.add_argument("--all", action="store_true", help="Equivalent to --single --stories --posts")
    p.add_argument("--count", type=int, default=None, metavar="N",
                   help="Exact number of story/post slides (redistributes content to fit)")
    p.add_argument("--max-count", type=int, default=None, metavar="N",
                   help="Maximum number of story/post slides (budgets content if natural pagination exceeds N)")
    p.add_argument("--cover", action="store_true",
                   help="Prepend a standalone cover slide (title + subtitle from doc header)")
    p.add_argument("--by-section", action="store_true",
                   help="Split by headings and render each section independently")
    p.add_argument("--section-level", default="auto", metavar="N|auto",
                   help="Heading level to split on for --by-section (default: auto). "
                        "Auto detects the highest heading level that appears more than once.")
    p.add_argument("--pdf", action="store_true",
                   help="Also generate PDF output (applies to --single and --by-section)")
    p.add_argument("--stdout-summary", action="store_true", help="Print generated file paths one per line")
    p.add_argument("--preview", action="store_true",
                   help="Dry run: print pagination stats (slide counts per section) without rendering")
    p.add_argument("--slide-footer", action="store_true",
                   help="Add slide number and doc title footer to each story/post slide")
    return p


def split_by_section(raw_blocks: List[RawBlock], section_level: int) -> List[Tuple[str, List[RenderBlock]]]:
    """Split raw blocks into sections at the given heading level.

    Returns list of (section_title, compiled_blocks) pairs.
    Content before the first heading at the target level goes into a
    section titled from the first H1 if present, else "intro".
    """
    sections: List[Tuple[str, List[RawBlock]]] = []
    current_title: Optional[str] = None
    current_blocks: List[RawBlock] = []
    first_h1: Optional[str] = None
    seen_section_level = False
    pending_superheading = False

    for block in raw_blocks:
        if block.kind == "heading":
            if block.level == 1 and first_h1 is None:
                first_h1 = block.text
            # A heading at exactly section_level starts a new section. Keep the
            # heading itself so section renders visibly at the top of its output.
            if block.level == section_level:
                if current_blocks and not pending_superheading:
                    sections.append((current_title or "intro", current_blocks))
                current_title = block.text
                if pending_superheading:
                    current_blocks.append(block)
                else:
                    current_blocks = [block]
                seen_section_level = True
                pending_superheading = False
                continue
            # A heading ABOVE section_level (lower level number) also starts a
            # new section once section-level headings have begun. The heading is
            # carried forward so chapter titles render above the next section.
            if block.level < section_level and seen_section_level:
                if current_blocks:
                    sections.append((current_title or "intro", current_blocks))
                current_title = block.text
                current_blocks = [block]
                pending_superheading = True
                continue
        current_blocks.append(block)

    if current_blocks:
        # If no section-level heading was found at all, treat the whole
        # document as one section (titled from H1 or "full").
        if not sections and current_title is None:
            current_title = first_h1 or "full"
        sections.append((current_title or "intro", current_blocks))

    # Compile each section's raw blocks into render blocks
    result: List[Tuple[str, List[RenderBlock]]] = []
    for title, blocks in sections:
        compiled = compile_blocks(blocks)
        if compiled:
            result.append((title, compiled))
    return result


def _slug_from_title(title: str) -> str:
    t = title.strip()
    # Strip leading patterns: "1.1 Title", "PART 2: Title", "2 - Title".
    t = re.sub(
        r"^(?:part\s+\d+\s*[:\-—–]?\s*|\d+\.\d+\s*[:\-—–]?\s*|\d+\s*[:\-—–]\s*)",
        "",
        t,
        flags=re.IGNORECASE,
    )
    slug = re.sub(r"[^a-z0-9]+", "-", t.strip().lower()).strip("-")
    slug = slug[:32].rstrip("-")
    return slug or "section"


def merge_pages(pages: List[List[RenderBlock]], target_count: int) -> List[List[RenderBlock]]:
    """Merge paginated slides down to target_count by combining adjacent pages."""
    if target_count <= 0 or len(pages) <= target_count:
        return pages
    n = len(pages)
    # Distribute original pages across target_count slots as evenly as possible
    merged: List[List[RenderBlock]] = []
    per_slot = n / target_count
    idx = 0
    for slot in range(target_count):
        start = int(round(slot * per_slot))
        end = int(round((slot + 1) * per_slot))
        combined: List[RenderBlock] = []
        for i in range(start, min(end, n)):
            combined.extend(pages[i])
        if combined:
            merged.append(combined)
    return merged if merged else pages


def count_paginate_preserving_content(
    blocks: Sequence[RenderBlock],
    mode: str,
    font_name: str,
    target_count: int,
    is_max: bool = False,
) -> Tuple[List[List[RenderBlock]], bool]:
    """Chunk document into target_count groups using semantic section boundaries.

    Uses document hierarchy (H1 parts → H2 subsections → H3) to find natural
    chunk boundaries. All content is preserved — no truncation, no ellipsis
    markers. Each chunk renders at variable height to fit its assigned content.

    Returns (chunks, variable_height). variable_height=True means each chunk
    will grow its canvas to fit rather than clipping at a fixed canvas size.
    """
    if target_count <= 0:
        return list(paginate_blocks(blocks, mode, font_name)), False

    block_list = list(blocks)
    if not block_list:
        return [], False

    # For --max-count: if natural pagination already fits, use it unchanged
    if is_max:
        natural_pages = paginate_blocks(block_list, mode, font_name)
        if len(natural_pages) <= target_count:
            return natural_pages, False

    chunks = _semantic_chunks(block_list, target_count)
    return chunks, True


def _measure_page_height(
    draw: ImageDraw.ImageDraw,
    spec: CanvasSpec,
    fonts: Fonts,
    page_blocks: Sequence[RenderBlock],
) -> int:
    """Measure total page height including top and bottom margins."""
    y = spec.top_margin
    prev: Optional[RenderBlock] = None
    for block in page_blocks:
        y += block_spacing_after(prev, block, spec)
        y += block_height(draw, spec, fonts, block)
        prev = block
    return y + spec.bottom_margin


def _slide_start_y(
    draw: ImageDraw.ImageDraw,
    spec: CanvasSpec,
    fonts: Fonts,
    page_blocks: Sequence[RenderBlock],
) -> int:
    """Return the starting y for a fixed-height slide, centering sparse content."""
    if spec.height is None:
        return spec.top_margin
    measured_height = _measure_page_height(draw, spec, fonts, page_blocks)
    content_height = measured_height - spec.top_margin - spec.bottom_margin
    if content_height < spec.height * 0.70:
        centered = (spec.height - content_height) // 2
        return max(centered, spec.top_margin)
    return spec.top_margin


def _page_fits(
    draw: ImageDraw.ImageDraw,
    spec: CanvasSpec,
    fonts: Fonts,
    page_blocks: Sequence[RenderBlock],
) -> bool:
    """Return True if the measured page fits in the fixed-height canvas."""
    return _measure_page_height(draw, spec, fonts, page_blocks) <= (spec.height or 999999)


def _check_page_overflow(
    spec: CanvasSpec,
    fonts: Fonts,
    page_blocks: List[RenderBlock],
    page_idx: int,
) -> None:
    """Warn if a page's content will overflow the canvas height."""
    temp = Image.new("RGB", (spec.width, spec.height or 2000), BG)
    draw = ImageDraw.Draw(temp)
    content_h = _measure_page_height(draw, spec, fonts, page_blocks)
    max_h = spec.height or 999999
    if content_h > max_h:
        print(
            f"  [oracle-render] WARNING: slide {page_idx} content height {content_h}px "
            f"exceeds canvas {max_h}px - {content_h - max_h}px will be clipped. "
            f"Use --max-count with a higher value or --by-section.",
            file=sys.stderr,
        )


def _render_page_image(
    spec: CanvasSpec,
    fonts: Fonts,
    page_blocks: Sequence[RenderBlock],
    *,
    variable_height: bool = False,
) -> Tuple[Image.Image, ImageDraw.ImageDraw]:
    """Create and draw one slide/page, growing height when requested."""
    temp = Image.new("RGB", (spec.width, spec.height or 2000), BG)
    temp_draw = ImageDraw.Draw(temp)
    measured_height = _measure_page_height(temp_draw, spec, fonts, page_blocks)
    if variable_height and spec.height is not None:
        height = max(spec.height, measured_height)
    else:
        height = spec.height or 2000

    img, draw = make_base_canvas(spec, height=height)
    y = _slide_start_y(draw, spec, fonts, page_blocks) if height == (spec.height or height) else spec.top_margin
    prev: Optional[RenderBlock] = None
    for block in page_blocks:
        y += block_spacing_after(prev, block, spec)
        y = render_block(draw, spec, fonts, y, block)
        prev = block
    return img, draw


def _section_word_count(blocks: List[RenderBlock]) -> int:
    """Count approximate words in a list of render blocks."""
    total = 0
    for block in blocks:
        if block.kind in ("paragraph", "bullet"):
            total += len(block.text.split())
        elif block.kind == "heading":
            total += len(block.text.split()) * 3
        elif block.kind == "table" and block.rows:
            total += sum(len(" ".join(row).split()) for row in block.rows)
        elif block.kind == "code" and block.lines:
            total += sum(len(line.split()) for line in block.lines)
    return max(total, 1)


def _split_into_logical_sections(
    blocks: List[RenderBlock],
) -> List[List[RenderBlock]]:
    """Group render blocks into logical sections by heading level.

    A new section starts at every H1 or H2 heading. Content before the first
    heading is its own section. Returns a list of block lists, each starting
    with its heading block (except possibly the first).
    """
    sections: List[List[RenderBlock]] = []
    current: List[RenderBlock] = []
    for block in blocks:
        if block.kind == "heading" and block.level <= 2:
            if current:
                sections.append(current)
            current = [block]
        else:
            current.append(block)
    if current:
        sections.append(current)
    return sections if sections else [blocks]


def _coalesce_sections_for_budget(
    sections: List[List[RenderBlock]],
    target_count: int,
) -> List[List[RenderBlock]]:
    """Merge adjacent logical sections when there are more sections than slides."""
    if target_count <= 0 or len(sections) <= target_count:
        return sections

    weights = [_section_word_count(section) for section in sections]
    total_weight = sum(weights)
    target_weight = total_weight / target_count if target_count else total_weight
    merged: List[List[RenderBlock]] = []
    current: List[RenderBlock] = []
    current_weight = 0.0

    for idx, section in enumerate(sections):
        current.extend(section)
        current_weight += weights[idx]
        remaining_sections = len(sections) - idx - 1
        remaining_groups = target_count - len(merged) - 1
        should_close = current_weight >= target_weight
        must_close = remaining_sections == remaining_groups
        if len(merged) < target_count - 1 and remaining_sections >= remaining_groups:
            if should_close or must_close:
                merged.append(current)
                current = []
                current_weight = 0.0

    if current:
        merged.append(current)

    while len(merged) > target_count:
        idx = min(range(len(merged)), key=lambda i: _section_word_count(merged[i]))
        if idx == 0:
            merged[1] = merged[0] + merged[1]
            del merged[0]
        else:
            merged[idx - 1].extend(merged[idx])
            del merged[idx]

    return merged


# -----------------------------
# Semantic chunking for --count
# -----------------------------

def _split_by_h1_parts(blocks: List[RenderBlock]) -> List[List[RenderBlock]]:
    """Split render blocks into sections at H1 boundaries.

    The document title H1 (no body content yet) is attached to the first
    substantive section rather than becoming its own one-heading chunk.
    """
    parts: List[List[RenderBlock]] = []
    current: List[RenderBlock] = []
    for block in blocks:
        if block.kind == "heading" and block.level == 1:
            if current:
                has_body = any(b.kind != "heading" for b in current)
                if has_body:
                    parts.append(current)
                    current = [block]
                else:
                    # Only headings so far — append and keep building
                    current.append(block)
            else:
                current.append(block)
        else:
            current.append(block)
    if current:
        parts.append(current)
    return parts if len(parts) > 1 else [list(blocks)]


def _split_section_at_h2(section: List[RenderBlock]) -> List[List[RenderBlock]]:
    """Split a section at H2 boundaries. Returns [section] if no H2 found."""
    subsections: List[List[RenderBlock]] = []
    current: List[RenderBlock] = []
    for block in section:
        if block.kind == "heading" and block.level == 2:
            if current:
                subsections.append(current)
            current = [block]
        else:
            current.append(block)
    if current:
        subsections.append(current)
    return subsections if len(subsections) > 1 else [section]


def _split_section_at_h3(section: List[RenderBlock]) -> List[List[RenderBlock]]:
    """Split a section at H3 boundaries. Returns [section] if no H3 found."""
    subsections: List[List[RenderBlock]] = []
    current: List[RenderBlock] = []
    for block in section:
        if block.kind == "heading" and block.level == 3:
            if current:
                subsections.append(current)
            current = [block]
        else:
            current.append(block)
    if current:
        subsections.append(current)
    return subsections if len(subsections) > 1 else [section]


def _expand_sections(
    sections: List[List[RenderBlock]],
    target_count: int,
    split_fn,
) -> List[List[RenderBlock]]:
    """Expand the largest splittable section using split_fn, repeatedly, until
    we reach target_count or no further splits are possible."""
    result = list(sections)
    while len(result) < target_count:
        best_idx: Optional[int] = None
        best_weight = 0
        for i, section in enumerate(result):
            parts = split_fn(section)
            if len(parts) > 1:
                w = _section_word_count(section)
                if w > best_weight:
                    best_weight = w
                    best_idx = i
        if best_idx is None:
            break
        subsections = split_fn(result[best_idx])
        result = result[:best_idx] + subsections + result[best_idx + 1:]
    return result


def _fix_trailing_headings(chunks: List[List[RenderBlock]]) -> List[List[RenderBlock]]:
    """Move any trailing heading at the end of a chunk to the start of the next."""
    result = [list(c) for c in chunks]
    for i in range(len(result) - 1):
        while result[i] and result[i][-1].kind == "heading":
            result[i + 1].insert(0, result[i].pop())
    return [c for c in result if c]


def _semantic_chunks(
    blocks: List[RenderBlock],
    target_count: int,
) -> List[List[RenderBlock]]:
    """Group blocks into target_count semantic chunks using document hierarchy.

    Priority order:
    1. H1-level sections as primary boundaries
    2. If more sections than N, merge adjacent by word count
    3. If fewer sections than N, split large sections at H2, then H3
    """
    parts = _split_by_h1_parts(blocks)

    if len(parts) >= target_count:
        merged = _coalesce_sections_for_budget(parts, target_count) if len(parts) > target_count else parts
        return _fix_trailing_headings(merged)

    # Expand at H2 first
    expanded = _expand_sections(parts, target_count, _split_section_at_h2)

    if len(expanded) > target_count:
        merged = _coalesce_sections_for_budget(expanded, target_count)
        return _fix_trailing_headings(merged)
    if len(expanded) == target_count:
        return _fix_trailing_headings(expanded)

    # Still short — expand at H3
    expanded2 = _expand_sections(expanded, target_count, _split_section_at_h3)

    if len(expanded2) > target_count:
        merged = _coalesce_sections_for_budget(expanded2, target_count)
        return _fix_trailing_headings(merged)
    return _fix_trailing_headings(expanded2)


def _append_continuation_marker(
    page_blocks: List[RenderBlock],
    spec: CanvasSpec,
    fonts: Fonts,
    marker: RenderBlock,
) -> List[RenderBlock]:
    """Append a soft truncation marker, dropping trailing blocks if needed."""
    temp = Image.new("RGB", (spec.width, spec.height or 2000), BG)
    draw = ImageDraw.Draw(temp)
    candidate_base = list(page_blocks)

    while candidate_base:
        candidate = candidate_base + [marker]
        if _page_fits(draw, spec, fonts, candidate):
            return candidate
        if len(candidate_base) == 1:
            break
        candidate_base.pop()

    marker_only = [marker]
    if _page_fits(draw, spec, fonts, marker_only):
        return marker_only
    return candidate_base or page_blocks


def budget_paginate(
    blocks: Sequence[RenderBlock],
    mode: str,
    font_name: str,
    target_count: int,
    is_max: bool = False,
) -> List[List[RenderBlock]]:
    """Paginate with a slide-count constraint using section budgets.

    Unlike merge_pages(), this never intentionally overflows a canvas. When
    content must be shortened, the last retained page in that section receives
    a soft continuation marker.
    """
    natural_pages = paginate_blocks(blocks, mode, font_name)
    if not natural_pages:
        return natural_pages
    if is_max and len(natural_pages) <= target_count:
        return natural_pages
    if len(natural_pages) <= target_count:
        return natural_pages

    sections = _split_into_logical_sections(list(blocks))
    sections = _coalesce_sections_for_budget(sections, target_count)
    if not sections:
        return natural_pages

    section_pages = [paginate_blocks(section, mode, font_name) for section in sections]
    word_counts = [_section_word_count(section) for section in sections]
    budgets = [1 for _ in sections]
    remaining = max(0, target_count - len(budgets))

    while remaining > 0:
        candidates = [
            i for i, pages_for_section in enumerate(section_pages)
            if budgets[i] < len(pages_for_section)
        ]
        if not candidates:
            break
        idx = max(
            candidates,
            key=lambda i: (
                word_counts[i] / max(budgets[i], 1),
                len(section_pages[i]) - budgets[i],
                word_counts[i],
            ),
        )
        budgets[idx] += 1
        remaining -= 1

    spec = make_spec(mode)
    fonts = make_fonts(spec, font_name)
    continuation = RenderBlock(kind="paragraph", text="· · ·")

    output_pages: List[List[RenderBlock]] = []
    for pages_for_section, budget in zip(section_pages, budgets):
        if len(pages_for_section) <= budget:
            output_pages.extend(pages_for_section)
            continue

        kept = [list(page) for page in pages_for_section[:budget]]
        kept[-1] = _append_continuation_marker(kept[-1], spec, fonts, continuation)
        output_pages.extend(kept)

    return output_pages[:target_count]


def _render_slide_footer(
    draw: ImageDraw.ImageDraw,
    spec: CanvasSpec,
    fonts: Fonts,
    page_num: int,
    total_pages: int,
    doc_title: str,
    canvas_height: Optional[int] = None,
) -> None:
    """Draw a subtle footer at the bottom of a slide canvas."""
    text = f"{page_num} / {total_pages}  ·  {doc_title[:40]}"
    y = (canvas_height or spec.height or 1920) - spec.bottom_margin + 18
    x = spec.inner_margin_x
    draw.text((x, y), text, font=fonts.meta, fill=TEXT_MUTED)


def render_blocks_with_count(
    blocks: Sequence[RenderBlock], mode: str, output_dir: Path,
    basename: str, font_name: str,
    exact_count: Optional[int] = None,
    max_count: Optional[int] = None,
    doc_title: str = "",
) -> List[Path]:
    """Like render_pages but respects --count and --max-count."""
    variable_height = False
    if exact_count is not None and exact_count > 0:
        pages, variable_height = count_paginate_preserving_content(
            blocks, mode, font_name, exact_count, is_max=False,
        )
    elif max_count is not None and max_count > 0:
        pages, variable_height = count_paginate_preserving_content(
            blocks, mode, font_name, max_count, is_max=True,
        )
    else:
        pages = paginate_blocks(blocks, mode, font_name)

    output_dir.mkdir(parents=True, exist_ok=True)
    rendered: List[Path] = []
    spec = make_spec(mode)
    fonts = make_fonts(spec, font_name)

    for idx, page_blocks in enumerate(pages, start=1):
        if not variable_height:
            _check_page_overflow(spec, fonts, page_blocks, idx)
        img, draw = _render_page_image(
            spec, fonts, page_blocks, variable_height=variable_height,
        )
        if doc_title:
            _render_slide_footer(
                draw, spec, fonts, idx, len(pages), doc_title,
                canvas_height=img.height,
            )
        suffix = "story" if mode == "story" else "post"
        out_path = output_dir / f"{basename}-{suffix}-{idx:02d}.png"
        img.save(out_path, "PNG", dpi=PNG_DPI)
        rendered.append(out_path)

    return rendered


def _render_section(
    section_title: str,
    section_blocks: List[RenderBlock],
    base_name: str,
    font_name: str,
    output_dir: Path,
    do_single: bool,
    do_stories: bool,
    do_posts: bool,
    exact_count: Optional[int],
    max_count: Optional[int],
    doc_title: str = "",
    pdf: bool = True,
) -> List[Path]:
    """Render a single section's blocks in the requested formats."""
    section_slug = _slug_from_title(section_title)
    section_base = f"{base_name}-{section_slug}"
    generated: List[Path] = []

    if do_single:
        single_base = output_dir / section_base
        png_path, pdf_path = render_single(section_blocks, single_base, font_name, pdf=pdf)
        generated.extend(p for p in [png_path, pdf_path] if p is not None)

    if do_stories:
        story_dir = output_dir / f"{section_base}-stories"
        generated.extend(render_blocks_with_count(
            section_blocks, "story", story_dir, section_base, font_name,
            exact_count=exact_count, max_count=max_count, doc_title=doc_title,
        ))

    if do_posts:
        post_dir = output_dir / f"{section_base}-posts"
        generated.extend(render_blocks_with_count(
            section_blocks, "post", post_dir, section_base, font_name,
            exact_count=exact_count, max_count=max_count, doc_title=doc_title,
        ))

    return generated


def _print_preview(
    raw_blocks: List[RawBlock],
    render_blocks: List[RenderBlock],
    font_name: str,
    by_section: bool,
    section_level: int,
    exact_count: Optional[int],
    max_count: Optional[int],
) -> None:
    """Print slide count estimates without rendering."""
    for mode in ("story", "post"):
        spec = make_spec(mode)
        print(f"\n[{mode.upper()} - {spec.width}x{spec.height}]")
        if by_section:
            sections = split_by_section(raw_blocks, section_level)
            total = 0
            for title, sec_blocks in sections:
                natural = paginate_blocks(sec_blocks, mode, font_name)
                print(f"  {title[:50]:<52} {len(natural):>3} slide(s)")
                total += len(natural)
            print(f"  {'TOTAL':<52} {total:>3} slide(s)")
            continue

        natural = paginate_blocks(render_blocks, mode, font_name)
        effective = natural
        if exact_count:
            effective, _ = count_paginate_preserving_content(
                render_blocks, mode, font_name, exact_count, is_max=False,
            )
        elif max_count:
            effective, _ = count_paginate_preserving_content(
                render_blocks, mode, font_name, max_count, is_max=True,
            )
        print(f"  {'full document':<52} {len(natural):>3} natural slide(s)")
        if exact_count or max_count:
            label = f"--count {exact_count}" if exact_count else f"--max-count {max_count}"
            print(f"  {label:<52} {len(effective):>3} effective slide(s)")

        logical_sections = _split_into_logical_sections(render_blocks)
        if len(logical_sections) > 1:
            print("  sections:")
            for section in logical_sections:
                title = "intro"
                for block in section:
                    if block.kind == "heading" and block.text:
                        title = block.text
                        break
                count = len(paginate_blocks(section, mode, font_name))
                print(f"    {title[:48]:<50} {count:>3} slide(s)")


def make_cover_blocks(raw_blocks: List[RawBlock]) -> List[RenderBlock]:
    """Extract title + first subtitle/paragraph for a cover slide."""
    cover_raw: List[RawBlock] = []
    for block in raw_blocks:
        if block.kind == "heading" and block.level == 1:
            cover_raw.append(block)
            break

    found_h1 = False
    for block in raw_blocks:
        if block.kind == "heading" and block.level == 1:
            found_h1 = True
            continue
        if found_h1 and block.kind == "paragraph" and block.text.strip():
            cover_raw.append(block)
            break
    return compile_blocks(cover_raw)


def _detect_section_level(raw_blocks: List[RawBlock]) -> int:
    """Detect the most useful heading level for --by-section.

    Returns the HIGHEST heading level (lowest number) that appears more than
    once — that is, the level where the document's major sections live.
    For a document with H1 PART headings (e.g. PART 1 … PART 6), this returns 1.
    For a typical reading post with H1 title + H2 sections, this returns 2.
    """
    from collections import Counter

    level_counts = Counter()
    for block in raw_blocks:
        if block.kind == "heading":
            level_counts[block.level] += 1

    # Prefer the minimum heading level (highest in hierarchy) that occurs > 1 time
    candidates = sorted(lvl for lvl, cnt in level_counts.items() if cnt > 1)
    if candidates:
        return candidates[0]
    if level_counts:
        return min(level_counts.keys())
    return 2


def main(argv=None) -> int:
    args = build_arg_parser().parse_args(argv)

    # --font with no input: list available fonts
    if args.input is None:
        _list_fonts()
        return 0

    input_path = Path(args.input).expanduser().resolve()
    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")
    try:
        font_name = resolve_font_profile_name(args.font)
    except ValueError as exc:
        raise SystemExit(str(exc))

    exact_count = args.count
    max_count = args.max_count
    has_count = (exact_count is not None) or (max_count is not None)
    has_format = args.single or args.stories or args.posts or args.all

    # When a count is given with no explicit format, default to stories mode.
    if has_count and not has_format:
        do_single = False
        do_stories = True
        do_posts = False
    elif args.all:
        do_single = True
        do_stories = True
        do_posts = True
    else:
        do_single = args.single or not has_format
        do_stories = args.stories
        do_posts = args.posts
    by_section = args.by_section
    raw_section_level = args.section_level

    if exact_count is not None and exact_count <= 0:
        raise SystemExit("--count must be a positive integer")
    if max_count is not None and max_count <= 0:
        raise SystemExit("--max-count must be a positive integer")
    if exact_count is not None and max_count is not None:
        raise SystemExit("Cannot specify both --count and --max-count")

    base_name = base_name_for_font(args.base_name or path_stem_safe(input_path), font_name)
    markdown = _preprocess_text(read_text_file(input_path))
    raw_blocks = parse_markdown(markdown)
    render_blocks = compile_blocks(raw_blocks)
    if not render_blocks:
        raise SystemExit("No renderable content found in markdown file")

    if raw_section_level == "auto":
        section_level = _detect_section_level(raw_blocks)
        print(f"  [oracle-render] --section-level auto -> detected level {section_level}")
    else:
        try:
            section_level = int(raw_section_level)
        except ValueError:
            raise SystemExit(
                f"--section-level must be a positive integer or 'auto', got: {raw_section_level!r}"
            )
        if section_level <= 0:
            raise SystemExit("--section-level must be a positive integer")

    if args.preview:
        _print_preview(
            raw_blocks, render_blocks, font_name, by_section, section_level,
            exact_count, max_count,
        )
        return 0

    output_dir = Path(args.output_dir).expanduser().resolve()
    ensure_dir(output_dir)

    doc_title = ""
    if args.slide_footer:
        for block in raw_blocks:
            if block.kind == "heading" and block.level == 1:
                doc_title = block.text[:40]
                break

    generated: List[Path] = []

    if args.cover and not by_section:
        cover_blocks = make_cover_blocks(raw_blocks)
        if cover_blocks:
            for mode, flag in (("story", do_stories), ("post", do_posts)):
                if not flag:
                    continue
                cover_dir = output_dir / f"{base_name}-cover"
                generated.extend(render_blocks_with_count(
                    cover_blocks, mode, cover_dir, f"{base_name}-cover",
                    font_name, exact_count=1, doc_title=doc_title,
                ))

    if by_section:
        sections = split_by_section(raw_blocks, section_level)
        if not sections:
            raise SystemExit(f"No sections found at heading level {section_level}")

        # Detect a preamble: the first section is a preamble if it contains no
        # heading at the detected section_level — meaning it's the bucket of
        # content that preceded the first real section heading (doc title + metadata).
        def _is_preamble(sec_blocks: List[RenderBlock]) -> bool:
            return not any(
                b.kind == "heading" and b.level == section_level for b in sec_blocks
            )

        sections_to_render = list(sections)
        if sections_to_render and _is_preamble(sections_to_render[0][1]):
            preamble_title, preamble_blocks = sections_to_render.pop(0)
            if args.cover:
                # Render preamble as a standalone cover section
                generated.extend(_render_section(
                    preamble_title, preamble_blocks, base_name, font_name, output_dir,
                    do_single, do_stories, do_posts, exact_count, max_count,
                    doc_title=doc_title, pdf=args.pdf,
                ))
            elif sections_to_render:
                # Fold preamble blocks into the top of the first content section
                first_title, first_blocks = sections_to_render[0]
                sections_to_render[0] = (first_title, preamble_blocks + first_blocks)
            # If cover=False and no sections follow, preamble is silently dropped.

        for section_title, section_blocks in sections_to_render:
            # Skip heading-only sections (chapter titles with no body content).
            if all(b.kind == "heading" for b in section_blocks):
                continue
            generated.extend(_render_section(
                section_title, section_blocks, base_name, font_name, output_dir,
                do_single, do_stories, do_posts, exact_count, max_count,
                doc_title=doc_title, pdf=args.pdf,
            ))
    else:
        if do_single:
            single_base = output_dir / f"{base_name}-single"
            png_path, pdf_path = render_single(render_blocks, single_base, font_name, pdf=args.pdf)
            generated.extend(p for p in [png_path, pdf_path] if p is not None)

        if do_stories:
            story_dir = output_dir / f"{base_name}-stories"
            generated.extend(render_blocks_with_count(
                render_blocks, "story", story_dir, base_name, font_name,
                exact_count=exact_count, max_count=max_count, doc_title=doc_title,
            ))

        if do_posts:
            post_dir = output_dir / f"{base_name}-posts"
            generated.extend(render_blocks_with_count(
                render_blocks, "post", post_dir, base_name, font_name,
                exact_count=exact_count, max_count=max_count, doc_title=doc_title,
            ))

    if args.stdout_summary:
        for path in generated:
            print(path)
    else:
        print(f"Rendered {len(generated)} file(s) into: {output_dir}")
        for path in generated:
            print(f"  {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
