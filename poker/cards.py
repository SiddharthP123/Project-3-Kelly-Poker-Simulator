"""Core card representations for the poker simulator.

A standard deck is 52 unique combinations of rank and suit. Modelling that
as two small enums plus an immutable Card that pairs one of each is enough
to guarantee every card in the deck is distinct -- there's no fifth suit or
fifteenth rank to accidentally create a duplicate from.
"""

from dataclasses import dataclass
from enum import Enum, IntEnum


class Suit(Enum):
    """The four suits. Standard Texas Hold'em never ranks suits against each
    other -- they only matter for matching (flushes), so a plain Enum
    (no ordering) is the right tool here."""

    CLUBS = 'c'
    DIAMONDS = 'd'
    HEARTS = 'h'
    SPADES = 's'

    def __str__(self):
        return self.value


class Rank(IntEnum):
    """Card ranks, 2 through Ace.

    IntEnum (rather than plain Enum) so ranks compare and sort numerically
    out of the box -- e.g. Rank.KING > Rank.TEN is True. That ordering is
    exactly what later parts (straights, high-card comparisons) need, so
    it's worth setting up correctly from the start.
    """

    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14

    def __str__(self):
        return _RANK_TO_CHAR[self]


# Standard poker shorthand. 'T' for ten (not '10') keeps every rank a single
# character, so a card is always exactly two characters, e.g. 'Ah', 'Tc', '9s'.
_RANK_TO_CHAR = {
    Rank.TWO: '2',
    Rank.THREE: '3',
    Rank.FOUR: '4',
    Rank.FIVE: '5',
    Rank.SIX: '6',
    Rank.SEVEN: '7',
    Rank.EIGHT: '8',
    Rank.NINE: '9',
    Rank.TEN: 'T',
    Rank.JACK: 'J',
    Rank.QUEEN: 'Q',
    Rank.KING: 'K',
    Rank.ACE: 'A',
}
_CHAR_TO_RANK = {char: rank for rank, char in _RANK_TO_CHAR.items()}


@dataclass(frozen=True)
class Card:
    """A single playing card. Frozen (immutable) and hashable, so cards can
    be safely used in sets/dicts (useful in Part 2 onwards for hand lookups)
    and can't be mutated after being dealt.
    """

    rank: Rank
    suit: Suit

    def __str__(self):
        return f'{self.rank}{self.suit}'

    def __repr__(self):
        return f"Card('{self}')"

    @classmethod
    def from_str(cls, text):
        """Parse standard 2-character notation, e.g. Card.from_str('Ah')."""
        if len(text) != 2:
            raise ValueError(f'Card notation must be 2 characters, got {text!r}')

        rank_char, suit_char = text[0].upper(), text[1].lower()

        if rank_char not in _CHAR_TO_RANK:
            raise ValueError(f'Unknown rank character: {rank_char!r}')
        if suit_char not in {suit.value for suit in Suit}:
            raise ValueError(f'Unknown suit character: {suit_char!r}')

        return cls(rank=_CHAR_TO_RANK[rank_char], suit=Suit(suit_char))
