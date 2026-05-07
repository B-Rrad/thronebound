import os
import random
import sys

import pygame

from ai_manager import configure_ai_from_env
from resource_manager import discover_music_tracks, load_cards
from settings import WINDOW_HEIGHT, WINDOW_WIDTH
from ui import UIController

from .ai_turns import AITurnMixin
from .audio import AudioMixin
from .combat import CombatMixin
from .drafting import DraftingMixin
from .events import EventLoopMixin
from .state import GameStateMixin


class RingboundGame(
    AudioMixin,
    GameStateMixin,
    DraftingMixin,
    CombatMixin,
    AITurnMixin,
    EventLoopMixin,
):
    MAX_REALM_CARDS = 6
    MAX_HERO_CARDS = 4
    MUSIC_END_EVENT = pygame.USEREVENT + 1
    DRAFT_REALM_DISPLAY_COUNT = 10
    DRAFT_HERO_DISPLAY_COUNT = 8

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Thronebound: Battle for the Throne")
        self.clock = pygame.time.Clock()

        if hasattr(sys, "_MEIPASS"):
            self.resource_root = sys._MEIPASS
        else:
            self.resource_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        self.music_tracks = discover_music_tracks(self.resource_root)
        self.music_enabled = False
        self.music_index = 0

        self.db = load_cards(self.resource_root)
        self.all_suits = sorted({card["suit"] for card in self.db["realm_cards"]})
        self.random = random.Random()

        self.p1_ai, self.p2_ai = configure_ai_from_env()
        self._last_ai_action = 0
        self._ai_action_delay_ms = 850
        self._last_draft_action = 0
        self._draft_action_delay_ms = 700

        self.ui = UIController((WINDOW_WIDTH, WINDOW_HEIGHT), self.resource_root)
        self.reset_game_state()
        self._start_music()
