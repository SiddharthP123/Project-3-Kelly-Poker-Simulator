"""Orchestrates one full multi-street hand -- dealing, blinds, streets,
bot turns, and showdown -- on top of poker/betting.py's single-street
primitives.

Key insight: a hand is just a sequence of BettingRounds (one per street)
joined by "deal the next street's cards, then start a fresh round" -- the
same PlayerState objects carry stack/status through every street, since
`committed_total` never resets and folded/all-in status is permanent for
the hand. advance_hand's job is to drive that sequence forward -- calling
bots' decisions and closing/opening streets -- until either it reaches
hero's turn (the resumability boundary an HTTP request needs, since hero
now decides across multiple separate requests instead of one) or the hand
is over.

Fold-outs and real showdowns are resolved by the exact same function
(`_resolve_pot`): build_pots + award_pots already handle a single eligible
seat as a trivial one-seat "pot", with no hand comparison needed -- so a
hand where everyone else folds needs no special-casing, it's just a
showdown where every pot layer happens to have exactly one eligible seat.

The whole board is dealt once, upfront, in create_hand -- not
street-by-street as _advance_street reaches each one. This has no effect
on the game itself (a shuffled deck's outcome is fixed at shuffle time
either way; revealing cards later doesn't change what they are or any
probability), but it means HandState never needs to hold a live, mutating
Deck object past hand creation -- everything needed to reconstruct
HandState later (e.g. from DB rows, across separate HTTP requests that
can't share Python object identity) is just plain data: the fixed
5-card board, dealt hole cards, and the action log. `board` is a slice of
that fixed board, sized to whatever the current street has revealed so
far, not a separately-tracked mutable list.
"""

from dataclasses import dataclass, field

from poker.betting import BettingRound, PlayerState, PlayerStatus, award_pots, build_pots
from poker.bots import PERSONA_REGISTRY
from poker.deck import Deck
from poker.equity import calculate_equity

_EPSILON = 1e-6

STREET_ORDER = ['preflop', 'flop', 'turn', 'river']

# How many of the 5 fixed board cards are visible once a given street is
# reached -- 'complete' shows the same full board 'river' does, showdown
# doesn't add a 6th card.
_VISIBLE_BOARD_CARDS = {'preflop': 0, 'flop': 3, 'turn': 4, 'river': 5, 'complete': 5}

# Bot-facing equity calls run far more often than hero-facing ones now (up
# to 4 bots x 4 streets = up to 16 calls per hand), so they default to a
# lower sample count than the 10000 used elsewhere in the project.
DEFAULT_BOT_NUM_SIMULATIONS = 750


@dataclass
class HandState:
    """Mutable state for one in-progress (or just-completed) hand."""

    players: dict            # seat -> PlayerState
    personas: dict            # seat -> persona key, for every non-hero seat
    hero_seat: int
    button_seat: int
    small_blind: float
    big_blind: float
    hole_cards: dict          # seat -> [Card, Card]
    full_board: list          # all 5 community cards, fixed from deal time
    street: str               # 'preflop' | 'flop' | 'turn' | 'river' | 'complete'
    betting_round: object     # BettingRound, or None once street == 'complete'
    action_log: list = field(default_factory=list)
    hand_number: int = 1
    result: dict = None       # populated once street == 'complete'

    @property
    def board(self):
        return self.full_board[:_VISIBLE_BOARD_CARDS[self.street]]


def create_hand(
    num_opponents, hero_stack, opponent_stacks, personas,
    small_blind=1.0, big_blind=2.0, hand_number=1, seed=None,
):
    """Deals a fresh hand: hole cards to every seat, blinds posted, the
    preflop BettingRound ready for its first action.

    hero always sits seat 0; opponents fill seats 1..num_opponents.
    `opponent_stacks`/`personas` are one entry per opponent, in seat order
    -- the caller decides those values (e.g. randomizing each bot's
    per-hand stack), this function only deals with the mechanics of
    starting the hand once they're chosen.

    Button rotates uniformly by hand_number, including heads-up (no
    special heads-up button treatment) -- a deliberate simplification;
    see the Part 12 plan for why.
    """
    if not 1 <= num_opponents <= 4:
        raise ValueError('num_opponents must be between 1 and 4')
    if len(opponent_stacks) != num_opponents:
        raise ValueError('opponent_stacks must have exactly one entry per opponent')
    if len(personas) != num_opponents:
        raise ValueError('personas must have exactly one entry per opponent')

    num_seats = num_opponents + 1

    deck = Deck(seed=seed)
    deck.shuffle()
    dealt_hands = deck.deal_hole_cards(num_seats)
    hole_cards = {seat: dealt_hands[seat] for seat in range(num_seats)}

    # Dealt in the same order/burn pattern _advance_street used to deal it
    # in (one street at a time): flop's burn+3, then turn's burn+1, then
    # river's burn+1. Doing it all now rather than as each street is
    # reached doesn't change which cards come up for a given seed -- see
    # the module docstring -- it just means nothing later needs the Deck.
    full_board = deck.deal_community(3, burn=True) + deck.deal_community(1, burn=True) + deck.deal_community(1, burn=True)

    stacks = [hero_stack] + list(opponent_stacks)
    players = {seat: PlayerState(seat=seat, stack=stacks[seat]) for seat in range(num_seats)}
    personas_by_seat = {seat + 1: persona for seat, persona in enumerate(personas)}

    button_seat = (hand_number - 1) % num_seats
    sb_seat = (button_seat + 1) % num_seats
    bb_seat = (button_seat + 2) % num_seats
    first_to_act = (bb_seat + 1) % num_seats
    order = [(first_to_act + i) % num_seats for i in range(num_seats)]

    round_ = BettingRound(players.values(), order, current_bet=0.0, min_raise=big_blind, street='preflop')

    action_log = [
        round_.post_blind(sb_seat, small_blind),
        round_.post_blind(bb_seat, big_blind),
    ]

    return HandState(
        players=players,
        personas=personas_by_seat,
        hero_seat=0,
        button_seat=button_seat,
        small_blind=small_blind,
        big_blind=big_blind,
        hole_cards=hole_cards,
        full_board=full_board,
        street='preflop',
        betting_round=round_,
        action_log=action_log,
        hand_number=hand_number,
    )


