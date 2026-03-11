from enum import Enum


class TrumpSuit(str, Enum):
    SANS = 'SANS'
    SPADES = 'SPADES'
    HEARTS = 'HEARTS'
    DIAMONDS = 'DIAMONDS'
    CLUBS = 'CLUBS'


class RoundType(str, Enum):
    OVER = 'OVER'
    UNDER = 'UNDER'


class DashType(str, Enum):
    OVER = 'OVER'
    UNDER = 'UNDER'


class RoundPhase(str, Enum):
    WAITING_FOR_PLAYERS = 'WAITING_FOR_PLAYERS'
    DISTRIBUTION = 'DISTRIBUTION'
    DASH_CALL = 'DASH_CALL'
    BIDDING = 'BIDDING'
    ESTIMATION = 'ESTIMATION'
    PLAYING = 'PLAYING'
    SCORING = 'SCORING'
    ROUND_END = 'ROUND_END'


class RoomStatus(str, Enum):
    WAITING = 'WAITING'
    IN_PROGRESS = 'IN_PROGRESS'
    FINISHED = 'FINISHED'
