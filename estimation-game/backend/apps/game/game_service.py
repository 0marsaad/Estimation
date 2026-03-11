"""
game_service.py

Business logic for game flow: starting games, advancing rounds,
computing scores, and enforcing game rules.

This module is the bridge between Django models and the pure scoring engine.
"""

import sys
import os

# Allow importing scoring_engine from project root
PROJECT_ROOT = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..')
sys.path.insert(0, os.path.abspath(PROJECT_ROOT))

from apps.rooms.models import Room, Player
from apps.game.models import Game, Round, Bid, Estimation, TrickResult
from apps.scoring.models import Score
from shared.constants import FIXED_TRUMP_ROUNDS, TOTAL_ROUNDS, TRICKS_PER_ROUND
from scoring_engine import calculate_score, calculate_risk, determine_dash_type


def start_game(room: Room) -> Game:
    """Create a Game and first Round for the given room."""
    game = Game.objects.create(room=room)
    room.status = Room.Status.IN_PROGRESS
    room.save(update_fields=['status'])
    _create_round(game, round_number=1, double_score=False)
    return game


def _create_round(game: Game, round_number: int, double_score: bool) -> Round:
    trump = FIXED_TRUMP_ROUNDS.get(round_number)
    return Round.objects.create(
        game=game,
        round_number=round_number,
        trump_suit=trump,
        double_score=double_score,
        phase=Round.Phase.DISTRIBUTION,
    )


def advance_phase(round_obj: Round) -> Round:
    """Move a round to its next phase."""
    order = list(Round.Phase.values)
    idx = order.index(round_obj.phase)
    if idx < len(order) - 1:
        round_obj.phase = order[idx + 1]
        round_obj.save(update_fields=['phase'])
    return round_obj


def submit_bid(round_obj: Round, player: Player, tricks_called, trump: str | None, is_pass: bool) -> Bid:
    """Record a bid for a player in the current round."""
    bid, _ = Bid.objects.update_or_create(
        round=round_obj,
        player=player,
        defaults={
            'tricks_called': None if is_pass else tricks_called,
            'trump': trump,
            'is_pass': is_pass,
        }
    )
    return bid


def determine_caller(round_obj: Round) -> Player | None:
    """
    Determine the caller from submitted bids.

    Highest (tricks_called, trump_strength) wins.
    If all pass → round is skipped.
    """
    from shared.constants import TRUMP_STRENGTH

    bids = round_obj.bids.filter(is_pass=False).select_related('player')
    if not bids.exists():
        round_obj.skipped = True
        round_obj.save(update_fields=['skipped'])
        return None

    def bid_strength(bid):
        trump_rank = len(TRUMP_STRENGTH) - TRUMP_STRENGTH.index(bid.trump)
        return (bid.tricks_called, trump_rank)

    winning_bid = max(bids, key=bid_strength)
    round_obj.caller = winning_bid.player
    if not round_obj.trump_suit:  # not a fixed-trump round
        round_obj.trump_suit = winning_bid.trump
    round_obj.save(update_fields=['caller', 'trump_suit'])
    return winning_bid.player


def submit_estimation(round_obj: Round, player: Player, tricks_estimated: int, is_dash_call: bool) -> Estimation:
    """Record a player's trick estimation for the round."""
    caller_bid = round_obj.bids.filter(player=round_obj.caller, is_pass=False).first()

    # Determine is_with: player bid the same trump suit as the caller
    is_with = False
    if round_obj.caller and player != round_obj.caller and caller_bid:
        player_bid = round_obj.bids.filter(player=player, is_pass=False).first()
        if player_bid and player_bid.trump == caller_bid.trump:
            is_with = True

    estimation, _ = Estimation.objects.update_or_create(
        round=round_obj,
        player=player,
        defaults={
            'tricks_estimated': tricks_estimated,
            'is_dash_call': is_dash_call,
            'is_with': is_with,
        }
    )
    return estimation


def record_tricks(round_obj: Round, results: list[dict]) -> list[TrickResult]:
    """
    Record tricks won per player and trigger score calculation.

    results: [{'player_id': int, 'tricks_won': int}, ...]
    """
    trick_results = []
    for r in results:
        player = Player.objects.get(id=r['player_id'])
        tr, _ = TrickResult.objects.update_or_create(
            round=round_obj,
            player=player,
            defaults={'tricks_won': r['tricks_won']}
        )
        trick_results.append(tr)

    _calculate_and_save_scores(round_obj)
    return trick_results


def _calculate_and_save_scores(round_obj: Round):
    """Run the scoring engine for all players and persist results."""
    estimations = {e.player_id: e for e in round_obj.estimations.all()}
    trick_results = {tr.player_id: tr for tr in round_obj.trick_results.all()}

    if not estimations or not trick_results:
        return

    total_called = sum(e.tricks_estimated for e in estimations.values())
    risk = calculate_risk(total_called)
    dash_type = determine_dash_type(total_called)

    # Determine round_type
    round_type = 'OVER' if total_called > TRICKS_PER_ROUND else 'UNDER'
    round_obj.round_type = round_type
    round_obj.save(update_fields=['round_type'])

    # Find winners and losers to detect "only winner/loser"
    winners = [
        pid for pid, est in estimations.items()
        if trick_results.get(pid) and trick_results[pid].tricks_won == est.tricks_estimated
    ]
    losers = [
        pid for pid, est in estimations.items()
        if trick_results.get(pid) and trick_results[pid].tricks_won != est.tricks_estimated
    ]

    caller_id = round_obj.caller_id

    for player_id, estimation in estimations.items():
        if player_id not in trick_results:
            continue

        won_tricks = trick_results[player_id].tricks_won
        is_caller = (player_id == caller_id)

        player_data = {
            'called_tricks': estimation.tricks_estimated,
            'won_tricks': won_tricks,
            'is_caller': is_caller,
            'is_with': estimation.is_with,
            'risk': risk,
            'is_dash_call': estimation.is_dash_call,
            'dash_type': dash_type.value,
            'is_only_winner': len(winners) == 1 and player_id in winners,
            'is_only_loser': len(losers) == 1 and player_id in losers,
            'round_type': round_type,
            'double_score': round_obj.double_score,
        }

        delta = calculate_score(player_data)

        Score.objects.update_or_create(
            player_id=player_id,
            round=round_obj,
            defaults={
                'called_tricks': estimation.tricks_estimated,
                'won_tricks': won_tricks,
                'score_delta': delta,
                'is_caller': is_caller,
                'is_with': estimation.is_with,
                'is_dash_call': estimation.is_dash_call,
                'risk': risk,
            }
        )

        # Update cumulative score on player
        Player.objects.filter(id=player_id).update(total_score=Player.objects.get(id=player_id).total_score + delta)

    round_obj.phase = Round.Phase.ROUND_END
    round_obj.save(update_fields=['phase'])


def advance_to_next_round(game: Game) -> Round | None:
    """
    Finish the current round and create the next one.
    Returns None if the game is over (18 rounds complete).
    """
    current_round = Round.objects.get(game=game, round_number=game.current_round)
    was_skipped = current_round.skipped

    if game.current_round >= TOTAL_ROUNDS:
        game.is_finished = True
        game.save(update_fields=['is_finished'])
        game.room.status = Room.Status.FINISHED
        game.room.save(update_fields=['status'])
        return None

    next_number = game.current_round + 1
    game.current_round = next_number
    game.save(update_fields=['current_round'])

    return _create_round(game, next_number, double_score=was_skipped)
