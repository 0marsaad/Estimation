"""
dash_call.py

Scoring rules for dash calls.

OVER Dash Call:  Win = +25,  Loss = -25
UNDER Dash Call: Win = +33,  Loss = -33
"""

from shared.enums import DashType
from shared.constants import DASH_OVER_BONUS, DASH_UNDER_BONUS


def calculate_dash_bonus(dash_type: DashType, won: bool) -> int:
    """Return the dash call bonus (positive on win, negative on loss)."""
    if dash_type == DashType.OVER:
        bonus = DASH_OVER_BONUS
    else:
        bonus = DASH_UNDER_BONUS

    return bonus if won else -bonus
