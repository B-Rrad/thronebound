import sys

import pygame

from ai_manager import make_ai
from settings import FPS, STATE_DRAFTING, STATE_GAMEOVER, STATE_PLAYING, STATE_SPLASH


class EventLoopMixin:
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == self.MUSIC_END_EVENT:
                self._advance_music()
                continue

            if event.type == pygame.VIDEORESIZE:
                resized_w = max(1024, event.w)
                resized_h = max(600, event.h)
                self.screen = pygame.display.set_mode((resized_w, resized_h), pygame.RESIZABLE)
                self.ui.on_resize(resized_w, resized_h)

            intent = self.ui.handle_event(event)
            if intent is not None:
                self.handle_intent(intent)

    def handle_intent(self, intent):
        action = intent.action
        payload = intent.payload

        if action == "start_game" and self.state == STATE_SPLASH:
            # payload may specify play mode and AI choices
            mode = payload.get("mode")
            # allow explicit AI selection for either player
            p1_choice = payload.get("p1_ai")
            p2_choice = payload.get("p2_ai")

            if mode == "2p":
                self.p1_ai = None
                self.p2_ai = None
            else:
                if p1_choice is not None:
                    self.p1_ai = make_ai(p1_choice)
                if p2_choice is not None:
                    self.p2_ai = make_ai(p2_choice)

            self.setup_game()
            self.state = STATE_DRAFTING
            return

        if action == "restart_game" and self.state == STATE_GAMEOVER:
            self.reset_game_state()
            return

        if action == "pick_draft_card" and self.state == STATE_DRAFTING:
            if not self.is_human_turn():
                return
            card_index = payload.get("card_index")
            card_type = payload.get("card_type")
            if isinstance(card_index, int) and card_type in ("realm", "hero"):
                self.attempt_draft(card_index, card_type)
            return

        if action == "select_aragorn_target" and self.state == STATE_PLAYING and self.pending_action is not None:
            if not self.is_human_turn():
                return
            if self.pending_action.get("type") == "aragorn_return":
                attack_index = payload.get("attack_index")
                if isinstance(attack_index, int):
                    self.resolve_aragorn(attack_index)
            return

        if action == "choose_suit" and self.state == STATE_PLAYING and self.pending_action is not None:
            if not self.is_human_turn():
                return
            if self.pending_action.get("type") == "choose_suit":
                suit = payload.get("suit")
                if suit in self.all_suits:
                    self.resolve_suit_choice(suit)
            return

        if action == "select_hand_card" and self.state == STATE_PLAYING:
            if not self.is_human_turn():
                return
            if self.pending_action is not None and self.pending_action.get("type") in ("aragorn_return", "choose_suit"):
                return
            card_index = payload.get("card_index")
            if isinstance(card_index, int) and 0 <= card_index < len(self.active_hand_visuals):
                self.handle_hand_card_click(self.active_hand_visuals[card_index])
            return

        if action == "concede_defense" and self.state == STATE_PLAYING:
            if not self.is_human_turn():
                return
            if self.play_phase == "DEFEND" and self.pending_action is None:
                self.concede_defense()
            return

        if action == "end_attack" and self.state == STATE_PLAYING:
            if not self.is_human_turn():
                return
            if self.play_phase == "REINFORCE" and self.pending_action is None:
                self.end_round(defender_took_wound=False, pickup_defenses=False)
            return

        if action == "confirm_selection":
            resolved = self.ui.resolve_space_intent()
            if resolved is not None:
                self.handle_intent(resolved)
            return

        if action == "request_redraw":
            return

        if action == "pause_confirm_yes":
            self.ui.input_handler.pause_confirm = False
            self.reset_game_state()
            return

        if action == "pause_confirm_no":
            self.ui.input_handler.pause_confirm = False
            return

    def run(self):
        while True:
            self.handle_events()
            self.step_drafting()
            self.step_ai()
            self.ui.draw(self.screen, self)
            pygame.display.flip()
            self.clock.tick(FPS)
