import pytest

from poker.cards import Card, Rank
from poker.hand_evaluator import (
    HandCategory,
    best_hand,
    compare_hands,
    evaluate_5,
)


def cards(text):
    """Helper: cards('Ah Kh Qh Jh Th') -> list of Card."""
    return [Card.from_str(token) for token in text.split()]


@pytest.mark.parametrize(
    'hand_text, expected_category',
    [
        ('2h 5d 9c Js Ah', HandCategory.HIGH_CARD),
        ('2h 2d 9c Js Ah', HandCategory.PAIR),
        ('2h 2d 9c 9s Ah', HandCategory.TWO_PAIR),
        ('2h 2d 2c 9s Ah', HandCategory.THREE_OF_A_KIND),
        ('5h 6d 7c 8s 9h', HandCategory.STRAIGHT),
        ('Ah 2d 3c 4s 5h', HandCategory.STRAIGHT),  # the wheel
        ('2h 5h 9h Jh Ah', HandCategory.FLUSH),
        ('2h 2d 2c 9s 9h', HandCategory.FULL_HOUSE),
        ('2h 2d 2c 2s 9h', HandCategory.FOUR_OF_A_KIND),
        ('5h 6h 7h 8h 9h', HandCategory.STRAIGHT_FLUSH),
        ('Th Jh Qh Kh Ah', HandCategory.STRAIGHT_FLUSH),  # royal flush
    ],
)
def test_evaluate_5_categorises_correctly(hand_text, expected_category):
    result = evaluate_5(cards(hand_text))
    assert result.category == expected_category


def test_wheel_straight_is_five_high_not_ace_high():
    wheel = evaluate_5(cards('Ah 2d 3c 4s 5h'))
    assert wheel.tiebreakers == (Rank.FIVE,)


def test_broadway_straight_beats_wheel_straight():
    wheel = evaluate_5(cards('Ah 2d 3c 4s 5h'))
    broadway = evaluate_5(cards('Th Jd Qc Ks Ah'))
    assert broadway > wheel
    assert broadway.category == wheel.category == HandCategory.STRAIGHT


def test_evaluate_5_rejects_wrong_card_count():
    with pytest.raises(ValueError):
        evaluate_5(cards('Ah Kh Qh Jh'))


def test_two_pair_compares_high_pair_first_then_low_pair_then_kicker():
    # Kings-and-twos should beat queens-and-jacks: the higher PAIR of each
    # hand is compared first (Kings > Queens), so it doesn't matter that
    # queens-and-jacks' low pair (Jacks) beats kings-and-twos' low pair (2s).
    kings_and_twos = evaluate_5(cards('Kh Kd 2c 2s 9h'))
    queens_and_jacks = evaluate_5(cards('Qh Qd Jc Js 9h'))
    assert kings_and_twos > queens_and_jacks


def test_full_house_compares_trips_before_pair():
    twos_full_of_aces = evaluate_5(cards('2h 2d 2c Ac Ah'))
    aces_full_of_twos = evaluate_5(cards('Ah Ad Ac 2c 2h'))
    assert aces_full_of_twos > twos_full_of_aces


def test_flush_compares_all_five_cards_in_order():
    ace_high_flush = evaluate_5(cards('Ah Kh 5h 4h 2h'))
    king_high_flush = evaluate_5(cards('Kd Qd Jd 9d 2d'))
    assert ace_high_flush > king_high_flush


def test_best_hand_picks_best_five_of_seven():
    # Hole cards give a pair of aces, but the board makes a flush possible
    # using only 3 of the hole/board cards plus 2 more -- best_hand must
    # find the flush, not just settle for the pair.
    seven_cards = cards('Ah Ad 2h 5h 9h Jh Qd')
    result, combo = best_hand(seven_cards)
    assert result.category == HandCategory.FLUSH
    assert len(combo) == 5
    assert all(card.suit.value == 'h' for card in combo)


def test_best_hand_rejects_wrong_card_count():
    with pytest.raises(ValueError):
        best_hand(cards('Ah Kh Qh Jh'))  # only 4 cards

    with pytest.raises(ValueError):
        best_hand(cards('Ah Kh Qh Jh Th 9h 8h 7h'))  # 8 cards


def test_compare_hands_finds_single_winner():
    # Player 0 has a pair of aces, player 1 has a pair of kings, same board.
    board = cards('2c 5d 9s Jh 3h')
    player_0 = cards('Ah Ad') + board
    player_1 = cards('Kh Kd') + board

    winners = compare_hands([player_0, player_1])
    assert winners == [0]


def test_compare_hands_finds_split_pot():
    # Both players play the same board straight -- neither hole card pair
    # improves on it, so it's a tie and both indices should be returned.
    board = cards('5h 6d 7c 8s 9h')
    player_0 = cards('2c 3d') + board
    player_1 = cards('2h 3s') + board

    winners = compare_hands([player_0, player_1])
    assert winners == [0, 1]
