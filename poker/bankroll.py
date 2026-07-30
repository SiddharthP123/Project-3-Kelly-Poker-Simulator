"""Simulate many bankroll sessions under different staking strategies to
compare long-run growth and risk of ruin.

Key insight: the "aggressive growth vs. safety" trade-off in bet sizing
isn't a matter of opinion or risk tolerance -- it's a direct mathematical
consequence of how the SAME sequence of wins and losses compounds under
different stake sizes. Betting more than Kelly doesn't trade "more risk
for more expected growth" the way it might for a single isolated bet:
past the Kelly fraction, both risk of ruin AND long-run growth get worse
together, because a big enough loss erases gains faster than wins can
rebuild them. Kelly betting can (mathematically) never reach exactly
zero from a finite run of bets, since every stake is a fraction below 1
of whatever remains -- "Kelly can't go broke." All-in betting is the
opposite extreme: with any win probability below 100%, a single loss is
total, immediate ruin. This part demonstrates that gap with simulated
data, rather than only proving it algebraically as Part 5 did.
"""

import random
import statistics
from dataclasses import dataclass

from poker.kelly import fractional_kelly

RUIN_THRESHOLD = 1e-9  # bankroll this close to zero counts as "ruined"


def fixed_stake_strategy(fraction_of_initial_bankroll):
    """Classic "flat betting": always stake the same absolute amount -- a
    fixed fraction of the STARTING bankroll -- no matter how the bankroll
    has grown or shrunk since. The simplest baseline, and usually the
    worst performer, because the stake never adapts to what's actually at
    risk.
    """

    def strategy(initial_bankroll, current_bankroll, win_probability, odds):
        return fraction_of_initial_bankroll * initial_bankroll

    return strategy


def kelly_strategy(kelly_multiplier=1.0):
    """Stake a (possibly fractional) Kelly fraction of the CURRENT
    bankroll each hand. kelly_multiplier=1.0 is full Kelly, 0.5 is half
    Kelly. Because the stake shrinks along with the bankroll, this
    strategy approaches zero but can never hit it exactly from a single
    bad run.
    """

    def strategy(initial_bankroll, current_bankroll, win_probability, odds):
        return fractional_kelly(win_probability, odds, kelly_multiplier) * current_bankroll

    return strategy


def all_in_strategy():
    """Stake the entire current bankroll every hand -- included as the
    "what NOT to do" baseline. With any win_probability < 1, a single
    loss is total ruin, and over enough hands a loss becomes near-certain
    no matter how strong the edge is.
    """

    def strategy(initial_bankroll, current_bankroll, win_probability, odds):
        return current_bankroll

    return strategy


@dataclass(frozen=True)
class SessionResult:
    """bankroll_history always has length num_hands + 1 (starting
    bankroll, then one entry per hand) regardless of whether ruin happens
    partway through, so sessions can be plotted/compared directly."""

    bankroll_history: tuple
    is_ruined: bool

    @property
    def final_bankroll(self):
        return self.bankroll_history[-1]


def simulate_session(strategy, initial_bankroll, win_probability, odds, num_hands, rng):
    """Simulate one sequence of num_hands independent, identical bets
    (same win_probability/odds every hand) -- a simplified stand-in for
    "many similar spots" rather than re-running the full poker engine per
    hand. Part 7's AI opponents are what actually generates
    hand-by-hand equity from real play; this part studies staking
    strategy in isolation, holding the edge constant.
    """
    if not 0 <= win_probability <= 1:
        raise ValueError('win_probability must be between 0 and 1')
    if odds <= 0:
        raise ValueError('odds must be positive')
    if initial_bankroll <= 0:
        raise ValueError('initial_bankroll must be positive')
    if num_hands < 1:
        raise ValueError('num_hands must be at least 1')

    bankroll = initial_bankroll
    history = [bankroll]
    ruined = False

    for _ in range(num_hands):
        if bankroll <= RUIN_THRESHOLD:
            ruined = True
            history.append(0.0)
            continue

        raw_bet = strategy(initial_bankroll, bankroll, win_probability, odds)
        bet = min(max(raw_bet, 0.0), bankroll)  # can never stake more than you have

        if rng.random() < win_probability:
            bankroll += bet * odds
        else:
            bankroll -= bet

        if bankroll <= RUIN_THRESHOLD:
            bankroll = 0.0
            ruined = True

        history.append(bankroll)

    return SessionResult(bankroll_history=tuple(history), is_ruined=ruined)


@dataclass(frozen=True)
class BankrollSimulationResult:
    sessions: tuple
    risk_of_ruin: float
    mean_final_bankroll: float
    median_final_bankroll: float


def simulate_many_sessions(
    strategy,
    initial_bankroll,
    win_probability,
    odds,
    num_hands,
    num_sessions=1000,
    seed=None,
):
    """Run num_sessions independent sessions and summarise them -- the
    same Monte Carlo idea as Part 3's equity calculator, applied to
    bankroll trajectories instead of single hands: repeat a random
    process many times and let the aggregate statistics (here, risk of
    ruin and typical final bankroll) converge.
    """
    if num_sessions < 1:
        raise ValueError('num_sessions must be at least 1')

    rng = random.Random(seed)
    sessions = tuple(
        simulate_session(strategy, initial_bankroll, win_probability, odds, num_hands, rng)
        for _ in range(num_sessions)
    )

    final_bankrolls = [session.final_bankroll for session in sessions]

    return BankrollSimulationResult(
        sessions=sessions,
        risk_of_ruin=sum(session.is_ruined for session in sessions) / num_sessions,
        mean_final_bankroll=statistics.mean(final_bankrolls),
        median_final_bankroll=statistics.median(final_bankrolls),
    )
