"""Deals and resolves real multi-street, multi-opponent poker hands (Part
12), replacing Parts 8-10's single fixed-pot/one-opponent model.

Key insight: a hand now spans multiple separate HTTP requests (deal, then
one or more acts, since a real human decides across several streets
instead of one instant decision) -- so HandState can't just live in a
Python variable between them the way poker.hand_flow's own tests do it in
one continuous process. poker.hand_flow.rebuild_hand_state reconstructs
it fresh from whatever's been persisted so far (HandPlayer/HandAction
rows) every time a request needs to continue a hand, and
advance_hand/apply_hero_action pick up exactly where the previous request
left off.

Bots get a randomized per-hand stack (50-150 big blinds), reset every
hand -- only hero's session.current_bankroll persists across hands, per
the Part 12 plan's simplification (tracking 4 more bot bankrolls doesn't
serve this project's hero-bankroll-centric purpose).

Redaction happens at response-assembly time (_build_live_response /
build_historical_response), not in storage -- HandPlayer.hole_cards is
always the real cards for every seat. A seat's cards are only ever
serialized once it's earned the right to be seen: always for hero's own
seat, and for every other seat once the hand reaches a genuine multi-way
showdown -- never for a folded seat, and never for a fold-out winner
either (matching real poker, and Part 10's original redaction guarantee,
just via a different mechanism that scales to 1-4 opponents).

GameSession.bot_persona is vestigial as of this part (kept NOT NULL with
a placeholder rather than dropped -- see the Part 12 plan); the real
per-seat personas live in GameSessionOpponent. HandHistory's old
single-opponent columns (opponent_hole_cards, equity_at_decision, etc.)
are likewise left untouched but unused going forward -- board_cards and
dealt_board_cards are the two exceptions, reused for their original
purpose (revealed-so-far vs. internal-only-until-earned), just now
holding a progressively-revealed multi-street board instead of an
instantly-dealt one.
"""

import random

from poker.betting import PlayerStatus
from poker.bots import assign_opponent_personas
from poker.cards import Card
from poker.hand_flow import advance_hand, apply_hero_action, create_hand, rebuild_hand_state

from backend.models import BankrollLog, GameSession, GameSessionOpponent, HandAction, HandHistory, HandPlayer

BOT_STACK_MIN_BB = 50
BOT_STACK_MAX_BB = 150


def _cards_to_str(cards):
    return ','.join(str(card) for card in cards)


def _cards_from_str(text):
    if not text:
        return []
    return [Card.from_str(token) for token in text.split(',')]


def create_game_session(current_user, body, db):
    starting_bankroll = body.starting_bankroll or current_user.starting_bankroll
    personas = assign_opponent_personas(body.num_opponents, random.Random())

    session = GameSession(
        user_id=current_user.id,
        starting_bankroll=starting_bankroll,
        current_bankroll=starting_bankroll,
        bot_persona='multi-opponent',  # vestigial placeholder -- see Part 12 plan
        kelly_multiplier=body.kelly_multiplier,
        num_opponents=body.num_opponents,
        small_blind=body.small_blind,
        big_blind=body.big_blind,
    )
    db.add(session)
    db.flush()

    for seat_index, persona in enumerate(personas, start=1):
        db.add(GameSessionOpponent(game_session_id=session.id, seat_index=seat_index, persona=persona))

    db.add(BankrollLog(game_session_id=session.id, bankroll_after=session.starting_bankroll))
    db.commit()
    db.refresh(session)
    return session


def get_pending_hand(session, db):
    """The hand dealt but not yet resolved for this session, if any."""
    return (
        db.query(HandHistory)
        .filter(
            HandHistory.game_session_id == session.id,
            HandHistory.street.isnot(None),
            HandHistory.street != 'complete',
        )
        .order_by(HandHistory.hand_number.desc())
        .first()
    )


def _load_and_sync_state(hand, db):
    """Reconstructs this hand's HandState from whatever's been persisted so
    far, then completes (and immediately persists) any street-transition
    or bot-turn resolution the persisted action log doesn't yet reflect.

    rebuild_hand_state only ever replays exactly what's recorded -- and
    nothing gets recorded for a fresh street until someone actually acts
    on it, so a hand whose last persisted action closed a street (with
    hero's real next turn landing on the NEW street, possibly after a bot
    acts first there) reconstructs one advance_hand cascade behind where
    it actually needs to be. Calling advance_hand here catches it up.

    This step MUST be persisted immediately, not just returned to the
    caller -- default_bot_action uses live, unseeded Monte Carlo equity,
    so recomputing this same "catch-up" again later (e.g. a second read
    of the same pending hand) could otherwise resolve a bot's turn
    differently each time, with nothing ever recorded as the real outcome.

    Returns (state, new_actions) -- new_actions is whatever this catch-up
    step resolved (possibly empty, when the persisted log already ended
    exactly at hero's turn or a completed hand).
    """
    previous_count = len(hand.actions)
    seat_data = [
        {
            'seat': p.seat_index, 'stack': p.starting_stack,
            'persona': p.persona, 'hole_cards': _cards_from_str(p.hole_cards),
        }
        for p in sorted(hand.players, key=lambda p: p.seat_index)
    ]
    action_log = [
        {'seq': a.seq, 'street': a.street, 'seat': a.seat_index, 'action': a.action, 'amount': a.amount}
        for a in sorted(hand.actions, key=lambda a: a.seq)
    ]
    session = hand.game_session

    state = rebuild_hand_state(
        hero_seat=0, button_seat=hand.button_seat,
        small_blind=session.small_blind, big_blind=session.big_blind,
        hand_number=hand.hand_number, seat_data=seat_data,
        full_board=_cards_from_str(hand.dealt_board_cards), action_log=action_log,
    )
    state = advance_hand(state)

    new_actions = state.action_log[previous_count:]
    _persist_progress(hand, state, new_actions, db)
    return state, new_actions


