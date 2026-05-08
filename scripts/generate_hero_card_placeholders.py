from __future__ import annotations

import json
import textwrap
from html import escape
from pathlib import Path
import re
from PIL import Image, ImageDraw, ImageFont


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output" / "card_placeholders" / "heroes"

CARD_W = 750
CARD_H = 1050
PRIMARY_GOLD = "#c9a84c"
DEEP_GOLD = "#8b6d21"
INK = "#241d12"
PAPER = "#f6f0e4"
PANEL = "#ece2cb"
HERO_NAME_BASE_SIZE = 116
HERO_NAME_MAX_WIDTH = 540


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def hero_name_font_size(name: str) -> int:
    try:
        font = ImageFont.truetype(r"C:\Windows\Fonts\timesbd.ttf", HERO_NAME_BASE_SIZE)
    except OSError:
        return HERO_NAME_BASE_SIZE

    draw = ImageDraw.Draw(Image.new("RGB", (2000, 400)))
    bbox = draw.textbbox((0, 0), name, font=font)
    width = bbox[2] - bbox[0]
    if width <= HERO_NAME_MAX_WIDTH:
        return HERO_NAME_BASE_SIZE

    scale = HERO_NAME_MAX_WIDTH / max(1, width)
    return max(42, int(HERO_NAME_BASE_SIZE * scale))


