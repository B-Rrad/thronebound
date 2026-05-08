from settings import STATE_GAMEOVER


class RoundMixin:
    def sync_turn_after_table_change(self):
        if len(self.table_attacks) > len(self.table_defenses):
            self.play_phase = "DEFEND"
            self.current_player = self.defender
            self.status_message = f"{self.defender} must answer the latest attack."
        elif self.table_attacks:
            self.play_phase = "REINFORCE"
            self.current_player = self.attacker
            self.status_message = f"{self.attacker} may reinforce or end the attack."
        elif self.round_effects["gandalf_ranks"]:
            self.play_phase = "REINFORCE"
            self.current_player = self.attacker
            self.status_message = f"{self.attacker} must continue with a played rank or end the attack."
        else:
            self.play_phase = "ATTACK"
            self.current_player = self.attacker
            self.status_message = f"{self.attacker} may lead a fresh attack."
        if self.is_ai_player(self.current_player):
            self._arm_ai_delay()

    def handle_hand_card_click(self, card_data):
        if self.pending_action is not None and self.pending_action["type"] == "saruman_exchange":
            if self.is_realm_card(card_data):
                self.resolve_saruman_exchange(card_data)
            return
        if self.pending_action is not None and self.pending_action["type"] == "hero_attack_card":
            if self.is_realm_card(card_data):
                self.resolve_hero_attack_card(card_data)
            return

        if self.is_hero_card(card_data):
            self.attempt_hero_play(card_data)
            return

        self.attempt_play_card(card_data)

    def attempt_play_card(self, card_data):
        card_data = getattr(card_data, "data", card_data)
        current_hand = self.get_player_realm_hand(self.current_player)
        if card_data not in current_hand:
            return
        if self.play_phase in ["ATTACK", "REINFORCE"] and not self.can_attack_with_card(card_data):
            return
        if self.play_phase == "DEFEND":
            attack_card = self.get_current_attack_card()
            if not self.can_defend_with_card(card_data, attack_card):
                return

        current_hand.remove(card_data)

        if self.play_phase in ["ATTACK", "REINFORCE"]:
            self.table_attacks.append(card_data)
            if self.round_effects["gandalf_ranks"]:
                self.round_effects["gandalf_ranks"] = []
            if self.round_effects["legolas_bonus"] > 0:
                self.round_effects["legolas_bonus"] -= 1

            self.play_phase = "DEFEND"
            self.current_player = self.defender
            self.status_message = f"{self.defender} must defend {card_data['name']}."
            self.update_hand_visuals()
            self.check_game_over()
            if self.state != STATE_GAMEOVER and self.is_ai_player(self.current_player):
                self._arm_ai_delay()

        elif self.play_phase == "DEFEND":
            self.table_defenses.append(card_data)

            if self.player_has_no_cards(self.defender):
                self.end_round(defender_took_wound=False, pickup_defenses=False)
            else:
                self.play_phase = "REINFORCE"
                self.current_player = self.attacker
                self.status_message = f"{self.attacker} may reinforce or end the attack."
                self.update_hand_visuals()
                if self.is_ai_player(self.current_player):
                    self._arm_ai_delay()
            self.check_game_over()

    def concede_defense(self):
        self.wounds[self.defender] += 1
        self.status_message = f"{self.defender} takes a wound."
        self.end_round(defender_took_wound=True, pickup_defenses=True)

    def clear_round_state(self):
        self.table_attacks = []
        self.table_defenses = []
        self.play_phase = "ATTACK"
        self.current_player = self.attacker
        self.pending_action = None
        self.revealed_hand = None
        self.round_effects = self.new_round_effects()

    def end_round(self, defender_took_wound, pickup_defenses):
        balrog_attack_card = self.round_effects["balrog_attack_card"]
        balrog_fully_defended = (
            balrog_attack_card is not None
            and any(attack_card is balrog_attack_card or attack_card == balrog_attack_card for attack_card in self.table_attacks)
            and len(self.table_attacks) == len(self.table_defenses)
        )
        if not defender_took_wound and self.round_effects["balrog_active"] == self.attacker and balrog_fully_defended:
            self.wounds[self.defender] += 1
            hero_name = self.get_hero_display_name({"id": "balrog"})
            self.status_message = f"{hero_name} wounds {self.defender} despite the defense."

        if not defender_took_wound:
            self.attacker, self.defender = self.defender, self.attacker
        elif pickup_defenses:
            defender_hand = self.get_player_realm_hand(self.defender)
            for defense_card in self.table_defenses:
                if self.is_realm_card(defense_card):
                    defender_hand.append(defense_card)

        for attack_card in self.table_attacks:
            self.discard_card(attack_card)

        for defense_card in self.table_defenses:
            if pickup_defenses and self.is_realm_card(defense_card):
                continue
            self.discard_card(defense_card)

        self.draw_back_to_six(self.attacker)
        self.draw_back_to_six(self.defender)
        self.clear_round_state()

        self.check_game_over()
        if self.state != STATE_GAMEOVER:
            if defender_took_wound:
                self.status_message = f"{self.attacker} keeps the attack."
            else:
                self.status_message = f"{self.attacker} leads the next round."
            self.update_hand_visuals()
            if self.is_ai_player(self.current_player):
                self._arm_ai_delay()

    def draw_back_to_six(self, player):
        hand = self.get_player_realm_hand(player)
        while len(hand) < 6 and len(self.realm_deck) > 0:
            hand.append(self.realm_deck.pop())

    def check_game_over(self):
        if self.wounds["P1"] >= 6:
            self.winner = "P2"
            self.win_reason = "P1 reached 6 wounds."
            self.state = STATE_GAMEOVER
            return
        if self.wounds["P2"] >= 6:
            self.winner = "P1"
            self.win_reason = "P2 reached 6 wounds."
            self.state = STATE_GAMEOVER
            return

        if len(self.realm_deck) == 0:
            p1_realm_empty = self.player_has_no_realm_cards("P1")
            p2_realm_empty = self.player_has_no_realm_cards("P2")
            if p1_realm_empty and not p2_realm_empty:
                self.winner = "P1"
                self.win_reason = "P1 emptied all realm cards after the deck ran out."
                self.state = STATE_GAMEOVER
            elif p2_realm_empty and not p1_realm_empty:
                self.winner = "P2"
                self.win_reason = "P2 emptied all realm cards after the deck ran out."
                self.state = STATE_GAMEOVER
            elif p1_realm_empty and p2_realm_empty:
                if self.wounds["P1"] < self.wounds["P2"]:
                    self.winner = "P1"
                    self.win_reason = "Both players ran out of realm cards; P1 had fewer wounds."
                    self.state = STATE_GAMEOVER
                elif self.wounds["P2"] < self.wounds["P1"]:
                    self.winner = "P2"
                    self.win_reason = "Both players ran out of realm cards; P2 had fewer wounds."
                    self.state = STATE_GAMEOVER
                else:
                    p1_total = self.get_player_total_cards("P1")
                    p2_total = self.get_player_total_cards("P2")
                    if p1_total < p2_total:
                        self.winner = "P1"
                        self.win_reason = "Realm cards were exhausted and tied on wounds; P1 had fewer total cards left."
                    elif p2_total < p1_total:
                        self.winner = "P2"
                        self.win_reason = "Realm cards were exhausted and tied on wounds; P2 had fewer total cards left."
                    else:
                        self.winner = self.random.choice(["P1", "P2"])
                        self.win_reason = "All endgame tiebreakers were equal, so the winner was chosen at random."
                    self.state = STATE_GAMEOVER
