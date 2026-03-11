"""
Unit tests for the Estimation scoring engine.

All examples are taken directly from SCORING_ENGINE.md.
"""

import sys
import os
import unittest

# Allow imports from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from scoring_engine.scoring import calculate_score
from scoring_engine.risk_logic import calculate_risk, determine_dash_type
from shared.enums import DashType


# ---------------------------------------------------------------------------
# Risk logic
# ---------------------------------------------------------------------------

class TestRiskCalculation(unittest.TestCase):

    def test_over_round(self):
        # total_called = 17 → diff = 4 → risk = 2
        self.assertEqual(calculate_risk(17), 2)

    def test_under_round(self):
        # total_called = 9 → diff = 4 → risk = 2
        self.assertEqual(calculate_risk(9), 2)

    def test_no_risk(self):
        # total_called = 13 → diff = 0 → risk = 0
        self.assertEqual(calculate_risk(13), 0)

    def test_odd_difference(self):
        # total_called = 14 → diff = 1 → risk = 0 (floor)
        self.assertEqual(calculate_risk(14), 0)


class TestDashType(unittest.TestCase):

    def test_over(self):
        self.assertEqual(determine_dash_type(17), DashType.OVER)

    def test_under(self):
        self.assertEqual(determine_dash_type(10), DashType.UNDER)

    def test_exactly_13(self):
        self.assertEqual(determine_dash_type(13), DashType.OVER)


# ---------------------------------------------------------------------------
# Standard scoring (called_tricks < 8)
# ---------------------------------------------------------------------------

class TestStandardScoringWin(unittest.TestCase):

    def test_basic_win_no_bonuses(self):
        # called=5, won=5, risk=0, not caller, not with
        data = {
            'called_tricks': 5, 'won_tricks': 5,
            'is_caller': False, 'is_with': False,
            'risk': 0, 'is_dash_call': False,
            'is_only_winner': False, 'is_only_loser': False,
            'round_type': 'OVER', 'double_score': False,
        }
        # +10 (round) + 5 (tricks) = 15
        self.assertEqual(calculate_score(data), 15)

    def test_win_with_caller_and_risk(self):
        # Example from SCORING_ENGINE.md §12
        # called=5, won=5, risk=1, is_caller=True
        data = {
            'called_tricks': 5, 'won_tricks': 5,
            'is_caller': True, 'is_with': False,
            'risk': 1, 'is_dash_call': False,
            'is_only_winner': False, 'is_only_loser': False,
            'round_type': 'OVER', 'double_score': False,
        }
        # +10 + 5 + 10 (caller) + 10 (risk×1) = 35
        self.assertEqual(calculate_score(data), 35)

    def test_win_only_winner_bonus(self):
        data = {
            'called_tricks': 3, 'won_tricks': 3,
            'is_caller': False, 'is_with': False,
            'risk': 0, 'is_dash_call': False,
            'is_only_winner': True, 'is_only_loser': False,
            'round_type': 'OVER', 'double_score': False,
        }
        # +10 + 3 + 10 (only winner) = 23
        self.assertEqual(calculate_score(data), 23)


class TestStandardScoringLoss(unittest.TestCase):

    def test_basic_loss(self):
        data = {
            'called_tricks': 4, 'won_tricks': 2,
            'is_caller': False, 'is_with': False,
            'risk': 0, 'is_dash_call': False,
            'is_only_winner': False, 'is_only_loser': False,
            'round_type': 'OVER', 'double_score': False,
        }
        # -10 - 4 = -14
        self.assertEqual(calculate_score(data), -14)

    def test_loss_only_loser(self):
        data = {
            'called_tricks': 4, 'won_tricks': 2,
            'is_caller': False, 'is_with': False,
            'risk': 1, 'is_dash_call': False,
            'is_only_winner': False, 'is_only_loser': True,
            'round_type': 'OVER', 'double_score': False,
        }
        # -10 - 4 - 10 (only loser) - 10 (risk) = -34
        self.assertEqual(calculate_score(data), -34)


# ---------------------------------------------------------------------------
# High call scoring (called_tricks >= 8)
# ---------------------------------------------------------------------------

