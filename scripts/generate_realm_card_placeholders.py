from __future__ import annotations

import json
from html import escape
from pathlib import Path
import re
from PIL import Image, ImageDraw, ImageFont


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output" / "card_placeholders" / "realm"

CARD_W = 750
CARD_H = 1050
REALM_TITLE_MAX_WIDTH = 610
REALM_TITLE_BASE_SIZE = 116


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def realm_title_font_size(title: str) -> int:
    try:
        font = ImageFont.truetype(r"C:\Windows\Fonts\timesbd.ttf", REALM_TITLE_BASE_SIZE)
    except OSError:
        return REALM_TITLE_BASE_SIZE

    draw = ImageDraw.Draw(Image.new("RGB", (2000, 400)))
    bbox = draw.textbbox((0, 0), title, font=font)
    width = bbox[2] - bbox[0]
    if width <= REALM_TITLE_MAX_WIDTH:
        return REALM_TITLE_BASE_SIZE

    scale = REALM_TITLE_MAX_WIDTH / max(1, width)
    return max(76, int(REALM_TITLE_BASE_SIZE * scale))


def palette_for_dominion(entry: dict) -> dict[str, str]:
    color = entry["color"]["hex"]
    dominion_id = entry["id"]
    if dominion_id == "verdant_court":
        return {
            "primary": color,
            "outline": color,
            "ink": "#2d3a2e",
            "paper": "#f3efe4",
            "panel": "#e4ead7",
            "accent": "#cdd8ba",
        }
    if dominion_id == "ember_throne":
        return {
            "primary": color,
            "outline": color,
            "ink": "#31181f",
            "paper": "#f5ece5",
            "panel": "#ead4d8",
            "accent": "#d69a78",
        }
    if dominion_id == "tidewake_dominion":
        return {
            "primary": color,
            "outline": color,
            "ink": "#1e3554",
            "paper": "#edf5fb",
            "panel": "#dbeaf9",
            "accent": "#90c8ef",
        }
    return {
        "primary": color,
        "outline": "#000000",
        "ink": "#1a1a1a",
        "paper": "#f0ebe1",
        "panel": "#ddd5c8",
        "accent": "#a6a0a0",
    }


def icon_svg(dominion_id: str, x: int, y: int, scale: float, color: str, stroke: str) -> str:
    if dominion_id == "verdant_court":
        return f"""
        <g transform="translate({x},{y}) scale({scale})">
          <path d="M-54 16 C-34 -24, -12 -44, 0 -44 C12 -44, 34 -24, 54 16" fill="none" stroke="{color}" stroke-width="10" stroke-linecap="round"/>
          <ellipse cx="-30" cy="-14" rx="12" ry="22" fill="{color}" transform="rotate(-26 -30 -14)"/>
          <ellipse cx="0" cy="-34" rx="12" ry="22" fill="{color}"/>
          <ellipse cx="30" cy="-14" rx="12" ry="22" fill="{color}" transform="rotate(26 30 -14)"/>
          <path d="M0 -18 V34" fill="none" stroke="{stroke}" stroke-width="8" stroke-linecap="round"/>
        </g>
        """
    if dominion_id == "ember_throne":
        return f"""
        <g transform="translate({x},{y}) scale({scale})">
          <path d="M-44 -18 L-66 -44 L-52 -8 L-20 -22 Z" fill="{color}"/>
          <path d="M44 -18 L66 -44 L52 -8 L20 -22 Z" fill="{color}"/>
          <path d="M0 -72 C24 -36 38 -10 38 18 C38 48 18 74 0 74 C-18 74 -38 48 -38 18 C-38 -2 -30 -20 -14 -38 C-16 -18 -12 0 0 16 C8 0 8 -22 0 -72 Z" fill="{color}"/>
          <path d="M0 -18 C10 -6 16 8 16 20 C16 36 8 48 0 48 C-8 48 -16 36 -16 20 C-16 10 -12 2 -4 -8 C-4 2 -2 8 0 12 C4 8 4 -2 0 -18 Z" fill="#d88852"/>
        </g>
        """
    if dominion_id == "tidewake_dominion":
        return f"""
        <g transform="translate({x},{y}) scale({scale})">
          <path d="M0 -64 V52" fill="none" stroke="{color}" stroke-width="10" stroke-linecap="round"/>
          <path d="M0 -64 L-28 -26" fill="none" stroke="{color}" stroke-width="10" stroke-linecap="round"/>
          <path d="M0 -64 L28 -26" fill="none" stroke="{color}" stroke-width="10" stroke-linecap="round"/>
          <path d="M-44 30 C-24 10, -8 6, 12 14 C28 20, 42 16, 56 0 C56 42, 24 66, -10 66 C-34 66, -56 52, -66 30 C-56 34, -50 34, -44 30 Z" fill="{color}"/>
          <path d="M-54 46 C-20 60, 8 50, 34 36 C48 28, 60 26, 72 28" fill="none" stroke="{stroke}" stroke-width="8" stroke-linecap="round"/>
        </g>
        """
    return f"""
    <g transform="translate({x},{y}) scale({scale})">
      <path d="M58 0 C58 32 32 58 0 58 C-30 58 -54 38 -58 10" fill="none" stroke="{color}" stroke-width="10" stroke-linecap="round"/>
      <path d="M-52 -18 C-42 -46 -18 -64 8 -64 C18 -64 28 -62 38 -56" fill="none" stroke="{color}" stroke-width="10" stroke-linecap="round"/>
      <path d="M42 -50 C50 -44 56 -36 62 -24" fill="none" stroke="{color}" stroke-width="10" stroke-linecap="round"/>
      <path d="M0 -60 L20 54 L0 42 L-20 54 Z" fill="{color}"/>
      <path d="M0 -32 L10 16 L0 10 L-10 16 Z" fill="{stroke}"/>
    </g>
    """


