import os
import unittest

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame

pygame.init()
pygame.display.set_mode((1, 1))

from ai_manager import make_ai
from ringbound_game import RingboundGame
from settings import STATE_DRAFTING, STATE_GAMEOVER, STATE_PLAYING


def realm(name, suit, rank):
    return {"name": name, "suit": suit, "rank": rank}


def hero(hero_id):
    return {"id": hero_id, "name": hero_id.title(), "faction": "Test", "power": "test"}


class ScriptedAI:
    name = "Scripted"

    def __init__(self, action):
        self.action = action

    def choose_draft_card(self, game, player, options):
        return options[0]

    def choose_attack_action(self, game, player, legal_realm, usable_heroes):
        return self.action(game, player, legal_realm, usable_heroes)

    def choose_reinforce_action(self, game, player, legal_realm, usable_heroes):
        return self.action(game, player, legal_realm, usable_heroes)

    def choose_defense_action(self, game, player, legal_realm, usable_heroes):
        return ("concede", None)

    def choose_suit(self, game, player, hero_card):
        return game.all_suits[0]

    def choose_aragorn_target(self, game, player):
        return game.table_attacks[0]

    def choose_saruman_exchange_card(self, game, player):
        return game.get_player_realm_hand(player)[0]


class DummyAI:
    name = "Dummy"


