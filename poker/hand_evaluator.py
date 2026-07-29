"""Rank 5-7 card poker hands and compare them to find a winner.

Key insight: every hand's strength can be reduced to a single sortable
tuple: (category, tiebreakers). Once every hand is turned into one of
these tuples, "who wins" is just a Python `max()` over tuples -- no
special-cased comparison logic between categories or within a category
is needed, because tuple comparison already does the right thing:
compare the category first, and only look at tiebreakers to break a tie
within the same category.
"""

from collections import Counter
from dataclasses import dataclass
from enum import IntEnum
from functools import total_ordering
from itertools import combinations

from poker.cards import Rank


class HandCategory(IntEnum):
    """Ordered worst to best. IntEnum so a HandCategory compares correctly
    against another just like a plain int -- FLUSH > STRAIGHT is True."""

    HIGH_CARD = 1
    PAIR = 2
    TWO_PAIR = 3
    THREE_OF_A_KIND = 4
    STRAIGHT = 5
    FLUSH = 6
    FULL_HOUSE = 7
    FOUR_OF_A_KIND = 8
    STRAIGHT_FLUSH = 9

    def __str__(self):
        return self.name.replace('_', ' ').title()


# The lowest possible straight: Ace plays low here ("the wheel"), so its
# high card for comparison purposes is the 5, not the Ace.
_WHEEL = (Rank.ACE, Rank.FIVE, Rank.FOUR, Rank.THREE, Rank.TWO)


@total_ordering
@dataclass(frozen=True)
class HandResult:
    """The outcome of evaluating one 5-card hand.

    tiebreakers holds only the ranks that matter for breaking a tie within
    this category, in comparison order -- e.g. for two pair that's
    (high_pair, low_pair, kicker), not all 5 cards.
    """

    category: HandCategory
    tiebreakers: tuple

    def _sort_key(self):
        return (self.category, self.tiebreakers)

    def __eq__(self, other):
        return self._sort_key() == other._sort_key()

    def __lt__(self, other):
        return self._sort_key() < other._sort_key()

    def __str__(self):
        ranks = ', '.join(str(rank) for rank in self.tiebreakers)
        return f'{self.category} ({ranks})'


def _straight_high(ranks):
    """ranks: any iterable of 5 Rank values (possibly with duplicates).
    Returns the high Rank if they form a straight (wheel included),
    otherwise None."""
    unique_sorted = sorted(set(ranks), reverse=True)

    if len(unique_sorted) != 5:
        return None  # a straight needs 5 distinct ranks
    if unique_sorted[0] - unique_sorted[-1] == 4:
        return unique_sorted[0]
    if tuple(unique_sorted) == _WHEEL:
        return Rank.FIVE

    return None


def evaluate_5(cards):
    """Evaluate exactly 5 cards into a HandResult."""
    cards = tuple(cards)
    if len(cards) != 5:
        raise ValueError(f'evaluate_5 requires exactly 5 cards, got {len(cards)}')

    ranks = [card.rank for card in cards]
    is_flush = len({card.suit for card in cards}) == 1
    straight_high = _straight_high(ranks)

    # Group ranks by how often they appear, then order the groups by
    # (count, rank) descending. That single ordering encodes every
    # pair/trips/quads/full-house tiebreak rule at once: e.g. two pair
    # Kings-and-Twos beats Queens-and-Aces because the higher *pair* is
    # compared before anything else.
    counts = Counter(ranks)
    groups = sorted(counts.items(), key=lambda rank_count: (rank_count[1], rank_count[0]), reverse=True)
    count_pattern = tuple(count for _rank, count in groups)
    group_ranks = tuple(rank for rank, _count in groups)

    if straight_high and is_flush:
        return HandResult(HandCategory.STRAIGHT_FLUSH, (straight_high,))
    if count_pattern == (4, 1):
        return HandResult(HandCategory.FOUR_OF_A_KIND, group_ranks)
    if count_pattern == (3, 2):
        return HandResult(HandCategory.FULL_HOUSE, group_ranks)
    if is_flush:
        return HandResult(HandCategory.FLUSH, tuple(sorted(ranks, reverse=True)))
    if straight_high:
        return HandResult(HandCategory.STRAIGHT, (straight_high,))
    if count_pattern == (3, 1, 1):
        return HandResult(HandCategory.THREE_OF_A_KIND, group_ranks)
    if count_pattern == (2, 2, 1):
        return HandResult(HandCategory.TWO_PAIR, group_ranks)
    if count_pattern == (2, 1, 1, 1):
        return HandResult(HandCategory.PAIR, group_ranks)

    return HandResult(HandCategory.HIGH_CARD, tuple(sorted(ranks, reverse=True)))


def best_hand(cards):
    """Find the best possible 5-card hand out of 5-7 cards -- e.g. 2 hole
    cards + up to 5 community cards in Texas Hold'em.

    There are at most C(7, 5) = 21 five-card combinations to check, so
    brute-forcing every combination and keeping the best is simple and
    fast enough -- no need for a cleverer algorithm here.

    Returns (HandResult, cards) for the best 5-card combination found.
    """
    cards = tuple(cards)
    if not 5 <= len(cards) <= 7:
        raise ValueError(f'best_hand requires 5-7 cards, got {len(cards)}')

    best_result = None
    best_combo = None
    for combo in combinations(cards, 5):
        result = evaluate_5(combo)
        if best_result is None or result > best_result:
            best_result, best_combo = result, combo

    return best_result, best_combo


def compare_hands(hands):
    """hands: a list of card collections (5-7 cards each), one per player.

    Returns the list of winning player indices -- a list with more than
    one index means those players tie and split the pot.
    """
    results = [best_hand(hand)[0] for hand in hands]
    best = max(results)
    return [index for index, result in enumerate(results) if result == best]
