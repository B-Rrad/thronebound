from __future__ import annotations

import json
from html import escape
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output" / "card_placeholders" / "realm"

CARD_W = 750
CARD_H = 1050


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


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


def card_svg(card: dict, dominion_entry: dict, palette: dict[str, str]) -> str:
    dominion_id = dominion_entry["id"]
    dominion_name = dominion_entry["name"]
    rank = escape(str(card["rank_code"]))
    card_name = escape(card["rank_title"])
    dominion_label = escape(dominion_name.upper())

    icon_corner = icon_svg(dominion_id, 0, 0, 0.48, palette["primary"], palette["ink"])
    silhouette = silhouette_svg(dominion_id, 375, 430, 1.34, palette["ink"], palette["primary"])

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CARD_W} {CARD_H}" role="img" aria-labelledby="title desc">
  <title id="title">{escape(card["name"])}</title>
  <desc id="desc">Placeholder card for {escape(card["name"])} using the {escape(dominion_name)} dominion frame.</desc>
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
  {silhouette}

  <line x1="118" y1="856" x2="632" y2="856" stroke="{palette["panel"]}" stroke-width="4"/>
  <text x="375" y="904" text-anchor="middle" font-size="42" font-weight="700" fill="{palette["ink"]}">{card_name}</text>
  <text x="375" y="952" text-anchor="middle" font-size="26" font-weight="700" fill="{palette["primary"]}" letter-spacing="3">{dominion_label}</text>
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
          <p>{escape(card["rank_title"])}</p>
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
  <title>Realm Card Placeholders</title>
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
  <h1>Realm Card Placeholder Gallery</h1>
  <p class="intro">These SVGs are generated from the dominion and realm-card asset spec files. They are meant to validate hierarchy, icon placement, rank readability, and overall per-dominion tone before final art generation.</p>
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
