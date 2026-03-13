#!/usr/bin/env python3
"""
End-to-end smoke test for the Estimation Calculator API.
Runs a full game flow: register → room → bid → estimate → play → scores.
"""
import sys
import requests

BASE = "http://localhost:8000/api"

PASS   = "\033[92m✓\033[0m"
FAIL   = "\033[91m✗\033[0m"
errors = []


def check(label, condition, detail=""):
    if condition:
        print(f"  {PASS} {label}")
    else:
        print(f"  {FAIL} {label}  ← {detail}")
        errors.append(label)


def session(username):
    """Return a requests.Session already logged-in as `username`."""
    s = requests.Session()
    # fetch CSRF
    s.get(f"{BASE}/auth/me/")
    csrf = s.cookies.get("csrftoken", "")
    r = s.post(
        f"{BASE}/auth/login/",
        json={"username": username, "password": "testpass1"},
        headers={"X-CSRFToken": csrf},
    )
    assert r.status_code == 200, f"login failed for {username}: {r.text}"
    return s


def post(s, path, data):
    csrf = s.cookies.get("csrftoken", "")
    return s.post(f"{BASE}{path}", json=data, headers={"X-CSRFToken": csrf})


# ── 1. Register 4 users ───────────────────────────────────────────────────────
print("\n=== 1. Register users ===")
users = ["t_alice", "t_bob", "t_carol", "t_dave"]
sessions = {}
for u in users:
    s = requests.Session()
    s.get(f"{BASE}/auth/me/")
    csrf = s.cookies.get("csrftoken", "")
    r = s.post(
        f"{BASE}/auth/register/",
        json={"username": u, "password": "testpass1"},
        headers={"X-CSRFToken": csrf},
    )
    # 201 = new user, 400 = already exists (re-run); both are fine
    ok = r.status_code in (201, 400)
    check(f"register {u}", ok, r.text[:80])
    sessions[u] = s

# Ensure all are logged in (in case they already existed)
for u in users:
    s = sessions[u]
    r = s.get(f"{BASE}/auth/me/")
    if r.status_code != 200:
        sessions[u] = session(u)

# ── 2. Create room ────────────────────────────────────────────────────────────
print("\n=== 2. Create room ===")
s_alice = sessions["t_alice"]
r = post(s_alice, "/rooms/create/", {})
# may already be in a room from a previous run
if r.status_code == 400 and "already in an active room" in r.text:
    # fetch the existing room
    # we'll just re-register fresh users with a timestamp suffix
    import time; ts = int(time.time()) % 10000
    users = [f"t_{n}_{ts}" for n in ["alice", "bob", "carol", "dave"]]
    sessions = {}
    for u in users:
        s = requests.Session()
        s.get(f"{BASE}/auth/me/")
        csrf = s.cookies.get("csrftoken", "")
        s.post(f"{BASE}/auth/register/",
               json={"username": u, "password": "testpass1"},
               headers={"X-CSRFToken": csrf})
        sessions[u] = s
    s_alice = sessions[users[0]]
    r = post(s_alice, "/rooms/create/", {})

check("create room", r.status_code == 201, r.text[:80])
room = r.json()
room_id   = room["id"]
room_code = room["room_code"]
print(f"  Room id={room_id}  code={room_code}")

# ── 3. Other 3 players join ───────────────────────────────────────────────────
print("\n=== 3. Other players join ===")
for u in users[1:]:
    r = post(sessions[u], "/rooms/join/", {"room_code": room_code})
    check(f"{u} joins", r.status_code == 200, r.text[:80])

# ── 4. Start game ─────────────────────────────────────────────────────────────
print("\n=== 4. Start game ===")
r = post(s_alice, "/game/start/", {"room_id": room_id})
check("start game (201)", r.status_code == 201, r.text[:80])
game = r.json()
check("is_finished=False", not game["is_finished"])

# ── 5. Advance DISTRIBUTION → DASH_CALL → BIDDING ────────────────────────────
print("\n=== 5. Advance phases ===")
r = post(s_alice, "/game/advance/", {"room_id": room_id})
check("→ DASH_CALL", r.status_code == 200 and r.json().get("phase") == "DASH_CALL", r.text[:80])
r = post(s_alice, "/game/advance/", {"room_id": room_id})
check("→ BIDDING",   r.status_code == 200 and r.json().get("phase") == "BIDDING",   r.text[:80])

