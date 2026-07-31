"""A no-limit betting round for N players, plus side-pot construction and
awarding once a hand reaches showdown.

Key insight: check-vs-call and bet-vs-raise are the same engine action
just seen from different starting bets -- "check" is "match a bet of $0."
Collapsing the human-facing 5-verb vocabulary (fold/check/call/bet/raise)
down to 3 engine primitives (`fold` / `match` / `raise_to`) means the
round only ever needs one comparison to validate any action: the amount
being committed versus `current_bet`. The friendlier verbs are just a
label on top, translated at the API layer, not a second implementation.

Side-pot math is a second, independent trick: it only needs each
player's final total contribution for the whole hand (`committed_total`)
and whether they folded -- it doesn't care about streets, bet sizes, or
turn order at all. That's why `build_pots` takes a flat list of
`PlayerState` and nothing else.
"""

from collections import defaultdict
from dataclasses import dataclass
from enum import Enum

from poker.hand_evaluator import compare_hands

_EPSILON = 1e-6


class PlayerStatus(Enum):
    ACTIVE = 'active'    # can still act this street
    FOLDED = 'folded'    # out; chips already committed stay in the pot
    ALL_IN = 'all_in'    # stack is 0; still eligible to win, can't act further


@dataclass
class PlayerState:
    """Mutable per-hand state for one seat. committed_street resets every
    street; committed_total never resets until the hand ends -- pot-
    splitting only ever needs committed_total, betting rounds only ever
    need committed_street, and one `commit()` call keeps both in sync so
    they can never drift apart.
    """

    seat: int
    stack: float
    status: PlayerStatus = PlayerStatus.ACTIVE
    committed_street: float = 0.0
    committed_total: float = 0.0

    def commit(self, amount):
        """Moves `amount` (capped at available stack) from stack into the
        pot. Flips to ALL_IN if the stack hits (approximately) zero.
        Returns the actual amount committed, which may be less than
        requested if the stack couldn't cover it.
        """
        actual = max(0.0, min(amount, self.stack))
        self.stack -= actual
        self.committed_street += actual
        self.committed_total += actual

        if self.stack <= _EPSILON:
            self.stack = 0.0
            if self.status == PlayerStatus.ACTIVE:
                self.status = PlayerStatus.ALL_IN

        return actual

    def start_new_street(self):
        """Resets committed_street to 0 without touching committed_total
        -- called once per player when a new street begins."""
        self.committed_street = 0.0


@dataclass(frozen=True)
class ActionBounds:
    can_fold: bool
    can_check: bool
    can_call: bool
    call_amount: float
    can_raise: bool
    min_raise_to: float   # smallest legal "raise to" TOTAL committed_street
    max_raise_to: float   # always stack + committed_street (no-limit)


@dataclass(frozen=True)
class BettingAction:
    seat: int
    street: str
    action: str    # 'post_blind' | 'fold' | 'match' | 'raise_to'
    amount: float          # incremental chips moved by this action
    total_committed: float  # this seat's committed_street AFTER the action
    pot_size_after: float = 0.0  # every seat's committed_total, summed, right after this action


