from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, inline_serializer
from drf_spectacular.types import OpenApiTypes
from rest_framework import serializers as drf_serializers
from apps.rooms.models import Room, Player
from apps.scoring.models import Score
from .models import Game, Round, Bid, Estimation
from .serializers import (
    GameSerializer, RoundSerializer,
    SubmitBidSerializer, SubmitEstimationSerializer, RecordTricksSerializer,
)
from .game_service import (
    start_game, submit_bid, determine_caller,
    submit_estimation, record_tricks, advance_to_next_round, advance_phase,
)
from apps.scoring.serializers import ScoreSerializer


def _get_player_or_404(request, room):
    player = room.players.filter(user=request.user).first()
    if not player:
        return None
    return player


@extend_schema(
    tags=['game'],
    summary='Start a game',
    description='Starts the game for a room. Creates a Game record and the first Round. Requires exactly 4 players.',
    request=inline_serializer('StartGameRequest', fields={'room_id': drf_serializers.IntegerField()}),
    responses={
        201: GameSerializer,
        400: OpenApiResponse(description='Game already started, or not enough players'),
        403: OpenApiResponse(description='You are not in this room'),
        404: OpenApiResponse(description='Room not found'),
    },
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def game_start(request):
    room_id = request.data.get('room_id')
    room = get_object_or_404(Room, id=room_id)

    if room.status != Room.Status.WAITING:
        return Response({'detail': 'Game already started or room is finished.'}, status=400)
    if room.players.count() != 4:
        return Response({'detail': 'Need exactly 4 players to start.'}, status=400)
    if not room.players.filter(user=request.user).exists():
        return Response({'detail': 'You are not in this room.'}, status=403)

    game = start_game(room)
    return Response(GameSerializer(game).data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=['game'],
    summary='Game state',
    description='Returns the complete game state including all rounds, bids, estimations, and trick results.',
    parameters=[
        OpenApiParameter('room_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=True, description='Room primary key'),
    ],
    responses={
        200: GameSerializer,
        404: OpenApiResponse(description='Room or game not found'),
    },
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def game_state(request):
    room_id = request.query_params.get('room_id')
    room = get_object_or_404(Room, id=room_id)
    game = get_object_or_404(Game, room=room)
    return Response(GameSerializer(game).data)


@extend_schema(
    tags=['game'],
    summary='Submit a bid',
    description=(
        'Submits a bid for the authenticated player in the current round. '
        'Set `is_pass=true` to pass. When not passing, `tricks_called` (≥4) and `trump` are required. '
        'After the 4th bid the caller is determined automatically and the round advances to ESTIMATION.'
    ),
    request=SubmitBidSerializer,
    responses={
        201: OpenApiResponse(description='Bid object'),
        400: OpenApiResponse(description='Round not in BIDDING phase or validation error'),
        403: OpenApiResponse(description='You are not in this room'),
    },
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bid(request):
    room_id = request.data.get('room_id')
    room = get_object_or_404(Room, id=room_id)
    player = _get_player_or_404(request, room)
    if not player:
        return Response({'detail': 'You are not in this room.'}, status=403)

    game = get_object_or_404(Game, room=room)
    current_round = get_object_or_404(Round, game=game, round_number=game.current_round)

    if current_round.phase != Round.Phase.BIDDING:
        return Response({'detail': 'Round is not in bidding phase.'}, status=400)

    serializer = SubmitBidSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)

    bid_obj = submit_bid(
        current_round, player,
        serializer.validated_data.get('tricks_called'),
        serializer.validated_data.get('trump'),
        serializer.validated_data['is_pass'],
    )

    # Auto-determine caller when all 4 bids are in
    if current_round.bids.count() == 4:
        determine_caller(current_round)
        advance_phase(current_round)

    from .serializers import BidSerializer
    return Response(BidSerializer(bid_obj).data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=['game'],
    summary='Submit an estimation',
    description=(
        'Submits a tricks estimation for the authenticated player. '
        'Caller must estimate ≥ their bid; other players must estimate ≤ caller bid. '
        'After the 4th estimation, the total must not equal 13 — if it does the last submission is rejected. '
        'On a valid 4th submission the round advances to PLAYING.'
    ),
    request=SubmitEstimationSerializer,
    responses={
        201: OpenApiResponse(description='Estimation object'),
        400: OpenApiResponse(description='Constraint violated or total equals 13'),
        403: OpenApiResponse(description='You are not in this room'),
    },
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def estimate(request):
    room_id = request.data.get('room_id')
    room = get_object_or_404(Room, id=room_id)
    player = _get_player_or_404(request, room)
    if not player:
        return Response({'detail': 'You are not in this room.'}, status=403)

    game = get_object_or_404(Game, room=room)
    current_round = get_object_or_404(Round, game=game, round_number=game.current_round)

    if current_round.phase != Round.Phase.ESTIMATION:
        return Response({'detail': 'Round is not in estimation phase.'}, status=400)

    serializer = SubmitEstimationSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)

    tricks_estimated = serializer.validated_data['tricks_estimated']

    # Validate estimate constraints
    caller_bid = current_round.bids.filter(player=current_round.caller, is_pass=False).first()
    if caller_bid:
        if player == current_round.caller and tricks_estimated < caller_bid.tricks_called:
            return Response({'detail': 'Caller estimate must be ≥ their bid.'}, status=400)
        if player != current_round.caller and tricks_estimated > caller_bid.tricks_called:
            return Response({'detail': 'Estimate must be ≤ caller bid.'}, status=400)

    est_obj = submit_estimation(
        current_round, player,
        tricks_estimated,
        serializer.validated_data['is_dash_call'],
    )

    # Validate total estimates ≠ 13 only when all 4 are in
    if current_round.estimations.count() == 4:
        total = sum(e.tricks_estimated for e in current_round.estimations.all())
        if total == 13:
            est_obj.delete()
            return Response(
                {'detail': 'Total estimates cannot equal 13. Please change your estimate.'},
                status=400
            )
        advance_phase(current_round)

    from .serializers import EstimationSerializer
    return Response(EstimationSerializer(est_obj).data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=['game'],
    summary='Record tricks (play)',
    description=(
        'Records the tricks won by each player after the physical card play. '
        'The `results` array must contain one entry per player and the `tricks_won` values must sum to 13. '
        'Triggers score calculation and advances the round to ROUND_END.'
    ),
    request=RecordTricksSerializer,
    responses={
        200: OpenApiResponse(description='{"detail": "Tricks recorded and scores calculated."}'),
        400: OpenApiResponse(description='Not in PLAYING phase, or tricks do not sum to 13'),
        403: OpenApiResponse(description='You are not in this room'),
    },
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def play(request):
    room_id = request.data.get('room_id')
    room = get_object_or_404(Room, id=room_id)
    player = _get_player_or_404(request, room)
    if not player:
        return Response({'detail': 'You are not in this room.'}, status=403)

    game = get_object_or_404(Game, room=room)
    current_round = get_object_or_404(Round, game=game, round_number=game.current_round)

    if current_round.phase != Round.Phase.PLAYING:
        return Response({'detail': 'Round is not in playing phase.'}, status=400)

    serializer = RecordTricksSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)

    trick_results = record_tricks(current_round, serializer.validated_data['results'])
    return Response({'detail': 'Tricks recorded and scores calculated.'})


@extend_schema(
    tags=['game'],
    summary='Advance to next round',
    description=(
        'Advances the game to the next round after the current one reaches ROUND_END. '
        'Returns the new Round object (201), or {"is_finished": true} when the game ends after round 18.'
    ),
    request=inline_serializer('NextRoundRequest', fields={'room_id': drf_serializers.IntegerField()}),
    responses={
        201: RoundSerializer,
        200: OpenApiResponse(description='{"detail": "Game finished.", "is_finished": true}'),
        400: OpenApiResponse(description='Current round is not finished yet'),
    },
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def next_round(request):
    room_id = request.data.get('room_id')
    room = get_object_or_404(Room, id=room_id)

    game = get_object_or_404(Game, room=room)
    current_round = get_object_or_404(Round, game=game, round_number=game.current_round)

    if current_round.phase != Round.Phase.ROUND_END:
        return Response({'detail': 'Current round is not finished yet.'}, status=400)

    new_round = advance_to_next_round(game)
    if new_round is None:
        return Response({'detail': 'Game finished.', 'is_finished': True})
    return Response(RoundSerializer(new_round).data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=['game'],
    summary='Advance phase (manual)',
    description=(
        'Manually advances the round through pre-bidding phases: DISTRIBUTION → DASH_CALL → BIDDING. '
        'All later transitions are triggered automatically by the bid/estimate/play endpoints.'
    ),
    request=inline_serializer('AdvancePhaseRequest', fields={'room_id': drf_serializers.IntegerField()}),
    responses={
        200: inline_serializer('AdvancePhaseResponse', fields={'phase': drf_serializers.CharField()}),
        400: OpenApiResponse(description='Cannot manually advance from current phase'),
        403: OpenApiResponse(description='You are not in this room'),
    },
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def advance_phase_view(request):
    room_id = request.data.get('room_id')
    room = get_object_or_404(Room, id=room_id)
    if not room.players.filter(user=request.user).exists():
        return Response({'detail': 'You are not in this room.'}, status=403)

    game = get_object_or_404(Game, room=room)
    current_round = get_object_or_404(Round, game=game, round_number=game.current_round)

    # Only allow advancing through pre-bidding phases manually
    allowed_phases = [Round.Phase.DISTRIBUTION, Round.Phase.DASH_CALL]
    if current_round.phase not in allowed_phases:
        return Response({'detail': f'Cannot manually advance from phase {current_round.phase}.'}, status=400)

    advance_phase(current_round)
    return Response({'phase': current_round.phase})


@extend_schema(
    tags=['game'],
    summary='Leaderboard scores',
    description='Returns all players in the room ordered by total score descending.',
    parameters=[
        OpenApiParameter('room_id', OpenApiTypes.INT, OpenApiParameter.QUERY, required=True, description='Room primary key'),
    ],
    responses={
        200: inline_serializer(
            'LeaderboardEntry',
            fields={
                'player': drf_serializers.CharField(),
                'seat': drf_serializers.IntegerField(),
                'total_score': drf_serializers.IntegerField(),
            },
            many=True,
        ),
        404: OpenApiResponse(description='Room not found'),
    },
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def scores(request):
    room_id = request.query_params.get('room_id')
    room = get_object_or_404(Room, id=room_id)
    players = room.players.select_related('user').order_by('-total_score')
    data = [
        {'player': p.user.username, 'seat': p.seat_position, 'total_score': p.total_score}
        for p in players
    ]
    return Response(data)
