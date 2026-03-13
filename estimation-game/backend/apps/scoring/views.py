from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from drf_spectacular.types import OpenApiTypes
from apps.rooms.models import Room
from .models import Score
from .serializers import ScoreSerializer


@extend_schema(
    tags=['scoring'],
    summary='Round scores',
    description='Returns the Score record for every player in a specific round.',
    parameters=[
        OpenApiParameter('room_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=True, description='Room primary key'),
        OpenApiParameter('round_number', OpenApiTypes.INT, OpenApiParameter.QUERY, required=True, description='Round number (1–18)'),
    ],
    responses={
        200: ScoreSerializer(many=True),
        404: OpenApiResponse(description='Room not found'),
    },
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def round_scores(request):
    """GET /scoring/round/?room_id=X&round_number=Y"""
    room_id = request.query_params.get('room_id')
    round_number = request.query_params.get('round_number')
    room = get_object_or_404(Room, id=room_id)
    scores = Score.objects.filter(
        player__room=room,
        round__round_number=round_number,
    ).select_related('player', 'player__user', 'round')
    return Response(ScoreSerializer(scores, many=True).data)


@extend_schema(
    tags=['scoring'],
    summary='Full game score history',
    description='Returns all Score records for an entire game ordered by round number ascending.',
    parameters=[
        OpenApiParameter('room_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=True, description='Room primary key'),
    ],
    responses={
        200: ScoreSerializer(many=True),
        404: OpenApiResponse(description='Room not found'),
    },
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def game_scores(request):
    """GET /scoring/game/?room_id=X  — full history"""
    room_id = request.query_params.get('room_id')
    room = get_object_or_404(Room, id=room_id)
    scores = Score.objects.filter(
        player__room=room,
    ).select_related('player', 'player__user', 'round').order_by('round__round_number')
    return Response(ScoreSerializer(scores, many=True).data)
