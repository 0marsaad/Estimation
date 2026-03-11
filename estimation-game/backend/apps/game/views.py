from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
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


# POST /game/start
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


# GET /game/state?room_id=X
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def game_state(request):
    room_id = request.query_params.get('room_id')
    room = get_object_or_404(Room, id=room_id)
    game = get_object_or_404(Game, room=room)
    return Response(GameSerializer(game).data)


# POST /game/bid
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


# POST /game/estimate
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


# POST /game/play   (record tricks won after physical play)
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


# POST /game/next-round
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


# POST /game/advance  (advance phase for UI-only transitions: DISTRIBUTION→DASH_CALL→BIDDING)
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


# GET /game/scores?room_id=X
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
