import pytest

from poker.cards import Card, Rank, Suit


def test_card_str_notation():
    assert str(Card(Rank.ACE, Suit.HEARTS)) == 'Ah'
    assert str(Card(Rank.TEN, Suit.CLUBS)) == 'Tc'
    assert str(Card(Rank.TWO, Suit.SPADES)) == '2s'


def test_card_from_str_round_trips():
    for text in ['Ah', 'Tc', '2s', 'Kd', '9h']:
        assert str(Card.from_str(text)) == text


def test_card_from_str_rejects_bad_input():
    with pytest.raises(ValueError):
        Card.from_str('Zh')  # invalid rank

    with pytest.raises(ValueError):
        Card.from_str('Ax')  # invalid suit

    with pytest.raises(ValueError):
        Card.from_str('Ahh')  # wrong length


def test_card_equality_and_hashing():
    assert Card(Rank.ACE, Suit.HEARTS) == Card(Rank.ACE, Suit.HEARTS)
    assert Card(Rank.ACE, Suit.HEARTS) != Card(Rank.ACE, Suit.SPADES)

    # Frozen + hashable means cards can go in a set without error.
    cards = {Card(Rank.ACE, Suit.HEARTS), Card(Rank.ACE, Suit.HEARTS)}
    assert len(cards) == 1


def test_rank_ordering():
    assert Rank.KING > Rank.TEN
    assert Rank.ACE > Rank.KING
    assert Rank.TWO < Rank.THREE
