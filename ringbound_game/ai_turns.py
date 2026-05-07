import pygame

from settings import STATE_PLAYING


class AITurnMixin:
    def step_ai(self):
        now = pygame.time.get_ticks()
        if now - getattr(self, "_last_ai_action", 0) < getattr(self, "_ai_action_delay_ms", 200):
            return
        if self.state != STATE_PLAYING:
            return
        player = self.current_interaction_player()
        ai = self.get_ai(player)
        if ai is None:
            return
        if self.pending_action is not None:
            if self.pending_action.get("type") == "choose_suit":
                hero = self.pending_action["hero"]
                suit = ai.choose_suit(self, player, hero)
                if suit in self.all_suits:
                    self.resolve_suit_choice(suit)
                    self._last_ai_action = now
            elif self.pending_action.get("type") == "hero_attack_card":
                owner = self.pending_action["owner"]
                mode = self.pending_action["mode"]
                options = list(self.get_player_realm_hand(owner))
                if mode != "legolas_bonus":
                    options = [card for card in options if self.can_attack_with_card(card)]
                if options:
                    action, payload = ai.choose_attack_action(self, owner, options, [])
                    if action == "realm" and payload in options:
                        self.resolve_hero_attack_card(payload)
                        self._last_ai_action = now
            elif self.pending_action.get("type") == "aragorn_return":
                target = ai.choose_aragorn_target(self, player)
                if target in self.table_attacks:
                    self.resolve_aragorn(self.table_attacks.index(target))
                    self._last_ai_action = now
            elif self.pending_action.get("type") == "saruman_exchange":
                choice = ai.choose_saruman_exchange_card(self, player)
                if choice in self.get_player_realm_hand(player):
                    self.resolve_saruman_exchange(choice)
                    self._last_ai_action = now
            return

        # Attacker turn
        if player == self.attacker and self.play_phase in ("ATTACK", "REINFORCE"):
            legal_realm = self.legal_attack_cards(player)
            usable = self.usable_heroes(player)
            if self.play_phase == "ATTACK":
                action, payload = ai.choose_attack_action(self, player, legal_realm, usable)
            else:
                action, payload = ai.choose_reinforce_action(self, player, legal_realm, usable)

            if action == "hero" and payload is not None:
                hero_card = payload if isinstance(payload, dict) else next((h for h in self.get_player_hero_hand(player) if h["id"] == payload), None)
                if hero_card is None:
                    self._last_ai_action = now
                    return
                self.attempt_hero_play(hero_card)
            elif action == "realm" and payload is not None:
                self.attempt_play_card(payload)
            else:
                self.end_round(False, False)

            self._last_ai_action = now
            return

        # Defender turn
        legal_realm = self.legal_defense_cards(player)
        usable = [h for h in self.usable_heroes(player) if h["id"] in {"gandalf", "galadriel", "boromir"}]
        action, payload = ai.choose_defense_action(self, player, legal_realm, usable)
        if action == "hero" and payload is not None:
            hero_card = payload if isinstance(payload, dict) else next((h for h in self.get_player_hero_hand(player) if h["id"] == payload), None)
            if hero_card is not None:
                self.attempt_hero_play(hero_card)
        elif action == "realm" and payload is not None:
            self.attempt_play_card(payload)
        else:
            self.concede_defense()

        self._last_ai_action = now