def silhouette_svg(dominion_id: str, x: int, y: int, scale: float, color: str, accent: str) -> str:
    if dominion_id == "verdant_court":
        return f"""
        <g transform="translate({x},{y}) scale({scale})">
          <path d="M0 -128 C18 -122 28 -106 28 -88 C28 -68 16 -54 0 -48 C-16 -54 -28 -68 -28 -88 C-28 -106 -18 -122 0 -128 Z" fill="{accent}" opacity="0.45"/>
          <path d="M0 -84 L18 -36 L42 92 L-42 92 L-18 -36 Z" fill="{color}"/>
          <rect x="-5" y="-118" width="10" height="160" rx="4" fill="{color}"/>
          <path d="M-28 -118 C-40 -110 -46 -94 -44 -80" fill="none" stroke="{color}" stroke-width="8" stroke-linecap="round"/>
          <path d="M28 -118 C40 -110 46 -94 44 -80" fill="none" stroke="{color}" stroke-width="8" stroke-linecap="round"/>
        </g>
        """
    if dominion_id == "ember_throne":
        return f"""
        <g transform="translate({x},{y}) scale({scale})">
          <path d="M0 -126 L26 -86 L44 10 L58 84 L-58 84 L-44 10 L-26 -86 Z" fill="{color}"/>
          <path d="M0 -136 L22 -122 L16 -104 L0 -112 L-16 -104 L-22 -122 Z" fill="{accent}" opacity="0.7"/>
          <rect x="-6" y="-82" width="12" height="126" rx="4" fill="{accent}" opacity="0.85"/>
          <path d="M-58 84 L0 46 L58 84" fill="{accent}" opacity="0.18"/>
        </g>
        """
    if dominion_id == "tidewake_dominion":
        return f"""
        <g transform="translate({x},{y}) scale({scale})">
          <path d="M-12 -118 C28 -118 42 -72 34 -38 C26 -4 28 40 58 90 L-30 90 C-42 48 -44 16 -36 -22 C-30 -52 -32 -92 -12 -118 Z" fill="{color}"/>
          <path d="M22 -102 L22 40" fill="none" stroke="{accent}" stroke-width="12" stroke-linecap="round"/>
          <path d="M22 -102 L-8 -62" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round"/>
          <path d="M22 -102 L52 -62" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round"/>
          <path d="M-48 40 C-18 22 12 22 44 40" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round" opacity="0.45"/>
        </g>
        """
    return f"""
    <g transform="translate({x},{y}) scale({scale})">
      <path d="M0 -128 L38 -92 L22 -14 L56 86 L-56 86 L-22 -14 L-38 -92 Z" fill="{color}"/>
      <path d="M0 -86 V62" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round" opacity="0.8"/>
      <path d="M-26 -112 C-16 -132 -4 -142 12 -148" fill="none" stroke="{accent}" stroke-width="8" stroke-linecap="round"/>
      <path d="M14 -148 C2 -128 -6 -116 -18 -106" fill="none" stroke="{accent}" stroke-width="8" stroke-linecap="round"/>
    </g>
    """


def art_slug(card: dict) -> str:
    text = f"{card['rank_title']} {card['art_brief']}".lower()
    if any(word in text for word in ("ancient hart", "wyrm", "leviathan", "revenant")):
        return "ancient_force"
    if any(word in text for word in ("oracle", "sage", "priest", "magus")):
        return "mystic"
    if any(word in text for word in ("sovereign", "throne")):
        return "sovereign"
    if any(word in text for word in ("champion", "knight", "guard")):
        return "warrior"
    return "scout"


def card_text(card: dict) -> str:
    return f"{card['rank_title']} {card['art_brief']}".lower()


