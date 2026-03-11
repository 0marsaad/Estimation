# SCORING_ENGINE.md

Estimation Game – Formal Scoring Specification

This document defines the **exact scoring logic** used by the Estimation game scoring engine.
It is intended for developers or coding agents implementing the **score calculation module**.

The scoring engine receives the **results of a completed round** and calculates the score change for each player.

---

# 1. Inputs to the Scoring Engine

For each player in a round, the scoring engine must receive the following data:

```json
{
  "estimated_tricks": int,
  "tricks_won": int,
  "is_caller": boolean,
  "is_with": boolean,
  "is_dash_call": boolean,
  "risk": int,
  "round_type": "OVER | UNDER",
  "double_score": boolean
}
```

Global round inputs:

```json
{
  "total_estimates": int,
  "trump": "SANS | SPADES | HEARTS | DIAMONDS | CLUBS"
}
```

---

# 2. Derived Round Values

Before calculating scores, the system must derive several round properties.

### Determine Round Type

```python
if total_estimates >= 14:
    round_type = "OVER"
elif total_estimates <= 12:
    round_type = "UNDER"
```

---

### Risk Calculation

Risk increases when estimates deviate from 13.

Formula:

```python
risk = floor(abs(total_estimates - 13) / 2)
```

Example:

```
total_estimates = 17
difference = 4
risk = 2
```

---

# 3. Base Scoring Concept

Players **win** if:

```
tricks_won == estimated_tricks
```

Players **lose** if:

```
tricks_won != estimated_tricks
```

Base scoring depends on:

* caller status
* with status
* dash call
* round type
* risk multiplier

---

# 4. Caller Scoring

The **Caller** is the player who won the bidding phase.

### Caller Win

Condition:

```
tricks_won == estimated_tricks
```

Score:

```
score = estimated_tricks × 10
```

Example:

```
estimate = 6
score = 60
```

---

### Caller Lose

Condition:

```
tricks_won != estimated_tricks
```

Score:

```
score = - (estimated_tricks × 10)
```

Example:

```
estimate = 6
score = -60
```

---

# 5. "With" Player Scoring

A player is **WITH** when:

```
estimated_tricks == caller_estimate
```

The WITH player uses **Caller scoring rules**.

### With Win

```
score = estimated_tricks × 10
```

### With Lose

```
score = - (estimated_tricks × 10)
```

---

# 6. Normal Player Scoring

For players that are **not Caller, not With, and not Dash Call**.

### Win

```
score = estimated_tricks × 10
```

### Lose

```
score = - (estimated_tricks × 10)
```

---

# 7. Dash Call Scoring

Dash Call means the player declared **0 tricks before bidding**.

Dash Call scoring differs depending on round type.

---

## Dash Call – Over Round

### Win (player wins 0 tricks)

```
score = +100
```

### Lose (player wins ≥1 trick)

```
score = -100
```

---

## Dash Call – Under Round

### Win

```
score = +70
```

### Lose

```
score = -70
```

---

# 8. Risk Multiplier

Risk increases rewards and penalties.

Risk value:

```
risk = floor(abs(total_estimates - 13) / 2)
```

Score multiplier:

```
multiplier = 1 + risk
```

Example:

```
risk = 2
multiplier = 3
```

Final score:

```
score = base_score × multiplier
```

Example:

```
base_score = 40
risk = 1
multiplier = 2

final_score = 80
```

---

# 9. Double Score Rule

If the previous round was skipped because **all players passed bidding**, the next round has:

```
double_score = True
```

If enabled:

```
score = score × 2
```

This applies **after risk calculation**.

---

# 10. Score Calculation Order

The scoring engine must apply calculations in this order:

```
1. Determine round type
2. Determine risk
3. Calculate base score
4. Apply risk multiplier
5. Apply double score
6. Return final score
```

Pseudo-implementation:

```python
def calculate_score(player, round_data):

    base_score = get_base_score(player)

    score = base_score * (1 + round_data.risk)

    if round_data.double_score:
        score *= 2

    return score
```

---

# 11. Example Round

Example round:

```
Caller: Player A
Caller Estimate: 6

Player A estimate = 6
Player B estimate = 4
Player C estimate = 2
Player D estimate = 2
```

Total estimates:

```
6 + 4 + 2 + 2 = 14
```

Round type:

```
OVER
```

Risk:

```
abs(14 - 13) = 1
risk = 0
```

Results:

```
Player A tricks = 6 → win → +60
Player B tricks = 3 → lose → -40
Player C tricks = 2 → win → +20
Player D tricks = 2 → win → +20
```

---

# 12. Final Score Update

After calculating the round score:

```
player.total_score += round_score
```

Example:

```
previous_total = 120
round_score = 40

new_total = 160
```

---

# 13. Recommended Implementation Pattern

The scoring engine should be implemented as a **pure logic module** separate from the backend framework.

Example structure:

```
scoring/
    engine.py
    dash_call.py
    caller_score.py
    risk.py
```

Example main function:

```python
def calculate_round_scores(round_data, players):
    for player in players:
        player.score = calculate_score(player, round_data)
```

---

# 14. Determining the Winner

After **18 rounds**:

```
winner = player with highest total_score
```

---

# End of Scoring Engine Specification
