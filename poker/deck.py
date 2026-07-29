"""A deck of 52 cards that can be shuffled and dealt from.

Key insight: dealing is modelled as *removing* cards from the deck's
internal list. Once a card has been dealt it is physically gone from
`self._cards` -- there is nothing left to check to prevent dealing it
again, because it's no longer there to deal. This is simpler and more
robust than building a deck, dealing cards, and separately tracking
"already dealt" cards to check against.
"""

import random

from poker.cards import Card, Rank, Suit


class Deck:
    def __init__(self, seed=None):
        """seed: optional int for reproducible shuffles -- useful for tests
        and, later, for reproducible Monte Carlo simulations."""
        self._rng = random.Random(seed)
        self._cards = []
        self.reset()

    def reset(self):
        """Rebuild the full, ordered 52-card deck (not shuffled)."""
        self._cards = [Card(rank, suit) for suit in Suit for rank in Rank]

    def shuffle(self):
        """Shuffle in place using this deck's own RNG instance (rather than
        the global `random` module) so a seeded Deck is fully reproducible
        even if other code elsewhere also calls `random.shuffle`."""
        self._rng.shuffle(self._cards)
        return self

    def deal(self, n=1):
        """Deal n cards off the top of the deck, removing them from it.

        Dealing from the end of the list (`pop()`) is O(1) per card, versus
        O(n) if dealing from the front -- an implementation detail, not a
        rules one, since the deck is already shuffled.
        """
        if n > len(self._cards):
            raise ValueError(
                f'Cannot deal {n} cards, only {len(self._cards)} remain in the deck'
            )

        dealt = [self._cards.pop() for _ in range(n)]
        return dealt

    def deal_hole_cards(self, num_players):
        """Deal 2 hole cards to each of num_players, one card at a time in
        rotation (player 1, player 2, ..., player 1, player 2, ...) --
        matching how a real dealer deals, rather than dealing both of one
        player's cards before moving to the next. The end result (which
        cards each player holds) is identical either way, but this mirrors
        the real deal order in case that ever matters (e.g. showing a
        dealing animation later).

        Returns a list of length num_players, each a list of 2 Cards.
        """
        if num_players < 1:
            raise ValueError('num_players must be at least 1')

        hands = [[] for _ in range(num_players)]
        for _ in range(2):
            for player_index in range(num_players):
                hands[player_index].extend(self.deal(1))

        return hands

    def deal_community(self, n, burn=False):
        """Deal n community (board) cards, e.g. 3 for the flop, 1 for the
        turn, 1 for the river.

        burn: if True, discards one card from the deck immediately before
        dealing (as a real dealer does, to guard against a marked top
        card). Defaults to False to keep things simple for the Monte Carlo
        equity calculator in Part 3, where there are no physical cards to
        protect against -- burning there would only shrink the deck for no
        benefit.
        """
        if burn:
            self.deal(1)

        return self.deal(n)

    def __len__(self):
        return len(self._cards)

    def __repr__(self):
        return f'Deck({len(self._cards)} cards remaining)'
