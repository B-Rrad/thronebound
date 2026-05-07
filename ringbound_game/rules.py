class RulesMixin:
    def can_defend_with_card(self, defense_card, attack_card):
        if attack_card is None:
            return False

        if self.round_effects["wormtongue_suit"] == defense_card["suit"]:
            return False

        if self.round_effects["nazgul_active"] and not self.is_trump_card(defense_card):
            return False

        if defense_card["suit"] == attack_card["suit"] and defense_card["rank"] > attack_card["rank"]:
            return True
        if self.is_trump_card(defense_card) and not self.is_trump_card(attack_card):
            return True
        if self.is_trump_card(defense_card) and self.is_trump_card(attack_card):
            return defense_card["rank"] > attack_card["rank"]
        return False

    def can_attack_with_card(self, attack_card):
        forced_ranks = self.round_effects["gandalf_ranks"]
        if self.play_phase == "ATTACK":
            if forced_ranks:
                return attack_card["rank"] in forced_ranks
            return True
        if self.play_phase != "REINFORCE":
            return False
        if self.round_effects["legolas_bonus"] > 0:
            return True

        valid_ranks = self.get_allowed_attack_ranks()
        if not valid_ranks:
            return True
        return attack_card["rank"] in valid_ranks

    def current_player_has_attack_action(self):
        if self.current_player != self.attacker or self.play_phase != "ATTACK":
            return False
        if any(self.can_attack_with_card(card) for card in self.get_player_realm_hand(self.current_player)):
            return True
        return any(
            hero_card["id"] in {"legolas", "balrog"} and self.can_use_hero(hero_card)
            for hero_card in self.get_player_hero_hand(self.current_player)
        )

    def can_end_attack(self):
        if self.pending_action is not None:
            return False
        if self.play_phase == "REINFORCE":
            return True
        if self.play_phase != "ATTACK":
            return False
        return not self.current_player_has_attack_action()

    def can_concede_defense(self):
        return self.play_phase == "DEFEND" and self.pending_action is None

    def get_saruman_target_card(self):
        defender_hand = list(self.get_player_realm_hand(self.defender))
        if not defender_hand:
            return None

        effective_trump = self.get_effective_trump_suit()
        trump_cards = [card for card in defender_hand if effective_trump is not None and card["suit"] == effective_trump]
        if trump_cards:
            return max(trump_cards, key=lambda card: card["rank"])
        return max(defender_hand, key=lambda card: card["rank"])

    def can_use_hero(self, hero_card):
        if self.pending_action is not None:
            return False

        hero_id = hero_card["id"]
        realm_count = len(self.get_player_realm_hand(self.current_player))
        attack_card = self.get_current_attack_card()
        legal_attack_exists = any(self.can_attack_with_card(card) for card in self.get_player_realm_hand(self.current_player))

        if hero_id == "aragorn":
            return self.current_player == self.attacker and self.play_phase in ("ATTACK", "REINFORCE") and bool(self.table_attacks)
        if hero_id == "legolas":
            return self.current_player == self.attacker and self.play_phase in ("ATTACK", "REINFORCE") and realm_count > 0 and self.round_effects["legolas_bonus"] == 0
        if hero_id == "gandalf":
            return self.current_player == self.defender and self.play_phase == "DEFEND" and attack_card is not None and not self.is_trump_card(attack_card)
        if hero_id == "galadriel":
            return self.wounds[self.current_player] > 0
        if hero_id == "frodo":
            return self.current_player == self.attacker and self.play_phase in ("ATTACK", "REINFORCE") and not self.round_effects["trump_disabled"]
        if hero_id == "boromir":
            return self.current_player == self.defender and self.play_phase == "DEFEND" and attack_card is not None
        if hero_id == "nazgul":
            return self.current_player == self.attacker and self.play_phase in ("ATTACK", "REINFORCE") and not self.round_effects["nazgul_active"] and self.get_effective_trump_suit() is not None
        if hero_id == "saruman":
            return self.current_player == self.attacker and self.play_phase == "ATTACK" and len(self.table_attacks) == 0 and realm_count > 0 and self.get_saruman_target_card() is not None
        if hero_id == "sauron":
            return self.current_player == self.attacker and self.play_phase == "ATTACK" and len(self.table_attacks) == 0 and self.revealed_hand is None
        if hero_id == "balrog":
            return self.current_player == self.attacker and self.play_phase in ("ATTACK", "REINFORCE") and self.round_effects["balrog_active"] is None and legal_attack_exists
        if hero_id == "gollum":
            return self.current_player == self.attacker and self.play_phase in ("ATTACK", "REINFORCE") and not self.round_effects["trump_disabled"] and self.round_effects["temporary_trump_suit"] is None
        if hero_id == "wormtongue":
            return self.current_player == self.attacker and self.play_phase in ("ATTACK", "REINFORCE") and self.round_effects["wormtongue_suit"] is None
        return False

    def update_hand_visuals(self):
        self.active_hand_visuals = []
        visible_player = self.visible_hand_player()
        if visible_player is None:
            return
        current_realm_hand = self.get_player_realm_hand(visible_player)
        current_hero_hand = self.get_player_hero_hand(visible_player)
        self.active_hand_visuals = current_realm_hand + current_hero_hand

    # AI compatibility helpers (used by balance_analysis AIs)

    def get_known_opponent_cards(self, player):
        if self.revealed_hand is not None and self.revealed_hand.get("viewer") == player:
            return list(self.get_player_realm_hand(self.get_opponent(player)))
        return None

    def legal_attack_cards(self, player):
        return [card for card in self.get_player_realm_hand(player) if self.can_attack_with_card(card)]

    def legal_defense_cards(self, player):
        attack_card = None
        if len(self.table_attacks) > len(self.table_defenses):
            attack_card = self.table_attacks[-1]
        if attack_card is None:
            return []
        return [card for card in self.get_player_realm_hand(player) if self.can_defend_with_card(card, attack_card)]

    def usable_heroes(self, player):
        heroes = list(self.get_player_hero_hand(player))
        usable = []
        for hero in heroes:
            prev = self.current_player
            self.current_player = player
            try:
                if self.can_use_hero(hero):
                    usable.append(hero)
            finally:
                self.current_player = prev
        return usable

    def can_select_hero_attack_card(self, card_data):
        if self.pending_action is None or self.pending_action["type"] != "hero_attack_card":
            return False
        if not self.is_realm_card(card_data):
            return False
        if card_data not in self.get_player_realm_hand(self.pending_action["owner"]):
            return False

        mode = self.pending_action["mode"]
        if mode == "legolas_bonus":
            return True
        return self.can_attack_with_card(card_data)

    def is_card_playable_in_hand(self, card_data):
        if not self.is_human_turn():
            return False
        if self.pending_action is not None:
            if self.pending_action["type"] == "saruman_exchange":
                return self.is_realm_card(card_data)
            if self.pending_action["type"] == "hero_attack_card":
                return self.can_select_hero_attack_card(card_data)
            return False
        if self.is_hero_card(card_data):
            return self.can_use_hero(card_data)
        if self.play_phase == "DEFEND":
            attack_card = self.get_current_attack_card()
            return self.can_defend_with_card(card_data, attack_card if attack_card else None)
        if self.play_phase in ("ATTACK", "REINFORCE"):
            return self.can_attack_with_card(card_data)
        return False

    def card_play_hint(self, card_data):
        if not self.is_human_turn():
            return "Waiting for the other player."
        if self.pending_action is not None:
            action_type = self.pending_action["type"]
            if action_type == "saruman_exchange":
                hero_name = self.get_hero_display_name("saruman")
                return f"Choose one of your realm cards for {hero_name}." if self.is_realm_card(card_data) else f"{hero_name} swaps realm cards only."
            if action_type == "hero_attack_card":
                return "Choose a realm card for this hero attack." if self.can_select_hero_attack_card(card_data) else "This hero needs a legal realm card."
            return "Finish the current hero choice first."
        if self.is_hero_card(card_data):
            return "Hero can be used now." if self.can_use_hero(card_data) else "Hero timing is not available in this phase."
        if self.play_phase == "DEFEND":
            if self.is_card_playable_in_hand(card_data):
                return "Playable defense."
            attack_card = self.get_current_attack_card()
            if attack_card is None:
                return "There is no attack to defend."
            if self.round_effects["wormtongue_suit"] == card_data.get("suit"):
                return f"{self.get_hero_display_name('wormtongue')} forbids {card_data.get('suit')} this round."
            if self.round_effects["nazgul_active"] and not self.is_trump_card(card_data):
                return f"{self.get_hero_display_name('nazgul')} allows only crown cards for defense."
            if card_data.get("suit") == attack_card.get("suit"):
                return "Same-suit defense must be higher than the attack."
            if self.is_trump_card(card_data) and self.is_trump_card(attack_card):
                return "Crown defense must be higher than the crown attack."
            return "Defend with a higher matching suit card or a crown card."
        if self.play_phase == "REINFORCE" and not self.can_attack_with_card(card_data):
            return "Reinforcements must match a rank already on the table."
        if self.play_phase in ("ATTACK", "REINFORCE"):
            return "Playable attack." if self.can_attack_with_card(card_data) else "This card cannot attack right now."
        return "This card is not playable right now."