def _persist_new_hand(session, hand_number, state, starting_stacks, db):
    hand = HandHistory(
        game_session_id=session.id,
        hand_number=hand_number,
        hero_hole_cards=_cards_to_str(state.hole_cards[state.hero_seat]),
        dealt_board_cards=_cards_to_str(state.full_board),
        pot_size=0.0,
        button_seat=state.button_seat,
        street=state.street,
    )
    db.add(hand)
    db.flush()

    for seat, player in state.players.items():
        db.add(HandPlayer(
            hand_history_id=hand.id, seat_index=seat, is_hero=(seat == state.hero_seat),
            persona=state.personas.get(seat), starting_stack=starting_stacks[seat],
            hole_cards=_cards_to_str(state.hole_cards[seat]),
            folded=(player.status == PlayerStatus.FOLDED),
            all_in=(player.status == PlayerStatus.ALL_IN),
        ))
    db.flush()

    return hand


def _persist_progress(hand, state, new_actions, db):
    """Appends whatever's new since the last time this hand was persisted
    (new HandAction rows) and syncs HandHistory/HandPlayer to reflect the
    state as it now stands. Called once after every deal_hand/act_on_hand
    call, whether or not the hand actually finished this time."""
    existing_count = len(hand.actions)
    for offset, action in enumerate(new_actions):
        db.add(HandAction(
            hand_history_id=hand.id, seq=existing_count + offset, street=action.street,
            seat_index=action.seat, action=action.action, amount=action.amount,
            pot_size_after=action.pot_size_after,
        ))

    players_by_seat = {p.seat_index: p for p in hand.players}
    is_complete = state.street == 'complete'
    for seat, player in state.players.items():
        hand_player = players_by_seat[seat]
        hand_player.folded = (player.status == PlayerStatus.FOLDED)
        hand_player.all_in = (player.status == PlayerStatus.ALL_IN)
        if is_complete:
            hand_player.final_stack = player.stack
            hand_player.net_result = player.stack - hand_player.starting_stack
            hand_player.is_winner = state.result['payouts'].get(seat, 0.0) > 0

    hand.street = state.street
    hand.board_cards = _cards_to_str(state.board)
    hand.pot_size = sum(p.committed_total for p in state.players.values())

    if is_complete:
        hero_hand_player = players_by_seat[state.hero_seat]
        hero_delta = state.players[state.hero_seat].stack - hero_hand_player.starting_stack
        session = hand.game_session
        session.current_bankroll = max(0.0, session.current_bankroll + hero_delta)
        db.add(BankrollLog(
            game_session_id=session.id, hand_history_id=hand.id, bankroll_after=session.current_bankroll,
        ))

    db.commit()


def _build_live_response(hand, state, new_actions):
    """Assembles the response for a hand that's actively being played --
    deal_hand, act_on_hand, and the pending-hand fetch all use this, since
    all three need the reconstructed HandState (for legal_action_bounds
    and live per-seat stacks), not just what's already in the DB."""
    is_complete = state.street == 'complete'
    reveal_seats = set(state.result['reveal'].keys()) if is_complete else set()
    players_by_seat = {p.seat_index: p for p in hand.players}

    player_responses = []
    for seat in sorted(state.players.keys()):
        player = state.players[seat]
        hand_player = players_by_seat[seat]
        can_reveal = seat == state.hero_seat or seat in reveal_seats
        player_responses.append({
            'seat_index': seat,
            'is_hero': seat == state.hero_seat,
            'persona': state.personas.get(seat),
            'stack': player.stack,
            'hole_cards': _cards_to_str(state.hole_cards[seat]) if can_reveal else None,
            'folded': player.status == PlayerStatus.FOLDED,
            'all_in': player.status == PlayerStatus.ALL_IN,
            'is_winner': hand_player.is_winner,
            'net_result': hand_player.net_result,
        })

    legal_action_bounds = None
    if not is_complete:
        bounds = state.betting_round.legal_action_bounds(state.hero_seat)
        legal_action_bounds = {
            'can_fold': bounds.can_fold, 'can_check': bounds.can_check, 'can_call': bounds.can_call,
            'call_amount': bounds.call_amount, 'can_raise': bounds.can_raise,
            'min_raise_to': bounds.min_raise_to, 'max_raise_to': bounds.max_raise_to,
        }

    start_seq = len(state.action_log) - len(new_actions)
    return {
        'id': hand.id,
        'hand_number': hand.hand_number,
        'button_seat': hand.button_seat,
        'street': state.street,
        'board_cards': _cards_to_str(state.board),
        'pot_size': hand.pot_size,
        'players': player_responses,
        'legal_action_bounds': legal_action_bounds,
        'actions': [
            {
                'seq': start_seq + i, 'street': a.street, 'seat_index': a.seat,
                'action': a.action, 'amount': a.amount, 'pot_size_after': a.pot_size_after,
            }
            for i, a in enumerate(new_actions)
        ],
        'winners': state.result['winners'] if is_complete else None,
        'played_at': hand.played_at,
    }