def backdrop_svg(dominion_id: str, card: dict, palette: dict[str, str]) -> str:
    art_type = art_slug(card)
    if dominion_id == "verdant_court":
        moon_y = 236 if art_type != "ancient_force" else 210
        return f"""
        <g opacity="0.9">
          <circle cx="375" cy="{moon_y}" r="102" fill="{palette["accent"]}" opacity="0.46"/>
          <path d="M194 568 C234 488 286 434 352 392 C294 452 258 520 244 612" fill="none" stroke="{palette["accent"]}" stroke-width="18" stroke-linecap="round" opacity="0.42"/>
          <path d="M556 568 C516 488 464 434 398 392 C456 452 492 520 506 612" fill="none" stroke="{palette["accent"]}" stroke-width="18" stroke-linecap="round" opacity="0.42"/>
          <path d="M292 338 L292 592 M458 338 L458 592" fill="none" stroke="{palette["panel"]}" stroke-width="16" stroke-linecap="round" opacity="0.52"/>
          <path d="M292 338 Q375 296 458 338" fill="none" stroke="{palette["panel"]}" stroke-width="16" stroke-linecap="round" opacity="0.52"/>
        </g>
        """
    if dominion_id == "ember_throne":
        flare = "M338 244 L375 154 L412 244" if art_type != "ancient_force" else "M318 248 L375 136 L432 248"
        return f"""
        <g opacity="0.94">
          <path d="M184 560 L274 414 L316 604 Z" fill="{palette["accent"]}" opacity="0.22"/>
          <path d="M566 560 L476 414 L434 604 Z" fill="{palette["accent"]}" opacity="0.22"/>
          <path d="M222 344 L304 278 L326 466 Z" fill="{palette["panel"]}" opacity="0.28"/>
          <path d="M528 344 L446 278 L424 466 Z" fill="{palette["panel"]}" opacity="0.28"/>
          <path d="{flare}" fill="{palette["accent"]}" opacity="0.5"/>
          <path d="M375 182 C404 220 420 250 420 282 C420 332 396 364 375 364 C354 364 330 332 330 282 C330 258 340 234 356 212 C354 236 362 256 375 272 C386 254 388 222 375 182 Z" fill="{palette["panel"]}" opacity="0.32"/>
        </g>
        """
    if dominion_id == "tidewake_dominion":
        return f"""
        <g opacity="0.92">
          <path d="M214 564 C266 486 326 438 392 406 C344 462 322 530 338 608" fill="none" stroke="{palette["accent"]}" stroke-width="18" stroke-linecap="round" opacity="0.4"/>
          <path d="M536 564 C486 486 426 438 360 406 C408 462 430 530 414 608" fill="none" stroke="{palette["accent"]}" stroke-width="18" stroke-linecap="round" opacity="0.4"/>
          <path d="M240 332 C286 294 330 284 375 302 C420 284 464 294 510 332" fill="none" stroke="{palette["panel"]}" stroke-width="16" stroke-linecap="round" opacity="0.52"/>
          <path d="M246 612 C306 582 362 574 430 592 C470 602 504 602 540 592" fill="none" stroke="{palette["panel"]}" stroke-width="14" stroke-linecap="round" opacity="0.48"/>
          <circle cx="294" cy="254" r="10" fill="{palette["accent"]}" opacity="0.34"/>
          <circle cx="454" cy="226" r="8" fill="{palette["accent"]}" opacity="0.28"/>
        </g>
        """
    return f"""
    <g opacity="0.95">
      <circle cx="375" cy="254" r="116" fill="{palette["panel"]}" opacity="0.34"/>
      <circle cx="375" cy="254" r="86" fill="none" stroke="{palette["accent"]}" stroke-width="16" opacity="0.42"/>
      <path d="M286 364 L318 304 L350 602" fill="none" stroke="{palette["accent"]}" stroke-width="14" stroke-linecap="round" opacity="0.36"/>
      <path d="M464 364 L432 304 L400 602" fill="none" stroke="{palette["accent"]}" stroke-width="14" stroke-linecap="round" opacity="0.36"/>
      <path d="M240 588 L294 428 L326 618 Z" fill="{palette["panel"]}" opacity="0.22"/>
      <path d="M510 588 L456 428 L424 618 Z" fill="{palette["panel"]}" opacity="0.22"/>
    </g>
    """


