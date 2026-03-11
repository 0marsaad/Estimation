from rest_framework import serializers
from .models import Score
from apps.rooms.serializers import PlayerSerializer
from apps.game.serializers import RoundSerializer


class ScoreSerializer(serializers.ModelSerializer):
    player = PlayerSerializer(read_only=True)

    class Meta:
        model = Score
        fields = [
            'id', 'player', 'round', 'called_tricks', 'won_tricks',
            'score_delta', 'is_caller', 'is_with', 'is_dash_call', 'risk',
        ]