def rebuild_hand_state(hero_seat, button_seat, small_blind, big_blind, hand_number, seat_data, full_board, action_log):
    """Reconstructs a HandState purely from already-persisted plain data --
    what a caller needs to resume a hand across separate HTTP requests,
    since a fresh request can't share Python object identity with whatever
    process handled the previous one. Takes plain dicts/lists rather than
    ORM objects, so this module stays fully decoupled from any particular
    storage layer, matching every other poker/ module in this project.

    seat_data: one dict per seat -- {'seat', 'stack' (this hand's STARTING
        stack, before anything was committed), 'persona' (None for hero),
        'hole_cards'}.
    full_board: the fixed 5 community cards dealt at hand creation.
    action_log: every action taken on this hand so far, in order --
        {'seq', 'street', 'seat', 'action', 'amount'}. This is exactly a
        prefix of what create_hand/advance_hand/apply_hero_action would
        have produced had the hand run continuously in one process --
        replaying it through the same BettingRound primitives
        (post_blind/apply) that originally generated it reconstructs an
        identical BettingRound (current_bet, min-raise, whose turn it is,
        all of it) with no separate bookkeeping needed. _advance_street is
        replayed too, exactly whenever the street changes, so a caller can
        immediately resume with advance_hand/apply_hero_action afterward
        as if execution had never paused.
    """
    num_seats = len(seat_data)
    players = {s['seat']: PlayerState(seat=s['seat'], stack=s['stack']) for s in seat_data}
    personas = {s['seat']: s['persona'] for s in seat_data if s['persona'] is not None}
    hole_cards = {s['seat']: s['hole_cards'] for s in seat_data}

    sb_seat = (button_seat + 1) % num_seats
    bb_seat = (button_seat + 2) % num_seats
    first_to_act = (bb_seat + 1) % num_seats
    order = [(first_to_act + i) % num_seats for i in range(num_seats)]

    state = HandState(
        players=players,
        personas=personas,
        hero_seat=hero_seat,
        button_seat=button_seat,
        small_blind=small_blind,
        big_blind=big_blind,
        hole_cards=hole_cards,
        full_board=full_board,
        street='preflop',
        betting_round=BettingRound(players.values(), order, current_bet=0.0, min_raise=big_blind, street='preflop'),
        hand_number=hand_number,
    )

    for entry in sorted(action_log, key=lambda a: a['seq']):
        while state.street != entry['street']:
            _advance_street(state)

        seat, action, amount = entry['seat'], entry['action'], entry['amount']
        if action == 'post_blind':
            record = state.betting_round.post_blind(seat, amount)
        elif action == 'raise_to':
            raise_to = state.players[seat].committed_street + amount
            record = state.betting_round.apply(seat, 'raise_to', raise_to=raise_to)
        else:  # 'fold' or 'match'
            record = state.betting_round.apply(seat, action)
        state.action_log.append(record)

    return state


