from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pygame

from .layout import LayoutManager
from .theme import Theme


class CardCache:
    def __init__(self):
        self._cache: dict[tuple[str, str, int, int], pygame.Surface] = {}

    def clear(self) -> None:
        self._cache.clear()

    def get(self, key: tuple[str, str, int, int]) -> pygame.Surface | None:
        return self._cache.get(key)

    def put(self, key: tuple[str, str, int, int], surface: pygame.Surface) -> None:
        self._cache[key] = surface


class CardRenderer:
    def __init__(self, theme: Theme, layout: LayoutManager, root_dir: str):
        self.theme = theme
        self.layout = layout
        self.cache = CardCache()
        self.root_dir = Path(root_dir)
        self._asset_cache: dict[str, pygame.Surface] = {}
        self._realm_title_by_id = self._load_realm_titles()

    def clear_cache(self) -> None:
        self.cache.clear()
        self._asset_cache.clear()

    def _id_for_card(self, card: dict[str, Any]) -> str:
        base = card.get("id", card.get("name", "card"))
        suit = card.get("suit", "")
        rank = card.get("rank", "")
        return f"{base}|{suit}|{rank}"

    def card_surface(self, card: dict[str, Any], state: str, size: tuple[int, int]) -> pygame.Surface:
        w, h = size
        key = (self._id_for_card(card), state, w, h)
        cached = self.cache.get(key)
        if cached is not None:
            return cached

        if "faction" in card:
            surface = self._draw_hero_card(card, state, size)
        else:
            surface = self._draw_realm_card(card, state, size)

        self.cache.put(key, surface)
        return surface

    def detailed_card_surface(self, card: dict[str, Any], size: tuple[int, int]) -> pygame.Surface:
        w, h = size
        key = (f"detail:{self._id_for_card(card)}", "normal", w, h)
        cached = self.cache.get(key)
        if cached is not None:
            return cached

        asset = self._load_card_asset(card, size)
        surface = asset[0] if asset is not None else None
        if surface is None:
            surface = self.card_surface(card, "normal", size)
        else:
            surface = surface.copy()
            asset_ext = asset[1]
            if asset_ext == ".svg":
                if "faction" in card:
                    self._overlay_hero_asset_labels(surface, card)
                else:
                    self._overlay_realm_asset_labels(surface, card)

        self.cache.put(key, surface)
        return surface

    def _load_card_asset(self, card: dict[str, Any], size: tuple[int, int]) -> tuple[pygame.Surface, str] | None:
        image_name = card.get("image")
        if not image_name:
            return None

        image_stem = Path(image_name).stem
        asset_group = "heroes" if "faction" in card else "realm"
        search_dirs = [
            self.root_dir / "assets" / "cards" / asset_group,
            self.root_dir / "output" / "card_placeholders" / asset_group,
        ]

        for asset_dir in search_dirs:
            for extension in (".png", ".svg"):
                asset_path = asset_dir / f"{image_stem}{extension}"
                if not asset_path.is_file():
                    continue

                cache_key = str(asset_path)
                original = self._asset_cache.get(cache_key)
                if original is None:
                    loaded = pygame.image.load(str(asset_path))
                    if pygame.display.get_surface() is not None:
                        loaded = loaded.convert_alpha()
                    original = loaded
                    self._asset_cache[cache_key] = original

                scaled = pygame.transform.smoothscale(original, size)
                return scaled, extension

        return None

    def _load_realm_titles(self) -> dict[str, str]:
        spec_path = self.root_dir / "data" / "realm_card_asset_specs.json"
        try:
            payload = json.loads(spec_path.read_text(encoding="utf-8"))
        except Exception:
            return {}

        titles: dict[str, str] = {}
        for dominion in payload.get("dominions", []):
            for card in dominion.get("cards", []):
                card_id = card.get("id")
                rank_title = card.get("rank_title")
                if card_id and rank_title:
                    titles[card_id] = rank_title
        return titles

    def _overlay_realm_asset_labels(self, surface: pygame.Surface, card: dict[str, Any]) -> None:
        w, h = surface.get_size()
        suit = card.get("suit", "")
        suit_color = self.theme.suit_colors.get(suit, self.theme.accent_gold)
        ink = self.theme.text_primary
        panel = (248, 244, 236, 0)

        rank_font = self.layout.font_cache.get(self.layout.font_cache.display_path, max(20, int(h * 0.115)))
        title_font = self.layout.font_cache.get(self.layout.font_cache.display_path, max(13, int(h * 0.046)))
        dominion_font = self.layout.font_cache.get(self.layout.font_cache.body_path, max(9, int(h * 0.024)))

        rank_surface = rank_font.render(self._rank_code(card.get("rank")), True, suit_color)
        self._blit_text_with_shadow(surface, rank_surface, (int(w * 0.11), int(h * 0.07)))
        self._draw_suit_icon_at(surface, suit, suit_color, int(w * 0.18), int(h * 0.165), int(w * 0.12), int(h * 0.10))

        title = self._realm_title_by_id.get(card.get("id", ""), card.get("name", ""))
        title_surface = title_font.render(title, True, ink)
        title_rect = title_surface.get_rect(center=(int(w * 0.50), int(h * 0.855)))
        self._blit_text_with_shadow(surface, title_surface, title_rect.topleft)

        dominion_surface = dominion_font.render(suit.upper(), True, suit_color)
        dominion_rect = dominion_surface.get_rect(center=(int(w * 0.50), int(h * 0.92)))
        self._blit_text_with_shadow(surface, dominion_surface, dominion_rect.topleft)

    def _overlay_hero_asset_labels(self, surface: pygame.Surface, card: dict[str, Any]) -> None:
        w, h = surface.get_size()
        gold = self.theme.accent_gold
        ink = self.theme.text_primary

        self._draw_hero_icon_at(surface, int(w * 0.15), int(h * 0.11), int(w * 0.11), gold, ink)

        panel_rect = pygame.Rect(int(w * 0.12), int(h * 0.64), int(w * 0.76), int(h * 0.18))
        panel = pygame.Surface(panel_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(panel, (236, 226, 203, 188), panel.get_rect(), border_radius=max(8, int(w * 0.03)))
        surface.blit(panel, panel_rect.topleft)

        power_font = self.layout.font_cache.get(self.layout.font_cache.body_path, max(10, int(h * 0.028)))
        name_font = self.layout.font_cache.get(self.layout.font_cache.display_path, max(13, int(h * 0.046)))
        footer_font = self.layout.font_cache.get(self.layout.font_cache.body_path, max(8, int(h * 0.020)))

        lines = self._wrap(card.get("power", ""), power_font, int(panel_rect.w * 0.86))[:5]
        rendered = [power_font.render(line, True, ink) for line in lines]
        if rendered:
            total_h = sum(line.get_height() for line in rendered) + max(0, len(rendered) - 1) * max(2, int(h * 0.006))
            y = panel_rect.y + (panel_rect.h - total_h) // 2
            for line_surface in rendered:
                line_rect = line_surface.get_rect(centerx=panel_rect.centerx, y=y)
                self._blit_text_with_shadow(surface, line_surface, line_rect.topleft)
                y += line_surface.get_height() + max(2, int(h * 0.006))

        name_surface = name_font.render(card.get("name", "Hero"), True, ink)
        name_rect = name_surface.get_rect(center=(int(w * 0.50), int(h * 0.885)))
        self._blit_text_with_shadow(surface, name_surface, name_rect.topleft)

        footer_surface = footer_font.render("HERO", True, gold)
        footer_rect = footer_surface.get_rect(center=(int(w * 0.50), int(h * 0.94)))
        self._blit_text_with_shadow(surface, footer_surface, footer_rect.topleft)

    def _rank_code(self, rank: Any) -> str:
        face = {11: "J", 12: "Q", 13: "K", 14: "A"}
        return face.get(rank, str(rank))

    def _blit_text_with_shadow(self, surface: pygame.Surface, text_surface: pygame.Surface, position: tuple[int, int]) -> None:
        shadow = text_surface.copy()
        shadow.fill((0, 0, 0, 90), special_flags=pygame.BLEND_RGBA_MULT)
        surface.blit(shadow, (position[0] + 1, position[1] + 2))
        surface.blit(text_surface, position)

    def _draw_suit_icon_at(self, surface: pygame.Surface, suit: str, color: tuple[int, int, int], cx: int, cy: int, icon_w: int, icon_h: int) -> None:
        suit_key = suit.strip().lower().replace(" ", "_")

        if suit_key == "gondor":
            points = [
                (cx, cy - icon_h // 2),
                (cx - icon_w // 3, cy + icon_h // 3),
                (cx - icon_w // 5, cy + icon_h // 2),
                (cx + icon_w // 5, cy + icon_h // 2),
                (cx + icon_w // 3, cy + icon_h // 3),
            ]
            pygame.draw.polygon(surface, self.theme.text_primary, points)
            pygame.draw.rect(surface, self.theme.text_primary, pygame.Rect(cx - max(1, icon_w // 10), cy + icon_h // 4, max(1, icon_w // 5), max(1, icon_h // 2)))
        elif suit_key == "shire":
            pygame.draw.ellipse(surface, color, pygame.Rect(cx - icon_w // 2, cy - icon_h // 2, icon_w, icon_h))
            pygame.draw.line(surface, self.theme.text_primary, (cx - icon_w // 4, cy + icon_h // 3), (cx + icon_w // 4, cy - icon_h // 3), max(1, icon_w // 10))
        elif suit_key == "mordor":
            pygame.draw.ellipse(surface, color, pygame.Rect(cx - icon_w // 2, cy - icon_h // 3, icon_w, int(icon_h * 0.7)))
            pygame.draw.ellipse(surface, self.theme.bg, pygame.Rect(cx - icon_w // 4, cy - icon_h // 6, icon_w // 2, icon_h // 3))
            pygame.draw.circle(surface, self.theme.text_primary, (cx, cy), max(1, icon_w // 10))
        elif suit_key == "rohan":
            horse = [
                (cx - icon_w // 2, cy),
                (cx - icon_w // 6, cy - icon_h // 3),
                (cx + icon_w // 4, cy - icon_h // 4),
                (cx + icon_w // 2, cy),
                (cx + icon_w // 6, cy + icon_h // 3),
                (cx - icon_w // 4, cy + icon_h // 3),
            ]
            pygame.draw.polygon(surface, color, horse)
        elif suit_key == "verdant_court":
            pygame.draw.arc(surface, color, pygame.Rect(cx - icon_w // 2, cy - icon_h // 2, icon_w, icon_h), 3.45, 5.95, max(1, icon_w // 10))
            for offset in (-icon_w // 3, 0, icon_w // 3):
                leaf_rect = pygame.Rect(cx + offset - icon_w // 10, cy - icon_h // 3, icon_w // 5, icon_h // 2)
                pygame.draw.ellipse(surface, color, leaf_rect)
            pygame.draw.line(surface, self.theme.text_primary, (cx, cy - icon_h // 6), (cx, cy + icon_h // 4), max(1, icon_w // 12))
        elif suit_key == "ember_throne":
            flame = [
                (cx, cy - icon_h // 2),
                (cx + icon_w // 5, cy - icon_h // 6),
                (cx + icon_w // 8, cy + icon_h // 2),
                (cx, cy + icon_h // 5),
                (cx - icon_w // 8, cy + icon_h // 2),
                (cx - icon_w // 5, cy - icon_h // 6),
            ]
            left_horn = [(cx - icon_w // 3, cy - icon_h // 5), (cx - icon_w // 2, cy - icon_h // 2), (cx - icon_w // 6, cy - icon_h // 3)]
            right_horn = [(cx + icon_w // 3, cy - icon_h // 5), (cx + icon_w // 2, cy - icon_h // 2), (cx + icon_w // 6, cy - icon_h // 3)]
            pygame.draw.polygon(surface, color, flame)
            pygame.draw.polygon(surface, color, left_horn)
            pygame.draw.polygon(surface, color, right_horn)
        elif suit_key == "tidewake_dominion":
            pygame.draw.line(surface, color, (cx, cy - icon_h // 2), (cx, cy + icon_h // 2), max(1, icon_w // 10))
            pygame.draw.line(surface, color, (cx - icon_w // 3, cy - icon_h // 8), (cx, cy - icon_h // 2), max(1, icon_w // 12))
            pygame.draw.line(surface, color, (cx + icon_w // 3, cy - icon_h // 8), (cx, cy - icon_h // 2), max(1, icon_w // 12))
            wave_rect = pygame.Rect(cx - icon_w // 2, cy, icon_w, icon_h // 2)
            pygame.draw.arc(surface, color, wave_rect, 3.14, 6.28, max(1, icon_w // 10))
        elif suit_key == "obsidian_veil":
            halo_rect = pygame.Rect(cx - icon_w // 2, cy - icon_h // 2, icon_w, icon_h)
            pygame.draw.arc(surface, color, halo_rect, 0.35, 2.70, max(1, icon_w // 10))
            pygame.draw.arc(surface, color, halo_rect, 3.55, 5.95, max(1, icon_w // 10))
            shard = [(cx, cy - icon_h // 2), (cx + icon_w // 7, cy + icon_h // 2), (cx - icon_w // 7, cy + icon_h // 2)]
            pygame.draw.polygon(surface, color, shard)

    def _draw_hero_icon_at(self, surface: pygame.Surface, cx: int, cy: int, size: int, color: tuple[int, int, int], stroke: tuple[int, int, int]) -> None:
        body = [
            (cx, cy - size // 2),
            (cx + size // 5, cy - size // 6),
            (cx + size // 8, cy + size // 2),
            (cx, cy + size // 5),
            (cx - size // 8, cy + size // 2),
            (cx - size // 5, cy - size // 6),
        ]
        pygame.draw.polygon(surface, color, body)
        pygame.draw.circle(surface, stroke, (cx, cy - size // 18), max(2, size // 10))
        pygame.draw.arc(surface, color, pygame.Rect(cx - size // 2, cy - size // 7, size // 3, size // 2), 1.8, 4.8, max(1, size // 14))
        pygame.draw.arc(surface, color, pygame.Rect(cx + size // 6, cy - size // 7, size // 3, size // 2), -1.7, 1.3, max(1, size // 14))

    def card_back_surface(self, state: str, size: tuple[int, int]) -> pygame.Surface:
        w, h = size
        key = ("card_back", state, w, h)
        cached = self.cache.get(key)
        if cached is not None:
            return cached

        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        radius = max(1, int(w * 0.09))
        border = max(1, int(w * 0.035))
        rect = pygame.Rect(0, 0, w, h)
        pygame.draw.rect(surf, (18, 14, 22), rect, border_radius=radius)
        pygame.draw.rect(surf, self.theme.accent_gold, rect, width=border, border_radius=radius)
        inner = rect.inflate(-int(w * 0.18), -int(h * 0.14))
        pygame.draw.rect(surf, (*self.theme.border_subtle, 170), inner, width=max(1, border // 2), border_radius=max(1, radius // 2))
        pygame.draw.circle(surf, self.theme.accent_ember, rect.center, max(2, int(w * 0.16)), width=max(1, border))
        pygame.draw.circle(surf, self.theme.accent_gold, rect.center, max(2, int(w * 0.07)))
        self.cache.put(key, surf)
        return surf

    def _draw_realm_card(self, card: dict[str, Any], state: str, size: tuple[int, int]) -> pygame.Surface:
        w, h = size
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        suit = card.get("suit", "")
        suit_color = self.theme.suit_colors.get(suit, self.theme.accent_gold)
        paper = (245, 241, 233)

        radius = max(1, int(w * 0.09))
        border = max(1, int(w * 0.03))
        card_rect = pygame.Rect(0, 0, w, h)

        if state == "hovered":
            glow = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*suit_color, self.theme.hover_glow_alpha), glow.get_rect(), border_radius=radius)
            surf.blit(glow, (0, 0))

        pygame.draw.rect(surf, paper, card_rect, border_radius=radius)
        pygame.draw.rect(surf, suit_color, card_rect, width=border, border_radius=radius)

        rank_code = self._rank_code(card.get("rank"))
        rank_font = self.layout.font_cache.get(self.layout.font_cache.display_path, max(16, int(h * 0.36)))
        center_rank = rank_font.render(rank_code, True, suit_color)
        center_rect = center_rank.get_rect(center=(int(w * 0.50), int(h * 0.55)))
        self._blit_text_with_shadow(surf, center_rank, center_rect.topleft)

        self._draw_suit_icon_at(surf, suit, suit_color, int(w * 0.17), int(h * 0.14), int(w * 0.16), int(h * 0.14))

        if state == "selected":
            pygame.draw.rect(surf, self.theme.selected_outline, card_rect, width=max(2, int(w * 0.045)), border_radius=radius)

        if state == "disabled":
            self._apply_disabled_overlay(surf)

        return surf

    def _draw_hero_card(self, card: dict[str, Any], state: str, size: tuple[int, int]) -> pygame.Surface:
        w, h = size
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        radius = max(1, int(w * 0.09))
        border = max(1, int(w * 0.03))
        card_rect = pygame.Rect(0, 0, w, h)
        paper = (246, 240, 228)

        if state == "hovered":
            glow = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*self.theme.accent_gold, self.theme.hover_glow_alpha), glow.get_rect(), border_radius=radius)
            surf.blit(glow, (0, 0))

        pygame.draw.rect(surf, paper, card_rect, border_radius=radius)
        pygame.draw.rect(surf, self.theme.accent_gold, card_rect, width=border, border_radius=radius)

        gold = self.theme.accent_gold
        ink = (42, 33, 24)
        self._draw_hero_icon_at(surf, int(w * 0.15), int(h * 0.14), int(w * 0.18), gold, ink)

        name_font = self.layout.font_cache.get(self.layout.font_cache.display_path, max(12, int(h * 0.12)))
        lines = self._wrap(card.get("name", "Hero"), name_font, int(w * 0.74))[:2]
        rendered = [name_font.render(line, True, ink) for line in lines]
        total_h = sum(line.get_height() for line in rendered) + max(0, len(rendered) - 1) * max(2, int(h * 0.02))
        y = int(h * 0.42) - total_h // 2
        for line_surface in rendered:
            line_rect = line_surface.get_rect(centerx=int(w * 0.50), y=y)
            self._blit_text_with_shadow(surf, line_surface, line_rect.topleft)
            y += line_surface.get_height() + max(2, int(h * 0.02))

        if state == "selected":
            pygame.draw.rect(surf, self.theme.selected_outline, card_rect, width=max(2, int(w * 0.045)), border_radius=radius)

        if state == "disabled":
            self._apply_disabled_overlay(surf)

        return surf

    def _draw_suit_icon(self, surface: pygame.Surface, suit: str, color: tuple[int, int, int], w: int, h: int) -> None:
        cx = int(w * 0.83)
        cy = int(h * 0.16)
        icon_w = int(w * 0.14)
        icon_h = int(h * 0.12)
        self._draw_suit_icon_at(surface, suit, color, cx, cy, icon_w, icon_h)

    def _draw_faction_crest(self, surface: pygame.Surface, faction: str, color: tuple[int, int, int], w: int, h: int) -> None:
        cx = int(w * 0.84)
        cy = int(h * 0.22)
        size = int(min(w, h) * 0.10)
        if faction == "Fellowship":
            pygame.draw.polygon(surface, color, [(cx, cy - size), (cx + size, cy), (cx, cy + size), (cx - size, cy)], width=0)
            pygame.draw.circle(surface, self.theme.surface, (cx, cy), max(1, size // 3))
        elif faction == "Shadow":
            pygame.draw.circle(surface, color, (cx, cy), size)
            pygame.draw.circle(surface, self.theme.surface, (cx, cy), max(1, size // 2), width=max(1, size // 4))
        else:
            pygame.draw.circle(surface, color, (cx, cy), size, width=max(1, size // 4))
            pygame.draw.circle(surface, color, (cx, cy), max(1, size // 5))
            for dx, dy in ((0, -size), (size, 0), (0, size), (-size, 0)):
                pygame.draw.circle(surface, color, (cx + dx, cy + dy), max(1, size // 6))

    def _apply_disabled_overlay(self, surface: pygame.Surface) -> None:
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill(self.theme.disabled_overlay)

        step = max(4, int(surface.get_width() * 0.08))
        for x in range(-surface.get_height(), surface.get_width(), step):
            pygame.draw.line(
                overlay,
                self.theme.disabled_pattern,
                (x, 0),
                (x + surface.get_height(), surface.get_height()),
                max(1, int(surface.get_width() * 0.015)),
            )

        surface.blit(overlay, (0, 0))

    def _wrap(self, text: str, font: pygame.font.Font, max_w: int) -> list[str]:
        words = text.split()
        if not words:
            return []

        lines = [words[0]]
        for word in words[1:]:
            candidate = f"{lines[-1]} {word}"
            if font.size(candidate)[0] <= max_w:
                lines[-1] = candidate
            else:
                lines.append(word)
        return lines
