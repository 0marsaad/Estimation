TOTAL_ROUNDS = 18
PLAYERS_PER_ROOM = 4
TRICKS_PER_ROUND = 13
MINIMUM_BID_TRICKS = 4
MINIMUM_BID_SUIT = 'CLUBS'

# Fixed trumps for the last 5 rounds (rounds 14-18)
FIXED_TRUMP_ROUNDS = {
    14: 'SANS',
    15: 'SPADES',
    16: 'HEARTS',
    17: 'DIAMONDS',
    18: 'CLUBS',
}

# Trump suit strength ranking (index 0 = strongest)
TRUMP_STRENGTH = ['SANS', 'SPADES', 'HEARTS', 'DIAMONDS', 'CLUBS']

# Card rank strength (index 0 = strongest)
CARD_RANK_STRENGTH = ['A', 'K', 'Q', 'J', '10', '9', '8', '7', '6', '5', '4', '3', '2']

# Scoring constants
ROUND_SCORE = 10
TRICKS_AMOUNT_MULTIPLIER = 1
CALLER_WITH_BONUS = 10
ONLY_WINNER_LOSER_BONUS = 10
RISK_BONUS_PER_UNIT = 10
DASH_OVER_BONUS = 25
DASH_UNDER_BONUS = 33
HIGH_CALL_THRESHOLD = 8