def motif_svg(dominion_id: str, card: dict, x: int, y: int, scale: float, color: str, accent: str) -> str:
    text = card_text(card)
    motifs: list[str] = []

    if dominion_id == "verdant_court":
        if any(word in text for word in ("staff", "sage", "oracle", "initiate")):
            motifs.append(f'<path d="M12 -154 L12 112" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round"/>')
        if "bow" in text:
            motifs.append(f'<path d="M-82 -62 C-112 -8 -112 48 -82 106" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round"/>')
            motifs.append(f'<path d="M-82 -62 C-56 -2 -56 46 -82 106" fill="none" stroke="{accent}" stroke-width="4" stroke-linecap="round" opacity="0.65"/>')
        if any(word in text for word in ("antler", "hart", "stag")):
            motifs.append(f'<path d="M-32 -138 C-52 -164 -74 -182 -100 -192 M32 -138 C52 -164 74 -182 100 -192" fill="none" stroke="{accent}" stroke-width="8" stroke-linecap="round"/>')
        if any(word in text for word in ("ruin", "standing stones", "stone")):
            motifs.append(f'<path d="M-132 102 L-118 -84 M132 102 L118 -84" fill="none" stroke="{color}" stroke-width="14" stroke-linecap="round" opacity="0.28"/>')
        if any(word in text for word in ("moon", "oracle")):
            motifs.append(f'<path d="M78 -124 C98 -124 114 -108 114 -88 C114 -64 92 -46 70 -52 C82 -60 90 -72 90 -88 C90 -102 84 -114 72 -122 C74 -123 76 -124 78 -124 Z" fill="{accent}" opacity="0.62"/>')

    elif dominion_id == "ember_throne":
        if any(word in text for word in ("spear", "champion", "knight")):
            motifs.append(f'<path d="M42 -156 L96 126" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round"/>')
            motifs.append(f'<path d="M32 -154 L54 -188 L68 -150 Z" fill="{accent}" opacity="0.84"/>')
        if any(word in text for word in ("dragon", "wyrm", "draconic")):
            motifs.append(f'<path d="M-112 -36 C-72 -82 -24 -104 32 -104 C70 -104 106 -90 132 -62" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round" opacity="0.74"/>')
        if any(word in text for word in ("citadel", "gates", "throne", "sovereign")):
            motifs.append(f'<path d="M-128 108 L-92 -18 L-52 108 M52 108 L92 -18 L128 108" fill="none" stroke="{color}" stroke-width="14" stroke-linecap="round" opacity="0.26"/>')
        if any(word in text for word in ("flame", "fire", "cinders", "ash")):
            motifs.append(f'<path d="M-66 88 C-50 56 -40 30 -40 6 C-24 30 -18 56 -24 86 M74 86 C86 60 88 32 76 2 C64 30 58 58 62 86" fill="none" stroke="{accent}" stroke-width="8" stroke-linecap="round" opacity="0.72"/>')

    elif dominion_id == "tidewake_dominion":
        if any(word in text for word in ("trident", "reef guard", "wave champion")):
            motifs.append(f'<path d="M44 -150 L44 110 M44 -150 L18 -112 M44 -150 L70 -112" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round"/>')
        if "shell" in text:
            motifs.append(f'<path d="M-108 22 C-84 -20 -46 -34 -8 -18 C18 -8 32 10 36 36 C22 24 6 18 -10 18 C-34 18 -54 28 -72 46 C-80 40 -90 32 -108 22 Z" fill="{accent}" opacity="0.28"/>')
        if any(word in text for word in ("coral", "palace", "arches")):
            motifs.append(f'<path d="M-124 108 C-116 66 -108 34 -88 6 M124 108 C116 66 108 34 88 6" fill="none" stroke="{color}" stroke-width="12" stroke-linecap="round" opacity="0.26"/>')
        if any(word in text for word in ("storm", "current", "tide", "leviathan")):
            motifs.append(f'<path d="M-120 74 C-70 42 -18 36 44 52 C80 62 110 60 130 50" fill="none" stroke="{accent}" stroke-width="9" stroke-linecap="round" opacity="0.8"/>')

    else:
        if any(word in text for word in ("shard", "sepulcher", "guard")):
            motifs.append(f'<path d="M-100 114 L-62 -74 M100 114 L62 -74" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round" opacity="0.72"/>')
        if any(word in text for word in ("eclipse", "oracle", "revenant")):
            motifs.append(f'<circle cx="0" cy="-112" r="54" fill="none" stroke="{accent}" stroke-width="10" opacity="0.72"/><circle cx="14" cy="-112" r="32" fill="{accent}" opacity="0.22"/>')
        if any(word in text for word in ("scythe", "knight", "champion")):
            motifs.append(f'<path d="M56 -138 L38 104" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round"/><path d="M56 -138 C94 -132 120 -104 126 -70 C106 -80 82 -80 62 -68" fill="{accent}" opacity="0.34"/>')
        if any(word in text for word in ("procession", "standards", "sovereign", "crown")):
            motifs.append(f'<path d="M-24 -154 L0 -182 L24 -154" fill="none" stroke="{accent}" stroke-width="8" stroke-linecap="round"/>')

    if not motifs:
        return ""

    return f'<g transform="translate({x},{y}) scale({scale})">{"".join(motifs)}</g>'


