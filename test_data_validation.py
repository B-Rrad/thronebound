import os
import unittest

from resource_manager import discover_music_tracks, load_cards


PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
EXPECTED_SUITS = {"Verdant Court", "Ember Throne", "Tidewake Dominion", "Obsidian Veil"}
EXPECTED_RANKS = set(range(6, 15))
EXPECTED_HERO_IDS = {
    "aragorn",
    "legolas",
    "gandalf",
    "galadriel",
    "frodo",
    "boromir",
    "nazgul",
    "saruman",
    "sauron",
    "balrog",
    "gollum",
    "wormtongue",
}


class CardDataValidationTests(unittest.TestCase):
    def setUp(self):
        self.db = load_cards(PROJECT_ROOT)
        self.realm_cards = self.db["realm_cards"]
        self.hero_cards = self.db["hero_cards"]

    def test_realm_deck_has_expected_suits_ranks_and_unique_ids(self):
        self.assertEqual(len(self.realm_cards), len(EXPECTED_SUITS) * len(EXPECTED_RANKS))

        ids = [card.get("id") for card in self.realm_cards]
        self.assertEqual(len(ids), len(set(ids)))

        cards_by_suit = {suit: [] for suit in EXPECTED_SUITS}
        for card in self.realm_cards:
            self.assertEqual({"id", "name", "suit", "rank", "image"}, set(card))
            self.assertIn(card["suit"], EXPECTED_SUITS)
            self.assertIn(card["rank"], EXPECTED_RANKS)
            self.assertIsInstance(card["name"], str)
            self.assertTrue(card["name"])
            cards_by_suit[card["suit"]].append(card["rank"])

        for suit, ranks in cards_by_suit.items():
            self.assertEqual(set(ranks), EXPECTED_RANKS, suit)

    def test_hero_deck_has_expected_unique_heroes_and_text_matches_rules(self):
        ids = [card.get("id") for card in self.hero_cards]
        self.assertEqual(set(ids), EXPECTED_HERO_IDS)
        self.assertEqual(len(ids), len(set(ids)))

        heroes_by_id = {card["id"]: card for card in self.hero_cards}
        for card in self.hero_cards:
            self.assertEqual({"id", "name", "faction", "power", "image"}, set(card))
            self.assertEqual(card["faction"], "Legend")
            self.assertTrue(card["name"])
            self.assertTrue(card["power"])

        self.assertIn("player who played", heroes_by_id["gollum"]["power"].lower())
        self.assertIn("fully defended", heroes_by_id["balrog"]["power"].lower())
        self.assertEqual(heroes_by_id["gollum"]["name"], "Autolycus")
        self.assertIn("crown suit", heroes_by_id["gollum"]["power"].lower())

    def test_packaged_resources_exist_for_runtime(self):
        self.assertTrue(os.path.isdir(os.path.join(PROJECT_ROOT, "data")))
        self.assertTrue(os.path.isfile(os.path.join(PROJECT_ROOT, "background.jpg")))
        self.assertTrue(os.path.isfile(os.path.join(PROJECT_ROOT, "release", "Ringbound.exe")))
        self.assertGreaterEqual(len(discover_music_tracks(PROJECT_ROOT)), 1)


if __name__ == "__main__":
    unittest.main()
