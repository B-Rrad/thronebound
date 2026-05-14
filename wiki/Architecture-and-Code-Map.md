# Architecture and Code Map

Return to [[Home]].

## Page Guide

- Why the architecture is worth building on
- Data flow through the desktop app
- Core files and responsibilities
- Shared-data pipeline across desktop and browser builds

## Why the Current Architecture Supports Further Investment

The current codebase is no longer a single prototype script. Responsibilities are split across state, drafting, combat, hero logic, rounds, AI turns, event handling, UI layout, rendering, animation, and browser-specific code. That separation makes the project easier to extend, test, and hand to another engineer. [R1](References#r1) [R4](References#r4)

## Desktop Data Flow

The desktop build follows a clean loop from input to intent to rules to rendering:

1. [`main.py`](https://github.com/B-Rrad/thronebound/blob/main/main.py) launches the game.
2. [`ringbound_game/ui_game.py`](https://github.com/B-Rrad/thronebound/blob/main/ringbound_game/ui_game.py) composes the main `RingboundGame` object from focused mixins.
3. [`ui/input_handler.py`](https://github.com/B-Rrad/thronebound/blob/main/ui/input_handler.py) and the public `UIController` turn pygame events into higher-level intents.
4. Rule modules enforce legality and mutate state.
5. [`ui/renderer.py`](https://github.com/B-Rrad/thronebound/blob/main/ui/renderer.py) reads the current state snapshot and draws the scene.

This division keeps rendering and input separate from the game rules while still allowing tight iteration on UI behavior. See also [`ARCHITECTURE.md`](https://github.com/B-Rrad/thronebound/blob/main/ARCHITECTURE.md).

## Core Files and Responsibilities

| File or directory | Responsibility |
| --- | --- |
| [`main.py`](https://github.com/B-Rrad/thronebound/blob/main/main.py) | Launch entry point that instantiates the desktop game. |
| [`ringbound_game/ui_game.py`](https://github.com/B-Rrad/thronebound/blob/main/ringbound_game/ui_game.py) | Composition root for the desktop build; initializes `pygame`, loads assets, configures AI, and wires in the main gameplay mixins. |
| [`ringbound_game/state.py`](https://github.com/B-Rrad/thronebound/blob/main/ringbound_game/state.py) | Deck setup, reset logic, player lookup helpers, round-effect tracking, and draft setup. |
| [`ringbound_game/drafting.py`](https://github.com/B-Rrad/thronebound/blob/main/ringbound_game/drafting.py) | Draft legality, AI drafting, drafter switching, and the transition into live play. |
| [`ringbound_game/rules.py`](https://github.com/B-Rrad/thronebound/blob/main/ringbound_game/rules.py) and [`ringbound_game/combat.py`](https://github.com/B-Rrad/thronebound/blob/main/ringbound_game/combat.py) | Attack and defense legality, playable-card checks, and combat helpers. |
| [`ringbound_game/heroes.py`](https://github.com/B-Rrad/thronebound/blob/main/ringbound_game/heroes.py) | Hero timing checks, pending hero actions, suit-choice resolution, healing, hand reveal, discard, and special attack handling. |
| [`ringbound_game/rounds.py`](https://github.com/B-Rrad/thronebound/blob/main/ringbound_game/rounds.py) | Wounds, role switching, cleanup, draw-up logic, and game-over checks. |
| [`ringbound_game/ai_turns.py`](https://github.com/B-Rrad/thronebound/blob/main/ringbound_game/ai_turns.py) | AI action selection and dispatch. |
| [`ringbound_game/events.py`](https://github.com/B-Rrad/thronebound/blob/main/ringbound_game/events.py) | Event loop, resize handling, and top-level runtime flow. |
| [`ui/`](https://github.com/B-Rrad/thronebound/tree/main/ui) | Responsive layout, animation, cached card rendering, font caching, input routing, and scene drawing. |
| [`data/`](https://github.com/B-Rrad/thronebound/tree/main/data) | JSON definitions for realm cards, heroes, dominions, and asset specifications. |
| [`balance_analysis.py`](https://github.com/B-Rrad/thronebound/blob/main/balance_analysis.py) | Simulation engine and heuristic AI evaluation used to generate balance evidence. |
| [`web/`](https://github.com/B-Rrad/thronebound/tree/main/web) | TypeScript and canvas rewrite that ports core rules and shares the JSON data pipeline. |

## UI Layer

The desktop UI package handles most of the project polish:

- [`ui/layout.py`](https://github.com/B-Rrad/thronebound/blob/main/ui/layout.py) computes responsive rectangles and scaled font sizes.
- [`ui/card_cache.py`](https://github.com/B-Rrad/thronebound/blob/main/ui/card_cache.py) caches rendered card surfaces to avoid unnecessary redraw work.
- [`ui/animator.py`](https://github.com/B-Rrad/thronebound/blob/main/ui/animator.py) manages short, time-based UI animation.
- [`ui/renderer.py`](https://github.com/B-Rrad/thronebound/blob/main/ui/renderer.py) draws splash, draft, play, and game-over scenes.
- [`ui/theme.py`](https://github.com/B-Rrad/thronebound/blob/main/ui/theme.py) centralizes visual tokens and colors.

These modules are part of why the report can argue that the project is more polished than a simple proof of concept. [R1](References#r1)

## Shared Data Across Platforms

One of the strongest engineering decisions in the repo is the shared content pipeline:

- Desktop loads card and dominion data through Python helpers and JSON.
- Browser loads the same card and dominion JSON files directly in TypeScript.
- Card placeholder art under [`output/card_placeholders/`](https://github.com/B-Rrad/thronebound/tree/main/output/card_placeholders) is reused by the web build.

Important entry points:

- Desktop data loading: [`resource_manager.py`](https://github.com/B-Rrad/thronebound/blob/main/resource_manager.py)
- Browser game implementation: [`web/src/ringbound.ts`](https://github.com/B-Rrad/thronebound/blob/main/web/src/ringbound.ts)
- Browser rewrite notes: [`WEB_REWRITE.md`](https://github.com/B-Rrad/thronebound/blob/main/WEB_REWRITE.md)

This structure supports low-risk content expansion and makes future deployment options more realistic. [R1](References#r1) [R4](References#r4)

## Extension Paths

The current architecture supports several practical next steps:

- Add new dominions or heroes by extending the JSON data files and art assets.
- Tune AI heuristics by updating [`balance_analysis.py`](https://github.com/B-Rrad/thronebound/blob/main/balance_analysis.py) and the AI modules.
- Continue decomposing the large browser file [`web/src/ringbound.ts`](https://github.com/B-Rrad/thronebound/blob/main/web/src/ringbound.ts) into smaller modules as that implementation stabilizes.
- Resolve the remaining `Ringbound` versus `Thronebound` naming mismatch to make the project easier for new contributors to navigate.

## Where to Go Next

- For measured evidence and balance data, continue to [[Testing and Results]].
- For deployment artifacts and multimedia, continue to [[Media and Deployment]].
