# Estimation Calculator — Backend API Documentation

## Table of Contents

1. [Overview](#1-overview)
2. [Authentication & Sessions](#2-authentication--sessions)
3. [Common Data Shapes](#3-common-data-shapes)
4. [Game Phase State Machine](#4-game-phase-state-machine)
5. [Auth API](#5-auth-api)
6. [Rooms API](#6-rooms-api)
7. [Game API](#7-game-api)
8. [Scoring API](#8-scoring-api)
9. [WebSocket API](#9-websocket-api)
10. [Error Responses](#10-error-responses)

---

## 1. Overview

| Property                  | Value                                            |
| ------------------------- | ------------------------------------------------ |
| **Framework**             | Django 4.2 + Django REST Framework 3.15          |
| **Transport**             | HTTP/1.1 (REST) + WebSockets (Django Channels 4) |
| **Base REST URL**         | `http://localhost:8000/api/`                     |
| **WebSocket URL**         | `ws://localhost:8000/ws/game/<room_code>/`       |
| **Authentication**        | Django sessions + CSRF tokens                    |
| **Database**              | PostgreSQL 16                                    |
| **Cache / Channel Layer** | Redis 7                                          |
| **Content-Type**          | `application/json` for all REST requests         |

---

## 2. Authentication & Sessions

The API uses **Django session-based authentication**. On a successful login or registration the server sets:

- `sessionid` — an HTTP-only session cookie (managed automatically by the browser).
- `csrftoken` — a CSRF cookie that must be read by the client and sent as the `X-CSRFToken` header on every **unsafe** request (`POST`, `PUT`, `PATCH`, `DELETE`).

### Obtaining the CSRF token

```
GET /api/auth/me/          (or any endpoint that sets the cookie)
```

Read the `csrftoken` cookie value and include it in all mutating requests:

```http
X-CSRFToken: <value-from-csrftoken-cookie>
```

The React frontend (included in this repo) handles this automatically via an Axios interceptor.

---

## 3. Common Data Shapes

All nested objects share the shapes below throughout every endpoint response.

### User object

```json
{
  "id": 1,
  "username": "alice",
  "created_at": "2024-01-15T10:00:00Z"
}
```

### Player object

```json
{
  "id": 1,
  "user": { "id": 1, "username": "alice", "created_at": "..." },
  "seat_position": 0,
  "total_score": 120
}
```

### Room object

```json
{
  "id": 1,
  "room_code": "ABCD12",
  "status": "WAITING",
  "created_at": "2024-01-15T10:00:00Z",
  "players": [
    /* Player objects */
  ]
}
```

Room `status` values: `WAITING`, `IN_PROGRESS`, `FINISHED`.

### Bid object

```json
{
  "id": 1,
  "player": {
    /* Player object */
  },
  "tricks_called": 7,
  "trump": "HEARTS",
  "is_pass": false
}
```

Trump values: `SANS`, `SPADES`, `HEARTS`, `DIAMONDS`, `CLUBS`.

### Estimation object

```json
{
  "id": 1,
  "player": {
    /* Player object */
  },
  "tricks_estimated": 4,
  "is_dash_call": false,
  "is_with": true
}
```

### Trick Result object

```json
{
  "id": 1,
  "player": {
    /* Player object */
  },
  "tricks_won": 5
}
```

### Round object

```json
{
  "id": 1,
  "round_number": 1,
  "trump_suit": "HEARTS",
  "round_type": "OVER",
  "double_score": false,
  "phase": "BIDDING",
  "caller": {
    /* Player object or null */
  },
  "skipped": false,
  "bids": [
    /* Bid objects */
  ],
  "estimations": [
    /* Estimation objects */
  ],
  "trick_results": [
    /* Trick Result objects */
  ]
}
```

`round_type` values: `OVER` (sum of called tricks > 13), `UNDER` (< 13), `null` (not yet determined).

### Game object

```json
{
  "id": 1,
  "room": 1,
  "current_round": 3,
  "is_finished": false,
  "rounds": [
    /* Round objects */
  ]
}
```

### Score object

```json
{
  "id": 1,
  "player": {
    /* Player object */
  },
  "round": 1,
  "called_tricks": 7,
  "won_tricks": 7,
  "score_delta": 14,
  "is_caller": true,
  "is_with": false,
  "is_dash_call": false,
  "risk": "NORMAL"
}
```

---

## 4. Game Phase State Machine

Each round advances through these phases in order:

```
DISTRIBUTION
     ↓  (POST /api/game/advance/)
DASH_CALL
     ↓  (POST /api/game/advance/)
BIDDING
     ↓  (automatic after 4th bid)
ESTIMATION
     ↓  (automatic after 4th valid estimate)
PLAYING
     ↓  (POST /api/game/play/ records tricks)
SCORING          ← scores are calculated here
     ↓  (automatic)
ROUND_END
     ↓  (POST /api/game/next-round/)
DISTRIBUTION     ← next round begins (or game ends after round 18)
```

**Special rules:**

- Rounds **14–18** have fixed trump suits (SANS, SPADES, HEARTS, DIAMONDS, CLUBS respectively). The bidding winner still becomes the caller but cannot change the trump.
- If **all 4 players pass**, the round is marked `skipped = true`. The _next_ round gets `double_score = true`.
- The game ends after **18 rounds**.

---

## 5. Auth API

Base path: `/api/auth/`

---

### 5.1 Register

Create a new user account. The user is also logged in immediately upon success.

**Request**

```
POST /api/auth/register/
```

| Field      | Type   | Required | Notes                |
| ---------- | ------ | -------- | -------------------- |
| `username` | string | Yes      | Must be unique       |
| `password` | string | Yes      | Minimum 6 characters |

**Example request body**

```json
{
  "username": "alice",
  "password": "secret123"
}
```

**Response `201 Created`**

```json
{
  "id": 1,
  "username": "alice",
  "created_at": "2024-01-15T10:00:00Z"
}
```

**Errors**
| Status | Detail |
|---|---|
| `400` | `username` already exists or password too short |

---

### 5.2 Login

**Request**

```
POST /api/auth/login/
```

| Field      | Type   | Required |
| ---------- | ------ | -------- |
| `username` | string | Yes      |
| `password` | string | Yes      |

**Response `200 OK`**

```json
{
  "id": 1,
  "username": "alice",
  "created_at": "2024-01-15T10:00:00Z"
}
```

**Errors**
| Status | Detail |
|---|---|
| `400` | Invalid credentials |

---

### 5.3 Logout

**Request**

```
POST /api/auth/logout/
```

No body required. Requires an active session.

**Response `200 OK`**

```json
{
  "detail": "Logged out."
}
```

---

### 5.4 Current User

Returns the authenticated user's profile.

**Request**

```
GET /api/auth/me/
```

**Response `200 OK`** — [User object](#user-object)

**Errors**
| Status | Detail |
|---|---|
| `403` | Not authenticated |

---

## 6. Rooms API

Base path: `/api/rooms/`

All endpoints require authentication.

---

### 6.1 Create Room

Creates a new room. The requesting user is automatically assigned **seat 0**.

**Request**

```
POST /api/rooms/create/
```

No body required.

**Response `201 Created`** — [Room object](#room-object)

**Errors**
| Status | Detail |
|---|---|
| `400` | You are already in an active room |

---

### 6.2 Join Room

Joins an existing room by its room code. The server automatically assigns the next free seat (0–3).

**Request**

```
POST /api/rooms/join/
```

| Field       | Type   | Required |
| ----------- | ------ | -------- |
| `room_code` | string | Yes      |

**Example request body**

```json
{
  "room_code": "ABCD12"
}
```

**Response `200 OK`** — [Room object](#room-object)

**Errors**
| Status | Detail |
|---|---|
| `404` | Room not found |
| `400` | Room is full (4 players) |
| `400` | Room is not in WAITING status |
| `400` | You are already in this room |

---

### 6.3 Room Detail

Returns the full state of a room including the players list.

**Request**

```
GET /api/rooms/<room_id>/
```

**Response `200 OK`** — [Room object](#room-object)

---

## 7. Game API

Base path: `/api/game/`

All endpoints require authentication. Most mutating endpoints require the requesting user to be a player in the relevant room.

---

### 7.1 Start Game

Starts the game for a room. Creates a `Game` record and the first `Round`.

**Request**

```
POST /api/game/start/
```

| Field     | Type    | Required |
| --------- | ------- | -------- |
| `room_id` | integer | Yes      |

**Response `201 Created`** — [Game object](#game-object)

**Errors**
| Status | Detail |
|---|---|
| `400` | Game already started or room is finished |
| `400` | Need exactly 4 players to start |
| `403` | You are not in this room |
| `404` | Room not found |

---

### 7.2 Game State

Returns the complete game state including all rounds, bids, estimations, and trick results.

**Request**

```
GET /api/game/state/?room_id=<room_id>
```

**Response `200 OK`** — [Game object](#game-object)

---

### 7.3 Advance Phase (Manual)

Manually advances the round through the pre-bidding phases. Only allowed from `DISTRIBUTION` → `DASH_CALL` and `DASH_CALL` → `BIDDING`. Later phase transitions are automatic.

**Request**

```
POST /api/game/advance/
```

| Field     | Type    | Required |
| --------- | ------- | -------- |
| `room_id` | integer | Yes      |

**Response `200 OK`**

```json
{
  "phase": "DASH_CALL"
}
```

**Errors**
| Status | Detail |
|---|---|
| `400` | Cannot manually advance from phase `<current_phase>` |
| `403` | You are not in this room |

---

### 7.4 Submit Bid

Submits a bid for the current player. Once all 4 players have bid, the caller is determined automatically and the round advances to ESTIMATION.

**Request**

```
POST /api/game/bid/
```

| Field           | Type        | Required       | Notes                                                   |
| --------------- | ----------- | -------------- | ------------------------------------------------------- |
| `room_id`       | integer     | Yes            |                                                         |
| `is_pass`       | boolean     | Yes            | Set `true` to pass                                      |
| `tricks_called` | integer ≥ 4 | If not passing | Number of tricks being bid                              |
| `trump`         | string      | If not passing | One of: `SANS`, `SPADES`, `HEARTS`, `DIAMONDS`, `CLUBS` |

**Example — active bid**

```json
{
  "room_id": 1,
  "is_pass": false,
  "tricks_called": 7,
  "trump": "HEARTS"
}
```

**Example — pass**

```json
{
  "room_id": 1,
  "is_pass": true
}
```

**Response `201 Created`** — [Bid object](#bid-object)

**Errors**
| Status | Detail |
|---|---|
| `400` | Round is not in bidding phase |
| `400` | `tricks_called` must be ≥ 4 |
| `400` | Serializer validation errors |
| `403` | You are not in this room |

---

### 7.5 Submit Estimation

Submits a tricks estimation for the current player. Once all 4 estimations are in, the server validates that the total does **not** equal 13, then advances to PLAYING.

**Request**

```
POST /api/game/estimate/
```

| Field              | Type         | Required | Notes                                              |
| ------------------ | ------------ | -------- | -------------------------------------------------- |
| `room_id`          | integer      | Yes      |                                                    |
| `tricks_estimated` | integer 0–13 | Yes      |                                                    |
| `is_dash_call`     | boolean      | Yes      | Whether the player claims a "dash call" (0 tricks) |

**Example**

```json
{
  "room_id": 1,
  "tricks_estimated": 4,
  "is_dash_call": false
}
```

**Response `201 Created`** — [Estimation object](#estimation-object)

**Estimation Constraints**

- The **caller** must estimate ≥ their own bid (`tricks_called`).
- All **other players** must estimate ≤ the caller's bid.
- After 4 estimations, the total must **not** equal 13. If it does, the request is rejected with `400` and the last player must re-submit with a different value.

**`is_with` Detection (automatic)**  
A non-caller player is automatically flagged `is_with = true` if they bid the same trump suit as the caller during BIDDING.

**Errors**
| Status | Detail |
|---|---|
| `400` | Round is not in estimation phase |
| `400` | Caller estimate must be ≥ their bid |
| `400` | Estimate must be ≤ caller bid |
| `400` | Total estimates cannot equal 13. Please change your estimate. |
| `403` | You are not in this room |

---

### 7.6 Record Tricks (Play)

Records the tricks won by each player after the physical card game is played. Triggers score calculation and advances the round to ROUND_END.

**Request**

```
POST /api/game/play/
```

| Field                  | Type         | Required | Notes                |
| ---------------------- | ------------ | -------- | -------------------- |
| `room_id`              | integer      | Yes      |                      |
| `results`              | array        | Yes      | One entry per player |
| `results[].player_id`  | integer      | Yes      | Player's DB id       |
| `results[].tricks_won` | integer 0–13 | Yes      |                      |

**Example**

```json
{
  "room_id": 1,
  "results": [
    { "player_id": 1, "tricks_won": 7 },
    { "player_id": 2, "tricks_won": 2 },
    { "player_id": 3, "tricks_won": 3 },
    { "player_id": 4, "tricks_won": 1 }
  ]
}
```

**Constraint:** The sum of all `tricks_won` values must equal **13**.

**Response `200 OK`**

```json
{
  "detail": "Tricks recorded and scores calculated."
}
```

**Errors**
| Status | Detail |
|---|---|
| `400` | Round is not in playing phase |
| `400` | Total tricks must equal 13 (serializer validation) |
| `403` | You are not in this room |

---

### 7.7 Next Round

Advances the game to the next round. If the game is finished (after round 18), returns a finished flag instead.

**Request**

```
POST /api/game/next-round/
```

| Field     | Type    | Required |
| --------- | ------- | -------- |
| `room_id` | integer | Yes      |

**Response `201 Created`** — [Round object](#round-object) for the new round.

**Response `200 OK`** — when the game ends after round 18:

```json
{
  "detail": "Game finished.",
  "is_finished": true
}
```

**Errors**
| Status | Detail |
|---|---|
| `400` | Current round is not finished yet |

---

### 7.8 Leaderboard Scores

Returns all players in the room ordered by total score descending.

**Request**

```
GET /api/game/scores/?room_id=<room_id>
```

**Response `200 OK`**

```json
[
  { "player": "alice", "seat": 0, "total_score": 220 },
  { "player": "bob", "seat": 1, "total_score": 180 },
  { "player": "carol", "seat": 2, "total_score": 130 },
  { "player": "dave", "seat": 3, "total_score": 90 }
]
```

---

## 8. Scoring API

Base path: `/api/scoring/`

All endpoints require authentication. These are **read-only** endpoints; scores are written automatically by the game engine when tricks are recorded.

---

### 8.1 Round Scores

Returns all Score records for a specific round.

**Request**

```
GET /api/scoring/round/?room_id=<room_id>&round_number=<N>
```

**Response `200 OK`** — array of [Score objects](#score-object)

```json
[
  {
    "id": 1,
    "player": { /* Player object */ },
    "round": 1,
    "called_tricks": 7,
    "won_tricks": 7,
    "score_delta": 14,
    "is_caller": true,
    "is_with": false,
    "is_dash_call": false,
    "risk": "NORMAL"
  },
  ...
]
```

**Score fields explained**

| Field           | Description                                                                |
| --------------- | -------------------------------------------------------------------------- |
| `called_tricks` | How many tricks the player bid (from Bid model)                            |
| `won_tricks`    | How many tricks the player actually won                                    |
| `score_delta`   | Points gained/lost this round (may be negative)                            |
| `is_caller`     | Whether this player won the bid and is the round caller                    |
| `is_with`       | Whether this non-caller bid the same trump suit as the caller              |
| `is_dash_call`  | Whether the player declared a "dash call" (0 tricks goal)                  |
| `risk`          | Scoring risk tier: `NORMAL` or `HIGH` (bid ≥ 8 triggers quadratic scoring) |

---

### 8.2 Game Scores

Returns all Score records for an entire game, ordered by round number.

**Request**

```
GET /api/scoring/game/?room_id=<room_id>
```

**Response `200 OK`** — array of [Score objects](#score-object), sorted by `round` ascending.

---

## 9. WebSocket API

### Connection

```
ws://localhost:8000/ws/game/<ROOM_CODE>/
```

Replace `<ROOM_CODE>` with the 6-character code returned when creating or joining a room (e.g. `ABCD12`).

The WebSocket uses the same session cookie as the REST API. Connect after logging in via the REST API.

---

### Server → Client Events

The server broadcasts JSON messages to all connected clients in the room group whenever significant game state changes occur.

| `type`               | Triggered when                                       |
| -------------------- | ---------------------------------------------------- |
| `player_ready`       | A player joins the room or signals readiness         |
| `dash_call_declared` | A player declares a dash call during DASH_CALL phase |
| `bid_submitted`      | A player submits a bid                               |
| `estimate_submitted` | A player submits an estimation                       |
| `round_finished`     | Round reaches ROUND_END after tricks are recorded    |
| `score_updated`      | Scores are recalculated and updated                  |

**Example message**

```json
{
  "type": "bid_submitted",
  "player_id": 2,
  "tricks_called": 7,
  "trump": "HEARTS"
}
```

> **Note:** The WebSocket layer is for real-time notifications only. All game actions are performed via REST. After receiving a WebSocket event, clients should re-fetch the game state via `GET /api/game/state/?room_id=<id>` to get the authoritative current state.

---

## 10. Error Responses

### Standard Error Shape

All error responses return a JSON object with a `detail` key (DRF convention) or a field-keyed object for validation errors.

**Single message**

```json
{
  "detail": "You are not in this room."
}
```

**Validation errors (field-level)**

```json
{
  "tricks_called": ["This field is required when not passing."],
  "trump": ["This field is required when not passing."]
}
```

### HTTP Status Codes Used

| Code              | Meaning                                               |
| ----------------- | ----------------------------------------------------- |
| `200 OK`          | Successful read or action                             |
| `201 Created`     | Resource successfully created                         |
| `400 Bad Request` | Validation error or business rule violation           |
| `403 Forbidden`   | Not authenticated or not authorized for this resource |
| `404 Not Found`   | Requested resource does not exist                     |

---

## Appendix: Fixed Trump Rounds

Rounds 14–18 have a predetermined trump suit. Players still bid and compete for the caller role, but the trump cannot be changed.

| Round | Trump Suit |
| ----- | ---------- |
| 14    | SANS       |
| 15    | SPADES     |
| 16    | HEARTS     |
| 17    | DIAMONDS   |
| 18    | CLUBS      |

## Appendix: Scoring Engine Summary

Full details are in [SCORING_ENGINE.md](SCORING_ENGINE.md). Key points:

- **OVER round** (sum of bids > 13): caller/with score = `tricks_won × 2`; others score = `tricks_won × 1`.
- **UNDER round** (sum of bids < 13): scoring is inverted — exceeding your estimate is penalised.
- **Caller bid ≥ 8**: quadratic scoring applies (`tricks_won²`).
- **Winner/Loser bonus**: `±10` points applied to the single highest/lowest scorer each round.
- **Dash call**: player who calls 0 tricks and succeeds earns a bonus; failing is penalised.
- **Double score rounds**: when the previous round was fully skipped (all passes), the next round's points are doubled.
