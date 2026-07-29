import pytest

from poker.deck import Deck


def test_fresh_deck_has_52_unique_cards():
    deck = Deck()
    assert len(deck) == 52

    all_dealt = deck.deal(52)
    assert len(all_dealt) == 52
    assert len(set(all_dealt)) == 52  # no duplicates


def test_shuffle_is_reproducible_with_seed():
    deck_one = Deck(seed=42).shuffle()
    deck_two = Deck(seed=42).shuffle()
    assert deck_one.deal(52) == deck_two.deal(52)


def test_shuffle_actually_changes_order():
    ordered = Deck()
    shuffled = Deck(seed=1).shuffle()
    assert ordered.deal(52) != shuffled.deal(52)


def test_deal_reduces_remaining_count():
    deck = Deck(seed=0).shuffle()
    deck.deal(5)
    assert len(deck) == 47


def test_deal_raises_when_deck_exhausted():
    deck = Deck()
    deck.deal(52)
    with pytest.raises(ValueError):
        deck.deal(1)


def test_deal_hole_cards_gives_two_cards_each_no_duplicates():
    deck = Deck(seed=7).shuffle()
    hands = deck.deal_hole_cards(num_players=4)

    assert len(hands) == 4
    assert all(len(hand) == 2 for hand in hands)

    all_hole_cards = [card for hand in hands for card in hand]
    assert len(set(all_hole_cards)) == 8  # all 8 dealt cards are unique
    assert len(deck) == 52 - 8


def test_hole_cards_and_community_never_overlap():
    deck = Deck(seed=99).shuffle()
    hands = deck.deal_hole_cards(num_players=6)  # 12 cards
    flop = deck.deal_community(3)
    turn = deck.deal_community(1)
    river = deck.deal_community(1)

    all_cards = [card for hand in hands for card in hand] + flop + turn + river
    assert len(all_cards) == 17  # 6 players x 2 hole cards + 3 + 1 + 1 board cards
    assert len(set(all_cards)) == 17  # no card appears twice anywhere
    assert len(deck) == 52 - 17


def test_deal_community_with_burn_removes_extra_card():
    deck = Deck(seed=3).shuffle()
    deck.deal_community(3, burn=True)
    assert len(deck) == 52 - 4  # 1 burned + 3 dealt
