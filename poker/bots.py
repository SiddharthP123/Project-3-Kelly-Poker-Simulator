"""Rule-based AI opponent personas that turn Part 3's equity, Part 4's
EV/pot-odds logic, and Part 5's Kelly sizing into an actual fold/call/raise
decision.

Key insight: every persona differs only in WHICH numbers it uses to turn
the same equity estimate into a decision. The fold/call/raise vocabulary
and the "never raise more than your bankroll" rule are shared by all of
them (in the Bot base class). That shared shape is exactly why different
personas can sit at the same table interchangeably from Part 8 onwards --
the game engine only ever calls `.decide(...)`, never caring which
persona it's talking to.
"""

import random
from dataclasses import dataclass

from poker.equity import calculate_equity
from poker.kelly import kelly_fraction_from_pot_odds


@dataclass(frozen=True)
class Action:
    action: str  # 'fold', 'call', or 'raise'
    raise_amount: float = 0.0  # only meaningful when action == 'raise'


class Bot:
    """Base class for all opponent personas. Subclasses implement
    _decide; this class handles the one rule every persona shares --
    never raise more than the bankroll actually holds."""

    name = 'Bot'

    def decide(self, equity, pot_size, bet_to_call, bankroll=None):
        action = self._decide(equity, pot_size, bet_to_call, bankroll)
        if action.action == 'raise' and bankroll is not None:
            return Action('raise', min(action.raise_amount, bankroll))
        return action

    def _decide(self, equity, pot_size, bet_to_call, bankroll):
        raise NotImplementedError

    def decide_from_hand(
        self, hole_cards, board, pot_size, bet_to_call, num_opponents=1,
        bankroll=None, num_simulations=2000, seed=None,
    ):
        """Convenience wrapper for the full path a real game loop (Part 8)
        will use: run Part 3's Monte Carlo equity calculator on the actual
        cards, then decide from that equity."""
        result = calculate_equity(
            hole_cards, num_opponents=num_opponents, board=board,
            num_simulations=num_simulations, seed=seed,
        )
        return self.decide(result.equity, pot_size, bet_to_call, bankroll)


class ThresholdBot(Bot):
    """Shared shape for simple threshold-based personas: fold below one
    equity bar, raise above another, call everything in between. Tight
    vs. loose and passive vs. aggressive are just different threshold
    values plugged into the same logic."""

    def __init__(self, fold_below, raise_above, raise_sizing):
        self.fold_below = fold_below
        self.raise_above = raise_above
        self.raise_sizing = raise_sizing  # raise size as a fraction of the pot

    def _decide(self, equity, pot_size, bet_to_call, bankroll):
        if equity < self.fold_below:
            return Action('fold')
        if equity >= self.raise_above:
            return Action('raise', self.raise_sizing * pot_size)
        return Action('call')


class VeryTightPassiveBot(ThresholdBot):
    """The "Rock": plays an even narrower range than a TAG, and rarely
    bets big even with a strong hand -- tight AND passive, the most
    conservative persona on the table."""

    name = 'Very-Tight-Passive'

    def __init__(self, fold_below=0.65, raise_above=0.90, raise_sizing=0.35):
        super().__init__(fold_below, raise_above, raise_sizing)


class TightAggressiveBot(ThresholdBot):
    """Plays a narrow range of strong hands, but bets big when it does --
    the classic "TAG" persona."""

    name = 'Tight-Aggressive'

    def __init__(self, fold_below=0.55, raise_above=0.65, raise_sizing=0.75):
        super().__init__(fold_below, raise_above, raise_sizing)


class VeryTightAggressiveBot(ThresholdBot):
    """The "Nit-Shark": plays even fewer hands than a TAG, but bets even
    bigger than a TAG when it does -- a step further along the same
    tight-aggressive axis, not a different style."""

    name = 'Very-Tight-Aggressive'

    def __init__(self, fold_below=0.70, raise_above=0.80, raise_sizing=0.90):
        super().__init__(fold_below, raise_above, raise_sizing)


class BalancedBot(ThresholdBot):
    """Sits squarely between tight/loose and passive/aggressive -- a
    rough "GTO-ish" reference point the more extreme personas can be
    compared against."""

    name = 'Balanced'

    def __init__(self, fold_below=0.45, raise_above=0.60, raise_sizing=0.65):
        super().__init__(fold_below, raise_above, raise_sizing)


class LoosePassiveBot(ThresholdBot):
    """Plays almost any hand (a "calling station") and rarely raises even
    with a strong one."""

    name = 'Loose-Passive'

    def __init__(self, fold_below=0.15, raise_above=0.85, raise_sizing=0.4):
        super().__init__(fold_below, raise_above, raise_sizing)


