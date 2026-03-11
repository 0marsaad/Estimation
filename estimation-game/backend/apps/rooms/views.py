from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Room, Player
from .serializers import RoomSerializer
from shared.constants import PLAYERS_PER_ROOM


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_room(request):
    # A user shouldn't be in an active room already
    active_player = Player.objects.filter(
        user=request.user,
        room__status__in=[Room.Status.WAITING, Room.Status.IN_PROGRESS]
    ).first()
    if active_player:
        return Response(
            {'detail': 'You are already in an active room.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    room = Room.objects.create()
    Player.objects.create(user=request.user, room=room, seat_position=0)
    return Response(RoomSerializer(room).data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def join_room(request):
    room_code = request.data.get('room_code', '').upper()
    if not room_code:
        return Response({'detail': 'room_code is required.'}, status=status.HTTP_400_BAD_REQUEST)

    room = get_object_or_404(Room, room_code=room_code)

    if room.status != Room.Status.WAITING:
        return Response({'detail': 'Room is not accepting players.'}, status=status.HTTP_400_BAD_REQUEST)

    if room.players.count() >= PLAYERS_PER_ROOM:
        return Response({'detail': 'Room is full.'}, status=status.HTTP_400_BAD_REQUEST)

    if room.players.filter(user=request.user).exists():
        return Response({'detail': 'You are already in this room.'}, status=status.HTTP_400_BAD_REQUEST)

    occupied_seats = set(room.players.values_list('seat_position', flat=True))
    seat = next(i for i in range(PLAYERS_PER_ROOM) if i not in occupied_seats)

    Player.objects.create(user=request.user, room=room, seat_position=seat)
    return Response(RoomSerializer(room).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def room_detail(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    return Response(RoomSerializer(room).data)
