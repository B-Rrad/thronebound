from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"


HERO_POWER_OVERRIDES = {
    "aragorn": "Return one played attack card to your hand.",
    "legolas": "Add one attack card regardless of rank (play with card).",
    "gandalf": "Cancel one non-crown attack (standalone).",
    "galadriel": "Heal two wounds (any time).",
    "frodo": "Disable the crown suit for one round.",
    "boromir": "Auto-defend one attack; attacker discards one random card.",
    "nazgul": "Defender may use only crown cards (standalone).",
    "saruman": "Exchange one card with defender's highest or crown card (start of round).",
    "sauron": "View opponent's hand (start of round).",
    "balrog": "Inflict one wound even if fully defended (end of round, play with card).",
    "gollum": "The player who played Autolycus may redefine the crown suit for one round.",
    "wormtongue": "Name a dominion; defender cannot play that dominion this round.",
}


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def build_realm_cards() -> dict:
    realm_specs = load_json(DATA_DIR / "realm_card_asset_specs.json")
    realm_cards = []
    for dominion in realm_specs["dominions"]:
        for card in dominion["cards"]:
            realm_cards.append(
                {
                    "id": card["id"],
                    "name": card["name"],
                    "suit": dominion["dominion_name"],
                    "rank": card["rank_value"],
                    "image": card["image"],
                }
            )
    return {"realm_cards": realm_cards}


def build_hero_cards() -> dict:
    hero_specs = load_json(DATA_DIR / "greek_hero_asset_specs.json")
    hero_cards = []
    for slot in hero_specs["hero_slots"]:
        hero_cards.append(
            {
                "id": slot["legacy_id"],
                "name": slot["selected_figure"],
                "faction": "Legend",
                "power": HERO_POWER_OVERRIDES[slot["legacy_id"]],
                "image": slot["image"],
            }
        )
    return {"hero_cards": hero_cards}


def main() -> None:
    write_json(DATA_DIR / "realm_cards.json", build_realm_cards())
    write_json(DATA_DIR / "hero_cards.json", build_hero_cards())
    print("Synced refaced runtime card data.")


if __name__ == "__main__":
    main()
