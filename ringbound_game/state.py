import pygame

from settings import STATE_DRAFTING, STATE_GAMEOVER, STATE_SPLASH


class GameStateMixin:
    def new_round_effects(self):
        return {
            "trump_disabled": False,
            "temporary_trump_suit": None,
            "nazgul_active": False,
            "wormtongue_suit": None,
            "legolas_bonus": 0,
            "balrog_active": None,
            "gandalf_ranks": [],
        }

    def reset_game_state(self):
        self.state = STATE_SPLASH
        self.p1_hand = []
        self.p2_hand = []
        self.p1_heroes = []
        self.p2_heroes = []
        self.wounds = {"P1": 0, "P2": 0}
        self.winner = None
        self.win_reason = ""

        self.realm_deck = []
        self.hero_deck = []
        self.trump_card = None
        self.trump_suit = None
        self.current_drafter = None
        self.first_attacker = None

        self.attacker = None
        self.defender = None
        self.play_phase = "ATTACK"
        self.table_attacks = []
        self.table_defenses = []

        self.realm_draft_visuals = []
        self.hero_draft_visuals = []
        self.active_hand_visuals = []
        self.current_player = None

        self.discard_pile = []
        self.hero_discard = []
        self.round_effects = self.new_round_effects()
        self.pending_action = None
        self.revealed_hand = None
        self.status_message = "Click to start the draft."

    def get_ai(self, player):
        return self.p1_ai if player == "P1" else self.p2_ai

    def is_ai_player(self, player):
        return player is not None and self.get_ai(player) is not None

    def human_players(self):
        return [player for player in ("P1", "P2") if not self.is_ai_player(player)]

    def visible_hand_player(self):
        if self.current_player is None:
            return None

        humans = self.human_players()
        if len(humans) == 1 and self.is_ai_player(self.current_player):
            return humans[0]

        return self.current_player

    def current_interaction_player(self):
        if self.state == STATE_DRAFTING:
            return self.current_drafter
        if self.pending_action is not None:
            if self.pending_action.get("type") == "choose_suit":
                return self.pending_action.get("chooser", self.pending_action.get("owner", self.current_player))
            return self.pending_action.get("owner", self.current_player)
        return self.current_player

    def is_human_turn(self):
        player = self.current_interaction_player()
        return player is not None and not self.is_ai_player(player)

    def _arm_ai_delay(self, draft=False):
        now = pygame.time.get_ticks()
        if draft:
            self._last_draft_action = now
        else:
            self._last_ai_action = now

    def get_player_realm_hand(self, player):
        return self.p1_hand if player == "P1" else self.p2_hand

    def get_player_hero_hand(self, player):
        return self.p1_heroes if player == "P1" else self.p2_heroes

    def get_player_total_cards(self, player):
        return len(self.get_player_realm_hand(player)) + len(self.get_player_hero_hand(player))

    def get_player_combined_hand(self, player):
        return self.get_player_realm_hand(player) + self.get_player_hero_hand(player)

    def get_opponent(self, player):
        return "P2" if player == "P1" else "P1"

    def player_has_no_cards(self, player):
        return self.get_player_total_cards(player) == 0

    def player_has_no_realm_cards(self, player):
        return len(self.get_player_realm_hand(player)) == 0

    def is_hero_card(self, card_data):
        return "faction" in card_data

    def is_realm_card(self, card_data):
        return "suit" in card_data

    def get_effective_trump_suit(self):
        if self.round_effects["trump_disabled"]:
            return None
        if self.round_effects["temporary_trump_suit"] is not None:
            return self.round_effects["temporary_trump_suit"]
        return self.trump_suit

    def is_trump_card(self, card_data):
        effective_trump = self.get_effective_trump_suit()
        return effective_trump is not None and card_data.get("suit") == effective_trump

    def get_current_attack_card(self):
        if len(self.table_attacks) > len(self.table_defenses):
            return self.table_attacks[-1]
        return None

    def get_reinforce_ranks(self):
        ranks = []
        for card in self.table_attacks + self.table_defenses:
            if "rank" in card:
                ranks.append(card["rank"])
        return ranks

    def get_allowed_attack_ranks(self):
        ranks = list(self.get_reinforce_ranks())
        for rank in self.round_effects["gandalf_ranks"]:
            if rank not in ranks:
                ranks.append(rank)
        return ranks

    def setup_game(self):
        self.realm_deck = list(self.db["realm_cards"])
        self.hero_deck = list(self.db["hero_cards"])
        self.random.shuffle(self.realm_deck)
        self.random.shuffle(self.hero_deck)

        if len(self.realm_deck) < 3:
            self.winner = "Setup Error"
            self.win_reason = "At least 3 realm cards are required to start a game."
            self.state = STATE_GAMEOVER
            return

        p1_init = self.realm_deck.pop()
        p2_init = self.realm_deck.pop()
        self.p1_hand.append(p1_init)
        self.p2_hand.append(p2_init)

        if p1_init["rank"] > p2_init["rank"]:
            self.current_drafter = "P1"
            self.first_attacker = "P2"
        elif p2_init["rank"] > p1_init["rank"]:
            self.current_drafter = "P2"
            self.first_attacker = "P1"
        else:
            self.current_drafter = self.random.choice(["P1", "P2"])
            self.first_attacker = "P2" if self.current_drafter == "P1" else "P1"

        self.trump_card = self.realm_deck.pop()
        self.trump_suit = self.trump_card["suit"]

        for _ in range(min(self.DRAFT_REALM_DISPLAY_COUNT, len(self.realm_deck))):
            self.realm_draft_visuals.append(self.realm_deck.pop())

        for _ in range(min(self.DRAFT_HERO_DISPLAY_COUNT, len(self.hero_deck))):
            self.hero_draft_visuals.append(self.hero_deck.pop())

        self.status_message = f"{self.current_drafter} drafts first."
        if self.is_ai_player(self.current_drafter):
            self._arm_ai_delay(draft=True)
