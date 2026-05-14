# Testing and Results

Return to [[Home]].

## Page Guide

- Simulation procedure
- Fairness evidence
- Skill-sensitivity evidence
- Pace and termination evidence
- Hero-usage indicators

## Testing Procedure

The main experimental method in this project is the simulator in [`balance_analysis.py`](https://github.com/B-Rrad/thronebound/blob/main/balance_analysis.py). The included report summarizes six experiment groups:

- Three self-play groups with `2,000` games each
- Three cross-play groups with `1,500` games each
- `10,500` total simulated games

The experiments answer three practical questions:

1. Does same-skill play stay close to even?
2. Do stronger policies beat weaker ones often enough to show skill sensitivity?
3. Do games terminate consistently without stalling? [R1](References#r1)

The exported data used by the report is stored under [`analysis_outputs/`](https://github.com/B-Rrad/thronebound/tree/main/analysis_outputs).

## Fairness Evidence

Same-skill self-play stays close to a 50/50 split, which suggests that no seat position or opening role dominates the game.

| Experiment | P1 win rate | First attacker win rate | Average rounds |
| --- | ---: | ---: | ---: |
| Random vs Random | 48.85% | 48.60% | 18.25 |
| Greedy vs Greedy | 51.00% | 46.90% | 17.21 |
| Strategic vs Strategic | 50.20% | 46.70% | 16.23 |

The largest first-attacker deviation appears in `Strategic` self-play at `46.7%`, which is only `3.3` percentage points away from a perfect split. That supports the claim that the game has role texture without a broken opening advantage. [R1](References#r1)

## Skill Sensitivity Evidence

Cross-skill matchups show that the game is not a pure coin flip. Better policy design changes outcomes noticeably.

| Experiment | Label A win rate | Average rounds |
| --- | ---: | ---: |
| Random vs Greedy | 15.93% | 17.79 |
| Random vs Strategic | 12.87% | 17.17 |
| Greedy vs Strategic | 55.60% | 17.36 |

These numbers show that `Random` performs much worse than the stronger policies. In the current heuristic design, `Greedy` also outperforms `Strategic`, which suggests the AI labels should be interpreted as current policy names rather than a permanent difficulty ladder. [R1](References#r1)

## Speed and Termination Evidence

Across all `10,500` simulated games, the pace metrics are strong for a short-session strategy prototype:

| Metric | Value |
| --- | ---: |
| Total simulated games | 10,500 |
| Average rounds per game | 17.32 |
| Median rounds per game | 17 |
| Minimum observed rounds | 6 |
| Maximum observed rounds | 27 |
| Games requiring emergency tiebreak | 0 |

Zero emergency tiebreak cases is especially important because it shows the current rules terminate cleanly in large simulation batches. [R1](References#r1)

## Hero-Usage Indicators

Hero-usage exports offer a second lens on balance. They do not prove that any one hero is overpowered by themselves, because use rate and AI timing both influence the numbers, but they help identify effects worth further playtesting.

| Hero ID | Uses | Use per draft | Winner share of uses |
| --- | ---: | ---: | ---: |
| Hades | 6656 | 0.947 | 0.492 |
| Medea | 6403 | 0.913 | 0.661 |
| Ares | 3374 | 0.477 | 0.732 |
| Asclepius | 1970 | 0.282 | 0.300 |
| Hermes | 1965 | 0.282 | 0.361 |

In the current data, `Medea` and `Ares` stand out with especially high winner-share values among used cases, while `Asclepius` and `Hermes` are used much less frequently in simulation. These are good targets for future human playtesting and AI-timing review. [R1](References#r1)

## Discussion

The results support three claims:

- The game is fair enough for a project prototype because same-skill matchups remain near even.
- The game rewards better decisions enough that policy strength changes outcomes.
- The rules terminate in a controlled number of rounds, making the game practical for demonstrations and solo learning sessions.

These findings strengthen the case for limited publication, especially when combined with the project's polished UI, browser demo path, and modular architecture. The remaining caution is that simulation measures fairness and termination, not player enjoyment. Human playtesting is still necessary. [R1](References#r1)

## Related Files

- Simulator: [`balance_analysis.py`](https://github.com/B-Rrad/thronebound/blob/main/balance_analysis.py)
- Summary export: [`analysis_outputs/summary.csv`](https://github.com/B-Rrad/thronebound/blob/main/analysis_outputs/summary.csv)
- Hero usage export: [`analysis_outputs/hero_usage.csv`](https://github.com/B-Rrad/thronebound/blob/main/analysis_outputs/hero_usage.csv)
- Draft report output: [`analysis_outputs/ringbound_balance_report_draft.md`](https://github.com/B-Rrad/thronebound/blob/main/analysis_outputs/ringbound_balance_report_draft.md)

## Where to Go Next

- For code structure behind these systems, continue to [[Architecture and Code Map]].
- For demo links and publishable artifacts, continue to [[Media and Deployment]].
