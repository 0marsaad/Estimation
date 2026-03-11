"""
scoring.py

Main scoring engine for the Estimation card game.

Public API:
    calculate_score(player_round_data) -> int

Input schema (dict):
    called_tricks    : int
    won_tricks       : int
    is_caller        : bool
    is_with          : bool
    risk             : int   (pre-calculated from risk_logic.calculate_risk)
    is_dash_call     : bool
    dash_type        : str   "OVER" | "UNDER"  (only relevant if is_dash_call)
    is_only_winner   : bool  (exactly 1 player won this round)
    is_only_loser    : bool  (exactly 1 player lost this round)
    round_type       : str   "OVER" | "UNDER"
    double_score     : bool

Scoring order (per SCORING_ENGINE.md §11):
    1. Determine win / loss
    2. Check called_tricks threshold
    3. If called_tricks < 8  → standard scoring
    4. If called_tricks >= 8 → quadratic scoring
    5. Apply dash call bonus  (if is_dash_call)
    6. Apply double score     (if double_score)
"""

import math
from shared.constants import (
    ROUND_SCORE,
    CALLER_WITH_BONUS,
    ONLY_WINNER_LOSER_BONUS,
    RISK_BONUS_PER_UNIT,
    HIGH_CALL_THRESHOLD,
)
from shared.enums import DashType
from .dash_call import calculate_dash_bonus


def _standard_score(player_data: dict, won: bool) -> int:
    """
    Apply the standard scoring table for called_tricks < 8.

    Components (all ±):
        Round Score          ±10
        Tricks Amount        ±called_tricks
        Caller / With bonus  ±10
        Only Winner / Loser  ±10
        Risk bonus           ±10 × risk
    """
    sign = 1 if won else -1
    called = player_data['called_tricks']

    score = 0
    score += sign * ROUND_SCORE
    score += sign * called

    if player_data.get('is_caller') or player_data.get('is_with'):
        score += sign * CALLER_WITH_BONUS

    if player_data.get('is_only_winner') or player_data.get('is_only_loser'):
        score += sign * ONLY_WINNER_LOSER_BONUS

    risk = player_data.get('risk', 0)
    score += sign * RISK_BONUS_PER_UNIT * risk

    return score


def _quadratic_score(player_data: dict, won: bool) -> int:
    """
    Apply quadratic scoring for called_tricks >= 8.

    Win:  score =  called²
    Loss: score = -(called² / 2) - (difference - 1)
          difference = abs(won_tricks - called_tricks)

    Result is rounded toward zero (int truncation).
    """
    called = player_data['called_tricks']
    won_tricks = player_data['won_tricks']

    if won:
        return called * called
    else:
        difference = abs(won_tricks - called)
        raw = -(called * called / 2) - (difference - 1)
        # Round toward zero
        return math.trunc(raw)


def calculate_score(player_round_data: dict) -> int:
    """
    Calculate the round score delta for one player.

    Parameters
    ----------
    player_round_data : dict  (see module docstring for full schema)

    Returns
    -------
    int : score change to add to player.total_score
    """
    called = player_round_data['called_tricks']
    won = player_round_data['won_tricks']
    did_win = (won == called)

    # Step 3 / 4: Standard vs Quadratic
    if called < HIGH_CALL_THRESHOLD:
        score = _standard_score(player_round_data, did_win)
    else:
        score = _quadratic_score(player_round_data, did_win)

    # Step 5: Dash call bonus (always added regardless of call size)
    if player_round_data.get('is_dash_call'):
        raw_dash_type = player_round_data.get('dash_type', 'OVER')
        dash_type = DashType(raw_dash_type)
        score += calculate_dash_bonus(dash_type, did_win)

    # Step 6: Double score
    if player_round_data.get('double_score'):
        score *= 2

    return score