def clean_text(text: str) -> str:
    try:
        repaired = text.encode("latin-1").decode("utf-8")
        if repaired.count("�") == 0:
            text = repaired
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass

    replacements = {
        "â€™": "'",
        "’": "'",
        "â€œ": '"',
        "“": '"',
        "â€": '"',
        "”": '"',
        "â€“": "-",
        "–": "-",
        "â€”": "-",
        "—": "-",
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    return text


def wrap_lines(text: str, width: int, limit: int) -> list[str]:
    return textwrap.wrap(clean_text(text), width=width)[:limit]


def icon_svg(x: int, y: int, scale: float, color: str, stroke: str) -> str:
    return f"""
    <g transform="translate({x},{y}) scale({scale})">
      <path d="M0 -58 C18 -48 30 -28 30 -6 C30 22 10 42 0 58 C-10 42 -30 22 -30 -6 C-30 -28 -18 -48 0 -58 Z" fill="{color}"/>
      <circle cx="0" cy="-6" r="12" fill="{stroke}"/>
      <path d="M-48 -4 C-44 18 -32 34 -18 46" fill="none" stroke="{color}" stroke-width="10" stroke-linecap="round"/>
      <path d="M48 -4 C44 18 32 34 18 46" fill="none" stroke="{color}" stroke-width="10" stroke-linecap="round"/>
      <path d="M-54 6 C-48 18 -42 28 -32 34" fill="none" stroke="{color}" stroke-width="8" stroke-linecap="round"/>
      <path d="M54 6 C48 18 42 28 32 34" fill="none" stroke="{color}" stroke-width="8" stroke-linecap="round"/>
    </g>
    """


def hero_emblem_svg(slot: dict, x: int, y: int, scale: float, color: str, stroke: str) -> str:
    hero_id = slot["legacy_id"]
    if hero_id == "aragorn":
        return f"""
        <g transform="translate({x},{y}) scale({scale})">
          <path d="M-54 18 C-26 -18 10 -34 54 -26" fill="none" stroke="{color}" stroke-width="10" stroke-linecap="round" opacity="0.34"/>
          <path d="M-28 -48 C-54 0 -56 36 -30 84" fill="none" stroke="{color}" stroke-width="10" stroke-linecap="round" opacity="0.34"/>
          <path d="M-28 -48 C-4 0 -2 36 -28 84" fill="none" stroke="{stroke}" stroke-width="4" stroke-linecap="round" opacity="0.28"/>
        </g>
        """
    if hero_id == "legolas":
        return f"""
        <g transform="translate({x},{y}) scale({scale})">
          <circle cx="0" cy="0" r="54" fill="none" stroke="{color}" stroke-width="10" opacity="0.3"/>
          <path d="M0 -54 V54 M-52 0 H52" fill="none" stroke="{stroke}" stroke-width="8" stroke-linecap="round" opacity="0.24"/>
          <path d="M-14 -66 L0 -92 L14 -66" fill="none" stroke="{color}" stroke-width="8" stroke-linecap="round" opacity="0.38"/>
        </g>
        """
    if hero_id == "gandalf":
        return f"""
        <g transform="translate({x},{y}) scale({scale})">
          <circle cx="0" cy="0" r="56" fill="none" stroke="{color}" stroke-width="10" opacity="0.3"/>
          <circle cx="0" cy="-6" r="12" fill="{color}" opacity="0.28"/>
          <path d="M-20 -18 C-6 -46 10 -56 28 -58 C22 -40 18 -24 20 -4" fill="none" stroke="{color}" stroke-width="10" stroke-linecap="round" opacity="0.38"/>
        </g>
        """
    if hero_id == "galadriel":
        return f"""
        <g transform="translate({x},{y}) scale({scale})">
          <path d="M0 -60 V56" fill="none" stroke="{color}" stroke-width="10" stroke-linecap="round" opacity="0.34"/>
          <path d="M0 -60 L-24 -24 M0 -60 L24 -24" fill="none" stroke="{color}" stroke-width="9" stroke-linecap="round" opacity="0.34"/>
          <path d="M0 -18 C18 -8 26 10 22 30 C18 48 4 62 -14 66 C-2 50 2 32 -2 12 C-6 -2 -14 -12 -24 -18" fill="none" stroke="{color}" stroke-width="8" stroke-linecap="round" opacity="0.38"/>
        </g>
        """
    if hero_id == "frodo":
        return f"""
        <g transform="translate({x},{y}) scale({scale})">
          <path d="M-38 6 C-18 -28 8 -40 36 -34" fill="none" stroke="{color}" stroke-width="10" stroke-linecap="round" opacity="0.34"/>
          <path d="M-34 0 C-8 18 18 18 42 0" fill="none" stroke="{color}" stroke-width="10" stroke-linecap="round" opacity="0.3"/>
          <path d="M-10 58 L8 24 L30 58" fill="none" stroke="{stroke}" stroke-width="8" stroke-linecap="round" opacity="0.22"/>
        </g>
        """
    if hero_id == "boromir":
        return f"""
        <g transform="translate({x},{y}) scale({scale})">
          <circle cx="-12" cy="6" r="44" fill="none" stroke="{color}" stroke-width="10" opacity="0.34"/>
          <path d="M16 -48 L54 52" fill="none" stroke="{color}" stroke-width="10" stroke-linecap="round" opacity="0.34"/>
          <path d="M10 -44 L30 -74 L42 -40" fill="{color}" opacity="0.18"/>
        </g>
        """
    if hero_id == "nazgul":
        return f"""
        <g transform="translate({x},{y}) scale({scale})">
          <circle cx="0" cy="0" r="54" fill="none" stroke="{color}" stroke-width="10" opacity="0.3"/>
          <path d="M0 -58 V56 M0 -58 L-22 -24 M0 -58 L22 -24" fill="none" stroke="{color}" stroke-width="10" stroke-linecap="round" opacity="0.34"/>
        </g>
        """
    if hero_id == "saruman":
        return f"""
        <g transform="translate({x},{y}) scale({scale})">
          <path d="M-18 54 C-44 18 -40 -26 -8 -54 C12 -38 24 -18 28 8 C32 34 24 52 6 68" fill="{color}" opacity="0.14"/>
          <path d="M-8 -42 C10 -62 28 -60 46 -44" fill="none" stroke="{color}" stroke-width="8" stroke-linecap="round" opacity="0.38"/>
          <path d="M-28 22 C0 8 24 8 46 22" fill="none" stroke="{stroke}" stroke-width="8" stroke-linecap="round" opacity="0.24"/>
        </g>
        """
    if hero_id == "sauron":
        return f"""
        <g transform="translate({x},{y}) scale({scale})">
          <circle cx="0" cy="0" r="56" fill="none" stroke="{color}" stroke-width="10" opacity="0.3"/>
          <circle cx="-24" cy="-2" r="7" fill="{color}" opacity="0.34"/>
          <circle cx="0" cy="-22" r="7" fill="{color}" opacity="0.34"/>
          <circle cx="24" cy="-2" r="7" fill="{color}" opacity="0.34"/>
          <circle cx="-16" cy="20" r="7" fill="{color}" opacity="0.34"/>
          <circle cx="16" cy="20" r="7" fill="{color}" opacity="0.34"/>
        </g>
        """
    if hero_id == "balrog":
        return f"""
        <g transform="translate({x},{y}) scale({scale})">
          <path d="M0 -60 L26 -24 L0 58 L-26 -24 Z" fill="{color}" opacity="0.16"/>
          <path d="M-26 -30 L-60 -54 M26 -30 L60 -54" fill="none" stroke="{color}" stroke-width="10" stroke-linecap="round" opacity="0.34"/>
        </g>
        """
    if hero_id == "gollum":
        return f"""
        <g transform="translate({x},{y}) scale({scale})">
          <path d="M-44 -8 C-28 -34 -2 -42 22 -34 C36 -30 48 -18 52 -2 C34 6 20 18 8 36 C-6 28 -26 14 -44 -8 Z" fill="{color}" opacity="0.16"/>
          <path d="M10 -48 L32 -70 L42 -44" fill="none" stroke="{color}" stroke-width="8" stroke-linecap="round" opacity="0.36"/>
        </g>
        """
    return f"""
    <g transform="translate({x},{y}) scale({scale})">
      <path d="M0 -54 C14 -42 24 -20 24 0 C24 24 10 44 -10 56 C-4 34 -10 14 -30 -2 C-18 -2 -8 -6 0 -14 C8 -22 12 -34 10 -46 Z" fill="{color}" opacity="0.18"/>
      <path d="M-34 20 H34" fill="none" stroke="{stroke}" stroke-width="8" stroke-linecap="round" opacity="0.22"/>
    </g>
    """


def hero_backdrop_svg(slot: dict, x: int, y: int, scale: float, color: str) -> str:
    hero_id = slot["legacy_id"]
    backdrops = {
        "aragorn": f'<path d="M-122 42 C-70 -18 -10 -40 66 -30 C90 -26 110 -20 126 -8" fill="none" stroke="{color}" stroke-width="10" stroke-linecap="round" opacity="0.22"/><path d="M-112 84 C-62 56 -12 50 46 64" fill="none" stroke="{color}" stroke-width="8" stroke-linecap="round" opacity="0.18"/>',
        "legolas": f'<circle cx="22" cy="-104" r="54" fill="none" stroke="{color}" stroke-width="10" opacity="0.24"/><path d="M-90 18 L108 18" fill="none" stroke="{color}" stroke-width="8" stroke-linecap="round" opacity="0.14"/>',
        "gandalf": f'<circle cx="0" cy="-96" r="72" fill="none" stroke="{color}" stroke-width="10" opacity="0.2"/><path d="M-94 30 C-46 0 0 -4 60 14" fill="none" stroke="{color}" stroke-width="8" stroke-linecap="round" opacity="0.16"/>',
        "galadriel": f'<path d="M-78 -112 L-78 66 M78 -112 L78 66" fill="none" stroke="{color}" stroke-width="10" stroke-linecap="round" opacity="0.16"/><path d="M-78 -112 Q0 -146 78 -112" fill="none" stroke="{color}" stroke-width="8" stroke-linecap="round" opacity="0.18"/>',
        "frodo": f'<path d="M-104 18 C-60 -18 -20 -22 18 4 C42 20 64 20 92 4" fill="none" stroke="{color}" stroke-width="8" stroke-linecap="round" opacity="0.18"/><path d="M0 -86 L0 82 M-36 -18 H36" fill="none" stroke="{color}" stroke-width="7" stroke-linecap="round" opacity="0.14"/>',
        "boromir": f'<circle cx="-8" cy="2" r="92" fill="none" stroke="{color}" stroke-width="10" opacity="0.18"/>',
        "nazgul": f'<circle cx="0" cy="-90" r="78" fill="none" stroke="{color}" stroke-width="10" opacity="0.18"/><path d="M-118 92 L-72 -28 M118 92 L72 -28" fill="none" stroke="{color}" stroke-width="8" stroke-linecap="round" opacity="0.14"/>',
        "saruman": f'<path d="M-84 -100 C-32 -142 26 -136 86 -90" fill="none" stroke="{color}" stroke-width="8" stroke-linecap="round" opacity="0.18"/><circle cx="56" cy="-32" r="32" fill="none" stroke="{color}" stroke-width="8" opacity="0.16"/>',
        "sauron": f'<circle cx="0" cy="-94" r="84" fill="none" stroke="{color}" stroke-width="10" opacity="0.2"/><circle cx="-50" cy="-94" r="10" fill="{color}" opacity="0.14"/><circle cx="50" cy="-94" r="10" fill="{color}" opacity="0.14"/>',
        "balrog": f'<path d="M-94 -72 L-24 -116 M94 -72 L24 -116" fill="none" stroke="{color}" stroke-width="10" stroke-linecap="round" opacity="0.18"/><path d="M-120 80 C-54 36 16 34 90 56" fill="none" stroke="{color}" stroke-width="8" stroke-linecap="round" opacity="0.16"/>',
        "gollum": f'<path d="M-118 48 C-78 6 -28 -10 28 0 C54 4 82 -4 114 -22" fill="none" stroke="{color}" stroke-width="8" stroke-linecap="round" opacity="0.18"/>',
        "wormtongue": f'<circle cx="0" cy="-46" r="66" fill="none" stroke="{color}" stroke-width="10" opacity="0.16"/><path d="M-42 -46 H42" fill="none" stroke="{color}" stroke-width="8" stroke-linecap="round" opacity="0.14"/>',
    }
    return f'<g transform="translate({x},{y}) scale({scale})">{backdrops.get(hero_id, "")}</g>'


def hero_prop_svg(slot: dict, x: int, y: int, scale: float, color: str, accent: str) -> str:
    hero_id = slot["legacy_id"]
    props = {
        "aragorn": f"""
          <path d="M38 -118 L90 108" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round"/>
          <path d="M34 -120 L58 -154 L72 -118 Z" fill="{accent}" opacity="0.76"/>
          <path d="M-96 18 C-56 -26 -12 -40 40 -32" fill="none" stroke="{accent}" stroke-width="8" stroke-linecap="round" opacity="0.6"/>
        """,
        "legolas": f"""
          <circle cx="-22" cy="-2" r="40" fill="none" stroke="{accent}" stroke-width="8" opacity="0.58"/>
          <path d="M18 -96 L84 112" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round"/>
          <path d="M10 -92 L34 -124 L48 -92 Z" fill="{accent}" opacity="0.8"/>
        """,
        "gandalf": f"""
          <path d="M-86 -18 C-46 -36 -2 -36 44 -10" fill="none" stroke="{accent}" stroke-width="8" stroke-linecap="round" opacity="0.64"/>
          <circle cx="58" cy="-84" r="14" fill="{accent}" opacity="0.82"/>
          <path d="M44 -100 C58 -118 74 -122 92 -116" fill="none" stroke="{accent}" stroke-width="8" stroke-linecap="round" opacity="0.58"/>
        """,
        "galadriel": f"""
          <path d="M44 -118 L44 88" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round"/>
          <path d="M44 -118 L18 -80 M44 -118 L70 -80" fill="none" stroke="{accent}" stroke-width="8" stroke-linecap="round"/>
          <path d="M48 -44 C72 -18 78 14 66 44" fill="none" stroke="{accent}" stroke-width="8" stroke-linecap="round" opacity="0.62"/>
        """,
        "frodo": f"""
          <path d="M-34 88 C-14 56 8 34 32 22" fill="none" stroke="{accent}" stroke-width="8" stroke-linecap="round" opacity="0.62"/>
          <path d="M-68 -4 C-34 -26 0 -30 38 -16" fill="none" stroke="{accent}" stroke-width="8" stroke-linecap="round" opacity="0.58"/>
          <path d="M10 -112 L42 -86" fill="none" stroke="{accent}" stroke-width="8" stroke-linecap="round" opacity="0.54"/>
        """,
        "boromir": f"""
          <circle cx="-50" cy="8" r="50" fill="none" stroke="{accent}" stroke-width="8" opacity="0.56"/>
          <path d="M22 -86 L76 106" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round"/>
          <path d="M16 -84 L38 -118 L52 -82 Z" fill="{accent}" opacity="0.74"/>
        """,
        "nazgul": f"""
          <path d="M10 -126 L10 92" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round"/>
          <path d="M10 -126 L-18 -86 M10 -126 L38 -86" fill="none" stroke="{accent}" stroke-width="8" stroke-linecap="round"/>
          <path d="M-12 -148 L8 -172 L28 -148" fill="none" stroke="{accent}" stroke-width="8" stroke-linecap="round" opacity="0.72"/>
        """,
        "saruman": f"""
          <path d="M46 -98 C72 -74 84 -42 80 -4" fill="{accent}" opacity="0.24"/>
          <path d="M-26 -6 C-2 -20 22 -20 48 -8" fill="none" stroke="{accent}" stroke-width="8" stroke-linecap="round" opacity="0.62"/>
          <circle cx="52" cy="-34" r="18" fill="none" stroke="{accent}" stroke-width="8" opacity="0.54"/>
        """,
        "sauron": f"""
          <circle cx="0" cy="-118" r="52" fill="none" stroke="{accent}" stroke-width="8" opacity="0.62"/>
          <circle cx="-28" cy="-116" r="6" fill="{accent}" opacity="0.72"/>
          <circle cx="0" cy="-132" r="6" fill="{accent}" opacity="0.72"/>
          <circle cx="28" cy="-116" r="6" fill="{accent}" opacity="0.72"/>
          <circle cx="-18" cy="-94" r="6" fill="{accent}" opacity="0.72"/>
          <circle cx="18" cy="-94" r="6" fill="{accent}" opacity="0.72"/>
        """,
        "balrog": f"""
          <path d="M20 -100 L88 110" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round"/>
          <path d="M14 -96 L40 -134 L54 -96 Z" fill="{accent}" opacity="0.8"/>
          <path d="M-34 -120 L-88 -158 M34 -120 L88 -158" fill="none" stroke="{accent}" stroke-width="8" stroke-linecap="round" opacity="0.62"/>
        """,
        "gollum": f"""
          <path d="M34 -104 L62 -128 L56 -94" fill="none" stroke="{accent}" stroke-width="8" stroke-linecap="round" opacity="0.72"/>
          <path d="M-48 -6 C-20 16 6 18 34 8" fill="none" stroke="{accent}" stroke-width="8" stroke-linecap="round" opacity="0.58"/>
          <path d="M12 -54 C30 -44 42 -28 48 -8" fill="none" stroke="{accent}" stroke-width="8" stroke-linecap="round" opacity="0.58"/>
        """,
        "wormtongue": f"""
          <path d="M40 -98 C66 -74 80 -42 80 -2" fill="{accent}" opacity="0.22"/>
          <path d="M-28 6 C0 -10 26 -10 54 0" fill="none" stroke="{accent}" stroke-width="8" stroke-linecap="round" opacity="0.58"/>
          <path d="M-26 -44 H26" fill="none" stroke="{accent}" stroke-width="8" stroke-linecap="round" opacity="0.5"/>
        """,
    }
    return f'<g transform="translate({x},{y}) scale({scale})">{props.get(hero_id, "")}</g>'


def portrait_svg(hero_id: str, x: int, y: int, scale: float, color: str, accent: str) -> str:
    portraits = {
        "aragorn": f"""
        <g transform="translate({x},{y}) scale({scale})">
          <path d="M-12 -128 C18 -126 38 -102 40 -70 C42 -42 30 -16 4 -2 C-24 -14 -40 -42 -38 -74 C-36 -102 -20 -126 -12 -128 Z" fill="{accent}" opacity="0.34"/>
          <path d="M-18 -86 L-44 12 L-60 108 L44 108 L28 12 L8 -86 Z" fill="{color}"/>
          <path d="M20 -124 L72 -64" fill="none" stroke="{color}" stroke-width="12" stroke-linecap="round"/>
          <path d="M60 -78 L92 122" fill="none" stroke="{color}" stroke-width="12" stroke-linecap="round"/>
          <path d="M-18 -90 C-36 -58 -60 -34 -88 -18" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round" opacity="0.8"/>
        </g>
        """,
        "legolas": f"""
        <g transform="translate({x},{y}) scale({scale})">
          <path d="M0 -132 L28 -102 L44 -8 L58 106 L-58 106 L-44 -8 L-28 -102 Z" fill="{color}"/>
          <path d="M22 -92 L74 -126" fill="none" stroke="{accent}" stroke-width="12" stroke-linecap="round"/>
          <path d="M58 -118 L90 116" fill="none" stroke="{accent}" stroke-width="12" stroke-linecap="round"/>
          <path d="M-6 -118 L16 -136 L24 -118" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round"/>
        </g>
        """,
        "gandalf": f"""
        <g transform="translate({x},{y}) scale({scale})">
          <path d="M0 -132 C22 -126 34 -110 34 -88 C34 -66 18 -48 0 -38 C-18 -48 -34 -66 -34 -88 C-34 -110 -22 -126 0 -132 Z" fill="{accent}" opacity="0.38"/>
          <path d="M0 -92 L28 -32 L42 106 L-42 106 L-28 -32 Z" fill="{color}"/>
          <circle cx="54" cy="-78" r="16" fill="{accent}" opacity="0.72"/>
          <path d="M-54 -10 C-30 -24 -10 -30 14 -28 C36 -26 54 -18 70 -4" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round"/>
        </g>
        """,
        "galadriel": f"""
        <g transform="translate({x},{y}) scale({scale})">
          <path d="M0 -132 C22 -126 34 -110 34 -88 C34 -64 18 -46 0 -36 C-18 -46 -34 -64 -34 -88 C-34 -110 -22 -126 0 -132 Z" fill="{accent}" opacity="0.34"/>
          <path d="M0 -92 L28 -26 L44 108 L-44 108 L-28 -26 Z" fill="{color}"/>
          <path d="M50 -108 L50 96" fill="none" stroke="{accent}" stroke-width="12" stroke-linecap="round"/>
          <path d="M50 -108 L24 -72 M50 -108 L76 -72" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round"/>
          <path d="M54 -42 C70 -20 76 8 72 34" fill="none" stroke="{accent}" stroke-width="8" stroke-linecap="round" opacity="0.8"/>
        </g>
        """,
        "frodo": f"""
        <g transform="translate({x},{y}) scale({scale})">
          <path d="M-8 -128 C20 -122 38 -100 38 -70 C38 -40 24 -16 2 -2 C-24 -16 -40 -42 -36 -78 C-32 -104 -18 -122 -8 -128 Z" fill="{accent}" opacity="0.34"/>
          <path d="M-18 -84 L-42 8 L-54 106 L40 106 L28 8 L12 -84 Z" fill="{color}"/>
          <path d="M-52 -12 C-30 -26 -8 -32 18 -28" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round"/>
          <path d="M30 82 C48 70 62 54 72 34" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round"/>
        </g>
        """,
        "boromir": f"""
        <g transform="translate({x},{y}) scale({scale})">
          <path d="M0 -132 L26 -96 L42 -8 L56 104 L-20 104 L-28 10 L-40 -88 Z" fill="{color}"/>
          <circle cx="-44" cy="12" r="46" fill="{color}"/>
          <circle cx="-44" cy="12" r="24" fill="{accent}" opacity="0.26"/>
          <path d="M30 -82 L88 112" fill="none" stroke="{accent}" stroke-width="12" stroke-linecap="round"/>
        </g>
        """,
        "nazgul": f"""
        <g transform="translate({x},{y}) scale({scale})">
          <path d="M0 -136 C26 -132 48 -108 54 -70 C60 -30 46 12 18 38 C8 48 2 62 0 104 C-2 62 -8 48 -18 38 C-46 12 -60 -30 -54 -70 C-48 -108 -26 -132 0 -136 Z" fill="{color}"/>
          <path d="M0 -108 V72" fill="none" stroke="{accent}" stroke-width="12" stroke-linecap="round" opacity="0.86"/>
          <path d="M46 -108 L78 -58" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round"/>
          <path d="M0 -132 L18 -150 L32 -132" fill="none" stroke="{accent}" stroke-width="8" stroke-linecap="round"/>
        </g>
        """,
        "saruman": f"""
        <g transform="translate({x},{y}) scale({scale})">
          <path d="M0 -132 C20 -126 32 -110 32 -88 C32 -66 18 -48 0 -38 C-18 -48 -32 -66 -32 -88 C-32 -110 -20 -126 0 -132 Z" fill="{accent}" opacity="0.34"/>
          <path d="M0 -90 L28 -26 L48 108 L-48 108 L-28 -26 Z" fill="{color}"/>
          <path d="M42 -98 C66 -78 78 -50 76 -18 C58 -32 44 -36 28 -32" fill="{accent}" opacity="0.44"/>
          <path d="M-34 -18 C-18 -30 0 -38 18 -40" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round"/>
        </g>
        """,
        "sauron": f"""
        <g transform="translate({x},{y}) scale({scale})">
          <path d="M0 -126 L30 -92 L46 -6 L58 108 L-58 108 L-46 -6 L-30 -92 Z" fill="{color}"/>
          <circle cx="0" cy="-116" r="44" fill="none" stroke="{accent}" stroke-width="10" opacity="0.72"/>
          <circle cx="-22" cy="-116" r="8" fill="{accent}" opacity="0.8"/>
          <circle cx="0" cy="-126" r="8" fill="{accent}" opacity="0.8"/>
          <circle cx="24" cy="-116" r="8" fill="{accent}" opacity="0.8"/>
          <circle cx="-14" cy="-92" r="8" fill="{accent}" opacity="0.8"/>
          <circle cx="14" cy="-92" r="8" fill="{accent}" opacity="0.8"/>
        </g>
        """,
        "balrog": f"""
        <g transform="translate({x},{y}) scale({scale})">
          <path d="M0 -134 L30 -102 L50 8 L62 110 L-62 110 L-50 8 L-30 -102 Z" fill="{color}"/>
          <path d="M-24 -112 L-74 -154 M24 -112 L74 -154" fill="none" stroke="{accent}" stroke-width="12" stroke-linecap="round"/>
          <path d="M26 -92 L88 116" fill="none" stroke="{accent}" stroke-width="12" stroke-linecap="round"/>
        </g>
        """,
        "gollum": f"""
        <g transform="translate({x},{y}) scale({scale})">
          <path d="M-10 -126 C18 -120 34 -96 34 -66 C34 -34 14 -10 -12 2 C-34 -16 -44 -42 -38 -76 C-34 -102 -22 -118 -10 -126 Z" fill="{accent}" opacity="0.34"/>
          <path d="M-24 -78 L-48 12 L-50 106 L28 106 L18 18 L4 -72 Z" fill="{color}"/>
          <path d="M24 -64 C44 -50 56 -30 60 -4" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round"/>
          <path d="M38 -100 L64 -118 L58 -88" fill="none" stroke="{accent}" stroke-width="8" stroke-linecap="round"/>
        </g>
        """,
        "wormtongue": f"""
        <g transform="translate({x},{y}) scale({scale})">
          <path d="M0 -132 C20 -126 32 -110 32 -88 C32 -66 18 -48 0 -38 C-18 -48 -32 -66 -32 -88 C-32 -110 -20 -126 0 -132 Z" fill="{accent}" opacity="0.34"/>
          <path d="M0 -88 L26 -24 L42 108 L-42 108 L-26 -24 Z" fill="{color}"/>
          <path d="M44 -96 C66 -72 78 -42 76 -8 C58 -18 40 -22 22 -20" fill="{accent}" opacity="0.42"/>
          <path d="M-42 10 C-16 -2 8 -4 34 2" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round"/>
        </g>
        """,
    }
    return portraits.get(hero_id, portraits["aragorn"])


def excerpt(text: str, words: int = 12) -> str:
    clean = re.sub(r"\s+", " ", clean_text(text)).strip()
    parts = clean.split(" ")
    if len(parts) <= words:
        return clean
    return " ".join(parts[:words]) + "..."


def resolve_preview_name(slot: dict) -> str:
    selected = clean_text(slot.get("selected_figure", "")).strip()
    if selected:
        return selected
    candidates = slot.get("candidate_figures", [])
    if candidates:
        return clean_text(candidates[0]).strip()
    return slot["legacy_id"].replace("_", " ").title()


def hero_art_scale_adjustment(legacy_id: str) -> float:
    if legacy_id in {"aragorn", "legolas", "boromir", "balrog"}:
        return 0.85
    return 1.0


def hero_svg(slot: dict, hero_card: dict) -> str:
    hero_name = escape(resolve_preview_name(slot))
    hero_name_size = hero_name_font_size(resolve_preview_name(slot))
    power_lines = [escape(line) for line in wrap_lines(hero_card["power"], width=20, limit=5)]
    line_height = 64
    text_box_y = 410
    text_box_h = 334
    baseline_offset = 40
    first_line_y = text_box_y + ((text_box_h - len(power_lines) * line_height) // 2) + baseline_offset
    power_svg = "\n".join(
        f'<text x="375" y="{first_line_y + idx * line_height}" text-anchor="middle" font-size="58" font-weight="600" fill="{INK}" opacity="0.9">{line}</text>'
        for idx, line in enumerate(power_lines)
    )
    icon = icon_svg(0, 0, 0.62, PRIMARY_GOLD, INK)
    art_scale = hero_art_scale_adjustment(slot["legacy_id"])
    backdrop = hero_backdrop_svg(slot, 375, 220, 0.76 * art_scale, PRIMARY_GOLD)
    emblem = hero_emblem_svg(slot, 375, 184, 0.70 * art_scale, PRIMARY_GOLD, INK)
    props = hero_prop_svg(slot, 375, 320, 0.68 * art_scale, INK, PRIMARY_GOLD)
    silhouette = portrait_svg(slot["legacy_id"], 375, 248, 0.62 * art_scale, INK, PRIMARY_GOLD)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CARD_W} {CARD_H}" role="img" aria-labelledby="title desc">
  <title id="title">{hero_name}</title>
  <desc id="desc">Concept art hero card for {hero_name} with gold hero framing.</desc>
  <defs>
    <linearGradient id="bg-{escape(slot["legacy_id"])}" x1="0" x2="0" y1="0" y2="1">
      <stop offset="0%" stop-color="{PAPER}"/>
      <stop offset="100%" stop-color="#ffffff"/>
    </linearGradient>
  </defs>
  <rect x="16" y="16" width="718" height="1018" rx="40" fill="url(#bg-{escape(slot["legacy_id"])})" stroke="{PRIMARY_GOLD}" stroke-width="16"/>
  <rect x="42" y="42" width="666" height="966" rx="28" fill="none" stroke="{DEEP_GOLD}" stroke-width="5"/>

  <g transform="translate(112,112)">
    {icon}
  </g>

  {backdrop}
  {emblem}
  {props}
  {silhouette}

  <line x1="92" y1="392" x2="658" y2="392" stroke="{PANEL}" stroke-width="4"/>
  <rect x="56" y="410" width="638" height="334" rx="24" fill="{PANEL}" opacity="0.72"/>
  {power_svg}

  <line x1="92" y1="760" x2="658" y2="760" stroke="{PANEL}" stroke-width="4"/>
  <text x="375" y="878" text-anchor="middle" font-size="{hero_name_size}" font-weight="700" fill="{INK}">{hero_name}</text>
  <text x="375" y="974" text-anchor="middle" font-size="68" font-weight="700" fill="{PRIMARY_GOLD}" letter-spacing="4">HERO</text>
</svg>
"""


def gallery_html(cards: list[dict]) -> str:
    tiles = []
    for card in cards:
        svg_name = escape(card["svg_name"])
        tiles.append(
            f"""
      <article class="card-tile">
        <img src="{svg_name}" alt="{escape(card["preview_name"])}">
        <h3>{escape(card["preview_name"])}</h3>
        <p><strong>{escape(card["mechanic_summary"])}</strong> {escape(card["art_excerpt"])}</p>
      </article>
            """.rstrip()
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Hero Card Concept Art</title>
  <style>
    :root {{
      --bg: #f2ede3;
      --panel: #fffaf2;
      --ink: #201b17;
      --muted: #6b645b;
      --border: #d9ceba;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      padding: 28px;
      font-family: "Segoe UI", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top, #fffdf7 0%, rgba(255, 253, 247, 0) 32%),
        linear-gradient(180deg, #f6f0e5 0%, var(--bg) 100%);
    }}
    h1 {{
      margin: 0 0 8px;
      font-size: 32px;
    }}
    .intro {{
      margin: 0 0 28px;
      max-width: 900px;
      color: var(--muted);
      line-height: 1.5;
    }}
    .card-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 18px;
    }}
    .card-tile {{
      padding: 12px;
      border-radius: 16px;
      background: rgba(255, 255, 255, 0.7);
      border: 1px solid rgba(196, 183, 161, 0.9);
    }}
    .card-tile img {{
      width: 100%;
      display: block;
      border-radius: 12px;
      background: #fff;
    }}
    .card-tile h3 {{
      margin: 10px 0 4px;
      font-size: 17px;
    }}
    .card-tile p {{
      margin: 0;
      color: var(--muted);
      font-size: 14px;
      line-height: 1.45;
    }}
  </style>
</head>
<body>
  <h1>Hero Card Concept Gallery</h1>
  <p class="intro">These hero cards keep the frame language you approved, but the central portrait zone now reflects each locked Greek identity more directly. Gold remains the shared hero material, while the portrait silhouette and emblem watermark are driven by the hero-specific art briefs.</p>
  <section class="card-grid">
    {''.join(tiles)}
  </section>
</body>
</html>
"""


def main() -> None:
    hero_data = load_json(DATA_DIR / "hero_cards.json")
    spec_data = load_json(DATA_DIR / "greek_hero_asset_specs.json")

    heroes_by_id = {card["id"]: card for card in hero_data["hero_cards"]}
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    gallery_cards: list[dict] = []
    for slot in spec_data["hero_slots"]:
        hero_card = heroes_by_id[slot["legacy_id"]]
        preview_name = resolve_preview_name(slot)
        svg_name = slot["image"].replace(".png", ".svg")
        out_path = OUTPUT_DIR / svg_name
        out_path.write_text(hero_svg(slot, hero_card), encoding="utf-8")
        gallery_cards.append(
            {
                "svg_name": svg_name,
                "preview_name": preview_name,
                "mechanic_summary": clean_text(hero_card["power"]),
                "art_excerpt": excerpt(slot["art_brief"]),
            }
        )

    (OUTPUT_DIR / "index.html").write_text(gallery_html(gallery_cards), encoding="utf-8")
    print(f"Generated {len(gallery_cards)} hero placeholder cards in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
