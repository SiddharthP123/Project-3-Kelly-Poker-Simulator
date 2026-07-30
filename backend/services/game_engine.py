"""Orchestrates one full hand end-to-end: deal, get each side's decision,
resolve the outcome, and persist everything in one transaction.

Key insight: hero is auto-played by a fixed KellyOptimalBot for this part
-- there's no interactive UI yet for a human to submit a decision from
(that's a Part 10 concern), and "what the textbook-optimal player would
do" is the most defensible stand-in for a human that doesn't exist yet.
GameSession.bot_persona is the actual named OPPONENT the session is
against.

Settlement reuses Part 4's ev_call directly: once the REAL outcome is
known (win / n-way split / lose, expressed as a 1 / (1/n) / 0 "realized
equity"), plugging that into the exact same call-EV formula used for
decision-making gives the real bankroll change -- no separate settlement
formula needed.
"""

from poker.bots import KellyOptimalBot, LoosePassiveBot, RandomBot, TightAggressiveBot
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
# structure yet (a Part 10 UI concern). pot_size already includes the
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


def play_hand(session, db, num_simulations=2000, seed=None):
    """session: a GameSession already added to db. db: the active SQLAlchemy
    session (same one FastAPI's get_db dependency yields)."""
    deck = Deck(seed=seed)
    deck.shuffle()
    hero_hole_cards, opponent_hole_cards = deck.deal_hole_cards(num_players=2)
    board = deck.deal_community(5)

    # Hero's equity is computed once, up front, and reused both for the
    # decision itself and for the equity_at_decision/kelly_recommended_stake
    # analytics fields -- no need to recompute it inside a second Bot call.
    equity_result = calculate_equity(
        hero_hole_cards, num_opponents=1, board=(),
        num_simulations=num_simulations, seed=seed,
    )
    equity_at_decision = equity_result.equity
    kelly_recommended_stake = kelly_fraction_from_pot_odds(
        equity_at_decision, DEFAULT_POT_SIZE, DEFAULT_BET_TO_CALL,
    ) * session.current_bankroll

    hero_action = KellyOptimalBot().decide(
        equity_at_decision, DEFAULT_POT_SIZE, DEFAULT_BET_TO_CALL, bankroll=session.current_bankroll,
    )

    opponent_bot = PERSONAS[session.bot_persona]()
    opponent_action = None
    board_cards_str = None
    opponent_hole_cards_str = None

    if hero_action.action == 'fold':
        # Real poker never reveals a folded opponent's hand -- neither
        # board_cards nor opponent_hole_cards get stored for this hand.
        winner, bankroll_delta = 'opponent', 0.0

    elif hero_action.action == 'call':
        winner, bankroll_delta = _resolve_showdown(
            hero_hole_cards, opponent_hole_cards, board, DEFAULT_POT_SIZE, DEFAULT_BET_TO_CALL,
        )
        board_cards_str = _cards_to_str(board)
        opponent_hole_cards_str = _cards_to_str(opponent_hole_cards)

    else:  # 'raise' -- give the opponent a chance to fold to it first
        opponent_action = opponent_bot.decide_from_hand(
            opponent_hole_cards, board=(), pot_size=DEFAULT_POT_SIZE,
            bet_to_call=hero_action.raise_amount, num_opponents=1,
            bankroll=OPPONENT_NOTIONAL_BANKROLL, num_simulations=num_simulations, seed=seed,
        )

        if opponent_action.action == 'fold':
            winner, bankroll_delta = 'hero', DEFAULT_POT_SIZE
        else:
            winner, bankroll_delta = _resolve_showdown(
                hero_hole_cards, opponent_hole_cards, board, DEFAULT_POT_SIZE, hero_action.raise_amount,
            )
            board_cards_str = _cards_to_str(board)
            opponent_hole_cards_str = _cards_to_str(opponent_hole_cards)

    new_bankroll = max(0.0, session.current_bankroll + bankroll_delta)
    hand_number = db.query(HandHistory).filter_by(game_session_id=session.id).count() + 1

    hand = HandHistory(
        game_session_id=session.id,
        hand_number=hand_number,
        hero_hole_cards=_cards_to_str(hero_hole_cards),
        board_cards=board_cards_str,
        opponent_hole_cards=opponent_hole_cards_str,
        pot_size=DEFAULT_POT_SIZE,
        hero_action=hero_action.action,
        bot_action=opponent_action.action if opponent_action else None,
        equity_at_decision=equity_at_decision,
        kelly_recommended_stake=kelly_recommended_stake,
        winner=winner,
        hero_bankroll_delta=bankroll_delta,
    )
    db.add(hand)
    session.current_bankroll = new_bankroll
    db.flush()  # populate hand.id before the bankroll log references it

    db.add(BankrollLog(game_session_id=session.id, hand_history_id=hand.id, bankroll_after=new_bankroll))
    db.commit()
    db.refresh(hand)

    return hand
