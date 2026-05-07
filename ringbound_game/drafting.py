import pygame

from settings import STATE_DRAFTING, STATE_PLAYING


class DraftingMixin:
    def step_drafting(self):
        # Auto-resolve draft picks for AI players
        if self.state != STATE_DRAFTING:
            return

        drafter = self.current_drafter
        ai = self.get_ai(drafter)
        if ai is None:
            return

        now = pygame.time.get_ticks()
        if now - self._last_draft_action < self._draft_action_delay_ms:
            return

        options = []
        if self.can_draft_card_type(drafter, "realm"):
            options.extend(("realm", card) for card in self.realm_draft_visuals)
        if self.can_draft_card_type(drafter, "hero"):
            options.extend(("hero", card) for card in self.hero_draft_visuals)
        if not options:
            return

        choice = ai.choose_draft_card(self, drafter, [card for _, card in options])
        pick_type = next((card_type for card_type, card in options if card is choice or card == choice), None)
        if pick_type == "realm":
            pick_index = self.realm_draft_visuals.index(choice)
        elif pick_type == "hero":
            pick_index = self.hero_draft_visuals.index(choice)
        else:
            pick_type, choice = options[0]
            pick_index = (self.realm_draft_visuals if pick_type == "realm" else self.hero_draft_visuals).index(choice)

        self.attempt_draft(pick_index, pick_type)
        self._last_draft_action = now

    def can_draft_card_type(self, player, card_type):
        if player is None:
            return False
        if card_type == "realm":
            return len(self.get_player_realm_hand(player)) < self.MAX_REALM_CARDS
        if card_type == "hero":
            return len(self.get_player_hero_hand(player)) < self.MAX_HERO_CARDS
        return False

    def player_completed_draft(self, player):
        return (
            len(self.get_player_realm_hand(player)) >= self.MAX_REALM_CARDS
            and len(self.get_player_hero_hand(player)) >= self.MAX_HERO_CARDS
        )

    def drafting_has_available_pick(self, player):
        return (
            self.can_draft_card_type(player, "realm") and bool(self.realm_draft_visuals)
        ) or (
            self.can_draft_card_type(player, "hero") and bool(self.hero_draft_visuals)
        )

    def drafting_is_complete(self):
        both_players_full = self.player_completed_draft("P1") and self.player_completed_draft("P2")
        no_picks_left = not self.drafting_has_available_pick("P1") and not self.drafting_has_available_pick("P2")
        return both_players_full or no_picks_left

    def attempt_draft(self, card_index, card_type):
        if not self.can_draft_card_type(self.current_drafter, card_type):
            return

        current_realm_hand = self.get_player_realm_hand(self.current_drafter)
        current_hero_hand = self.get_player_hero_hand(self.current_drafter)

        if not isinstance(card_index, int):
            draft_cards = self.realm_draft_visuals if card_type == "realm" else self.hero_draft_visuals
            if card_index in draft_cards:
                card_index = draft_cards.index(card_index)
            else:
                return

        if card_type == "realm" and 0 <= card_index < len(self.realm_draft_visuals):
            current_realm_hand.append(self.realm_draft_visuals.pop(card_index))
            self.switch_drafter()
        elif card_type == "hero" and 0 <= card_index < len(self.hero_draft_visuals):
            current_hero_hand.append(self.hero_draft_visuals.pop(card_index))
            self.switch_drafter()
        else:
            return

        self.check_draft_complete()

    def switch_drafter(self):
        next_drafter = self.get_opponent(self.current_drafter)
        if not self.drafting_has_available_pick(next_drafter) and self.drafting_has_available_pick(self.current_drafter):
            next_drafter = self.current_drafter
        self.current_drafter = next_drafter
        self.status_message = f"{self.current_drafter} is drafting."
        if self.is_ai_player(self.current_drafter):
            self._arm_ai_delay(draft=True)

    def check_draft_complete(self):
        if self.drafting_is_complete():
            self.attacker = self.first_attacker
            self.defender = self.get_opponent(self.attacker)
            self.current_player = self.attacker

            self.update_hand_visuals()
            self.state = STATE_PLAYING
            self.status_message = f"{self.attacker} opens the first attack."
            if self.is_ai_player(self.current_player):
                self._arm_ai_delay()

