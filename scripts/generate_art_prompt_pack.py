from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output" / "generation_prompts"


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def realm_prompt(dominion: dict, card: dict, dominion_meta: dict) -> str:
    color_name = dominion_meta["color"]["name"]
    frame_notes = dominion_meta["frame_notes"]
    feel = ", ".join(dominion_meta["card_feel"])
    motifs = ", ".join(dominion_meta["motifs"])
    silhouette = ", ".join(dominion_meta["silhouette_language"])
    tags = ", ".join(dominion_meta["prompt_tags"])
    return f"""Use case: illustration-story
Asset type: final realm card art
Primary request: create the illustrated art for {card["name"]}.
Scene/backdrop: {frame_notes}
Subject: {card["rank_title"]} of {dominion["dominion_name"]}; {card["art_brief"]}
Style/medium: mythic illustrated playing card art, elegant fantasy book-painting finish, readable silhouette.
Composition/framing: portrait card illustration, single central subject, clear empty space in the top-left for the rank and crown-sigil overlay, title band reserved at the bottom.
Lighting/mood: {feel}
Color palette: emphasize {color_name}; use only this dominion's visual family.
Materials/textures: {motifs}; silhouette language includes {silhouette}; extra tags: {tags}
Constraints: one focal figure or creature only, no text baked into art, no modern props, no crowd scene, preserve strong center composition for card readability.
Avoid: muddy rendering, mixed dominion motifs, photoreal card mockup borders, tiny unreadable background clutter.
"""


def hero_prompt(slot: dict, hero_card: dict) -> str:
    return f"""Use case: illustration-story
Asset type: final hero card art
Primary request: create the illustrated portrait art for {slot["selected_figure"]}.
Scene/backdrop: mythic Greek setting with restrained environmental storytelling.
Subject: {slot["selected_figure"]}; {slot["art_brief"]}
Style/medium: heroic mythic illustration, painterly but readable, card-portrait composition.
Composition/framing: single centered hero portrait with preserved space at the lower third for power text and preserved top-left space for the gold hero icon.
Lighting/mood: legendary, dramatic, clear at small scale.
Color palette: warm ivory, gold detailing, and colors that support the subject's mythic identity without overpowering the portrait.
Materials/textures: include emblem cues from {slot["hero_emblem"]}.
Text (verbatim): "{hero_card["power"]}"
Constraints: one clear subject only, no faction badge, no text baked into the art, no modern props, no crowd scene, no photoreal trading-card frame.
Avoid: muddy backgrounds, weak silhouette, duplicated limbs or weapons, overly realistic photo style.
"""


def write_text(path: Path, text: str) -> None:
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def main() -> None:
    dominions_data = load_json(DATA_DIR / "dominions.json")
    realm_specs = load_json(DATA_DIR / "realm_card_asset_specs.json")
    hero_specs = load_json(DATA_DIR / "greek_hero_asset_specs.json")
    hero_cards = {card["id"]: card for card in load_json(DATA_DIR / "hero_cards.json")["hero_cards"]}

    dominion_lookup = {entry["id"]: entry for entry in dominions_data["dominions"]}

    realm_dir = OUTPUT_DIR / "realm"
    hero_dir = OUTPUT_DIR / "heroes"
    ensure_dir(realm_dir)
    ensure_dir(hero_dir)

    realm_index_lines = ["# Realm Art Prompt Pack", ""]
    for dominion in realm_specs["dominions"]:
        meta = dominion_lookup[dominion["dominion_id"]]
        realm_index_lines.append(f"## {dominion['dominion_name']}")
        for card in dominion["cards"]:
            filename = card["image"].replace(".png", ".md")
            write_text(realm_dir / filename, realm_prompt(dominion, card, meta))
            realm_index_lines.append(f"- `{filename}`")
        realm_index_lines.append("")

    hero_index_lines = ["# Hero Art Prompt Pack", ""]
    for slot in hero_specs["hero_slots"]:
        hero_card = hero_cards[slot["legacy_id"]]
        filename = slot["image"].replace(".png", ".md")
        write_text(hero_dir / filename, hero_prompt(slot, hero_card))
        hero_index_lines.append(f"- `{filename}`: {slot['selected_figure']}")

    write_text(OUTPUT_DIR / "realm_index.md", "\n".join(realm_index_lines))
    write_text(OUTPUT_DIR / "hero_index.md", "\n".join(hero_index_lines))
    print("Generated realm and hero art prompt packs.")


if __name__ == "__main__":
    main()