def signature_prop_svg(card: dict, dominion_id: str, x: int, y: int, scale: float, color: str, accent: str) -> str:
    card_id = card["id"]
    props = {
        "verdant_court_6": f'<path d="M28 -150 L28 110" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round"/><path d="M-108 100 L-92 -58 M108 100 L92 -58" fill="none" stroke="{color}" stroke-width="12" stroke-linecap="round" opacity="0.22"/>',
        "verdant_court_7": f'<path d="M-74 -64 C-104 -6 -104 50 -74 112" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round"/><path d="M-74 -64 C-48 -2 -48 48 -74 112" fill="none" stroke="{accent}" stroke-width="4" stroke-linecap="round" opacity="0.64"/>',
        "verdant_court_8": f'<path d="M-116 108 L-116 -22 L-76 -56 M116 108 L116 -22 L76 -56" fill="none" stroke="{color}" stroke-width="12" stroke-linecap="round" opacity="0.26"/>',
        "verdant_court_9": f'<path d="M-86 -62 C-118 -2 -118 54 -86 114" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round"/><path d="M78 -124 C98 -124 114 -108 114 -88 C114 -64 92 -46 70 -52 C82 -60 90 -72 90 -88 C90 -102 84 -114 72 -122 C74 -123 76 -124 78 -124 Z" fill="{accent}" opacity="0.6"/>',
        "verdant_court_10": f'<circle cx="12" cy="-96" r="56" fill="none" stroke="{accent}" stroke-width="8" opacity="0.6"/><path d="M18 -150 L18 110" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round"/>',
        "verdant_court_jack": f'<path d="M0 -148 L0 104" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round"/><path d="M-34 -136 C-52 -162 -72 -180 -96 -188 M34 -136 C52 -162 72 -180 96 -188" fill="none" stroke="{accent}" stroke-width="8" stroke-linecap="round"/>',
        "verdant_court_queen": f'<path d="M-86 -10 C-38 -46 6 -48 48 -18" fill="none" stroke="{accent}" stroke-width="8" stroke-linecap="round" opacity="0.62"/><circle cx="72" cy="-98" r="34" fill="none" stroke="{accent}" stroke-width="8" opacity="0.46"/>',
        "verdant_court_king": f'<path d="M-96 98 L-54 40 L0 40 L54 40 L96 98" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round" opacity="0.4"/><path d="M-24 -146 L0 -174 L24 -146" fill="none" stroke="{accent}" stroke-width="8" stroke-linecap="round"/>',
        "verdant_court_ace": f'<path d="M-8 -76 C-34 -122 -66 -150 -104 -168 M16 -72 C48 -122 82 -148 124 -162" fill="none" stroke="{accent}" stroke-width="8" stroke-linecap="round" opacity="0.84"/>',
        "ember_throne_6": f'<path d="M32 -128 L72 52" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round"/><path d="M92 76 C106 52 108 26 96 -4" fill="none" stroke="{accent}" stroke-width="8" stroke-linecap="round" opacity="0.62"/>',
        "ember_throne_7": f'<path d="M30 -148 L78 112" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round"/><path d="M24 -144 L46 -180 L60 -144 Z" fill="{accent}" opacity="0.74"/>',
        "ember_throne_8": f'<path d="M-112 108 L-88 -28 L-44 108 M112 108 L88 -28 L44 108" fill="none" stroke="{color}" stroke-width="12" stroke-linecap="round" opacity="0.24"/>',
        "ember_throne_9": f'<path d="M36 -152 L88 118" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round"/><path d="M-86 -98 C-42 -128 2 -134 50 -114" fill="none" stroke="{accent}" stroke-width="8" stroke-linecap="round" opacity="0.56"/>',
        "ember_throne_10": f'<circle cx="18" cy="-78" r="44" fill="none" stroke="{accent}" stroke-width="8" opacity="0.52"/><path d="M18 -150 L18 112" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round"/>',
        "ember_throne_jack": f'<path d="M28 -150 L88 120" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round"/><path d="M-102 -16 C-62 -62 -10 -84 46 -74" fill="none" stroke="{accent}" stroke-width="8" stroke-linecap="round" opacity="0.58"/>',
        "ember_throne_queen": f'<circle cx="14" cy="-94" r="52" fill="none" stroke="{accent}" stroke-width="8" opacity="0.54"/><path d="M-74 90 C-50 54 -40 28 -42 4" fill="none" stroke="{accent}" stroke-width="8" stroke-linecap="round" opacity="0.58"/>',
        "ember_throne_king": f'<path d="M-92 94 L-52 30 L0 30 L52 30 L92 94" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round" opacity="0.4"/><path d="M-28 -142 L0 -176 L28 -142" fill="none" stroke="{accent}" stroke-width="8" stroke-linecap="round"/>',
        "ember_throne_ace": f'<path d="M-114 -28 C-62 -86 8 -112 90 -94" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round" opacity="0.74"/><path d="M26 -112 L60 -148 L82 -114" fill="none" stroke="{accent}" stroke-width="8" stroke-linecap="round"/>',
        "tidewake_dominion_6": f'<path d="M-92 18 C-68 -24 -28 -36 8 -14 C28 -2 42 18 44 44" fill="{accent}" opacity="0.24"/><path d="M72 78 C88 66 102 50 112 30" fill="none" stroke="{accent}" stroke-width="8" stroke-linecap="round" opacity="0.58"/>',
        "tidewake_dominion_7": f'<path d="M44 -34 C76 -22 96 0 106 32" fill="none" stroke="{accent}" stroke-width="8" stroke-linecap="round" opacity="0.58"/><path d="M-98 68 C-44 32 12 28 76 42" fill="none" stroke="{accent}" stroke-width="8" stroke-linecap="round" opacity="0.48"/>',
        "tidewake_dominion_8": f'<path d="M44 -148 L44 110 M44 -148 L18 -108 M44 -148 L70 -108" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round"/><path d="M-104 96 C-74 46 -56 12 -46 -8" fill="none" stroke="{color}" stroke-width="10" stroke-linecap="round" opacity="0.22"/>',
        "tidewake_dominion_9": f'<path d="M54 -152 L54 108 M54 -152 L24 -114 M54 -152 L84 -114" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round"/><path d="M-110 76 C-46 26 24 20 98 44" fill="none" stroke="{accent}" stroke-width="8" stroke-linecap="round" opacity="0.56"/>',
        "tidewake_dominion_10": f'<circle cx="16" cy="-92" r="54" fill="none" stroke="{accent}" stroke-width="8" opacity="0.56"/><path d="M-102 68 C-44 42 14 44 82 66" fill="none" stroke="{accent}" stroke-width="8" stroke-linecap="round" opacity="0.5"/>',
        "tidewake_dominion_jack": f'<path d="M-112 58 C-40 2 26 -6 110 22" fill="none" stroke="{accent}" stroke-width="9" stroke-linecap="round" opacity="0.62"/><path d="M56 -144 L56 102 M56 -144 L30 -106 M56 -144 L82 -106" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round"/>',
        "tidewake_dominion_queen": f'<path d="M-92 12 C-66 -30 -28 -40 10 -18 C34 -4 48 18 50 42" fill="{accent}" opacity="0.24"/><circle cx="72" cy="-92" r="30" fill="none" stroke="{accent}" stroke-width="8" opacity="0.48"/>',
        "tidewake_dominion_king": f'<path d="M-92 98 L-52 34 L0 34 L52 34 L92 98" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round" opacity="0.38"/><path d="M-112 78 C-42 32 22 28 96 48" fill="none" stroke="{accent}" stroke-width="8" stroke-linecap="round" opacity="0.5"/>',
        "tidewake_dominion_ace": f'<path d="M-120 32 C-72 -28 -8 -56 66 -42 C94 -36 116 -28 132 -14" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round" opacity="0.72"/><circle cx="84" cy="-32" r="8" fill="{accent}" opacity="0.72"/>',
        "obsidian_veil_6": f'<path d="M18 -148 L18 112" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round"/><path d="M-106 102 L-80 -48 M106 102 L80 -48" fill="none" stroke="{color}" stroke-width="10" stroke-linecap="round" opacity="0.24"/>',
        "obsidian_veil_7": f'<path d="M-86 -122 L-86 92" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round" opacity="0.62"/><path d="M-86 -122 L-42 -94" fill="none" stroke="{accent}" stroke-width="8" stroke-linecap="round"/><circle cx="54" cy="-94" r="38" fill="none" stroke="{accent}" stroke-width="8" opacity="0.46"/>',
        "obsidian_veil_8": f'<path d="M-104 106 L-68 -82 M104 106 L68 -82" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round" opacity="0.62"/><path d="M-34 26 L34 26" fill="none" stroke="{accent}" stroke-width="8" stroke-linecap="round" opacity="0.42"/>',
        "obsidian_veil_9": f'<path d="M58 -152 L40 104" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round"/><path d="M58 -152 C98 -146 124 -118 128 -82 C106 -90 82 -90 62 -78" fill="{accent}" opacity="0.28"/>',
        "obsidian_veil_10": f'<circle cx="8" cy="-104" r="58" fill="none" stroke="{accent}" stroke-width="8" opacity="0.56"/><circle cx="24" cy="-104" r="34" fill="{accent}" opacity="0.18"/><path d="M-90 100 L-28 54 L28 54 L90 100" fill="none" stroke="{color}" stroke-width="10" stroke-linecap="round" opacity="0.22"/>',
        "obsidian_veil_jack": f'<path d="M-94 -116 L-94 90" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round" opacity="0.62"/><path d="M-94 -116 L-44 -88" fill="none" stroke="{accent}" stroke-width="8" stroke-linecap="round"/><path d="M-24 -146 L0 -174 L24 -146" fill="none" stroke="{accent}" stroke-width="8" stroke-linecap="round"/>',
        "obsidian_veil_queen": f'<circle cx="0" cy="-108" r="56" fill="none" stroke="{accent}" stroke-width="8" opacity="0.58"/><circle cx="16" cy="-108" r="34" fill="{accent}" opacity="0.18"/><path d="M-74 12 C-40 -18 -2 -20 42 0" fill="none" stroke="{accent}" stroke-width="8" stroke-linecap="round" opacity="0.52"/>',
        "obsidian_veil_king": f'<path d="M-96 98 L-58 30 L0 30 L58 30 L96 98" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round" opacity="0.38"/><path d="M-26 -146 L0 -176 L26 -146" fill="none" stroke="{accent}" stroke-width="8" stroke-linecap="round"/>',
        "obsidian_veil_ace": f'<circle cx="0" cy="-108" r="64" fill="none" stroke="{accent}" stroke-width="8" opacity="0.62"/><circle cx="18" cy="-108" r="38" fill="{accent}" opacity="0.18"/><path d="M-110 84 L-66 -24 M110 84 L66 -24" fill="none" stroke="{accent}" stroke-width="8" stroke-linecap="round" opacity="0.5"/>',
    }
    return f'<g transform="translate({x},{y}) scale({scale})">{props.get(card_id, "")}</g>'