class TestHighCallWin(unittest.TestCase):

    def test_call_8_win(self):
        # SCORING_ENGINE.md §13: called=8, won=8 → 64
        data = {
            'called_tricks': 8, 'won_tricks': 8,
            'is_caller': True, 'is_with': False,
            'risk': 0, 'is_dash_call': False,
            'is_only_winner': False, 'is_only_loser': False,
            'round_type': 'OVER', 'double_score': False,
        }
        self.assertEqual(calculate_score(data), 64)

    def test_call_9_win(self):
        data = {
            'called_tricks': 9, 'won_tricks': 9,
            'is_caller': True, 'is_with': False,
            'risk': 0, 'is_dash_call': False,
            'is_only_winner': False, 'is_only_loser': False,
            'round_type': 'OVER', 'double_score': False,
        }
        self.assertEqual(calculate_score(data), 81)


class TestHighCallLoss(unittest.TestCase):

    def test_call_8_loss_diff_2(self):
        # SCORING_ENGINE.md §14: called=8, won=6 → -33
        data = {
            'called_tricks': 8, 'won_tricks': 6,
            'is_caller': True, 'is_with': False,
            'risk': 0, 'is_dash_call': False,
            'is_only_winner': False, 'is_only_loser': False,
            'round_type': 'OVER', 'double_score': False,
        }
        self.assertEqual(calculate_score(data), -33)

    def test_call_9_loss_diff_2(self):
        # SCORING_ENGINE.md §7: called=9, won=7 → -41 (trunc of -41.5)
        data = {
            'called_tricks': 9, 'won_tricks': 7,
            'is_caller': True, 'is_with': False,
            'risk': 0, 'is_dash_call': False,
            'is_only_winner': False, 'is_only_loser': False,
            'round_type': 'OVER', 'double_score': False,
        }
        self.assertEqual(calculate_score(data), -41)

    def test_call_8_loss_diff_1(self):
        # called=8, won=7: -(64/2) - (1-1) = -32
        data = {
            'called_tricks': 8, 'won_tricks': 7,
            'is_caller': True, 'is_with': False,
            'risk': 0, 'is_dash_call': False,
            'is_only_winner': False, 'is_only_loser': False,
            'round_type': 'OVER', 'double_score': False,
        }
        self.assertEqual(calculate_score(data), -32)


# ---------------------------------------------------------------------------
# Dash call
# ---------------------------------------------------------------------------

class TestDashCallBonus(unittest.TestCase):

    def test_over_dash_win(self):
        data = {
            'called_tricks': 0, 'won_tricks': 0,
            'is_caller': False, 'is_with': False,
            'risk': 2, 'is_dash_call': True, 'dash_type': 'OVER',
            'is_only_winner': False, 'is_only_loser': False,
            'round_type': 'OVER', 'double_score': False,
        }
        # Standard win: +10 + 0 + 20 (risk×2) + 25 (over dash) = 55
        self.assertEqual(calculate_score(data), 55)

    def test_under_dash_win(self):
        data = {
            'called_tricks': 0, 'won_tricks': 0,
            'is_caller': False, 'is_with': False,
            'risk': 0, 'is_dash_call': True, 'dash_type': 'UNDER',
            'is_only_winner': False, 'is_only_loser': False,
            'round_type': 'UNDER', 'double_score': False,
        }
        # +10 + 0 + 33 = 43
        self.assertEqual(calculate_score(data), 43)

    def test_over_dash_loss(self):
        data = {
            'called_tricks': 0, 'won_tricks': 1,
            'is_caller': False, 'is_with': False,
            'risk': 0, 'is_dash_call': True, 'dash_type': 'OVER',
            'is_only_winner': False, 'is_only_loser': False,
            'round_type': 'OVER', 'double_score': False,
        }
        # -10 - 0 - 25 = -35
        self.assertEqual(calculate_score(data), -35)


# ---------------------------------------------------------------------------
# Double score
# ---------------------------------------------------------------------------

class TestDoubleScore(unittest.TestCase):

    def test_double_applied_after_all(self):
        data = {
            'called_tricks': 5, 'won_tricks': 5,
            'is_caller': True, 'is_with': False,
            'risk': 1, 'is_dash_call': False,
            'is_only_winner': False, 'is_only_loser': False,
            'round_type': 'OVER', 'double_score': True,
        }
        # 35 × 2 = 70
        self.assertEqual(calculate_score(data), 70)

    def test_double_on_loss(self):
        data = {
            'called_tricks': 4, 'won_tricks': 2,
            'is_caller': False, 'is_with': False,
            'risk': 0, 'is_dash_call': False,
            'is_only_winner': False, 'is_only_loser': False,
            'round_type': 'OVER', 'double_score': True,
        }
        # -14 × 2 = -28
        self.assertEqual(calculate_score(data), -28)


if __name__ == '__main__':
    unittest.main()
