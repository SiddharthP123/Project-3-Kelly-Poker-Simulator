import math

import pytest

from poker.kelly import (
    expected_log_growth,
    fractional_kelly,
    kelly_fraction,
    kelly_fraction_from_pot_odds,
)


def test_kelly_fraction_matches_classic_example():
    # Classic textbook example: 60% win probability at even money (b=1)
    # -> bet 20% of bankroll.
    assert kelly_fraction(win_probability=0.6, odds=1) == pytest.approx(0.2)


def test_kelly_fraction_is_zero_with_no_edge():
    # 50/50 at even money has no edge at all -- bet nothing.
    assert kelly_fraction(win_probability=0.5, odds=1) == pytest.approx(0.0)


def test_kelly_fraction_is_negative_with_a_losing_edge():
    assert kelly_fraction(win_probability=0.4, odds=1) < 0


def test_kelly_fraction_rejects_invalid_probability():
    with pytest.raises(ValueError):
        kelly_fraction(win_probability=1.5, odds=1)
    with pytest.raises(ValueError):
        kelly_fraction(win_probability=-0.1, odds=1)


def test_kelly_fraction_rejects_non_positive_odds():
    with pytest.raises(ValueError):
        kelly_fraction(win_probability=0.6, odds=0)


def test_fractional_kelly_clips_negative_edge_to_zero():
    assert fractional_kelly(win_probability=0.3, odds=1) == 0.0


def test_fractional_kelly_full_matches_raw_kelly_when_positive():
    assert fractional_kelly(win_probability=0.6, odds=1, fraction=1.0) == pytest.approx(
        kelly_fraction(0.6, 1)
    )


def test_fractional_kelly_half_is_half_of_full():
    full = fractional_kelly(win_probability=0.6, odds=1, fraction=1.0)
    half = fractional_kelly(win_probability=0.6, odds=1, fraction=0.5)
    assert half == pytest.approx(full / 2)


def test_kelly_fraction_from_pot_odds_uses_pot_over_bet_as_odds():
    # equity=0.6, pot=100, bet=50 -> odds b = 100/50 = 2
    # f* = (0.6*2 - 0.4) / 2 = 0.8 / 2 = 0.4
    result = kelly_fraction_from_pot_odds(equity=0.6, pot_size=100, bet_to_call=50)
    assert result == pytest.approx(0.4)


def test_kelly_fraction_from_pot_odds_applies_multiplier():
    full = kelly_fraction_from_pot_odds(equity=0.6, pot_size=100, bet_to_call=50)
    half = kelly_fraction_from_pot_odds(equity=0.6, pot_size=100, bet_to_call=50, kelly_multiplier=0.5)
    assert half == pytest.approx(full / 2)


def test_kelly_fraction_from_pot_odds_rejects_non_positive_bet():
    with pytest.raises(ValueError):
        kelly_fraction_from_pot_odds(equity=0.6, pot_size=100, bet_to_call=0)


def test_expected_log_growth_matches_manual_calculation():
    p, b, f = 0.6, 1, 0.2
    expected = p * math.log(1 + f * b) + (1 - p) * math.log(1 - f)
    assert expected_log_growth(p, b, f) == pytest.approx(expected)


def test_expected_log_growth_rejects_full_bankroll_bet():
    with pytest.raises(ValueError):
        expected_log_growth(win_probability=0.6, odds=1, fraction=1.0)


@pytest.mark.parametrize(
    'win_probability, odds',
    [
        (0.6, 1),
        (0.55, 2),
        (0.7, 0.5),
        (0.8, 3),
    ],
)
def test_kelly_fraction_maximises_expected_log_growth(win_probability, odds):
    # This is the real proof the formula is implemented correctly: Kelly
    # is *defined* as the fraction that maximises expected log-growth, so
    # nearby fractions (both lower and higher) should never grow the
    # bankroll faster than betting exactly the Kelly fraction.
    optimal = kelly_fraction(win_probability, odds)
    growth_at_optimal = expected_log_growth(win_probability, odds, optimal)

    for offset in (-0.10, -0.05, -0.01, 0.01, 0.05, 0.10):
        nearby_fraction = optimal + offset
        if not 0 <= nearby_fraction < 1:
            continue
        growth_nearby = expected_log_growth(win_probability, odds, nearby_fraction)
        assert growth_at_optimal >= growth_nearby - 1e-9