class BettingRound:
    """One street's worth of betting for a set of players.

    `order`: seat indices in the order they act, starting from whoever
    acts first on this street. `current_bet`: the amount already required
    to stay in (the big blind preflop, 0 on every later street unless
    someone's already posted something). `min_raise`: the smallest legal
    raise INCREMENT; defaults to `current_bet` (a reasonable self-
    contained fallback -- real callers should pass the actual big blind).

    Simplification (deliberate, matches this project's brief for keeping
    real-poker fidelity balanced against implementation cost): an
    undersized all-in (a raise below the normal minimum, because the
    raiser doesn't have enough to make a full raise) still reopens the
    action for everyone else, exactly like a full raise would. Official
    poker rules treat this as a special case that does NOT reopen action
    for players who already matched the previous bet -- that distinction
    isn't implemented here.
    """

    def __init__(self, players, order, current_bet=0.0, min_raise=None, street='preflop'):
        self.players = {p.seat: p for p in players}
        self.order = list(order)
        self.current_bet = current_bet
        self.last_raise_increment = min_raise if min_raise is not None else (current_bet or 1.0)
        self.street = street
        self.actions = []
        self.needs_to_act = {
            seat for seat in self.order
            if self.players[seat].status == PlayerStatus.ACTIVE
        }
        self._cursor = 0

    def _active_non_folded_count(self):
        return sum(1 for p in self.players.values() if p.status != PlayerStatus.FOLDED)

    def _pot_size(self):
        """Every seat's committed_total, summed -- the whole hand's pot so
        far, not just this street's. committed_total never resets between
        streets, so this is correct regardless of which street this round
        is for, with no separate running total to keep in sync."""
        return sum(p.committed_total for p in self.players.values())

    def is_closed(self):
        return not self.needs_to_act or self._active_non_folded_count() < 2

    def next_to_act(self):
        if self.is_closed():
            return None

        n = len(self.order)
        for offset in range(n):
            seat = self.order[(self._cursor + offset) % n]
            if seat in self.needs_to_act:
                return seat

        return None  # pragma: no cover -- unreachable if is_closed() is accurate

    def legal_action_bounds(self, seat):
        player = self.players[seat]
        to_call = self.current_bet - player.committed_street

        call_amount = max(0.0, min(to_call, player.stack))
        can_check = to_call <= _EPSILON
        can_call = to_call > _EPSILON and player.stack > _EPSILON

        max_raise_to = player.committed_street + player.stack
        min_raise_to = self.current_bet + self.last_raise_increment
        can_raise = player.stack > _EPSILON and max_raise_to > self.current_bet + _EPSILON

        if can_raise and min_raise_to > max_raise_to:
            # Not enough stack for a full min-raise -- the only legal
            # "raise" left is an undersized all-in.
            min_raise_to = max_raise_to

        return ActionBounds(
            can_fold=True,
            can_check=can_check,
            can_call=can_call,
            call_amount=call_amount,
            can_raise=can_raise,
            min_raise_to=min_raise_to,
            max_raise_to=max_raise_to,
        )

    def apply(self, seat, action, raise_to=None):
        if self.is_closed():
            raise ValueError('betting round is already closed')
        if seat not in self.needs_to_act:
            raise ValueError(f'seat {seat} is not eligible to act right now')

        player = self.players[seat]
        bounds = self.legal_action_bounds(seat)

        if action == 'fold':
            player.status = PlayerStatus.FOLDED
            self.needs_to_act.discard(seat)
            record = BettingAction(seat, self.street, 'fold', 0.0, player.committed_street, self._pot_size())

        elif action == 'match':
            if not (bounds.can_check or bounds.can_call):
                raise ValueError(f'seat {seat} cannot check or call right now')
            actual = player.commit(bounds.call_amount)
            self.needs_to_act.discard(seat)
            record = BettingAction(seat, self.street, 'match', actual, player.committed_street, self._pot_size())

        elif action == 'raise_to':
            if not bounds.can_raise:
                raise ValueError(f'seat {seat} cannot raise right now')
            if raise_to is None:
                raise ValueError('raise_to amount is required for a raise_to action')

            is_all_in = abs(raise_to - bounds.max_raise_to) < _EPSILON
            if raise_to > bounds.max_raise_to + _EPSILON:
                raise ValueError('raise_to exceeds this seat\'s available stack')
            if raise_to < bounds.min_raise_to - _EPSILON and not is_all_in:
                raise ValueError('raise_to is below the minimum legal raise')

            old_current_bet = self.current_bet
            delta = raise_to - player.committed_street
            actual = player.commit(delta)
            new_total = player.committed_street

            self.current_bet = new_total
            self.last_raise_increment = new_total - old_current_bet

            # A raise reopens the action for every other seat still able
            # to act -- including seats that already matched this street,
            # since the bar just moved (see the class docstring for the
            # undersized-all-in simplification this includes).
            self.needs_to_act = {
                s for s, p in self.players.items()
                if p.status == PlayerStatus.ACTIVE and s != seat
            }
            record = BettingAction(seat, self.street, 'raise_to', actual, new_total, self._pot_size())

        else:
            raise ValueError(f'unknown action {action!r}')

        self.actions.append(record)
        if seat in self.order:
            self._cursor = (self.order.index(seat) + 1) % len(self.order)

        return record

    def post_blind(self, seat, amount):
        """Forced post, not a choice -- bypasses needs_to_act entirely.
        Call this before any apply() calls for the street."""
        player = self.players[seat]
        actual = player.commit(amount)
        self.current_bet = max(self.current_bet, player.committed_street)
        record = BettingAction(seat, self.street, 'post_blind', actual, player.committed_street, self._pot_size())
        self.actions.append(record)
        return record

    def refund_uncalled_bet(self):
        """Call once, after the round has closed, before pots are built.
        Returns the excess of the single largest committed_street this
        street over the second-largest -- among EVERY player still in the
        round, folded or not, since even a folded player's partial call
        genuinely contested that portion of the bet. Without this, chip
        totals silently don't balance and a pot layer can end up with no
        eligible winners (build_pots raises loudly if that ever happens).

        Covers both flavors: everyone folds to a bet (refunds the whole
        thing, since nobody matched any of it), and the remaining
        opponents are only able to call for less (refunds the difference).
        A no-op (returns None) when the top two commitments are equal --
        nothing was left uncalled.
        """
        committed = sorted((p.committed_street for p in self.players.values()), reverse=True)
        highest = committed[0] if committed else 0.0
        second_highest = committed[1] if len(committed) > 1 else 0.0

        if highest <= second_highest + _EPSILON:
            return None

        top_player = max(self.players.values(), key=lambda p: p.committed_street)
        refund = highest - second_highest

        top_player.stack += refund
        top_player.committed_street -= refund
        top_player.committed_total -= refund
        if top_player.status == PlayerStatus.ALL_IN and top_player.stack > _EPSILON:
            top_player.status = PlayerStatus.ACTIVE

        return refund