class VeryLoosePassiveBot(ThresholdBot):
    """The "Weak-Loose": calls with almost anything and almost never
    raises even with the nuts -- the extreme end of the loose-passive
    axis, one step further than LoosePassiveBot."""

    name = 'Very-Loose-Passive'

    def __init__(self, fold_below=0.05, raise_above=0.95, raise_sizing=0.30):
        super().__init__(fold_below, raise_above, raise_sizing)


class LooseAggressiveBot(ThresholdBot):
    """The "LAG": plays a wide range like a loose-passive bot, but bets
    aggressively rather than just calling along -- loose AND aggressive,
    a genuinely different combination from either axis alone."""

    name = 'Loose-Aggressive'

    def __init__(self, fold_below=0.25, raise_above=0.45, raise_sizing=0.85):
        super().__init__(fold_below, raise_above, raise_sizing)


class VeryLooseAggressiveBot(ThresholdBot):
    """The "Maniac": plays almost any two cards and raises big with a
    huge range -- the most aggressive, least selective persona on the
    table, betting more than the pot itself when it raises."""

    name = 'Very-Loose-Aggressive'

    def __init__(self, fold_below=0.10, raise_above=0.30, raise_sizing=1.10):
        super().__init__(fold_below, raise_above, raise_sizing)


class RandomBot(Bot):
    """Ignores equity completely -- a control/baseline opponent, so the
    smarter personas' decisions can be judged against pure randomness
    rather than just against each other."""

    name = 'Random'

    def __init__(self, seed=None):
        self._rng = random.Random(seed)

    def _decide(self, equity, pot_size, bet_to_call, bankroll):
        choice = self._rng.choice(['fold', 'call', 'raise'])
        if choice == 'raise':
            return Action('raise', 0.5 * pot_size)
        return Action(choice)


class KellyOptimalBot(Bot):
    """Sizes every decision directly from Part 5's Kelly Criterion rather
    than fixed heuristics -- the "textbook" bot the other personas are
    implicitly being compared against.

    It doesn't need to separately re-run Part 4's pot-odds check: Kelly's
    numerator (p*b - q) is positive exactly when calling is +EV under pot
    odds, since Part 4's breakeven equity (bet / (pot + bet)) and Kelly's
    "no edge" point (1 / (b + 1), where b = pot/bet) are the same number
    algebraically. So "Kelly recommends staking nothing" and "folding is
    correct" are one and the same condition here, not two separate checks.

    Requires bankroll to be known, since Kelly sizing is a fraction of
    bankroll, not of the pot.
    """

    name = 'Kelly-Optimal'

    def __init__(self, kelly_multiplier=1.0):
        self.kelly_multiplier = kelly_multiplier

    def _decide(self, equity, pot_size, bet_to_call, bankroll):
        if bankroll is None:
            raise ValueError('KellyOptimalBot requires a known bankroll')

        kelly_stake = kelly_fraction_from_pot_odds(
            equity, pot_size, bet_to_call, self.kelly_multiplier
        ) * bankroll

        if kelly_stake <= 0:
            return Action('fold')
        if kelly_stake <= bet_to_call:
            return Action('call')
        return Action('raise', kelly_stake)


# Persona key -> class, so callers (the Part 12 hand orchestrator, the
# backend's game engine) can assign/store a persona by name rather than a
# class reference. Kept here rather than in the orchestrator since
# persona registration belongs next to the persona classes themselves.
PERSONA_REGISTRY = {
    'very-tight-passive': VeryTightPassiveBot,
    'tight-aggressive': TightAggressiveBot,
    'very-tight-aggressive': VeryTightAggressiveBot,
    'balanced': BalancedBot,
    'loose-passive': LoosePassiveBot,
    'very-loose-passive': VeryLoosePassiveBot,
    'loose-aggressive': LooseAggressiveBot,
    'very-loose-aggressive': VeryLooseAggressiveBot,
    'random': RandomBot,
    'kelly-optimal': KellyOptimalBot,
}


def assign_opponent_personas(num_opponents, rng):
    """Randomly assigns num_opponents distinct personas out of all 10
    registered ones (every persona, including Random and Kelly-Optimal,
    is eligible) -- one persona per opponent seat, no repeats within a
    single table.

    rng: a random.Random instance, so callers control reproducibility
    (tests pass a seeded one; a real game passes an unseeded one).
    """
    if not 1 <= num_opponents <= len(PERSONA_REGISTRY):
        raise ValueError(f'num_opponents must be between 1 and {len(PERSONA_REGISTRY)}')

    return rng.sample(list(PERSONA_REGISTRY.keys()), k=num_opponents)
