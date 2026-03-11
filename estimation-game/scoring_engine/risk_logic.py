"""
risk_logic.py

Calculates the risk value for a round based on the total called tricks.

Risk formula:
    risk = floor(abs(total_called - 13) / 2)

Dash type:
    total_called - 13 > 0  → OVER dash
    total_called - 13 < 0  → UNDER dash
"""

import math
from shared.enums import DashType


def calculate_risk(total_called_tricks: int) -> int:
    """Return the risk value for the round."""
    return math.floor(abs(total_called_tricks - 13) / 2)


def determine_dash_type(total_called_tricks: int) -> DashType:
    """
    Determine whether the round is an OVER or UNDER round.
    total_called - 13 > 0 → OVER
    total_called - 13 < 0 → UNDER
    If exactly 13 (invalid per rules but handled) → defaults to OVER.
    """
    diff = total_called_tricks - 13
    return DashType.OVER if diff >= 0 else DashType.UNDER
