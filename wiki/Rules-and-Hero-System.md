# Rules and Hero System

Return to [[Home]].

## Page Guide

- Match setup and draft flow
- Live-play rules
- Implemented hero clarifications
- Theme mapping from Ringbound to Thronebound

## Rules of Play in the Current Build

The realm deck contains 36 cards: four dominions with ranks `6` through `Ace`. The hero deck contains 12 unique special cards. At match start:

1. Each player receives one realm card from the shuffled realm deck.
2. Those two opening cards determine draft order and the first attacker.
3. One additional realm card is revealed as the crowned dominion for the match.
4. The game reveals 10 more realm cards and 8 hero cards as shared visible draft pools.
5. Players alternate drafting until both draft caps are filled or no legal picks remain.

Each player finishes with a maximum of 6 realm cards and 4 hero cards, counting the opening realm card. [R1](References#r1) [R3](References#r3)

## Live Play

During play, the attacker leads with a realm card. The defender must answer the newest attack with a higher card of the same dominion or a valid crowned-dominion card. If the defense succeeds, the attacker may reinforce with a card whose rank matches one already on the table unless a hero effect changes the rule.

If the defender cannot or chooses not to continue:

- The defender concedes the round.
- The defender takes one wound.
- The attacker keeps initiative for the next round.

If the round is fully defended:

- The roles swap.
- Both players clean up and draw back toward six realm cards while the realm deck still has cards.

A player loses immediately upon reaching six wounds. Once the realm deck is empty, the code applies this tiebreak order:

1. First player to empty all realm cards wins.
2. If both realm hands are empty, fewer wounds wins.
3. If wounds are tied, fewer total remaining cards wins.
4. If everything is equal, the game selects a winner at random and records the reason on the game-over screen. [R1](References#r1)

## Implemented Hero Clarifications

The hero system is the most rules-dense part of the project, so the current build's exact behavior matters. These are the important implementation notes carried over from the report:

| Topic | Implemented behavior |
| --- | --- |
| `Asclepius` timing | May be used whenever that player has wounds remaining; the code does not restrict it to a narrow phase window. |
| `Autolycus` timing | Lets the player who used it choose a temporary crowned dominion for the current round. |
| `Circe` timing | Names one dominion that the defender cannot play for the rest of the round. |
| `Ares` timing | Must be paired with an attack card, and the extra wound applies only if that specific attack survives through a fully defended round end. |
| Conceded defense cleanup | Attack cards are discarded, but defense cards already played return to the defender's hand. |
| Deck-empty endgame | The code checks empty realm hands first, then wounds, then total remaining cards; it does not require all hero cards to be spent first. |

For the source-level implementation of these rules, see:

- Hero handling: [`ringbound_game/heroes.py`](https://github.com/B-Rrad/thronebound/blob/main/ringbound_game/heroes.py)
- Combat and legality checks: [`ringbound_game/combat.py`](https://github.com/B-Rrad/thronebound/blob/main/ringbound_game/combat.py), [`ringbound_game/rules.py`](https://github.com/B-Rrad/thronebound/blob/main/ringbound_game/rules.py)
- Round cleanup and endgame: [`ringbound_game/rounds.py`](https://github.com/B-Rrad/thronebound/blob/main/ringbound_game/rounds.py)
- Browser rewrite parity notes: [`WEB_REWRITE.md`](https://github.com/B-Rrad/thronebound/blob/main/WEB_REWRITE.md)

## Hero Mapping

The player-facing hero roster has been rethemed. Internally, several IDs still use older `Ringbound` names, which is why both naming systems appear in the code.

| Legacy Ringbound character | Current Thronebound character | Current ability |
| --- | --- | --- |
| Aragorn | Odysseus | Return one played attack card to your hand |
| Legolas | Achilles | Add one attack card regardless of rank |
| Gandalf | Athena | Cancel one non-crown attack |
| Galadriel | Asclepius | Heal two wounds at any time |
| Frodo | Hermes | Disable the crowned dominion for one round |
| Boromir | Ajax | Auto-defend one attack; attacker discards one random card |
| Nazgul | Hades | Defender may use only crown cards |
| Saruman | Medea | Exchange one card with defender's highest or crown card |
| Sauron | Argus Panoptes | View opponent's hand |
| Balrog | Ares | Inflict one wound even if fully defended |
| Gollum | Autolycus | Redefine the crown suit for one round |
| Wormtongue | Circe | Name a dominion the defender cannot play this round |

The canonical current hero data lives in [`data/hero_cards.json`](https://github.com/B-Rrad/thronebound/blob/main/data/hero_cards.json).

## Dominion Mapping

| Legacy Ringbound region | Current Thronebound dominion |
| --- | --- |
| Gondor | Verdant Court |
| Shire | Ember Throne |
| Rohan | Tidewake Dominion |
| Mordor | Obsidian Veil |

Dominion identity and art-direction notes live in [`data/dominions.json`](https://github.com/B-Rrad/thronebound/blob/main/data/dominions.json).

## Visual Reference

| Hero | Card art |
| --- | --- |
| Odysseus | ![Odysseus](https://raw.githubusercontent.com/B-Rrad/thronebound/main/output/card_placeholders/heroes/odysseus.png) |
| Achilles | ![Achilles](https://raw.githubusercontent.com/B-Rrad/thronebound/main/output/card_placeholders/heroes/achilles.png) |
| Athena | ![Athena](https://raw.githubusercontent.com/B-Rrad/thronebound/main/output/card_placeholders/heroes/athena.png) |
| Medea | ![Medea](https://raw.githubusercontent.com/B-Rrad/thronebound/main/output/card_placeholders/heroes/medea.png) |

## Where to Go Next

- For architecture and module responsibilities, continue to [[Architecture and Code Map]].
- For balance evidence and testing results, continue to [[Testing and Results]].
