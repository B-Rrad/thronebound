# UI Architecture

## Data Flow

1. `ringbound_game/ui_game.py` composes the game object from focused rule/state mixins.
2. `UIController` receives pygame events and returns high-level `Intent` values.
3. `RingboundGame.handle_intent()` maps each intent to rule methods (`attempt_draft`, `handle_hand_card_click`, `resolve_suit_choice`, etc.).
4. `RingboundGame.run()` calls `ui.draw(screen, self)` every frame.
5. `Renderer` reads the immutable snapshot of game state and draws the scene.

This keeps UI rendering/input separate from rule enforcement.

## Package Layout

- `ringbound_game/ui_game.py`: composition root and pygame setup.
- `ringbound_game/state.py`: decks, hands, player lookup, trump state, setup/reset helpers.
- `ringbound_game/drafting.py`: draft legality, AI draft picks, and transition into play.
- `ringbound_game/rules.py`: attack/defense legality, playable-card checks, and AI-visible card queries.
- `ringbound_game/heroes.py`: hero activation, pending hero choices, and hero resolution.
- `ringbound_game/rounds.py`: card play, concessions, round cleanup, draw-up, and game-over checks.
- `ringbound_game/ai_turns.py`: AI action selection and dispatch.
- `ringbound_game/events.py`: pygame event handling, intent mapping, resize handling, and main loop.
- `ringbound_game/audio.py`: music playback.
- `ui/__init__.py`: `UIController` and public export surface.
- `ui/theme.py`: design tokens and color constants.
- `ui/font_cache.py`: cached `pygame.font.Font` objects by file path and point size.
- `ui/layout.py`: `LayoutManager` computes all responsive rectangles and scaled font sizes.
- `ui/card_cache.py`: vector card rendering and surface cache keyed by card/state/size.
- `ui/animator.py`: tween model and easing for short UI animations.
- `ui/input_handler.py`: event routing and click-hit logic returning `Intent`.
- `ui/renderer.py`: full scene composition for splash, drafting, playing, and game over.

## Resize Behavior

- `RingboundGame.handle_events()` listens for `VIDEORESIZE`.
- Window is recreated with `pygame.RESIZABLE` dimensions clamped to at least `1024x600`.
- `UIController.on_resize()` calls `LayoutManager.reflow(new_w, new_h)` and clears cached card surfaces.
- Input re-hit-testing runs immediately so hover state stays correct.

## Adding a New Card Type

1. Add the card shape/text rules in `ui/card_cache.py`.
2. Extend cache key construction if the new card introduces extra visual state.
3. Ensure game state passes a distinct marker field so renderer can branch card drawing.

## Adding a New Game Phase

1. Keep game logic in the relevant `ringbound_game/` module.
2. Add phase presentation in `ui/renderer.py` (labels, actionable buttons, zones).
3. Add any new interactions in `ui/input_handler.py` as intents.
4. Map new intents in `RingboundGame.handle_intent`.

## Performance Notes

- Card surfaces are cached and reused; drawing primitives are not rerun every frame for unchanged size/state.
- Font objects are cached and rebuilt only on resize.
- Animations are time-based and non-blocking (no sleep/wait in main loop).