def figure_svg(card: dict, dominion_id: str, x: int, y: int, scale: float, color: str, accent: str) -> str:
    art_type = art_slug(card)
    if art_type == "ancient_force":
        if dominion_id == "verdant_court":
            return f"""
            <g transform="translate({x},{y}) scale({scale})">
              <path d="M-16 -54 C-44 -52 -70 -30 -78 8 C-84 34 -76 60 -56 76 C-38 92 -14 94 18 92 C58 88 86 64 88 24 C90 -12 70 -40 34 -50 C24 -70 4 -86 -18 -84 C-36 -82 -50 -72 -56 -56" fill="{color}"/>
              <path d="M-8 -72 C-26 -118 -56 -146 -92 -164" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round"/>
              <path d="M18 -70 C46 -118 74 -144 114 -158" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round"/>
              <path d="M-56 -120 L-28 -100 L-52 -84" fill="none" stroke="{accent}" stroke-width="8" stroke-linecap="round"/>
              <path d="M58 -116 L28 -96 L54 -82" fill="none" stroke="{accent}" stroke-width="8" stroke-linecap="round"/>
              <path d="M10 34 L22 136 M-22 38 L-18 136 M46 34 L54 130 M-54 34 L-60 130" fill="none" stroke="{color}" stroke-width="12" stroke-linecap="round"/>
            </g>
            """
        if dominion_id == "ember_throne":
            return f"""
            <g transform="translate({x},{y}) scale({scale})">
              <path d="M-92 52 C-94 -8 -56 -64 14 -84 C58 -96 92 -86 118 -54 C92 -20 72 8 62 48 C56 76 58 106 70 132 C26 128 -18 118 -48 102 C-74 88 -90 72 -92 52 Z" fill="{color}"/>
              <path d="M-10 -94 L42 -142 L60 -110 L28 -74 Z" fill="{accent}" opacity="0.78"/>
              <path d="M24 -40 C44 -12 56 14 54 44" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round"/>
              <path d="M-26 28 L-42 122 M6 36 L2 130 M40 46 L54 126" fill="none" stroke="{color}" stroke-width="12" stroke-linecap="round"/>
            </g>
            """
        if dominion_id == "tidewake_dominion":
            return f"""
            <g transform="translate({x},{y}) scale({scale})">
              <path d="M-106 42 C-88 -12 -42 -54 24 -68 C82 -80 132 -50 142 2 C150 42 126 82 74 98 C52 106 18 108 -20 104 C-46 100 -70 86 -86 70 C-102 54 -110 46 -106 42 Z" fill="{color}"/>
              <path d="M52 -18 C76 -44 106 -52 138 -40" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round"/>
              <path d="M-54 22 C-12 44 36 54 88 46" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round" opacity="0.86"/>
              <path d="M-32 68 C-10 92 10 114 28 136" fill="none" stroke="{color}" stroke-width="12" stroke-linecap="round"/>
            </g>
            """
        return f"""
        <g transform="translate({x},{y}) scale({scale})">
          <path d="M0 -128 C36 -124 64 -96 72 -52 C80 -12 68 24 40 48 C24 62 12 76 0 96 C-12 76 -24 62 -40 48 C-68 24 -80 -12 -72 -52 C-64 -96 -36 -124 0 -128 Z" fill="{color}"/>
          <path d="M0 -88 V76" fill="none" stroke="{accent}" stroke-width="12" stroke-linecap="round" opacity="0.88"/>
          <path d="M-34 -24 L-74 24 M34 -24 L74 24" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round"/>
          <path d="M-22 86 L-28 136 M22 86 L28 136" fill="none" stroke="{color}" stroke-width="12" stroke-linecap="round"/>
        </g>
        """
    if art_type == "mystic":
        return f"""
        <g transform="translate({x},{y}) scale({scale})">
          <path d="M0 -136 C20 -130 32 -114 32 -92 C32 -70 16 -52 0 -42 C-16 -52 -32 -70 -32 -92 C-32 -114 -20 -130 0 -136 Z" fill="{accent}" opacity="0.4"/>
          <path d="M0 -92 L26 -38 L44 108 L-44 108 L-26 -38 Z" fill="{color}"/>
          <rect x="-6" y="-122" width="12" height="178" rx="4" fill="{color}"/>
          <path d="M-54 8 C-34 -20 -18 -32 0 -34 C18 -32 34 -20 54 8" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round" opacity="0.82"/>
          <circle cx="0" cy="-16" r="12" fill="{accent}" opacity="0.8"/>
        </g>
        """
    if art_type == "sovereign":
        return f"""
        <g transform="translate({x},{y}) scale({scale})">
          <path d="M0 -138 L28 -102 L46 10 L62 104 L-62 104 L-46 10 L-28 -102 Z" fill="{color}"/>
          <path d="M-32 -116 L-10 -146 L0 -122 L10 -146 L32 -116" fill="{accent}" opacity="0.82"/>
          <path d="M-70 88 L-28 54 L28 54 L70 88" fill="{accent}" opacity="0.2"/>
          <rect x="-8" y="-86" width="16" height="146" rx="5" fill="{accent}" opacity="0.74"/>
        </g>
        """
    if art_type == "warrior":
        return f"""
        <g transform="translate({x},{y}) scale({scale})">
          <path d="M0 -132 L30 -92 L48 6 L58 96 L-58 96 L-48 6 L-30 -92 Z" fill="{color}"/>
          <path d="M0 -144 L20 -126 L12 -106 L0 -114 L-12 -106 L-20 -126 Z" fill="{accent}" opacity="0.8"/>
          <path d="M0 -106 V72" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round" opacity="0.88"/>
          <path d="M-72 28 L-8 -18 M72 28 L8 -18" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round" opacity="0.66"/>
        </g>
        """
    return silhouette_svg(dominion_id, x, y, scale, color, accent)


