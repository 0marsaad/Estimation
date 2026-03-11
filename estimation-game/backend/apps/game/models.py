from django.db import models
from apps.rooms.models import Room, Player
from shared.constants import FIXED_TRUMP_ROUNDS


class Game(models.Model):
    room = models.OneToOneField(Room, on_delete=models.CASCADE, related_name='game')
    current_round = models.PositiveSmallIntegerField(default=1)
    is_finished = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'games'

    def __str__(self):
        return f'Game in {self.room.room_code} (round {self.current_round})'


class Round(models.Model):
    class TrumpSuit(models.TextChoices):
        SANS = 'SANS', 'Sans'
        SPADES = 'SPADES', 'Spades'
        HEARTS = 'HEARTS', 'Hearts'
        DIAMONDS = 'DIAMONDS', 'Diamonds'
        CLUBS = 'CLUBS', 'Clubs'

    class RoundType(models.TextChoices):
        OVER = 'OVER', 'Over'
        UNDER = 'UNDER', 'Under'

    class Phase(models.TextChoices):
        WAITING_FOR_PLAYERS = 'WAITING_FOR_PLAYERS', 'Waiting for Players'
        DISTRIBUTION = 'DISTRIBUTION', 'Distribution'
        DASH_CALL = 'DASH_CALL', 'Dash Call'
        BIDDING = 'BIDDING', 'Bidding'
        ESTIMATION = 'ESTIMATION', 'Estimation'
        PLAYING = 'PLAYING', 'Playing'
        SCORING = 'SCORING', 'Scoring'
        ROUND_END = 'ROUND_END', 'Round End'

    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='rounds')
    round_number = models.PositiveSmallIntegerField()
    trump_suit = models.CharField(max_length=10, choices=TrumpSuit.choices, null=True, blank=True)
    round_type = models.CharField(max_length=10, choices=RoundType.choices, null=True, blank=True)
    double_score = models.BooleanField(default=False)
    phase = models.CharField(max_length=30, choices=Phase.choices, default=Phase.DISTRIBUTION)
    # The player (seat) who won the bid and becomes caller
    caller = models.ForeignKey(
        Player, on_delete=models.SET_NULL, null=True, blank=True, related_name='called_rounds'
    )
    skipped = models.BooleanField(default=False)  # All players passed

    class Meta:
        db_table = 'rounds'
        unique_together = [('game', 'round_number')]

    def __str__(self):
        return f'Round {self.round_number} of game {self.game_id}'

    @property
    def has_fixed_trump(self):
        return self.round_number in FIXED_TRUMP_ROUNDS


class Bid(models.Model):
    class TrumpSuit(models.TextChoices):
        SANS = 'SANS', 'Sans'
        SPADES = 'SPADES', 'Spades'
        HEARTS = 'HEARTS', 'Hearts'
        DIAMONDS = 'DIAMONDS', 'Diamonds'
        CLUBS = 'CLUBS', 'Clubs'
        PASS = 'PASS', 'Pass'

    round = models.ForeignKey(Round, on_delete=models.CASCADE, related_name='bids')
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='bids')
    tricks_called = models.PositiveSmallIntegerField(null=True, blank=True)  # null when PASS
    trump = models.CharField(max_length=10, choices=TrumpSuit.choices, null=True, blank=True)
    is_pass = models.BooleanField(default=False)

    class Meta:
        db_table = 'bids'
        unique_together = [('round', 'player')]

    def __str__(self):
        if self.is_pass:
            return f'{self.player} PASS'
        return f'{self.player} bid ({self.tricks_called}, {self.trump})'


class Estimation(models.Model):
    round = models.ForeignKey(Round, on_delete=models.CASCADE, related_name='estimations')
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='estimations')
    tricks_estimated = models.PositiveSmallIntegerField()
    is_dash_call = models.BooleanField(default=False)
    # is_with is derived: player bid same trump as caller
    is_with = models.BooleanField(default=False)

    class Meta:
        db_table = 'estimations'
        unique_together = [('round', 'player')]

    def __str__(self):
        return f'{self.player} estimated {self.tricks_estimated} (round {self.round.round_number})'


class TrickResult(models.Model):
    round = models.ForeignKey(Round, on_delete=models.CASCADE, related_name='trick_results')
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='trick_results')
    tricks_won = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = 'trick_results'
        unique_together = [('round', 'player')]

    def __str__(self):
        return f'{self.player} won {self.tricks_won} tricks (round {self.round.round_number})'
