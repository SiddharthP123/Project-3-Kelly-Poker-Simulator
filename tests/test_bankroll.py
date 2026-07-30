import random

import pytest

from poker.bankroll import (
    all_in_strategy,
    fixed_stake_strategy,
    kelly_strategy,
    simulate_many_sessions,
    simulate_session,
)


def test_fixed_stake_strategy_ignores_current_bankroll():
    strategy = fixed_stake_strategy(fraction_of_initial_bankroll=0.1)
    assert strategy(1000, 1000, 0.6, 1) == pytest.approx(100)
    assert strategy(1000, 50, 0.6, 1) == pytest.approx(100)  # unchanged despite current=50


def test_kelly_strategy_scales_with_current_bankroll():
    # p=0.6, b=1 -> full Kelly fraction is 0.2 (see Part 5).
    strategy = kelly_strategy(kelly_multiplier=1.0)
    assert strategy(1000, 1000, 0.6, 1) == pytest.approx(200)
    assert strategy(1000, 500, 0.6, 1) == pytest.approx(100)  # 0.2 of CURRENT, not initial


def test_all_in_strategy_always_bets_current_bankroll():
    strategy = all_in_strategy()
    assert strategy(1000, 250, 0.6, 1) == 250
    assert strategy(1000, 1, 0.9, 5) == 1


def test_simulate_session_history_length_matches_num_hands_plus_one():
    rng = random.Random(1)
    result = simulate_session(fixed_stake_strategy(0.1), 1000, 0.5, 1, num_hands=10, rng=rng)
    assert len(result.bankroll_history) == 11


def test_guaranteed_loss_reaches_ruin_deterministically():
    # win_probability=0.0 means rng.random() < 0.0 is never true, so this
    # is fully deterministic regardless of the RNG's actual state.
    rng = random.Random(999)
    result = simulate_session(
        fixed_stake_strategy(0.5), initial_bankroll=1000, win_probability=0.0, odds=1,
        num_hands=5, rng=rng,
    )
    assert result.bankroll_history == (1000, 500, 0.0, 0.0, 0.0, 0.0)
    assert result.is_ruined is True


def test_guaranteed_win_doubles_bankroll_deterministically():
    # win_probability=1.0 means rng.random() < 1.0 is always true
    # (random() is always in [0, 1)), so this is deterministic too.
    # Full Kelly at p=1, b=1 is 1.0 -- betting the entire bankroll, which
    # then doubles every hand since it always wins.
    rng = random.Random(123)
    result = simulate_session(
        kelly_strategy(1.0), initial_bankroll=100, win_probability=1.0, odds=1,
        num_hands=3, rng=rng,
    )
    assert result.bankroll_history == pytest.approx((100, 200, 400, 800))
    assert result.is_ruined is False


def test_bankroll_never_goes_negative():
    rng = random.Random(7)
    result = simulate_session(
        fixed_stake_strategy(0.3), initial_bankroll=1000, win_probability=0.4, odds=1,
        num_hands=50, rng=rng,
    )
    assert all(value >= 0 for value in result.bankroll_history)


def test_simulate_many_sessions_returns_requested_count():
    result = simulate_many_sessions(
        kelly_strategy(0.5), 1000, win_probability=0.55, odds=1, num_hands=20,
        num_sessions=200, seed=1,
    )
    assert len(result.sessions) == 200


def test_all_in_has_near_certain_ruin_despite_a_real_edge():
    # p=0.55 is a genuine, meaningful edge, but all-in means any single
    # loss is total ruin. Surviving 20 hands undefeated has probability
    # 0.55^20 ~ 6e-6, so ruin should be near-certain across 500 sessions.
    result = simulate_many_sessions(
        all_in_strategy(), 1000, win_probability=0.55, odds=1, num_hands=20,
        num_sessions=500, seed=2,
    )
    assert result.risk_of_ruin > 0.99


def test_full_kelly_never_ruins_across_many_sessions():
    # Kelly betting can't hit exactly zero from a finite number of bets,
    # since every stake is a fraction below 1 of what remains.
    result = simulate_many_sessions(
        kelly_strategy(1.0), 1000, win_probability=0.55, odds=1, num_hands=200,
        num_sessions=300, seed=3,
    )
    assert result.risk_of_ruin == 0.0


def test_risk_of_ruin_ordering_across_strategies():
    # Same edge, same number of hands, same seed -- only the staking
    # strategy differs. This is the core demonstration of the part: risk
    # of ruin should strictly worsen as bet sizing gets more aggressive
    # relative to Kelly.
    common_args = dict(
        initial_bankroll=1000, win_probability=0.6, odds=1, num_hands=100,
        num_sessions=500, seed=4,
    )

    full_kelly = simulate_many_sessions(kelly_strategy(1.0), **common_args)
    fixed_stake = simulate_many_sessions(fixed_stake_strategy(0.1), **common_args)
    all_in = simulate_many_sessions(all_in_strategy(), **common_args)

    assert full_kelly.risk_of_ruin == 0.0
    assert full_kelly.risk_of_ruin < fixed_stake.risk_of_ruin
    assert fixed_stake.risk_of_ruin < all_in.risk_of_ruin


def test_simulate_session_rejects_invalid_inputs():
    rng = random.Random(0)
    with pytest.raises(ValueError):
        simulate_session(fixed_stake_strategy(0.1), 1000, 1.5, 1, num_hands=10, rng=rng)
    with pytest.raises(ValueError):
        simulate_session(fixed_stake_strategy(0.1), 1000, 0.5, 0, num_hands=10, rng=rng)
    with pytest.raises(ValueError):
        simulate_session(fixed_stake_strategy(0.1), 0, 0.5, 1, num_hands=10, rng=rng)
    with pytest.raises(ValueError):
        simulate_session(fixed_stake_strategy(0.1), 1000, 0.5, 1, num_hands=0, rng=rng)


def test_simulate_many_sessions_rejects_invalid_num_sessions():
    with pytest.raises(ValueError):
        simulate_many_sessions(
            fixed_stake_strategy(0.1), 1000, win_probability=0.5, odds=1, num_hands=10,
            num_sessions=0,
        )
