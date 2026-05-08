from settings import STATE_GAMEOVER, STATE_PLAYING


class HeroMixin:
    def discard_card(self, card_data):
        self.discard_pile.append(card_data)
        if self.is_hero_card(card_data):
            self.hero_discard.append(card_data)

    def consume_hero_card(self, player, hero_card):
        hero_hand = self.get_player_hero_hand(player)
        if hero_card in hero_hand:
            hero_hand.remove(hero_card)
            self.discard_card(hero_card)

    def find_player_hero(self, player, hero_id):
        for hero_card in self.get_player_hero_hand(player):
            if hero_card["id"] == hero_id:
                return hero_card
        return None

    def can_activate_galadriel(self, player):
        return (
            self.state == STATE_PLAYING
            and self.pending_action is None
            and self.wounds[player] > 0
            and self.find_player_hero(player, "galadriel") is not None
        )

    def activate_galadriel(self, player):
        hero_card = self.find_player_hero(player, "galadriel")
        if hero_card is None or self.wounds[player] <= 0 or self.state != STATE_PLAYING:
            return

        previous_wounds = self.wounds[player]
        self.wounds[player] = max(0, previous_wounds - 2)
        healed = previous_wounds - self.wounds[player]
        self.consume_hero_card(player, hero_card)
        hero_name = self.get_hero_display_name(hero_card)
        self.status_message = f"{hero_name} heals {healed} wound(s) for {player}."
        self.check_game_over()
        if self.state != STATE_GAMEOVER:
            self.update_hand_visuals()
            if self.is_ai_player(self.current_player):
                self._arm_ai_delay()

    def remove_random_card_from_player(self, player):
        realm_hand = self.get_player_realm_hand(player)
        hero_hand = self.get_player_hero_hand(player)
        combined = realm_hand + hero_hand
        if not combined:
            return None

        discarded = self.random.choice(combined)
        if discarded in realm_hand:
            realm_hand.remove(discarded)
        else:
            hero_hand.remove(discarded)
        self.discard_card(discarded)
        return discarded

    def set_pending_action(self, action_type, hero_card, prompt, chooser=None, current_player_override=None, **kwargs):
        self.pending_action = {
            "type": action_type,
            "hero": hero_card,
            "owner": self.current_player,
            "chooser": chooser if chooser is not None else self.current_player,
            "prompt": prompt,
            **kwargs,
        }
        if current_player_override is not None:
            self.current_player = current_player_override
        self.status_message = prompt
        self.update_hand_visuals()

    def attempt_hero_play(self, hero_card):
        if not self.can_use_hero(hero_card):
            return

        hero_id = hero_card["id"]
        hero_name = self.get_hero_display_name(hero_card)

        if hero_id == "aragorn":
            self.set_pending_action(
                "aragorn_return",
                hero_card,
                f"{hero_name}: click one attack card on the table to return it to your hand.",
            )
            return
        if hero_id == "saruman":
            target_card = self.get_saruman_target_card()
            if target_card is None:
                return
            self.set_pending_action(
                "saruman_exchange",
                hero_card,
                f"{hero_name}: click one of your realm cards to swap with {target_card['name']}.",
                target_card=target_card,
            )
            return
        if hero_id == "gollum":
            self.set_pending_action(
                "choose_suit",
                hero_card,
                f"{hero_name}: choose the suit that becomes the crown suit for this round.",
                mode="gollum_trump",
            )
            return
        if hero_id == "wormtongue":
            self.set_pending_action(
                "choose_suit",
                hero_card,
                f"{hero_name}: choose the dominion the defender cannot play this round.",
                mode="wormtongue_block",
            )
            return
        if hero_id == "galadriel":
            self.activate_galadriel(self.current_player)
            return
        if hero_id == "legolas":
            self.set_pending_action(
                "hero_attack_card",
                hero_card,
                f"{hero_name}: choose one realm card to attack with now, ignoring rank restrictions.",
                mode="legolas_bonus",
            )
            return
        if hero_id == "balrog":
            self.set_pending_action(
                "hero_attack_card",
                hero_card,
                f"{hero_name}: choose one realm card to attack with now.",
                mode="balrog_attack",
            )
            return

        self.consume_hero_card(self.current_player, hero_card)

        if hero_id == "gandalf":
            self.resolve_gandalf(hero_card)
        elif hero_id == "frodo":
            self.round_effects["trump_disabled"] = True
            self.round_effects["temporary_trump_suit"] = None
            self.status_message = f"{hero_name} disables the crown suit for the rest of the round."
        elif hero_id == "boromir":
            self.resolve_boromir(hero_card)
        elif hero_id == "nazgul":
            self.round_effects["nazgul_active"] = True
            self.status_message = f"{hero_name} forces the defender to rely on crown cards only."
        elif hero_id == "sauron":
            self.revealed_hand = {
                "viewer": self.current_player,
                "target": self.get_opponent(self.current_player),
            }
            self.status_message = f"{hero_name} reveals {self.revealed_hand['target']}'s hand for this round."

        self.pending_action = None
        self.check_game_over()
        if self.state != STATE_GAMEOVER:
            self.update_hand_visuals()
            if self.is_ai_player(self.current_player):
                self._arm_ai_delay()

    def resolve_gandalf(self, hero_card):
        attack_card = self.get_current_attack_card()
        if attack_card is None:
            return

        played_ranks = self.get_reinforce_ranks()
        removed_attack = self.table_attacks.pop()
        self.discard_card(removed_attack)
        self.round_effects["gandalf_ranks"] = played_ranks

        if self.player_has_no_cards(self.defender) and len(self.table_attacks) == len(self.table_defenses):
            self.end_round(defender_took_wound=False, pickup_defenses=False)
            return

        self.sync_turn_after_table_change()
        hero_name = self.get_hero_display_name(hero_card)
        self.status_message = f"{hero_name} cancels the latest non-crown attack. The attacker must continue with a played rank or end the attack."

    def resolve_boromir(self, hero_card):
        if self.get_current_attack_card() is None:
            return

        hero_name = self.get_hero_display_name(hero_card)
        boromir_guard = {"id": "boromir_guard", "name": hero_name, "faction": "Legend", "power": "Auto-defense"}
        self.table_defenses.append(boromir_guard)

        discarded = self.remove_random_card_from_player(self.attacker)
        if self.player_has_no_cards(self.defender):
            self.status_message = f"{hero_name} defends the attack and the round ends."
            self.end_round(defender_took_wound=False, pickup_defenses=False)
            return

        if discarded is None:
            self.status_message = f"{hero_name} auto-defends the attack."
        else:
            self.status_message = f"{hero_name} auto-defends. {self.attacker} discards {discarded['name']}."

        self.play_phase = "REINFORCE"
        self.current_player = self.attacker
        if self.is_ai_player(self.current_player):
            self._arm_ai_delay()

    def resolve_suit_choice(self, suit):
        hero_card = self.pending_action["hero"]
        owner = self.pending_action["owner"]
        mode = self.pending_action["mode"]
        self.consume_hero_card(owner, hero_card)
        hero_name = self.get_hero_display_name(hero_card)

        if mode == "gollum_trump":
            self.round_effects["temporary_trump_suit"] = suit
            self.status_message = f"{hero_name} sets the crown suit to {suit} for this round."
        else:
            self.round_effects["wormtongue_suit"] = suit
            self.status_message = f"{hero_name} forbids the defender from playing {suit} this round."

        self.pending_action = None
        self.current_player = owner
        self.update_hand_visuals()
        if self.is_ai_player(self.current_player):
            self._arm_ai_delay()

    def resolve_aragorn(self, attack_index):
        owner = self.pending_action["owner"]
        hero_card = self.pending_action["hero"]
        if not isinstance(attack_index, int):
            target_data = getattr(attack_index, "data", attack_index)
            match_index = next(
                (
                    index
                    for index, attack_card in enumerate(self.table_attacks)
                    if attack_card is target_data or attack_card == target_data
                ),
                None,
            )
            if match_index is None:
                return
            attack_index = match_index
        if not (0 <= attack_index < len(self.table_attacks)):
            return

        returned_attack = self.table_attacks.pop(attack_index)
        self.get_player_realm_hand(owner).append(returned_attack)

        if attack_index < len(self.table_defenses):
            removed_defense = self.table_defenses.pop(attack_index)
            self.discard_card(removed_defense)

        self.consume_hero_card(owner, hero_card)
        self.pending_action = None
        hero_name = self.get_hero_display_name(hero_card)

        if self.player_has_no_cards(self.defender) and len(self.table_attacks) == len(self.table_defenses):
            self.status_message = f"{hero_name} recovers an attack and the defense holds."
            self.end_round(defender_took_wound=False, pickup_defenses=False)
            return

        self.sync_turn_after_table_change()
        self.status_message = f"{hero_name} returns an attack card to your hand."
        self.update_hand_visuals()
        if self.is_ai_player(self.current_player):
            self._arm_ai_delay()

    def resolve_saruman_exchange(self, chosen_card):
        hero_card = self.pending_action["hero"]
        owner = self.pending_action["owner"]
        target_card = self.pending_action["target_card"]
        owner_realm = self.get_player_realm_hand(owner)
        defender_realm = self.get_player_realm_hand(self.defender)

        if chosen_card not in owner_realm or target_card not in defender_realm:
            return

        owner_realm.remove(chosen_card)
        defender_realm.remove(target_card)
        owner_realm.append(target_card)
        defender_realm.append(chosen_card)

        self.consume_hero_card(owner, hero_card)
        self.pending_action = None
        hero_name = self.get_hero_display_name(hero_card)
        self.status_message = f"{hero_name} swaps {chosen_card['name']} for {target_card['name']}."
        self.update_hand_visuals()
        if self.is_ai_player(self.current_player):
            self._arm_ai_delay()

    def resolve_hero_attack_card(self, chosen_card):
        hero_card = self.pending_action["hero"]
        owner = self.pending_action["owner"]
        mode = self.pending_action["mode"]
        if chosen_card not in self.get_player_realm_hand(owner):
            return
        if not self.can_select_hero_attack_card(chosen_card):
            return

        self.pending_action = None
        self.current_player = owner
        self.consume_hero_card(owner, hero_card)
        hero_name = self.get_hero_display_name(hero_card)
        if mode == "legolas_bonus":
            self.round_effects["legolas_bonus"] = 1
        elif mode == "balrog_attack":
            self.round_effects["balrog_active"] = owner
            self.round_effects["balrog_attack_card"] = chosen_card

        self.attempt_play_card(chosen_card)
        if self.state != STATE_GAMEOVER:
            if mode == "legolas_bonus":
                self.status_message = f"{hero_name} joins the attack with {chosen_card['name']}."
            else:
                self.status_message = f"{hero_name} charges with {chosen_card['name']}."
            self.update_hand_visuals()
            if self.is_ai_player(self.current_player):
                self._arm_ai_delay()
