# AGENT_WORKFLOW.md

Project Bootstrap Workflow for Estimation Card Game

You are an autonomous coding agent tasked with building a **full-stack multiplayer web application** for the Estimation card game.

The workspace currently contains only two specification files:

* `README.md` → Complete game rules and mechanics
* `SCORING_ENGINE.md` → Formal mathematical definition of scoring

Your job is to **create the full project structure and begin implementing the system.**

---

# 1. Project Goal

Build a **room-based multiplayer Estimation card game calculator** where:

• 4 players join a room
• Players perform bidding and trick estimation
• Players track tricks during play
• The system calculates scores automatically using the scoring engine
• Scores persist across rounds and the full 18-round game

The application should support **multiple concurrent rooms**.

---

# 2. Required Tech Stack

Backend:

Django
Django REST Framework
Django Channels (WebSockets)

Database:

PostgreSQL

Frontend:

React

Realtime:

WebSockets

Deployment readiness:

Docker compatible

---

# 3. Required Project Architecture

Generate the following **monorepo structure**:

```
estimation-game/
│
├── backend/
│   ├── manage.py
│   ├── config/
│   │   ├── settings.py
│   │   ├── asgi.py
│   │   ├── urls.py
│   │
│   ├── apps/
│   │   ├── users/
│   │   ├── rooms/
│   │   ├── game/
│   │   ├── scoring/
│   │
│   └── requirements.txt
│
├── frontend/
│   ├── package.json
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── api/
│   │   ├── websocket/
│   │   └── state/
│
├── game_engine/
│   ├── cards.py
│   ├── deck.py
│   ├── trick_logic.py
│   ├── bidding_logic.py
│   ├── round_manager.py
│
├── scoring_engine/
│   ├── scoring.py
│   ├── dash_call.py
│   ├── risk_logic.py
│
├── shared/
│   ├── constants.py
│   ├── enums.py
│
├── docs/
│   ├── README.md
│   ├── SCORING_ENGINE.md
│
└── docker/
    ├── Dockerfile
    └── docker-compose.yml
```

Move the existing specification files into the **docs/** directory.

---

# 4. Core Domain Models

Implement the following Django models.

User

```
User
id
username
created_at
```

Room

```
Room
id
room_code
status
created_at
```

Player

```
Player
id
user
room
seat_position
total_score
```

Game

```
Game
id
room
current_round
is_finished
```

Round

```
Round
id
game
round_number
trump_suit
round_type
double_score
```

Bid

```
Bid
id
player
round
tricks_called
trump
is_caller
is_with
risk
```

Trick

```
Trick
id
round
winner
cards
```

Score

```
Score
id
player
round
called_tricks
won_tricks
score_delta
```

---

# 5. Game Engine Responsibilities

The game engine should be implemented **independent of Django**.

Responsibilities:

Card representation
Deck generation
Card dealing
Suit validation
Trick winner determination
Round progression

Modules:

cards.py
Defines card structure.

deck.py
Generates shuffled 52-card deck.

trick_logic.py
Determines trick winner.

bidding_logic.py
Handles bidding competition.

round_manager.py
Controls phase transitions.

---

# 6. Scoring Engine Responsibilities

The scoring engine must strictly follow the formulas in:

```
SCORING_ENGINE.md
```

Responsibilities:

Calculate win/loss
Detect over/under rounds
Calculate risk
Apply caller/with bonuses
Handle quadratic scoring when call ≥ 8
Apply dash call scoring
Apply double score logic

Expose a single function:

```
calculate_score(player_round_data)
```

---

# 7. Game State Flow

Each round progresses through the following phases:

1 Distribution
2 Dash Call
3 Trump Bidding
4 Trick Estimation
5 Playing Phase
6 Score Calculation

Implement a **Round State Machine**:

```
WAITING_FOR_PLAYERS
DISTRIBUTION
DASH_CALL
BIDDING
ESTIMATION
PLAYING
SCORING
ROUND_END
```

---

# 8. WebSocket Events

Implement real-time events for gameplay.

Events:

```
room_join
player_ready
cards_dealt
dash_call_declared
bid_submitted
bid_winner
estimate_submitted
card_played
trick_won
round_finished
score_updated
game_finished
```

---

# 9. REST API Endpoints

Implement the following endpoints.

Rooms

```
POST /rooms/create
POST /rooms/join
GET  /rooms/{id}
```

Game

```
POST /game/start
GET  /game/state
```

Bidding

```
POST /bid
```

Estimate

```
POST /estimate
```

Play Card

```
POST /play
```

Scores

```
GET /scores
```

---

# 10. Frontend Pages

Implement basic React pages.

Lobby

```
Create room
Join room
```

Room

```
Player list
Start game
```

Game Table

```
Player cards
Table cards
Trump display
Trick count
Player estimates
Scoreboard
```

Scoreboard

```
Round history
Total scores
```

---

# 11. Immediate Tasks

Execute the following steps in order.

Step 1
Initialize Django project.

Step 2
Create Django apps:

```
users
rooms
game
scoring
```

Step 3
Implement database models.

Step 4
Implement game engine modules.

Step 5
Implement scoring engine using formulas from SCORING_ENGINE.md.

Step 6
Implement REST API.

Step 7
Add WebSocket server with Django Channels.

Step 8
Initialize React frontend.

Step 9
Implement room system UI.

Step 10
Implement gameplay UI.

---

# 12. Development Rules

The agent must follow these constraints:

The rules in `README.md` are the **source of truth for gameplay**.

The formulas in `SCORING_ENGINE.md` are the **source of truth for scoring**.

Game logic must be **pure Python modules separate from Django models**.

The scoring engine must be **fully unit testable**.

All critical logic must include **tests**.

---

# 13. First Deliverable

After executing the workflow, the agent should produce:

• Full project structure
• Django server running
• Database models migrated
• Basic room creation working
• Scoring engine implemented

---

# End of Workflow
