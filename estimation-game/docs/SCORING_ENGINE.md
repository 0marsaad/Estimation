# SCORING_ENGINE.md

Formal Scoring Rules for Estimation Game

This document defines the **exact scoring formulas** used by the Estimation scoring engine.

The scoring rules follow the **standard Estimation scoring table** shown in the game UI, with one exception:

> When a player's **called tricks ≥ 8**, a **quadratic scoring rule** is applied instead of the standard scoring formula.

This document describes both systems.

---

# 1. Inputs

For each player in a round:

```json
{
  "called_tricks": int,
  "won_tricks": int,
  "is_caller": boolean,
  "is_with": boolean,
  "risk": int,
  "is_dash_call": boolean,
  "dash_type": "OVER | UNDER",
  "is_only_winner": boolean,
  "is_only_loser": boolean
}
```

Round inputs:

```json
{
  "round_type": "OVER | UNDER",
  "double_score": boolean
}
```

---

# 2. Determine Win / Loss

A player **wins** if:

```
won_tricks == called_tricks
```

A player **loses** if:

```
won_tricks != called_tricks
```

---

# 3. Standard Scoring (Calls < 8)

If:

```
called_tricks < 8
```

the scoring follows the **table shown in the game UI**.

Base score components:

| Component           | Win            | Loss           |
| ------------------- | -------------- | -------------- |
| Round Score         | +10            | -10            |
| Tricks Amount       | +called_tricks | -called_tricks |
| Caller / With       | +10            | -10            |
| Only Winner / Loser | +10            | -10            |
| Each Risk           | +10            | -10            |
| (+ ) Dash Call      | +25            | -25            |
| (- ) Dash Call      | +33            | -33            |

---

# 4. Standard Score Formula (Calls < 8)

Initialize score:

```
score = 0
```

Then apply:

### Round Score

```
score += ±10
```

---

### Tricks Amount

```
score += ±called_tricks
```

---

### Caller / With Bonus

If:

```
is_caller == True
OR
is_with == True
```

then:

```
score += ±10
```

---

### Only Winner / Loser

If:

```
is_only_winner == True
OR
is_only_loser == True
```

then:

```
score += ±10
```

---

### Risk Bonus

For each risk:

```
score += ±10 × risk
```

---

### Dash Call Bonus

If dash call occurred:

```
OVER Dash Call → ±25
UNDER Dash Call → ±33
```

---

# 5. High Call Scoring (Calls ≥ 8)

When:

```
called_tricks ≥ 8
```

the game uses **quadratic scoring** instead of the standard scoring table.

---

# 6. High Call Win Formula

If the player **wins**:

```
score = called_tricks²
```

Example:

```
called_tricks = 8

score = 8² = 64
```

Example:

```
called_tricks = 9

score = 9² = 81
```

---

# 7. High Call Loss Formula

If the player **loses**:

First compute:

```
difference = abs(won_tricks - called_tricks)
```

Then compute:

```
score = -(called_tricks² / 2) - (difference - 1)
```

Example:

```
called_tricks = 8
won_tricks = 6

difference = 2

score = -(64 / 2) - (2 - 1)
score = -32 - 1
score = -33
```

Example:

```
called_tricks = 9
won_tricks = 7

difference = 2

score = -(81 / 2) - (2 - 1)
score = -40.5 - 1
score = -41.5
```

Scores should be **rounded toward zero or to the nearest integer depending on implementation policy**.

---

# 8. Bonuses for High Calls

When **called_tricks ≥ 8**, the following rules apply:

The **quadratic score replaces the entire standard table**, meaning:

The following components are **NOT applied**:

```
Round Score
Tricks Amount
Caller / With
Only Winner / Loser
Risk
```

Dash Call scoring **still applies** if relevant.

---

# 9. Dash Call Scoring

Dash calls are evaluated separately.

## Over Dash Call

```
Win  = +25
Loss = -25
```

---

## Under Dash Call

```
Win  = +33
Loss = -33
```

These values are **added to the final score**.

---

# 10. Double Score Rule

If the previous round was skipped due to all players passing:

```
double_score = True
```

Then:

```
score = score × 2
```

This is applied **after all calculations**.

---

# 11. Score Calculation Order

The scoring engine must apply calculations in this order:

```
1. Determine win or loss
2. Check called_tricks
3. If called_tricks < 8 → apply standard scoring
4. If called_tricks ≥ 8 → apply quadratic scoring
5. Apply dash call bonus
6. Apply double score if active
```

---

# 12. Example (Standard Call)

```
called_tricks = 5
won_tricks = 5
risk = 1
is_caller = True
```

Calculation:

```
Round Score = +10
Tricks Amount = +5
Caller Bonus = +10
Risk = +10

Total = 35
```

---

# 13. Example (High Call)

```
called_tricks = 8
won_tricks = 8
```

Calculation:

```
score = 8² = 64
```

---

# 14. Example (High Call Loss)

```
called_tricks = 8
won_tricks = 6
```

Calculation:

```
difference = 2

score = -(8² / 2) - (2 - 1)

score = -32 - 1

score = -33
```

---

# 15. Final Score Update

After calculating the round score:

```
player.total_score += score
```

---

# End of Scoring Engine Specification
