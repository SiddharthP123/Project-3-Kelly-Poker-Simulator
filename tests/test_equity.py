import pytest

from poker.cards import Card
from poker.equity import calculate_equity


def cards(text):
    return [Card.from_str(token) for token in text.split()]


def test_probabilities_sum_to_one():
    result = calculate_equity(cards('Ah Kd'), num_opponents=1, num_simulations=2000, seed=1)
    assert result.win + result.tie + result.lose == pytest.approx(1.0)


def test_reproducible_with_seed():
    first = calculate_equity(cards('Ah Kd'), num_opponents=2, num_simulations=1000, seed=42)
    second = calculate_equity(cards('Ah Kd'), num_opponents=2, num_simulations=1000, seed=42)
    assert first == second


def test_pocket_aces_heads_up_is_strong_favourite():
    # Well-known benchmark: AA vs. a random hand heads-up wins ~85%. With
    # 5000 simulations the standard error is small (~0.5%), so a wide
    # 0.78-0.92 band comfortably confirms the simulation without being
    # flaky, while still catching a badly broken evaluator/equity loop.
    result = calculate_equity(cards('Ah Ac'), num_opponents=1, num_simulations=5000, seed=7)
    assert 0.78 < result.win < 0.92
    assert 0.78 < result.equity < 0.92


def test_equity_decreases_as_opponents_increase():
    heads_up = calculate_equity(cards('Ah Ac'), num_opponents=1, num_simulations=3000, seed=3)
    four_way = calculate_equity(cards('Ah Ac'), num_opponents=3, num_simulations=3000, seed=3)
    assert heads_up.equity > four_way.equity


def test_royal_flush_on_board_is_a_guaranteed_tie_for_everyone():
    # If the board itself is already a royal flush, every player's best
    # 7-card hand is at least that royal flush (the board 5 cards are one
    # of the valid 5-card combinations) -- and nothing beats a royal
    # flush. So no matter what hole cards anyone holds, this is always a
    # full tie. That makes the outcome deterministic despite the random
    # sampling, which is what makes it a solid correctness test.
    hole_cards = cards('2c 3d')
    board = cards('Th Jh Qh Kh Ah')

    result = calculate_equity(hole_cards, num_opponents=3, board=board, num_simulations=50, seed=5)

    assert result.win == 0.0
    assert result.lose == 0.0
    assert result.tie == 1.0
    assert result.equity == pytest.approx(1 / 4)  # hero ties with all 3 opponents, every time


def test_rejects_wrong_hole_card_count():
    with pytest.raises(ValueError):
        calculate_equity(cards('Ah'), num_opponents=1, num_simulations=10)


def test_rejects_invalid_board_length():
    with pytest.raises(ValueError):
        calculate_equity(cards('Ah Kd'), board=cards('2c 3d'), num_simulations=10)  # 2 is invalid


def test_rejects_duplicate_cards_between_hole_and_board():
    with pytest.raises(ValueError):
        calculate_equity(cards('Ah Kd'), board=cards('Ah 3d 4c'), num_simulations=10)


def test_rejects_non_positive_num_opponents():
    with pytest.raises(ValueError):
        calculate_equity(cards('Ah Kd'), num_opponents=0, num_simulations=10)


def test_rejects_too_many_opponents_for_remaining_deck():
    with pytest.raises(ValueError):
        # Pre-flop needs 5 board + 2 per opponent from 50 remaining cards.
        calculate_equity(cards('Ah Kd'), num_opponents=30, num_simulations=10)
