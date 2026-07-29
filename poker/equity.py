"""Estimate win probability ("equity") via Monte Carlo simulation.

Key insight: we don't know the opponents' hole cards or the rest of the
board, but we know the pool of cards they could possibly come from (the
deck minus whatever is already known). So instead of solving the
probability analytically, we just repeatedly guess a plausible reality --
deal the unknown cards at random, see who would win -- thousands of times,
and let the law of large numbers converge the win rate to the true
probability. This is the same Monte Carlo idea as Project 1, applied to
cards instead of asset price paths.
"""

import random
from dataclasses import dataclass

from poker.cards import Card, Rank, Suit
from poker.hand_evaluator import compare_hands


@dataclass(frozen=True)
class EquityResult:
    """win/tie/lose are shares of simulations. equity is the expected pot
    share -- 1 per outright win, 1/n per n-way tie, 0 per loss -- which is
    the number that later parts (EV, Kelly) actually need, since a tie only
    wins back a fraction of the pot."""

    win: float
    tie: float
    lose: float
    equity: float

    def __str__(self):
        return (
            f'win={self.win:.1%} tie={self.tie:.1%} lose={self.lose:.1%} '
            f'equity={self.equity:.1%}'
        )


def _full_deck():
    return [Card(rank, suit) for suit in Suit for rank in Rank]


def calculate_equity(hole_cards, num_opponents=1, board=(), num_simulations=10000, seed=None):
    """Estimate hero's equity against num_opponents random opponents.

    hole_cards: hero's 2 known cards.
    board: 0 (pre-flop), 3 (flop), 4 (turn), or 5 (river) known community
        cards. Any remaining board cards are dealt randomly each simulation.
    num_opponents: opponents are assumed to hold uniformly random hole
        cards (no known range) -- the simplest, most common equity
        calculation. Modelling opponent ranges is a possible future
        extension, not needed for this part.
    seed: optional int for reproducible results (useful for tests).
    """
    if num_opponents < 1:
        raise ValueError('num_opponents must be at least 1')
    if len(hole_cards) != 2:
        raise ValueError('hole_cards must contain exactly 2 cards')
    if len(board) not in (0, 3, 4, 5):
        raise ValueError('board must have 0, 3, 4, or 5 cards')

    known_cards = set(hole_cards) | set(board)
    if len(known_cards) != len(hole_cards) + len(board):
        raise ValueError('hole_cards and board must not share duplicate cards')

    remaining = [card for card in _full_deck() if card not in known_cards]
    board_cards_needed = 5 - len(board)
    cards_per_simulation = board_cards_needed + 2 * num_opponents

    if cards_per_simulation > len(remaining):
        raise ValueError('Not enough unknown cards left in the deck for this many opponents')

    rng = random.Random(seed)

    wins = 0
    ties = 0
    losses = 0
    equity_total = 0.0

    for _ in range(num_simulations):
        # Sampling straight from the small "remaining" pool (rather than
        # building and shuffling a full Deck each time) is both simpler and
        # faster -- we only ever need `cards_per_simulation` cards per run.
        drawn = rng.sample(remaining, cards_per_simulation)
        run_out_board = list(board) + drawn[:board_cards_needed]
        opponent_hole_cards = [
            drawn[board_cards_needed + 2 * i : board_cards_needed + 2 * i + 2]
            for i in range(num_opponents)
        ]

        hero_hand = list(hole_cards) + run_out_board
        all_hands = [hero_hand] + [opponent + run_out_board for opponent in opponent_hole_cards]

        winners = compare_hands(all_hands)  # hero is always index 0

        if 0 in winners:
            equity_total += 1 / len(winners)
            if len(winners) == 1:
                wins += 1
            else:
                ties += 1
        else:
            losses += 1

    return EquityResult(
        win=wins / num_simulations,
        tie=ties / num_simulations,
        lose=losses / num_simulations,
        equity=equity_total / num_simulations,
    )
