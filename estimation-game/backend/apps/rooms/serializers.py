from rest_framework import serializers
from .models import Room, Player
from apps.users.serializers import UserSerializer


class PlayerSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Player
        fields = ['id', 'user', 'seat_position', 'total_score']


class RoomSerializer(serializers.ModelSerializer):
    players = PlayerSerializer(many=True, read_only=True)

    class Meta:
        model = Room
        fields = ['id', 'room_code', 'status', 'created_at', 'players']
        read_only_fields = ['id', 'room_code', 'created_at']
