"""The Kelly Criterion: what fraction of your bankroll to stake on a
repeatable bet with a known edge, to maximise long-run growth.

This is the direct finance parallel the whole project is built around.
Kelly was originally derived for exactly this kind of gambling problem,
but the identical formula is used to size positions in an investment
portfolio: if you have an edge (an expected return better than break-even)
and know the "odds" (the payoff structure of the bet/trade), Kelly gives
the fraction of capital to allocate that maximises the long-run compound
growth rate of your bankroll/portfolio. Ed Thorp used this exact
reasoning to go from card counting in blackjack to running a hedge fund.

Key insight: betting more than Kelly isn't just "riskier for more
reward" -- above the Kelly fraction, *both* your risk of ruin and your
long-run growth rate get worse at the same time, because the wins can no
longer compound fast enough to outrun the increasingly severe losses.
Kelly is the single fraction that maximises long-run growth; the
"variance vs. growth" trade-off practitioners actually make is between
full Kelly and *fractional* Kelly (betting less than Kelly), not between
Kelly and betting more.
"""

import math


def kelly_fraction(win_probability, odds):
    """The raw, unclipped optimal fraction of bankroll to bet, f*.

    win_probability (p): probability of winning the bet.
    odds (b): net odds received -- if you win, you gain b units per unit
        staked (b=1 is even money, b=2 is "2 to 1", etc).

    Derivation: f* maximises the expected log-growth per bet (see
    expected_log_growth below); solving d/df = 0 gives:
        f* = (p*b - q) / b       where q = 1 - p

    Can be negative (there is no edge -- don't take this bet at all) or,
    in extreme cases, greater than 1 (would require leverage). Callers
    that need a directly bettable fraction should use fractional_kelly,
    which clips negative results to 0.
    """
    if not 0 <= win_probability <= 1:
        raise ValueError('win_probability must be between 0 and 1')
    if odds <= 0:
        raise ValueError('odds must be positive')

    p = win_probability
    q = 1 - p
    return (p * odds - q) / odds


def fractional_kelly(win_probability, odds, fraction=1.0):
    """The practically bettable Kelly stake: the raw Kelly fraction,
    scaled by `fraction` and clipped to a minimum of 0.

    fraction=1.0 is full Kelly. fraction=0.5 ("half Kelly") is a common
    real-world choice -- it gives up some long-run growth in exchange for
    meaningfully lower variance/drawdowns, since growth near the Kelly
    peak is flat (see expected_log_growth) but variance keeps rising
    linearly with bet size. Part 6 compares these strategies directly.

    Clipped to 0 rather than allowed to go negative: in this project
    there's no way to "bet the other way" on a poker hand you're already
    holding, so a negative edge simply means bet nothing.
    """
    raw = kelly_fraction(win_probability, odds)
    return max(0.0, raw * fraction)


def kelly_fraction_from_pot_odds(equity, pot_size, bet_to_call, kelly_multiplier=1.0):
    """Bridge from a poker call decision (Parts 3 & 4) into Kelly terms.

    Calling risks bet_to_call to potentially win pot_size, so for every 1
    unit risked you stand to win pot_size / bet_to_call units -- exactly
    the "b to 1" odds the Kelly formula expects. equity (from Part 3) is
    win_probability (p).
    """
    if pot_size < 0:
        raise ValueError('pot_size cannot be negative')
    if bet_to_call <= 0:
        raise ValueError('bet_to_call must be positive')

    odds = pot_size / bet_to_call
    return fractional_kelly(equity, odds, kelly_multiplier)


def expected_log_growth(win_probability, odds, fraction):
    """The expected per-bet log-growth rate of your bankroll if you
    repeatedly bet `fraction` of it on this win_probability=p, odds=b bet.

    Winning multiplies your bankroll by (1 + fraction*odds); losing
    multiplies it by (1 - fraction). Log-growth (rather than plain
    expected value) is the right quantity to maximise for a bet you
    repeat many times, because bankroll compounds multiplicatively, not
    additively -- this is exactly why Kelly, not naive EV-maximising
    (which would push you to bet your entire bankroll every time), is the
    correct sizing rule for a sequence of bets.
    """
    if not 0 <= win_probability <= 1:
        raise ValueError('win_probability must be between 0 and 1')
    if odds <= 0:
        raise ValueError('odds must be positive')
    if not 0 <= fraction < 1:
        raise ValueError('fraction must be in [0, 1) -- betting 100% of bankroll risks total ruin on a single loss')

    p = win_probability
    q = 1 - p
    return p * math.log(1 + fraction * odds) + q * math.log(1 - fraction)
