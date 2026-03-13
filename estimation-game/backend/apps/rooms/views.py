from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from drf_spectacular.types import OpenApiTypes
from .models import Room, Player
from .serializers import RoomSerializer
from shared.constants import PLAYERS_PER_ROOM


@extend_schema(
    tags=['rooms'],
    summary='Create a room',
    description='Creates a new game room. The requesting user is automatically assigned seat 0.',
    request=None,
    responses={
        201: RoomSerializer,
        400: OpenApiResponse(description='You are already in an active room'),
    },
)
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


@extend_schema(
    tags=['rooms'],
    summary='Join a room',
    description=(
        'Joins an existing room by its 6-character room code. '
        'The server automatically assigns the next available seat (0–3).'
    ),
    request={
        'application/json': {
            'type': 'object',
            'properties': {'room_code': {'type': 'string', 'example': 'ABCD12'}},
            'required': ['room_code'],
        }
    },
    responses={
        200: RoomSerializer,
        400: OpenApiResponse(description='Room is full, not accepting players, or you are already in it'),
        404: OpenApiResponse(description='Room not found'),
    },
)
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


@extend_schema(
    tags=['rooms'],
    summary='Room detail',
    description='Returns the full state of a room including its players list.',
    parameters=[
        OpenApiParameter('room_id', OpenApiTypes.INT, OpenApiParameter.PATH, description='Room primary key'),
    ],
    responses={
        200: RoomSerializer,
        404: OpenApiResponse(description='Room not found'),
    },
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def room_detail(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    return Response(RoomSerializer(room).data)