# ── 6. All 4 players bid ──────────────────────────────────────────────────────
print("\n=== 6. Bidding ===")
bids = [
    {"room_id": room_id, "is_pass": False, "tricks_called": 7, "trump": "HEARTS"},
    {"room_id": room_id, "is_pass": True},
    {"room_id": room_id, "is_pass": True},
    {"room_id": room_id, "is_pass": True},
]
for u, bid_data in zip(users, bids):
    r = post(sessions[u], "/game/bid/", bid_data)
    check(f"{u} bid", r.status_code == 201, r.text[:80])

# ── 7. Verify phase advanced to ESTIMATION ───────────────────────────────────
print("\n=== 7. Check phase after bidding ===")
r = s_alice.get(f"{BASE}/game/state/", params={"room_id": room_id})
state = r.json()
cur_round = state["rounds"][-1]
check("phase=ESTIMATION", cur_round["phase"] == "ESTIMATION", cur_round["phase"])
check("caller set", cur_round["caller"] is not None)

# ── 8. Estimations ───────────────────────────────────────────────────────────
print("\n=== 8. Estimations ===")
# caller (alice, bid=7) must estimate >= 7
# others must estimate <= 7; total must != 13
est_map = {
    users[0]: {"room_id": room_id, "tricks_estimated": 7,  "is_dash_call": False},  # caller
    users[1]: {"room_id": room_id, "tricks_estimated": 2,  "is_dash_call": False},
    users[2]: {"room_id": room_id, "tricks_estimated": 1,  "is_dash_call": False},
    users[3]: {"room_id": room_id, "tricks_estimated": 1,  "is_dash_call": False},
}
# total = 11, safe (≠ 13)
for u, est_data in est_map.items():
    r = post(sessions[u], "/game/estimate/", est_data)
    check(f"{u} estimate", r.status_code == 201, r.text[:80])

# ── 9. Record tricks (play) ───────────────────────────────────────────────────
print("\n=== 9. Record tricks ===")
r = s_alice.get(f"{BASE}/game/state/", params={"room_id": room_id})
state = r.json()
cur_round = state["rounds"][-1]
check("phase=PLAYING", cur_round["phase"] == "PLAYING", cur_round["phase"])

# Get player IDs from room detail
r = s_alice.get(f"{BASE}/rooms/{room_id}/")
players = r.json()["players"]
pid = {p["user"]["username"]: p["id"] for p in players}

# Distribute 13 tricks: alice=7, bob=3, carol=2, dave=1
trick_winners = {users[0]: 7, users[1]: 3, users[2]: 2, users[3]: 1}
results = [{"player_id": pid[u], "tricks_won": w} for u, w in trick_winners.items()]
r = post(s_alice, "/game/play/", {"room_id": room_id, "results": results})
check("record tricks", r.status_code == 200, r.text[:80])

# ── 10. Check scores ─────────────────────────────────────────────────────────
print("\n=== 10. Scores ===")
r = s_alice.get(f"{BASE}/game/scores/", params={"room_id": room_id})
check("scores endpoint 200", r.status_code == 200, r.text[:80])
scores = r.json()
check("4 player scores returned", len(scores) == 4, str(len(scores)))
print(f"  Leaderboard:")
for entry in scores:
    print(f"    {entry['player']:20s}  seat={entry['seat']}  total={entry['total_score']}")

r2 = s_alice.get(f"{BASE}/scoring/round/", params={"room_id": room_id, "round_number": 1})
check("round scores endpoint 200", r2.status_code == 200, r2.text[:80])

# ── 11. Next round ────────────────────────────────────────────────────────────
print("\n=== 11. Next round ===")
r = post(s_alice, "/game/next-round/", {"room_id": room_id})
check("next-round 201", r.status_code == 201, r.text[:80])
new_round = r.json()
check("round 2 starts", new_round.get("round_number") == 2, str(new_round))

# ── 12. Swagger UI ────────────────────────────────────────────────────────────
print("\n=== 12. Swagger UI ===")
s_open = requests.Session()
r = s_open.get("http://localhost:8000/api/docs/")
check("Swagger UI (200)", r.status_code == 200)
r = s_open.get("http://localhost:8000/api/schema/")
check("OpenAPI schema (200)", r.status_code == 200)

# ── Summary ───────────────────────────────────────────────────────────────────
print()
if errors:
    print(f"  \033[91m{len(errors)} FAILED:\033[0m")
    for e in errors:
        print(f"    - {e}")
    sys.exit(1)
else:
    print("  \033[92mAll checks passed!\033[0m")