def excerpt(text: str, words: int = 11) -> str:
    clean = re.sub(r"\s+", " ", text).strip()
    parts = clean.split(" ")
    if len(parts) <= words:
        return clean
    return " ".join(parts[:words]) + "..."


def card_svg(card: dict, dominion_entry: dict, palette: dict[str, str]) -> str:
    dominion_id = dominion_entry["id"]
    dominion_name = dominion_entry["name"]
    rank = escape(str(card["rank_code"]))
    card_name = escape(card["rank_title"])
    dominion_label = escape(dominion_name.upper())
    dominion_font_size = 54 if dominion_id == "tidewake_dominion" else 68
    title_font_size = realm_title_font_size(card["rank_title"])

    icon_corner = icon_svg(dominion_id, 0, 0, 0.48, palette["primary"], palette["ink"])
    backdrop = backdrop_svg(dominion_id, card, palette)
    figure = figure_svg(card, dominion_id, 375, 450, 1.34, palette["ink"], palette["primary"])
    motifs = motif_svg(dominion_id, card, 375, 432, 1.0, palette["ink"], palette["primary"])
    signature = signature_prop_svg(card, dominion_id, 375, 432, 1.0, palette["ink"], palette["primary"])

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CARD_W} {CARD_H}" role="img" aria-labelledby="title desc">
  <title id="title">{escape(card["name"])}</title>
  <desc id="desc">Concept art card for {escape(card["name"])} using the {escape(dominion_name)} dominion frame.</desc>
  <defs>
    <linearGradient id="bg-{escape(card["id"])}" x1="0" x2="0" y1="0" y2="1">
      <stop offset="0%" stop-color="{palette["paper"]}"/>
      <stop offset="100%" stop-color="#ffffff"/>
    </linearGradient>
  </defs>
  <rect x="16" y="16" width="718" height="1018" rx="40" fill="url(#bg-{escape(card["id"])})" stroke="{palette["outline"]}" stroke-width="16"/>
  <rect x="42" y="42" width="666" height="966" rx="28" fill="none" stroke="{palette["outline"]}" stroke-width="5"/>

  <g transform="translate(94,150)">
    <text x="0" y="0" font-size="108" font-weight="700" fill="{palette["primary"]}">{rank}</text>
    <g transform="translate(24,74)">{icon_corner}</g>
  </g>
  {backdrop}
  {motifs}
  {signature}
  {figure}

  <line x1="96" y1="742" x2="654" y2="742" stroke="{palette["panel"]}" stroke-width="4"/>
  <text x="375" y="866" text-anchor="middle" font-size="{title_font_size}" font-weight="700" fill="{palette["ink"]}">{card_name}</text>
  <text x="375" y="976" text-anchor="middle" font-size="{dominion_font_size}" font-weight="700" fill="{palette["primary"]}" letter-spacing="2">{dominion_label}</text>
