# Estimation Game – Full Project Specification

This document describes the **entire Estimation Game project** including:

* Game rules
* Game flow
* System architecture
* Backend requirements
* Frontend requirements
* Data models
* API behavior
* Real-time communication
* Scoring engine requirements

This README is designed so that a **coding agent or developer can build the full project**.

---

# 1. Project Overview

The project is a **web-based multiplayer score calculator for the Estimation card game**.

Players join a **shared game room from their phones**, play the card game physically, and use the web app to:

* manage rounds
* record bids
* record tricks won
* calculate scores automatically
* display leaderboards

The system **does not need to simulate cards**, only the **logic of bidding, estimation, and scoring**.

---

# 2. Game Summary

* Players: **4**
* Cards per player: **13**
* Tricks per round: **13**
* Total rounds: **18**
* Winner: **Highest score after 18 rounds**

Each round contains:

```
Dash Call Phase
Bidding Phase
Estimation Phase
Playing Phase
Score Calculation
```

---

# 3. Game Rules

## Trick Rules

Each player plays **one card per trick**.

Turn order is **counter-clockwise**.

Players must follow suit if possible.

Example:

```
First card: Jack of Hearts
```

All players must play **Hearts if available**.

If a player cannot follow suit, they may play any card.

The player with the **highest valid card** wins the trick.

The winner leads the next trick.

---

# 4. Card Ranking

Card values (high → low):

```
A
K
Q
J
10
9
8
7
6
5
4
3
2
```

---

# 5. Trump Suit Ranking

Trump strength (high → low):

```
Sans (No Trump)
Spades
Hearts
Diamonds
Clubs
```

Trump cards beat cards of other suits.

---

# 6. Bidding

A bid contains:

```
(number_of_tricks, trump_suit)
```

Example:

```
(5, Spades)
```

Minimum bid:

```
4 Clubs
```

Players may also:

```
PASS
```

---

# 7. Bid Winner (Caller)

The player with the **highest bid** becomes the:

```
Caller
```

The caller determines the **trump suit for the round**.

---

# 8. Dash Call

Before bidding begins, players may declare:

```
Dash Call
```

Meaning:

```
estimated tricks = 0
```

Properties:

* declared before trump is known
* high risk / high reward
* special scoring rules apply

---

# 9. Estimation Phase

After the caller is determined, each player must estimate the number of tricks they expect to win.

Constraint:

```
estimate ≤ caller_bid
```

Example:

Caller bid = 6

Valid estimates:

```
0
1
2
3
4
5
6
```

---

# 10. “With” Rule

If a player estimates the **same number of tricks as the caller**, they are marked:

```
WITH
```

Their score is calculated using **caller scoring rules**.

---

# 11. Trick Counting

At the end of the round each player has:

```
tricks_won
```

Example:

```
Player A = 4
Player B = 3
Player C = 2
Player D = 4
```

---

# 12. Total Estimate Rule

The sum of estimates **cannot equal 13**.

Invalid:

```
4 + 3 + 3 + 3 = 13
```

This ensures at least one player loses the round.

---

# 13. Round Types

## Over Round

```
total_estimates ≥ 14
```

Players attempt to win tricks quickly.

---

## Under Round

```
total_estimates ≤ 12
```

Players avoid winning extra tricks.

---

# 14. Risk

Risk occurs when estimates differ significantly from 13.

Formula:

```
risk = floor(abs(total_estimates - 13) / 2)
```

Example:

```
total_estimates = 17
difference = 4
risk = 2
```

Risk affects score multipliers.

---

# 15. All Players Pass

If all players pass during bidding:

```
round skipped
```

Next round has:

```
double_score = true
```

---

# 16. Final 5 Rounds

Last 5 rounds have fixed trumps:

```
Round 14 → Sans
Round 15 → Spades
Round 16 → Hearts
Round 17 → Diamonds
Round 18 → Clubs
```

Exception:

If a player bids **8 or more tricks**, trump may change.

---

# 17. Round Lifecycle

Each round follows this order:

```
1. Start round
2. Dash call phase
3. Bidding phase
4. Determine caller
5. Estimation phase
6. Playing phase
7. Record tricks won
8. Calculate scores
9. Update leaderboard
10. Start next round
```

---

# 18. System Architecture

The system consists of:

```
Frontend
Backend
Database
Realtime communication
```

Recommended architecture:

```
Client (Phones)
      ↓
Web Frontend
      ↓
Backend API
      ↓
Game Logic / Scoring Engine
      ↓
Database
```

---

# 19. Backend Responsibilities

The backend must:

* manage rooms
* manage players
* track rounds
* record bids
* record tricks
* calculate scores
* enforce game rules

Recommended backend framework:

```
Django
```

---

# 20. Frontend Responsibilities

The frontend must provide:

### Lobby Screen

```
Create Room
Join Room
```

---

### Room Screen

Displays:

```
Room Code
Players List
Start Game Button
```

---

### Dash Call Screen

Each player selects:

```
Dash Call
OR
No Dash Call
```

---

### Bidding Screen

Players choose:

```
PASS
OR
(tricks, trump)
```

---

### Estimation Screen

Players select:

```
estimated tricks
```

---

### Trick Entry Screen

Players input:

```
tricks won
```

---

### Scoreboard Screen

Displays:

```
Round results
Total scores
Leaderboard
```

---

# 21. Real-Time Communication

All players must see updates instantly.

Examples:

```
player joined
bid submitted
estimate submitted
round started
scores updated
```

Use WebSockets for real-time updates.

---

# 22. Data Models

The system should include these entities:

```
Game
Room
Player
Round
Bid
Score
```

Each round should store:

```
trump
caller
estimates
tricks_won
risk
over_or_under
dash_calls
```

---

# 23. Simplified Round Algorithm

```
function play_round():

    dash_call_phase()

    bidding_phase()

    determine_caller()

    estimation_phase()

    record_tricks()

    calculate_scores()

    update_leaderboard()
```

---

# 24. Score Calculation Engine

Inputs:

```
estimated_tricks
tricks_won
is_caller
is_with
is_dash_call
risk
round_type
double_score
```

Outputs:

```
score_change
```

The scoring engine should be implemented as a **separate module** so rules can be modified easily.

---

# 25. Game End

The game ends after:

```
18 rounds
```

The winner is:

```
player with highest total score
```

---

# 26. Optional Features

Recommended additional features:

```
Round history
Score graphs
Game replay
Player statistics
Leaderboard
```

---

# End of Project Specification
