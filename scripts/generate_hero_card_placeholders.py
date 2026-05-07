from __future__ import annotations

import json
import textwrap
from html import escape
from pathlib import Path


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


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


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


def silhouette_svg(seed: str, x: int, y: int, scale: float, color: str, accent: str) -> str:
    index = sum(ord(ch) for ch in seed) % 4
    if index == 0:
        return f"""
        <g transform="translate({x},{y}) scale({scale})">
          <path d="M0 -134 C18 -128 30 -114 30 -92 C30 -70 18 -54 0 -46 C-18 -54 -30 -70 -30 -92 C-30 -114 -18 -128 0 -134 Z" fill="{accent}" opacity="0.42"/>
          <path d="M0 -88 L24 -34 L48 98 L-48 98 L-24 -34 Z" fill="{color}"/>
          <rect x="-6" y="-120" width="12" height="176" rx="4" fill="{color}"/>
        </g>
        """
    if index == 1:
        return f"""
        <g transform="translate({x},{y}) scale({scale})">
          <path d="M0 -136 L34 -108 L54 28 L62 96 L-62 96 L-54 28 L-34 -108 Z" fill="{color}"/>
          <path d="M0 -146 L18 -128 L10 -108 L0 -116 L-10 -108 L-18 -128 Z" fill="{accent}" opacity="0.75"/>
          <path d="M-58 80 L0 40 L58 80" fill="{accent}" opacity="0.18"/>
        </g>
        """
    if index == 2:
        return f"""
        <g transform="translate({x},{y}) scale({scale})">
          <path d="M-18 -124 C24 -124 42 -70 40 -34 C38 0 42 42 62 94 L-42 94 C-52 52 -54 22 -46 -18 C-38 -56 -36 -108 -18 -124 Z" fill="{color}"/>
          <path d="M18 -114 L18 42" fill="none" stroke="{accent}" stroke-width="12" stroke-linecap="round"/>
          <path d="M18 -114 L-10 -74" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round"/>
          <path d="M18 -114 L46 -74" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round"/>
        </g>
        """
    return f"""
    <g transform="translate({x},{y}) scale({scale})">
      <path d="M0 -136 L40 -96 L24 -10 L56 94 L-56 94 L-24 -10 L-40 -96 Z" fill="{color}"/>
      <path d="M0 -92 V70" fill="none" stroke="{accent}" stroke-width="10" stroke-linecap="round" opacity="0.84"/>
      <path d="M-28 -116 C-20 -138 -4 -150 12 -154" fill="none" stroke="{accent}" stroke-width="8" stroke-linecap="round"/>
      <path d="M16 -154 C4 -132 -4 -120 -18 -108" fill="none" stroke="{accent}" stroke-width="8" stroke-linecap="round"/>
    </g>
    """


def resolve_preview_name(slot: dict) -> str:
    selected = clean_text(slot.get("selected_figure", "")).strip()
    if selected:
        return selected
    candidates = slot.get("candidate_figures", [])
    if candidates:
        return clean_text(candidates[0]).strip()
    return slot["legacy_id"].replace("_", " ").title()


def hero_svg(slot: dict, hero_card: dict) -> str:
    hero_name = escape(resolve_preview_name(slot))
    power_lines = [escape(line) for line in wrap_lines(hero_card["power"], width=34, limit=5)]
    line_height = 34
    text_box_y = 676
    text_box_h = 188
    baseline_offset = 22
    first_line_y = text_box_y + ((text_box_h - len(power_lines) * line_height) // 2) + baseline_offset
    power_svg = "\n".join(
        f'<text x="375" y="{first_line_y + idx * line_height}" text-anchor="middle" font-size="29" font-weight="600" fill="{INK}" opacity="0.9">{line}</text>'
        for idx, line in enumerate(power_lines)
    )
    icon = icon_svg(0, 0, 0.62, PRIMARY_GOLD, INK)
    silhouette = silhouette_svg(slot["legacy_id"], 375, 372, 1.32, INK, PRIMARY_GOLD)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CARD_W} {CARD_H}" role="img" aria-labelledby="title desc">
  <title id="title">{hero_name}</title>
  <desc id="desc">Placeholder hero card for {hero_name} with gold hero framing.</desc>
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

  {silhouette}

  <line x1="118" y1="658" x2="632" y2="658" stroke="{PANEL}" stroke-width="4"/>
  <rect x="92" y="676" width="566" height="188" rx="22" fill="{PANEL}" opacity="0.72"/>
  {power_svg}

  <line x1="118" y1="892" x2="632" y2="892" stroke="{PANEL}" stroke-width="4"/>
  <text x="375" y="944" text-anchor="middle" font-size="42" font-weight="700" fill="{INK}">{hero_name}</text>
  <text x="375" y="980" text-anchor="middle" font-size="22" font-weight="700" fill="{PRIMARY_GOLD}" letter-spacing="4">HERO</text>
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
        <p>{escape(card["mechanic_summary"])}</p>
      </article>
            """.rstrip()
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Hero Card Placeholders</title>
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
  <h1>Hero Card Placeholder Gallery</h1>
  <p class="intro">These hero placeholders use the same overall framing language as the realm cards: centered art, restrained border treatment, and a bottom title stack. The gold icon and border establish the shared hero-card identity, and the power description sits directly beneath the portrait area. The roster shown here reflects the locked Greek identities from the hero spec file.</p>
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
        svg_name = f"{slot['legacy_id']}.svg"
        out_path = OUTPUT_DIR / svg_name
        out_path.write_text(hero_svg(slot, hero_card), encoding="utf-8")
        gallery_cards.append(
            {
                "svg_name": svg_name,
                "preview_name": preview_name,
                "mechanic_summary": clean_text(hero_card["power"]),
            }
        )

    (OUTPUT_DIR / "index.html").write_text(gallery_html(gallery_cards), encoding="utf-8")
    print(f"Generated {len(gallery_cards)} hero placeholder cards in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