def build_historical_response(hand):
    """Assembles the response for listing hand history -- cheaper than
    the live path, since a finished (or abandoned) hand needs no
    HandState reconstruction at all; everything it needs is already
    persisted directly on HandHistory/HandPlayer/HandAction."""
    is_complete = hand.street == 'complete'

    return {
        'id': hand.id,
        'hand_number': hand.hand_number,
        'button_seat': hand.button_seat,
        'street': hand.street,
        'board_cards': hand.board_cards,
        'pot_size': hand.pot_size,
        'players': [
            {
                'seat_index': p.seat_index,
                'is_hero': p.is_hero,
                'persona': p.persona,
                'stack': p.final_stack if p.final_stack is not None else p.starting_stack,
                'hole_cards': p.hole_cards if (p.is_hero or (is_complete and not p.folded)) else None,
                'folded': p.folded,
                'all_in': p.all_in,
                'is_winner': p.is_winner,
                'net_result': p.net_result,
            }
            for p in sorted(hand.players, key=lambda p: p.seat_index)
        ],
        'legal_action_bounds': None,
        'actions': [
            {
                'seq': a.seq, 'street': a.street, 'seat_index': a.seat_index,
                'action': a.action, 'amount': a.amount, 'pot_size_after': a.pot_size_after,
            }
            for a in sorted(hand.actions, key=lambda a: a.seq)
        ],
        'winners': [p.seat_index for p in hand.players if p.is_winner] if is_complete else None,
        'played_at': hand.played_at,
    }


def get_pending_hand_response(hand, db):
    """The live view of a hand that's already been dealt but not yet
    resolved. Reconstructing can itself resolve (and persist) a pending
    bot-turn/street-transition catch-up -- see _load_and_sync_state --
    so any actions that produced are reported too, not hidden from a
    client that's specifically asking to see this hand's current state."""
    state, new_actions = _load_and_sync_state(hand, db)
    return _build_live_response(hand, state, new_actions=new_actions)


def deal_hand(session, db, seed=None):
    """Deals a new hand, resolving any bot turns that come before hero's
    first decision. Idempotent: a pending hand already existing for this
    session is returned as-is rather than dealing a new one over it
    (guards against a double-click or a React StrictMode double-invoke
    burning cards)."""
    existing = get_pending_hand(session, db)
    if existing is not None:
        return get_pending_hand_response(existing, db)

    rng = random.Random(seed)
    opponents = sorted(session.opponents, key=lambda o: o.seat_index)
    num_opponents = session.num_opponents
    opponent_stacks = [
        rng.uniform(BOT_STACK_MIN_BB, BOT_STACK_MAX_BB) * session.big_blind for _ in range(num_opponents)
    ]
    personas = [o.persona for o in opponents]
    hand_number = db.query(HandHistory).filter_by(game_session_id=session.id).count() + 1
    hero_stack = session.current_bankroll

    state = create_hand(
        num_opponents=num_opponents, hero_stack=hero_stack, opponent_stacks=opponent_stacks,
        personas=personas, small_blind=session.small_blind, big_blind=session.big_blind,
        hand_number=hand_number, seed=seed,
    )
    state = advance_hand(state)  # resolve any bot turns before hero's first decision

    starting_stacks = {0: hero_stack}
    starting_stacks.update({seat + 1: opponent_stacks[seat] for seat in range(num_opponents)})

    hand = _persist_new_hand(session, hand_number, state, starting_stacks, db)
    _persist_progress(hand, state, state.action_log, db)

    return _build_live_response(hand, state, new_actions=state.action_log)


def act_on_hand(hand, action, raise_to, db):
    """Applies hero's fold/call/raise decision to a pending hand, then
    resolves whatever follows (further bot turns, street transitions,
    possibly a full showdown) before returning. Raises ValueError for an
    illegal action (not hero's turn, hand already complete, bad raise_to)
    -- translated to an HTTP 400 by the router, not here."""
    state, _ = _load_and_sync_state(hand, db)
    previous_count = len(hand.actions)  # reflects whatever _load_and_sync_state just persisted

    state = apply_hero_action(state, action, raise_to=raise_to)
    state = advance_hand(state)

    new_actions = state.action_log[previous_count:]
    _persist_progress(hand, state, new_actions, db)

    return _build_live_response(hand, state, new_actions=new_actions)