</svg>
"""


def gallery_html(groups: list[dict]) -> str:
    sections = []
    for group in groups:
        cards_html = []
        for card in group["cards"]:
            svg_name = escape(card["image"].replace(".png", ".svg"))
            cards_html.append(
                f"""
        <article class="card-tile">
          <img src="{svg_name}" alt="{escape(card["name"])}">
          <h3>{escape(card["name"])}</h3>
          <p>{escape(card["rank_title"])}. {escape(excerpt(card["art_brief"]))}</p>
        </article>
                """.rstrip()
            )
        sections.append(
            f"""
      <section class="dominion-block">
        <h2>{escape(group["dominion_name"])}</h2>
        <div class="card-grid">
          {''.join(cards_html)}
        </div>
      </section>
            """.rstrip()
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Realm Card Concept Art</title>
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
    .dominion-block {{
      margin: 0 0 36px;
      padding: 20px;
      background: rgba(255, 250, 242, 0.8);
      border: 1px solid var(--border);
      border-radius: 20px;
      box-shadow: 0 12px 30px rgba(30, 22, 16, 0.06);
    }}
    h2 {{
      margin: 0 0 18px;
      font-size: 24px;
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
    }}
  </style>
</head>
<body>
  <h1>Realm Card Concept Gallery</h1>
  <p class="intro">These SVGs now use the dominion and per-card art briefs to push beyond pure placeholders. They still preserve the card layout you approved, but the central illustration area now carries more of each dominion's environment, silhouette language, and rank progression.</p>
  {''.join(sections)}
</body>
</html>
"""


def main() -> None:
    dominions_data = load_json(DATA_DIR / "dominions.json")
    realm_data = load_json(DATA_DIR / "realm_card_asset_specs.json")

    dominion_lookup = {entry["id"]: entry for entry in dominions_data["dominions"]}
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for group in realm_data["dominions"]:
        dominion_entry = dominion_lookup[group["dominion_id"]]
        palette = palette_for_dominion(dominion_entry)
        for card in group["cards"]:
            out_path = OUTPUT_DIR / card["image"].replace(".png", ".svg")
            out_path.write_text(card_svg(card, dominion_entry, palette), encoding="utf-8")

    index_html = gallery_html(realm_data["dominions"])
    (OUTPUT_DIR / "index.html").write_text(index_html, encoding="utf-8")

    print(f"Generated {sum(len(group['cards']) for group in realm_data['dominions'])} placeholder cards in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
