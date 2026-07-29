"""Expected value (EV) and pot odds -- turning an equity estimate (Part 3)
into an actual decision: fold, call, or raise.

Key insight: pot odds convert a bet size into a probability threshold.
Comparing your equity against that threshold tells you whether calling is
profitable, without ever needing to compute a dollar EV. This is the same
"compare an estimated probability to a break-even threshold" logic used to
decide whether an investment's expected return justifies its risk --
pot odds are a poker-specific breakeven analysis.
"""

from dataclasses import dataclass


def pot_odds_breakeven_equity(pot_size, bet_to_call):
    """The minimum win probability needed for calling to break even.

    pot_size: the pot BEFORE your call (this includes whatever the
        opponent just bet).
    bet_to_call: how much you must put in to continue.

    Derivation: calling breaks even when
        equity * pot_size == (1 - equity) * bet_to_call
    Solving for equity gives bet_to_call / (pot_size + bet_to_call).
    """
    if pot_size < 0:
        raise ValueError('pot_size cannot be negative')
    if bet_to_call <= 0:
        raise ValueError('bet_to_call must be positive')

    return bet_to_call / (pot_size + bet_to_call)


def ev_fold():
    """Folding forfeits everything already in the pot, but that's a sunk
    cost from this decision's point of view -- from here, folding risks
    nothing further and wins nothing further. EV is always exactly 0."""
    return 0.0


def ev_call(equity, pot_size, bet_to_call):
    """Expected net profit of calling, in the same units as pot_size/bet.

    If you win (probability = equity), you net the pot as it stood before
    your call (your own call is returned to you, so it isn't profit).
    If you lose, you net -bet_to_call.
    """
    if not 0 <= equity <= 1:
        raise ValueError('equity must be between 0 and 1')
    if pot_size < 0:
        raise ValueError('pot_size cannot be negative')
    if bet_to_call <= 0:
        raise ValueError('bet_to_call must be positive')

    return equity * pot_size - (1 - equity) * bet_to_call


def ev_raise(equity, pot_size, raise_amount, fold_probability):
    """Expected net profit of raising, given an assumed probability that
    the opponent folds to the raise.

    Two branches, weighted by how often each happens:
    - Opponent folds (fold_probability): you win the pot as it stood
      before your raise -- net profit = pot_size.
    - Opponent calls (1 - fold_probability): it goes to showdown with
      raise_amount now matched by both players. From here the math is
      identical to a call -- you're both risking raise_amount into a pot
      that was pot_size -- so this branch reuses ev_call directly.
    """
    if not 0 <= equity <= 1:
        raise ValueError('equity must be between 0 and 1')
    if not 0 <= fold_probability <= 1:
        raise ValueError('fold_probability must be between 0 and 1')
    if pot_size < 0:
        raise ValueError('pot_size cannot be negative')
    if raise_amount <= 0:
        raise ValueError('raise_amount must be positive')

    ev_if_called = ev_call(equity, pot_size, raise_amount)
    return fold_probability * pot_size + (1 - fold_probability) * ev_if_called


@dataclass(frozen=True)
class Decision:
    """The recommended action plus the EV of every action considered, so
    the reasoning is inspectable rather than just a single label."""

    action: str
    evs: dict

    def __str__(self):
        evs_text = ', '.join(f'{action}={ev:+.2f}' for action, ev in self.evs.items())
        return f'{self.action} ({evs_text})'


def best_action(equity, pot_size, bet_to_call, raise_amount=None, fold_probability=None):
    """Pick the highest-EV action out of fold, call, and (optionally) raise.

    raise_amount and fold_probability must be supplied together -- raising
    isn't evaluated at all unless both are known.
    """
    if raise_amount is None and fold_probability is not None:
        raise ValueError('raise_amount must be provided if fold_probability is given')
    if fold_probability is None and raise_amount is not None:
        raise ValueError('fold_probability must be provided if raise_amount is given')

    evs = {
        'fold': ev_fold(),
        'call': ev_call(equity, pot_size, bet_to_call),
    }

    if raise_amount is not None:
        evs['raise'] = ev_raise(equity, pot_size, raise_amount, fold_probability)

    best = max(evs, key=evs.get)
    return Decision(action=best, evs=evs)
