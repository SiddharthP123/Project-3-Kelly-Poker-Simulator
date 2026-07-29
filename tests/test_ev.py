import pytest

from poker.cards import Card
from poker.equity import calculate_equity
from poker.ev import (
    Decision,
    best_action,
    ev_call,
    ev_fold,
    ev_raise,
    pot_odds_breakeven_equity,
)


def test_pot_odds_matches_known_example():
    # Pot is $100, facing a $50 bet -> total pot after call is $150, so you
    # need to win 50/150 = 33.33% of the time to break even.
    assert pot_odds_breakeven_equity(pot_size=100, bet_to_call=50) == pytest.approx(1 / 3)


def test_pot_odds_rejects_non_positive_bet():
    with pytest.raises(ValueError):
        pot_odds_breakeven_equity(pot_size=100, bet_to_call=0)


def test_pot_odds_rejects_negative_pot():
    with pytest.raises(ValueError):
        pot_odds_breakeven_equity(pot_size=-10, bet_to_call=50)


def test_ev_fold_is_always_zero():
    assert ev_fold() == 0.0


def test_ev_call_is_zero_at_exactly_the_breakeven_equity():
    pot_size, bet_to_call = 100, 50
    breakeven = pot_odds_breakeven_equity(pot_size, bet_to_call)
    assert ev_call(breakeven, pot_size, bet_to_call) == pytest.approx(0.0)


def test_ev_call_is_positive_above_breakeven_and_negative_below():
    pot_size, bet_to_call = 100, 50
    breakeven = pot_odds_breakeven_equity(pot_size, bet_to_call)

    assert ev_call(breakeven + 0.1, pot_size, bet_to_call) > 0
    assert ev_call(breakeven - 0.1, pot_size, bet_to_call) < 0


def test_ev_raise_when_opponent_always_folds_equals_current_pot():
    # If fold_probability is 1.0, your equity/raise size never even matter
    # -- you always just win the pot as it stood.
    ev = ev_raise(equity=0.2, pot_size=100, raise_amount=40, fold_probability=1.0)
    assert ev == pytest.approx(100)


def test_ev_raise_when_opponent_never_folds_equals_ev_call():
    equity, pot_size, raise_amount = 0.6, 100, 40
    raise_ev = ev_raise(equity, pot_size, raise_amount, fold_probability=0.0)
    call_ev = ev_call(equity, pot_size, raise_amount)
    assert raise_ev == pytest.approx(call_ev)


def test_ev_raise_is_weighted_average_of_fold_and_call_branches():
    equity, pot_size, raise_amount = 0.4, 100, 40
    fold_prob = 0.3

    expected = fold_prob * pot_size + (1 - fold_prob) * ev_call(equity, pot_size, raise_amount)
    assert ev_raise(equity, pot_size, raise_amount, fold_prob) == pytest.approx(expected)


def test_ev_call_rejects_out_of_range_equity():
    with pytest.raises(ValueError):
        ev_call(1.5, pot_size=100, bet_to_call=50)
    with pytest.raises(ValueError):
        ev_call(-0.1, pot_size=100, bet_to_call=50)


def test_best_action_folds_when_equity_well_below_breakeven():
    decision = best_action(equity=0.1, pot_size=100, bet_to_call=50)
    assert decision.action == 'fold'
    assert decision.evs['fold'] == 0.0


def test_best_action_calls_when_equity_comfortably_above_breakeven():
    decision = best_action(equity=0.9, pot_size=100, bet_to_call=50)
    assert decision.action == 'call'


def test_best_action_considers_raise_when_supplied():
    # Strong equity plus a high fold probability should make raising the
    # clear best action -- it wins the pot outright most of the time, and
    # still has strong showdown equity on the branch where it doesn't.
    decision = best_action(
        equity=0.8,
        pot_size=100,
        bet_to_call=50,
        raise_amount=60,
        fold_probability=0.6,
    )
    assert decision.action == 'raise'
    assert set(decision.evs.keys()) == {'fold', 'call', 'raise'}


def test_best_action_omits_raise_when_not_supplied():
    decision = best_action(equity=0.9, pot_size=100, bet_to_call=50)
    assert 'raise' not in decision.evs


def test_best_action_requires_raise_params_together():
    with pytest.raises(ValueError):
        best_action(equity=0.5, pot_size=100, bet_to_call=50, raise_amount=60)

    with pytest.raises(ValueError):
        best_action(equity=0.5, pot_size=100, bet_to_call=50, fold_probability=0.5)


def test_decision_str_is_readable():
    decision = Decision(action='call', evs={'fold': 0.0, 'call': 12.5})
    assert str(decision) == 'call (fold=+0.00, call=+12.50)'


def test_integration_pocket_aces_equity_recommends_calling_good_pot_odds():
    # Ties Part 3's Monte Carlo equity directly into Part 4's decision:
    # pocket aces heads-up have far more than enough equity to profitably
    # call a pot-sized bet.
    hole_cards = [Card.from_str('Ah'), Card.from_str('Ac')]
    result = calculate_equity(hole_cards, num_opponents=1, num_simulations=3000, seed=11)

    decision = best_action(equity=result.equity, pot_size=100, bet_to_call=100)
    assert decision.action == 'call'
