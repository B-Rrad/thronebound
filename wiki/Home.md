# Thronebound Wiki

This wiki translates the written technical report into a navigable GitHub knowledge base for the current `Thronebound` build. It keeps the report's core goals intact while adding direct links to code, playable artifacts, and multimedia.

![Thronebound background](https://raw.githubusercontent.com/B-Rrad/thronebound/main/background.jpg)

## Quick Start

- Play the browser build: [Live web demo](https://drpeterjamieson.com/PROJECTS/THRONEBOUND/index.html)
- Watch the project in action: [Gameplay video](https://youtu.be/ONRpg0IdMZ4)
- Browse the source: [GitHub repository](https://github.com/B-Rrad/thronebound)
- Jump into the design pages: [[Game Overview]] | [[Rules and Hero System]] | [[Architecture and Code Map]] | [[Testing and Results]] | [[Media and Deployment]] | [[References]]

## Executive Summary

`Thronebound` is a two-player fantasy card game inspired by the attack-and-defense structure of *Durak*. The current digital build supports local two-player play, one-player matches against multiple AI opponents, responsive desktop UI, a browser rewrite, generated card art, and simulation-based balance analysis. The project is publishable as a class-project prototype because it is playable, measurable, and structured well enough for future contributors to extend without reverse engineering one large script. [R1](References#r1) [R4](References#r4)

## Why This Project Matters

- Digital rules enforcement removes the bookkeeping burden of the tabletop version.
- AI opponents make the game teachable and usable in single-player mode.
- The current build is modular enough to support new content, balance tuning, and deployment experiments.
- The browser rewrite lowers distribution friction and creates a path toward web-first publishing.

## Requirement Coverage

| Requirement | Evidence in the current build |
| --- | --- |
| Reasonable AI stronger than random | The desktop version includes `Random`, `Greedy`, and `Strategic` AI, and simulation results show `Random` loses heavily to stronger policies. See [[Testing and Results]]. |
| One-player or two-player support | The desktop build supports one human versus AI or two local human players. The browser build currently supports local play with the rewrite scaffold already in place. |
| Polished UI | The project includes a dedicated splash screen, music toggle, animated card motion, cached card rendering, custom fonts, and distinct draft/play/game-over scenes. |
| Balance testing | [`balance_analysis.py`](https://github.com/B-Rrad/thronebound/blob/main/balance_analysis.py) produces repeatable simulation output stored under [`analysis_outputs/`](https://github.com/B-Rrad/thronebound/tree/main/analysis_outputs). |
| Submission-ready artifacts | The repo includes the desktop source, a packaged browser build archive, a previous Windows executable, and linked demo media. |

## Recommended Reading Path

1. Start with [[Game Overview]] for the problem statement, audience, and current project identity.
2. Read [[Rules and Hero System]] to understand the implemented gameplay and the Ringbound-to-Thronebound theme transition.
3. Use [[Architecture and Code Map]] to connect the report to the actual source files.
4. Review [[Testing and Results]] for balance, pacing, and hero-usage evidence.
5. Finish with [[Media and Deployment]] for publishing artifacts, multimedia, and future release paths.

## Code Entry Points

- Desktop launcher: [`main.py`](https://github.com/B-Rrad/thronebound/blob/main/main.py)
- Desktop composition root: [`ringbound_game/ui_game.py`](https://github.com/B-Rrad/thronebound/blob/main/ringbound_game/ui_game.py)
- Browser rewrite: [`web/src/ringbound.ts`](https://github.com/B-Rrad/thronebound/blob/main/web/src/ringbound.ts)
- Core data files: [`data/realm_cards.json`](https://github.com/B-Rrad/thronebound/blob/main/data/realm_cards.json), [`data/hero_cards.json`](https://github.com/B-Rrad/thronebound/blob/main/data/hero_cards.json), [`data/dominions.json`](https://github.com/B-Rrad/thronebound/blob/main/data/dominions.json)

## Notes for Contributors

The repository still contains some legacy `Ringbound` names in file paths and IDs even though the player-facing build is now `Thronebound`. That mismatch is documented throughout this wiki so future contributors can navigate both naming systems safely. See [[Game Overview]] and [[Rules and Hero System]].
