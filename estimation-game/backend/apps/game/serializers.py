from rest_framework import serializers
from .models import Game, Round, Bid, Estimation, TrickResult
from apps.rooms.serializers import PlayerSerializer


class BidSerializer(serializers.ModelSerializer):
    player = PlayerSerializer(read_only=True)

    class Meta:
        model = Bid
        fields = ['id', 'player', 'tricks_called', 'trump', 'is_pass']


class EstimationSerializer(serializers.ModelSerializer):
    player = PlayerSerializer(read_only=True)

    class Meta:
        model = Estimation
        fields = ['id', 'player', 'tricks_estimated', 'is_dash_call', 'is_with']


class TrickResultSerializer(serializers.ModelSerializer):
    player = PlayerSerializer(read_only=True)

    class Meta:
        model = TrickResult
        fields = ['id', 'player', 'tricks_won']


class RoundSerializer(serializers.ModelSerializer):
    bids = BidSerializer(many=True, read_only=True)
    estimations = EstimationSerializer(many=True, read_only=True)
    trick_results = TrickResultSerializer(many=True, read_only=True)
    caller = PlayerSerializer(read_only=True)

    class Meta:
        model = Round
        fields = [
            'id', 'round_number', 'trump_suit', 'round_type',
            'double_score', 'phase', 'caller', 'skipped',
            'bids', 'estimations', 'trick_results',
        ]


class GameSerializer(serializers.ModelSerializer):
    rounds = RoundSerializer(many=True, read_only=True)

    class Meta:
        model = Game
        fields = ['id', 'room', 'current_round', 'is_finished', 'rounds']


# ---- Input serializers ----

class SubmitBidSerializer(serializers.Serializer):
    tricks_called = serializers.IntegerField(min_value=4, required=False, allow_null=True)
    trump = serializers.ChoiceField(choices=[c[0] for c in Bid.TrumpSuit.choices], required=False, allow_null=True)
    is_pass = serializers.BooleanField(default=False)

    def validate(self, data):
        if not data.get('is_pass'):
            if data.get('tricks_called') is None:
                raise serializers.ValidationError('tricks_called is required when not passing.')
            if not data.get('trump'):
                raise serializers.ValidationError('trump is required when not passing.')
        return data


class SubmitEstimationSerializer(serializers.Serializer):
    tricks_estimated = serializers.IntegerField(min_value=0, max_value=13)
    is_dash_call = serializers.BooleanField(default=False)


class SubmitTrickResultSerializer(serializers.Serializer):
    player_id = serializers.IntegerField()
    tricks_won = serializers.IntegerField(min_value=0, max_value=13)


class RecordTricksSerializer(serializers.Serializer):
    results = SubmitTrickResultSerializer(many=True)

    def validate_results(self, value):
        total = sum(r['tricks_won'] for r in value)
        if total != 13:
            raise serializers.ValidationError('Total tricks won must equal 13.')
        return value