class CurrentGameRuleTests(unittest.TestCase):
    def setUp(self):
        self.game = RingboundGame()
        self.game.music_enabled = False
        self.game._ai_action_delay_ms = 0
        self.game._draft_action_delay_ms = 0
        self.reset_play_state()

    def reset_play_state(self):
        game = self.game
        game.state = STATE_PLAYING
        game.attacker = "P1"
        game.defender = "P2"
        game.current_player = "P1"
        game.play_phase = "ATTACK"
        game.p1_ai = None
        game.p2_ai = None
        game.p1_hand = []
        game.p2_hand = []
        game.p1_heroes = []
        game.p2_heroes = []
        game.table_attacks = []
        game.table_defenses = []
        game.discard_pile = []
        game.hero_discard = []
        game.pending_action = None
        game.revealed_hand = None
        game.wounds = {"P1": 0, "P2": 0}
        game.winner = None
        game.win_reason = ""
        game.round_effects = game.new_round_effects()
        game.realm_deck = []
        game.hero_deck = []
        game.trump_suit = "Gondor"
        game.trump_card = realm("Trump", "Gondor", 11)

    def test_engine_rejects_off_rank_reinforcement(self):
        lead = realm("Lead", "Shire", 7)
        block = realm("Block", "Shire", 9)
        illegal = realm("Off Rank", "Mordor", 5)
        self.game.play_phase = "REINFORCE"
        self.game.table_attacks = [lead]
        self.game.table_defenses = [block]
        self.game.p1_hand = [illegal]

        self.game.attempt_play_card(illegal)

        self.assertIn(illegal, self.game.p1_hand)
        self.assertNotIn(illegal, self.game.table_attacks)
        self.assertEqual(self.game.play_phase, "REINFORCE")

    def test_engine_rejects_illegal_defense(self):
        attack = realm("Attack", "Shire", 10)
        illegal = realm("Low Same Suit", "Shire", 8)
        self.game.current_player = "P2"
        self.game.play_phase = "DEFEND"
        self.game.table_attacks = [attack]
        self.game.p2_hand = [illegal]

        self.game.attempt_play_card(illegal)

        self.assertIn(illegal, self.game.p2_hand)
        self.assertEqual(self.game.table_defenses, [])
        self.assertEqual(self.game.play_phase, "DEFEND")

    def test_gollum_owner_chooses_temporary_trump(self):
        gollum = hero("gollum")
        self.game.p1_heroes = [gollum]

        self.game.attempt_hero_play(gollum)

        self.assertEqual(self.game.pending_action["type"], "choose_suit")
        self.assertEqual(self.game.pending_action["owner"], "P1")
        self.assertEqual(self.game.pending_action["chooser"], "P1")
        self.assertEqual(self.game.current_player, "P1")

    def test_ai_aragorn_pending_action_resolves_cleanly(self):
        attack = realm("Attack", "Shire", 7)
        defense = realm("Defense", "Shire", 9)
        aragorn = hero("aragorn")
        spare = realm("Spare", "Mordor", 4)
        self.game.p2_ai = ScriptedAI(lambda game, player, legal, heroes: ("hero", aragorn))
        self.game.attacker = "P2"
        self.game.defender = "P1"
        self.game.current_player = "P2"
        self.game.play_phase = "REINFORCE"
        self.game.table_attacks = [attack]
        self.game.table_defenses = [defense]
        self.game.p2_hand = [spare]
        self.game.p2_heroes = [aragorn]

        self.game.step_ai()
        self.assertEqual(self.game.pending_action["type"], "aragorn_return")

        self.game.step_ai()

        self.assertIsNone(self.game.pending_action)
        self.assertIn(attack, self.game.p2_hand)
        self.assertIn(defense, self.game.discard_pile)
        self.assertIn(aragorn, self.game.hero_discard)

    def test_ai_draft_uses_selected_ai_without_random_attribute_crash(self):
        self.game = RingboundGame()
        self.game.music_enabled = False
        self.game._draft_action_delay_ms = 0
        self.game.p1_ai = None
        self.game.p2_ai = make_ai("Random")
        self.game.setup_game()
        self.game.state = STATE_DRAFTING

        steps = 0
        while self.game.state == STATE_DRAFTING and steps < 50:
            if self.game.is_human_turn():
                if self.game.can_draft_card_type(self.game.current_drafter, "realm") and self.game.realm_draft_visuals:
                    self.game.attempt_draft(0, "realm")
                elif self.game.can_draft_card_type(self.game.current_drafter, "hero") and self.game.hero_draft_visuals:
                    self.game.attempt_draft(0, "hero")
            else:
                self.game.step_drafting()
            steps += 1

        self.assertEqual(self.game.state, STATE_PLAYING)
        self.assertEqual(len(self.game.p1_hand), self.game.MAX_REALM_CARDS)
        self.assertEqual(len(self.game.p2_hand), self.game.MAX_REALM_CARDS)
        self.assertEqual(len(self.game.p1_heroes), self.game.MAX_HERO_CARDS)
        self.assertEqual(len(self.game.p2_heroes), self.game.MAX_HERO_CARDS)

    def test_headless_vs_ai_game_reaches_legal_gameover(self):
        self.game = RingboundGame()
        self.game.music_enabled = False
        self.game._ai_action_delay_ms = 0
        self.game._draft_action_delay_ms = 0
        self.game.p1_ai = None
        self.game.p2_ai = make_ai("Greedy")
        self.game.setup_game()
        self.game.state = STATE_DRAFTING

        steps = 0
        while self.game.state == STATE_DRAFTING and steps < 50:
            if self.game.is_human_turn():
                if self.game.can_draft_card_type(self.game.current_drafter, "realm") and self.game.realm_draft_visuals:
                    self.game.attempt_draft(0, "realm")
                elif self.game.can_draft_card_type(self.game.current_drafter, "hero") and self.game.hero_draft_visuals:
                    self.game.attempt_draft(0, "hero")
            else:
                self.game.step_drafting()
            steps += 1
        self.assertEqual(self.game.state, STATE_PLAYING)

        steps = 0
        while self.game.state == STATE_PLAYING and steps < 2000:
            if self.game.is_human_turn():
                self.play_first_legal_human_action()
            else:
                self.game.step_ai()
            self.assertLessEqual(len(self.game.table_defenses), len(self.game.table_attacks))
            self.assertLessEqual(len(self.game.table_attacks), len(self.game.table_defenses) + 1)
            self.assert_card_zone_integrity(self.game)
            steps += 1

        self.assertEqual(self.game.state, STATE_GAMEOVER)
        self.assertIn(self.game.winner, {"P1", "P2"})

    def test_defender_pickup_and_round_effect_cleanup_after_failed_defense(self):
        attack = realm("Attack", "Shire", 10)
        defense = realm("Defense", "Shire", 12)
        self.game.table_attacks = [attack]
        self.game.table_defenses = [defense]
        self.game.round_effects["nazgul_active"] = True
        self.game.round_effects["wormtongue_suit"] = "Shire"

        self.game.concede_defense()

        self.assertEqual(self.game.wounds["P2"], 1)
        self.assertEqual(self.game.attacker, "P1")
        self.assertIn(defense, self.game.p2_hand)
        self.assertIn(attack, self.game.discard_pile)
        self.assertEqual(self.game.round_effects, self.game.new_round_effects())
        self.assertIsNone(self.game.pending_action)
        self.assertIsNone(self.game.revealed_hand)

    def test_vs_ai_does_not_display_ai_hand_during_ai_turn(self):
        human_card = realm("Human Card", "Rohan", 4)
        ai_card = realm("AI Card", "Mordor", 11)
        self.game.p1_ai = None
        self.game.p2_ai = DummyAI()
        self.game.p1_hand = [human_card]
        self.game.p2_hand = [ai_card]
        self.game.p1_heroes = []
        self.game.p2_heroes = []
        self.game.current_player = "P2"

        self.game.update_hand_visuals()

        self.assertEqual(self.game.active_hand_visuals, [human_card])
        self.assertNotIn(ai_card, self.game.active_hand_visuals)

    def test_same_suit_higher_defense_is_playable(self):
        attack = realm("6 of Shire", "Shire", 6)
        defense = realm("12 of Shire", "Shire", 12)
        self.game.attacker = "P1"
        self.game.defender = "P2"
        self.game.current_player = "P2"
        self.game.play_phase = "DEFEND"
        self.game.table_attacks = [attack]
        self.game.table_defenses = []
        self.game.p2_hand = [defense]

        self.game.update_hand_visuals()

        self.assertTrue(self.game.can_defend_with_card(defense, attack))
        self.assertTrue(self.game.is_card_playable_in_hand(defense))
        self.assertEqual(self.game.card_play_hint(defense), "Playable defense.")

    def test_defense_hint_names_wormtongue_blocker(self):
        attack = realm("6 of Shire", "Shire", 6)
        defense = realm("12 of Shire", "Shire", 12)
        self.game.current_player = "P2"
        self.game.play_phase = "DEFEND"
        self.game.table_attacks = [attack]
        self.game.p2_hand = [defense]
        self.game.round_effects["wormtongue_suit"] = "Shire"

        self.assertFalse(self.game.is_card_playable_in_hand(defense))
        self.assertEqual(self.game.card_play_hint(defense), "Circe forbids Shire this round.")

    def test_deck_empty_tiebreak_uses_empty_realm_hands_before_wounds(self):
        self.game.realm_deck = []
        self.game.p1_hand = []
        self.game.p2_hand = [realm("Remaining", "Gondor", 6)]
        self.game.wounds = {"P1": 5, "P2": 0}

        self.game.check_game_over()

        self.assertEqual(self.game.state, STATE_GAMEOVER)
        self.assertEqual(self.game.winner, "P1")
        self.assertIn("emptied all realm cards", self.game.win_reason)

    def play_first_legal_human_action(self):
        game = self.game
        if game.pending_action is not None:
            action_type = game.pending_action["type"]
            if action_type == "choose_suit":
                game.resolve_suit_choice(game.all_suits[0])
            elif action_type == "aragorn_return" and game.table_attacks:
                game.resolve_aragorn(0)
            elif action_type == "saruman_exchange":
                hand = game.get_player_realm_hand(game.pending_action["owner"])
                if hand:
                    game.resolve_saruman_exchange(hand[0])
            elif action_type == "hero_attack_card":
                hand = game.get_player_realm_hand(game.pending_action["owner"])
                for card in hand:
                    if game.can_select_hero_attack_card(card):
                        game.resolve_hero_attack_card(card)
                        break
            return

        if game.play_phase in ("ATTACK", "REINFORCE"):
            for card in list(game.get_player_realm_hand(game.current_player)):
                if game.can_attack_with_card(card):
                    game.attempt_play_card(card)
                    return
            for card in list(game.get_player_hero_hand(game.current_player)):
                if game.can_use_hero(card):
                    game.attempt_hero_play(card)
                    return
            game.end_round(False, False)
            return

        if game.play_phase == "DEFEND":
            attack = game.get_current_attack_card()
            for card in list(game.get_player_realm_hand(game.current_player)):
                if game.can_defend_with_card(card, attack):
                    game.attempt_play_card(card)
                    return
            game.concede_defense()

    def assert_card_zone_integrity(self, game):
        zones = []
        zones.extend(("p1_hand", card) for card in game.p1_hand)
        zones.extend(("p2_hand", card) for card in game.p2_hand)
        zones.extend(("p1_heroes", card) for card in game.p1_heroes)
        zones.extend(("p2_heroes", card) for card in game.p2_heroes)
        zones.extend(("realm_deck", card) for card in game.realm_deck)
        zones.extend(("hero_deck", card) for card in game.hero_deck)
        zones.extend(("realm_draft", card) for card in game.realm_draft_visuals)
        zones.extend(("hero_draft", card) for card in game.hero_draft_visuals)
        zones.extend(("attacks", card) for card in game.table_attacks)
        zones.extend(("defenses", card) for card in game.table_defenses)
        zones.extend(("discard", card) for card in game.discard_pile)
        if game.trump_card is not None:
            zones.append(("trump", game.trump_card))

        seen = {}
        for zone_name, card in zones:
            card_id = card.get("id")
            if card_id == "boromir_guard":
                continue
            self.assertIsNotNone(card_id, zone_name)
            self.assertNotIn(card_id, seen, f"{card_id} appears in {seen.get(card_id)} and {zone_name}")
            seen[card_id] = zone_name

        self.assertTrue(set(card["id"] for card in game.hero_discard).issubset(set(card["id"] for card in game.discard_pile)))


if __name__ == "__main__":
    unittest.main()
