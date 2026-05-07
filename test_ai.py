"""Headless smoke test for the active AI integration path."""

import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame

pygame.init()
pygame.display.set_mode((1, 1))

from ai_manager import make_ai
from ringbound_game import RingboundGame
from settings import STATE_DRAFTING, STATE_GAMEOVER, STATE_PLAYING


def run_full_game(ai_name, label):
    game = RingboundGame()
    game.music_enabled = False
    game._ai_action_delay_ms = 0
    game._draft_action_delay_ms = 0
    game.p1_ai = None
    game.p2_ai = make_ai(ai_name)
    game.setup_game()
    game.state = STATE_DRAFTING

    steps = 0
    while game.state == STATE_DRAFTING and steps < 50:
        if game.is_human_turn():
            simulate_human_draft(game)
        else:
            game.step_drafting()
        steps += 1

    assert game.state == STATE_PLAYING, f"[{label}] Draft did not complete (state={game.state}, steps={steps})"
    print(f"  [{label}] Draft OK. P1: {len(game.p1_hand)}R+{len(game.p1_heroes)}H  P2: {len(game.p2_hand)}R+{len(game.p2_heroes)}H")

    steps = 0
    while game.state == STATE_PLAYING and steps < 2000:
        if game.is_human_turn():
            simulate_human_play(game)
        else:
            game.step_ai()
        assert len(game.table_defenses) <= len(game.table_attacks), f"[{label}] More defenses than attacks"
        assert len(game.table_attacks) <= len(game.table_defenses) + 1, f"[{label}] More than one unanswered attack"
        steps += 1

    assert game.state == STATE_GAMEOVER, f"[{label}] Game stuck (state={game.state}, steps={steps})"
    print(f"  [{label}] Done in {steps} steps. Winner: {game.winner}  Wounds: P1={game.wounds['P1']} P2={game.wounds['P2']}")


def simulate_human_draft(game):
    if game.can_draft_card_type(game.current_drafter, "realm") and game.realm_draft_visuals:
        game.attempt_draft(0, "realm")
    elif game.can_draft_card_type(game.current_drafter, "hero") and game.hero_draft_visuals:
        game.attempt_draft(0, "hero")


def simulate_human_play(game):
    if game.pending_action is not None:
        resolve_pending_human_action(game)
        return

    if game.play_phase in ("ATTACK", "REINFORCE"):
        for card in list(game.get_player_realm_hand(game.current_player)):
            if game.can_attack_with_card(card):
                game.attempt_play_card(card)
                return
        for hero in list(game.get_player_hero_hand(game.current_player)):
            if game.can_use_hero(hero):
                game.attempt_hero_play(hero)
                return
        game.end_round(defender_took_wound=False, pickup_defenses=False)
        return

    if game.play_phase == "DEFEND":
        attack = game.get_current_attack_card()
        for card in list(game.get_player_realm_hand(game.current_player)):
            if game.can_defend_with_card(card, attack):
                game.attempt_play_card(card)
                return
        game.concede_defense()


def resolve_pending_human_action(game):
    action_type = game.pending_action["type"]
    owner = game.pending_action["owner"]

    if action_type == "choose_suit":
        game.resolve_suit_choice(game.all_suits[0])
    elif action_type == "aragorn_return" and game.table_attacks:
        game.resolve_aragorn(0)
    elif action_type == "saruman_exchange":
        realm = game.get_player_realm_hand(owner)
        if realm:
            game.resolve_saruman_exchange(realm[0])
    elif action_type == "hero_attack_card":
        for card in list(game.get_player_realm_hand(owner)):
            if game.can_select_hero_attack_card(card):
                game.resolve_hero_attack_card(card)
                return


if __name__ == "__main__":
    print("Running AI smoke tests...\n")
    for name in ["Random", "Greedy", "Strategic"]:
        print(f"Testing {name} AI:")
        for trial in range(10):
            run_full_game(name, f"{name} #{trial + 1}")
        print()
    print("All smoke tests passed!")
