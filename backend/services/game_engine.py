"""Deals a hand, lets the human decide, resolves the outcome, and persists
everything.

Key insight: dealing and acting are two separate HTTP requests now (Part
10 -- there's a real human deciding, not an instant bot call), so the
board and the opponent's real hand have to be remembered server-side
between them. dealt_board_cards/dealt_opponent_hole_cards on HandHistory
are that memory -- deliberately never exposed in HandHistoryResponse, so
the secret state a human hasn't earned the right to see yet (by calling
or raising) is structurally unreachable through the API, not just
policy-redacted.

GameSession.bot_persona is the actual named OPPONENT the session is
against. Settlement reuses Part 4's ev_call directly: once the REAL
outcome is known (win / n-way split / lose, expressed as a 1 / (1/n) / 0
"realized equity"), plugging that into the exact same call-EV formula
used for decision-making gives the real bankroll change -- no separate
settlement formula needed.
"""

from poker.bots import KellyOptimalBot, LoosePassiveBot, RandomBot, TightAggressiveBot
from poker.cards import Card
from poker.deck import Deck
from poker.equity import calculate_equity
from poker.ev import ev_call
from poker.hand_evaluator import compare_hands
from poker.kelly import kelly_fraction_from_pot_odds

from backend.models import BankrollLog, HandHistory

PERSONAS = {
    'tight-aggressive': TightAggressiveBot,
    'loose-passive': LoosePassiveBot,
    'random': RandomBot,
    'kelly-optimal': KellyOptimalBot,
}

# Simplified fixed stakes for this part -- there's no multi-street betting
# structure yet (a Part 11+ UI concern). pot_size already includes the
# opponent's implied bet, matching Part 4's ev_call convention. A 1:1
# ("pot-sized bet") ratio puts the breakeven point at 50% equity -- a
# standard reference scenario, and one that naturally produces a mix of
# fold/call/raise outcomes across realistic hands (see Kelly: with these
# odds, the "call" zone -- where Kelly says risk more than nothing but not
# more than the bet itself -- is equity in roughly (0.50, 0.55]).
DEFAULT_POT_SIZE = 100.0
DEFAULT_BET_TO_CALL = 100.0

# Notional bankroll used only for the opponent bot's own bet-sizing math
# (KellyOptimalBot requires one) -- never persisted, since only hero's
# bankroll is tracked by this game.
OPPONENT_NOTIONAL_BANKROLL = 10_000.0


def _cards_to_str(cards):
    return ','.join(str(card) for card in cards)


def _cards_from_str(text):
    return [Card.from_str(token) for token in text.split(',')]


def _resolve_showdown(hero_cards, opponent_cards, board, pot_size, stake):
    hero_hand = list(hero_cards) + list(board)
    opponent_hand = list(opponent_cards) + list(board)
    winners = compare_hands([hero_hand, opponent_hand])

    if 0 in winners:
        realized_fraction = 1 / len(winners)
        winner = 'hero' if len(winners) == 1 else 'split'
    else:
        realized_fraction = 0.0
        winner = 'opponent'

    return winner, ev_call(realized_fraction, pot_size, stake)


def get_pending_hand(session, db):
    """The hand dealt but not yet acted on for this session, if any."""
    return (
        db.query(HandHistory)
        .filter_by(game_session_id=session.id, hero_action=None)
        .first()
    )