@dataclass(frozen=True)
class Pot:
    amount: float
    eligible_seats: frozenset


def build_pots(players):
    """The standard 'layer' side-pot algorithm. Only needs each player's
    final committed_total and status -- doesn't care how the money
    arrived, what street it is, or turn order.

    Worked example: 3 players all-in for $50/$120/$200 (no folds).
    Thresholds: 50, 120, 200.
      - Layer 0->50:   3 contributors, amount = 50*3  = 150, eligible = all 3.
      - Layer 50->120: 2 contributors, amount = 70*2  = 140, eligible = the $120/$200 players.
      - Layer 120->200: 1 contributor, amount = 80*1  =  80, eligible = the $200 player (wins it uncontested).
      Checksum: 150 + 140 + 80 = 370 = 50 + 120 + 200.
    """
    contributors = [p for p in players if p.committed_total > _EPSILON]
    if not contributors:
        return []

    thresholds = sorted({round(p.committed_total, 2) for p in contributors})

    pots = []
    previous = 0.0
    for threshold in thresholds:
        layer_contributors = [p for p in contributors if round(p.committed_total, 2) >= threshold]
        layer_amount = round((threshold - previous) * len(layer_contributors), 2)

        if layer_amount > _EPSILON:
            eligible = frozenset(
                p.seat for p in layer_contributors if p.status != PlayerStatus.FOLDED
            )
            if not eligible:
                # Should be unreachable if the uncalled-bet refund (a
                # hand-flow-level responsibility, not this function's) ran
                # before build_pots was called -- if every contributor to
                # a layer folded, that layer's excess should already have
                # been refunded rather than left in the pot. Surface this
                # loudly rather than silently vanishing real money.
                raise ValueError(
                    f'pot layer of {layer_amount} has no eligible (non-folded) winners -- '
                    'an uncalled bet was not refunded before pots were built'
                )
            pots.append(Pot(layer_amount, eligible))

        previous = threshold

    return pots


def award_pots(pots, hands):
    """hands: dict of seat -> best-hand-eligible card collection (hole +
    board), for every seat eligible for at least one pot (i.e. every
    non-folded seat). Returns dict of seat -> amount won.

    Reuses poker.hand_evaluator.compare_hands UNCHANGED per pot layer --
    it already returns N-way winner indices, exactly what a contested
    layer needs. A layer with only one eligible seat is awarded directly,
    with no hand comparison needed.
    """
    payouts = defaultdict(float)

    for pot in pots:
        eligible_seats = sorted(pot.eligible_seats)

        if len(eligible_seats) == 1:
            payouts[eligible_seats[0]] += pot.amount
            continue

        hands_list = [hands[seat] for seat in eligible_seats]
        winner_indices = compare_hands(hands_list)
        share = pot.amount / len(winner_indices)

        for index in winner_indices:
            payouts[eligible_seats[index]] += share

    return dict(payouts)
