from django.db import models
from apps.rooms.models import Player
from apps.game.models import Round


class Score(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='scores')
    round = models.ForeignKey(Round, on_delete=models.CASCADE, related_name='scores')
    called_tricks = models.PositiveSmallIntegerField()
    won_tricks = models.PositiveSmallIntegerField()
    score_delta = models.IntegerField()
    # Snapshot of flags used in calculation (for auditing / display)
    is_caller = models.BooleanField(default=False)
    is_with = models.BooleanField(default=False)
    is_dash_call = models.BooleanField(default=False)
    risk = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = 'scores'
        unique_together = [('player', 'round')]

    def __str__(self):
        return f'{self.player} round {self.round.round_number}: {self.score_delta:+d}'