def deal_hand(session, db, num_simulations=2000, seed=None):
    """Deals a new hand and computes hero's equity/Kelly-recommended stake,
    but does NOT resolve it -- that's resolve_hand's job once the human
    submits an actual decision.

    Idempotent: if a pending hand already exists for this session, returns
    it unchanged rather than dealing a new one over it (guards against a
    double-click or a React StrictMode double-invoke burning cards).
    """
    existing = get_pending_hand(session, db)
    if existing is not None:
        return existing

    deck = Deck(seed=seed)
    deck.shuffle()
    hero_hole_cards, opponent_hole_cards = deck.deal_hole_cards(num_players=2)
    board = deck.deal_community(5)

    equity_result = calculate_equity(
        hero_hole_cards, num_opponents=1, board=(),
        num_simulations=num_simulations, seed=seed,
    )
    equity_at_decision = equity_result.equity
    kelly_recommended_stake = kelly_fraction_from_pot_odds(
        equity_at_decision, DEFAULT_POT_SIZE, DEFAULT_BET_TO_CALL, session.kelly_multiplier or 1.0,
    ) * session.current_bankroll

    hand_number = db.query(HandHistory).filter_by(game_session_id=session.id).count() + 1

    hand = HandHistory(
        game_session_id=session.id,
        hand_number=hand_number,
        hero_hole_cards=_cards_to_str(hero_hole_cards),
        dealt_board_cards=_cards_to_str(board),
        dealt_opponent_hole_cards=_cards_to_str(opponent_hole_cards),
        pot_size=DEFAULT_POT_SIZE,
        equity_at_decision=equity_at_decision,
        kelly_recommended_stake=kelly_recommended_stake,
    )
    db.add(hand)
    db.commit()
    db.refresh(hand)

    return hand


def resolve_hand(session, hand, hero_action, hero_raise_amount, db, num_simulations=2000, seed=None):
    """Resolves a pending hand (from deal_hand) given the human's real
    fold/call/raise decision. Everything from here on is the same
    settlement logic the pre-Part-10 auto-played play_hand used, just fed
    a human decision instead of KellyOptimalBot's.
    """
    hero_hole_cards = _cards_from_str(hand.hero_hole_cards)
    board = _cards_from_str(hand.dealt_board_cards)
    opponent_hole_cards = _cards_from_str(hand.dealt_opponent_hole_cards)

    opponent_bot = PERSONAS[session.bot_persona]()
    bot_action = None
    board_cards_str = None
    opponent_hole_cards_str = None

    if hero_action == 'fold':
        # Real poker never reveals a folded opponent's hand -- neither
        # board_cards nor opponent_hole_cards get stored for this hand.
        winner, bankroll_delta = 'opponent', 0.0

    elif hero_action == 'call':
        winner, bankroll_delta = _resolve_showdown(
            hero_hole_cards, opponent_hole_cards, board, DEFAULT_POT_SIZE, DEFAULT_BET_TO_CALL,
        )
        board_cards_str = _cards_to_str(board)
        opponent_hole_cards_str = _cards_to_str(opponent_hole_cards)

    else:  # 'raise' -- give the opponent a chance to fold to it first
        opponent_decision = opponent_bot.decide_from_hand(
            opponent_hole_cards, board=(), pot_size=DEFAULT_POT_SIZE,
            bet_to_call=hero_raise_amount, num_opponents=1,
            bankroll=OPPONENT_NOTIONAL_BANKROLL, num_simulations=num_simulations, seed=seed,
        )
        bot_action = opponent_decision.action

        if bot_action == 'fold':
            winner, bankroll_delta = 'hero', DEFAULT_POT_SIZE
        else:
            winner, bankroll_delta = _resolve_showdown(
                hero_hole_cards, opponent_hole_cards, board, DEFAULT_POT_SIZE, hero_raise_amount,
            )
            board_cards_str = _cards_to_str(board)
            opponent_hole_cards_str = _cards_to_str(opponent_hole_cards)

    new_bankroll = max(0.0, session.current_bankroll + bankroll_delta)

    hand.board_cards = board_cards_str
    hand.opponent_hole_cards = opponent_hole_cards_str
    hand.hero_action = hero_action
    hand.bot_action = bot_action
    hand.winner = winner
    hand.hero_bankroll_delta = bankroll_delta
    # The private deal-time memory has served its purpose -- clear it now
    # that the public columns above hold whatever's actually allowed to be
    # seen (which may still be nothing at all, if hero folded).
    hand.dealt_board_cards = None
    hand.dealt_opponent_hole_cards = None

    session.current_bankroll = new_bankroll
    db.add(BankrollLog(game_session_id=session.id, hand_history_id=hand.id, bankroll_after=new_bankroll))
    db.commit()
    db.refresh(hand)

    return hand