def default_bot_action(state, seat, num_simulations=DEFAULT_BOT_NUM_SIMULATIONS):
    """The real-persona bot decision used unless a caller (tests, mostly)
    supplies a stub. Translates poker.bots' fold/call/raise vocabulary
    into the betting engine's fold/match/raise_to primitives.

    Two simplifications, deliberate and specific to this translation
    layer (poker/bots.py itself is untouched):

    - When there's nothing to call (checking is free), "fold" is never a
      realistic choice, and "call" means the same thing as "check" since
      the actual required amount is 0 -- both collapse to `match`. Only a
      "raise" response (the bot wants to bet into a checked-around pot)
      changes what actually happens. Bot.decide still needs a nonzero
      bet_to_call to evaluate against (KellyOptimalBot requires one), so a
      nominal big-blind-sized amount is passed purely to ask "would you
      bet here" -- it is never actually committed.
    - A bot's raise is interpreted as its desired absolute committed_street
      total for the street (not an increment on top of whatever it's
      already put in), then clamped against legal_action_bounds: below the
      minimum legal raise becomes a call, above the seat's stack is capped
      at all-in.
    """
    round_ = state.betting_round
    bounds = round_.legal_action_bounds(seat)
    player = state.players[seat]
    bot = PERSONA_REGISTRY[state.personas[seat]]()

    num_live_opponents = sum(
        1 for other_seat, other in state.players.items()
        if other_seat != seat and other.status != PlayerStatus.FOLDED
    )
    equity_result = calculate_equity(
        state.hole_cards[seat],
        num_opponents=max(1, num_live_opponents),
        board=tuple(state.board),
        num_simulations=num_simulations,
    )
    pot_size = sum(p.committed_total for p in state.players.values())

    facing_bet = bounds.call_amount > _EPSILON
    nominal_bet_to_call = bounds.call_amount if facing_bet else state.big_blind
    decision = bot.decide(equity_result.equity, pot_size, nominal_bet_to_call, bankroll=player.stack)

    if not facing_bet:
        if decision.action != 'raise':
            return 'match', None
    elif decision.action == 'fold':
        return 'fold', None
    elif decision.action == 'call':
        return 'match', None

    raise_to = decision.raise_amount
    if raise_to < bounds.min_raise_to - _EPSILON:
        return 'match', None
    if raise_to > bounds.max_raise_to:
        raise_to = bounds.max_raise_to
    return 'raise_to', raise_to


def _advance_street(state):
    state.betting_round.refund_uncalled_bet()

    for player in state.players.values():
        player.start_new_street()

    next_street = STREET_ORDER[STREET_ORDER.index(state.street) + 1]
    state.street = next_street  # state.board reveals more automatically -- see the property

    num_seats = len(state.players)
    first_to_act = (state.button_seat + 1) % num_seats
    order = [(first_to_act + i) % num_seats for i in range(num_seats)]

    state.betting_round = BettingRound(
        state.players.values(), order, current_bet=0.0, min_raise=state.big_blind, street=next_street,
    )


def _resolve_pot(state):
    state.betting_round.refund_uncalled_bet()

    non_folded = [
        seat for seat, player in state.players.items() if player.status != PlayerStatus.FOLDED
    ]
    pots = build_pots(list(state.players.values()))
    hands = {seat: state.hole_cards[seat] + state.board for seat in non_folded}
    payouts = award_pots(pots, hands)

    for seat, amount in payouts.items():
        state.players[seat].stack += amount

    # A folded hand is never revealed, and neither is a fold-out winner's
    # (nobody was left to call) -- cards only get shown at a genuine 2+
    # player showdown, matching real poker and this project's existing
    # redaction guarantee.
    reveal = {seat: state.hole_cards[seat] for seat in non_folded} if len(non_folded) >= 2 else {}

    state.result = {
        'payouts': payouts,
        'pots': pots,
        'reveal': reveal,
        'winners': sorted(payouts.keys()),
    }
    state.street = 'complete'
    state.betting_round = None


def advance_hand(state, decide_bot_action=default_bot_action):
    """Resolves bot turns and street transitions until either it's hero's
    turn to act or the hand is complete. Safe to call repeatedly -- a
    no-op (returns immediately) once the hand is already complete."""
    while True:
        if state.street == 'complete':
            return state

        non_folded = [
            seat for seat, player in state.players.items() if player.status != PlayerStatus.FOLDED
        ]
        if len(non_folded) < 2:
            _resolve_pot(state)
            return state

        round_ = state.betting_round
        if round_.is_closed():
            if state.street == 'river':
                _resolve_pot(state)
                return state
            _advance_street(state)
            continue

        seat = round_.next_to_act()
        if seat == state.hero_seat:
            return state

        action, raise_to = decide_bot_action(state, seat)
        record = round_.apply(seat, action, raise_to=raise_to)
        state.action_log.append(record)


def apply_hero_action(state, action, raise_to=None):
    """Applies hero's one fold/call/raise decision. Does not itself
    resolve whatever follows (further bot turns, street transitions,
    showdown) -- the caller runs advance_hand again for that, keeping the
    two responsibilities separate."""
    if state.street == 'complete':
        raise ValueError('hand is already complete')

    round_ = state.betting_round
    if round_.next_to_act() != state.hero_seat:
        raise ValueError('it is not hero\'s turn to act')

    if action == 'fold':
        record = round_.apply(state.hero_seat, 'fold')
    elif action == 'call':
        record = round_.apply(state.hero_seat, 'match')
    elif action == 'raise':
        if raise_to is None:
            raise ValueError('raise_to is required for a raise action')
        record = round_.apply(state.hero_seat, 'raise_to', raise_to=raise_to)
    else:
        raise ValueError(f'unknown hero action {action!r}')

    state.action_log.append(record)
    return state
