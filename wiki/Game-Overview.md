# Game Overview

Return to [[Home]].

## Page Guide

- Problem statement and publication rationale
- Intended audience
- What the current build is
- Why the theme and data model matter

## Relevance and Problem Statement

`Thronebound` exists because the original tabletop design benefits from digital enforcement. The game asks players to track draft order, the crowned dominion, attack and defense legality, hero powers, wound totals, and endgame tiebreakers. Those systems create interesting decisions, but they also create many opportunities for human error when managed manually. The digital build solves that by acting as the rules referee and by exposing only legal actions that make sense in the current phase. [R1](References#r1) [R3](References#r3)

The project also addresses continuity. Earlier versions were playable but harder to maintain. The current repository refactors the game into focused modules, preserves a demonstration executable, and begins a browser rewrite that shares the same JSON card data. That makes the project easier to extend, hand off, and evaluate. [R1](References#r1) [R4](References#r4)

## Why This Design Should Be Published

This build already demonstrates the qualities of a small publishable strategy prototype:

- Matches are readable and fast because the game uses a 36-card realm deck, 12 unique hero cards, and only two players.
- Solo play is available through multiple AI opponents, so the game does not require online multiplayer to be useful.
- The current presentation includes refreshed theme work, custom fonts, background art, music, animation, and separate splash and gameplay screens.

These features make the project more than a design document. They show a working artifact with a clear player experience and measurable behavior. [R1](References#r1)

## Audience and Technical Assumptions

This wiki is written for technically literate readers who want both design context and engineering context. It assumes familiarity with basic programming concepts such as modules, JSON, state, and event loops, but it does not assume prior knowledge of `Thronebound`. Readers who want the implementation map should continue to [[Architecture and Code Map]].

## What the Current Game Is

`Thronebound` is a two-player fantasy card duel. Each match begins with a visible shared draft of realm cards and hero cards. After drafting, one player attacks and the other defends. Realm cards handle the baseline combat loop, while hero cards create one-time disruptions or exceptions. Players continue until one reaches six wounds or the realm-deck endgame determines a winner. [R1](References#r1)

The current player-facing theme is Greek-myth-inspired `Thronebound`, but the repository lineage still shows older `Ringbound` naming in some file paths, executable names, and hero IDs. This matters for anyone reading the source:

- Player-facing title: `Thronebound: Battle for the Throne`
- Legacy code namespace: `ringbound_game`
- Legacy internal hero IDs in JSON and logic: `aragorn`, `legolas`, `gandalf`, and similar keys now map to new mythic hero names

The detailed name mapping is documented in [[Rules and Hero System]].

## Why the Theme and Structure Matter

The theme refresh improves originality and publishability by moving away from earlier direct fantasy franchise inspiration and toward a more distinct Greek-mythology presentation. At the same time, the project's data-driven structure keeps content separate from logic:

- Dominion definitions: [`data/dominions.json`](https://github.com/B-Rrad/thronebound/blob/main/data/dominions.json)
- Realm cards: [`data/realm_cards.json`](https://github.com/B-Rrad/thronebound/blob/main/data/realm_cards.json)
- Hero cards: [`data/hero_cards.json`](https://github.com/B-Rrad/thronebound/blob/main/data/hero_cards.json)
- Browser rewrite consuming shared data: [`web/src/ringbound.ts`](https://github.com/B-Rrad/thronebound/blob/main/web/src/ringbound.ts)

Because of that separation, new content and future balance passes do not require redesigning the entire engine. [R1](References#r1) [R4](References#r4)

## Where to Go Next

- For gameplay rules and hero clarifications, continue to [[Rules and Hero System]].
- For source-level structure and code links, continue to [[Architecture and Code Map]].
