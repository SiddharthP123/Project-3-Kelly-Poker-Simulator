import pytest

from poker.bots import (
    Action,
    Bot,
    KellyOptimalBot,
    LoosePassiveBot,
    RandomBot,
    TightAggressiveBot,
)
from poker.cards import Card
from poker.kelly import kelly_fraction_from_pot_odds


def test_tight_aggressive_folds_below_threshold():
    bot = TightAggressiveBot()
    action = bot.decide(equity=0.3, pot_size=100, bet_to_call=20)
    assert action == Action('fold')


def test_tight_aggressive_calls_in_middle_range():
    bot = TightAggressiveBot()  # fold_below=0.55, raise_above=0.65
    action = bot.decide(equity=0.6, pot_size=100, bet_to_call=20)
    assert action == Action('call')


def test_tight_aggressive_raises_above_threshold():
    bot = TightAggressiveBot(raise_sizing=0.75)
    action = bot.decide(equity=0.8, pot_size=100, bet_to_call=20)
    assert action == Action('raise', 75.0)


def test_loose_passive_plays_a_much_wider_range():
    # Equity of 0.2 would make a TAG fold (threshold 0.55), but a loose
    # passive bot (threshold 0.15) should still call.
    bot = LoosePassiveBot()
    action = bot.decide(equity=0.2, pot_size=100, bet_to_call=20)
    assert action == Action('call')


def test_loose_passive_rarely_raises():
    # Equity of 0.6 would make a TAG raise (threshold 0.65 -- close, but
    # 0.6 is actually below it so TAG would call too; use 0.7 to be sure
    # it's comfortably above TAG's raise threshold but still well below
    # loose-passive's 0.85).
    bot = LoosePassiveBot()
    action = bot.decide(equity=0.7, pot_size=100, bet_to_call=20)
    assert action == Action('call')


def test_random_bot_is_reproducible_with_seed():
    first = RandomBot(seed=7)
    second = RandomBot(seed=7)

    decisions_first = [first.decide(0.5, 100, 20) for _ in range(20)]
    decisions_second = [second.decide(0.5, 100, 20) for _ in range(20)]

    assert decisions_first == decisions_second


def test_random_bot_ignores_equity():
    bot_low = RandomBot(seed=1)
    bot_high = RandomBot(seed=1)

    # Same seed -> same underlying random sequence regardless of the
    # (unused) equity argument passed in.
    assert bot_low.decide(0.01, 100, 20) == bot_high.decide(0.99, 100, 20)


def test_random_bot_raise_amount_is_half_pot():
    bot = RandomBot(seed=3)  # seed chosen so the first draw is 'raise'
    decisions = [bot.decide(0.5, 100, 20) for _ in range(10)]
    raises = [action for action in decisions if action.action == 'raise']
    assert raises  # sanity check the seed actually produces at least one
    assert all(action.raise_amount == pytest.approx(50.0) for action in raises)


def test_kelly_optimal_bot_folds_with_no_edge():
    # equity below the pot-odds breakeven point -> no Kelly edge -> fold.
    bot = KellyOptimalBot()
    action = bot.decide(equity=0.2, pot_size=100, bet_to_call=100, bankroll=1000)
    assert action == Action('fold')


def test_kelly_optimal_bot_calls_when_edge_is_small():
    # Equity just above breakeven (100/(100+100)=0.5) with a modest
    # bankroll -> Kelly recommends staking less than the call itself
    # requires, so the right move is just to call, not raise.
    bot = KellyOptimalBot()
    action = bot.decide(equity=0.52, pot_size=100, bet_to_call=100, bankroll=200)
    assert action == Action('call')


def test_kelly_optimal_bot_raises_when_edge_and_bankroll_are_large():
    bot = KellyOptimalBot()
    action = bot.decide(equity=0.9, pot_size=100, bet_to_call=50, bankroll=10_000)
    assert action.action == 'raise'
    assert action.raise_amount > 50  # stakes more than merely calling would


def test_kelly_optimal_bot_matches_manual_kelly_calculation():
    equity, pot_size, bet_to_call, bankroll = 0.9, 100, 50, 10_000
    expected_stake = kelly_fraction_from_pot_odds(equity, pot_size, bet_to_call) * bankroll

    bot = KellyOptimalBot()
    action = bot.decide(equity, pot_size, bet_to_call, bankroll)

    assert action.raise_amount == pytest.approx(expected_stake)


def test_kelly_optimal_bot_requires_bankroll():
    bot = KellyOptimalBot()
    with pytest.raises(ValueError):
        bot.decide(equity=0.9, pot_size=100, bet_to_call=50, bankroll=None)


def test_raise_is_capped_to_bankroll_when_provided():
    # Pot-sized raise would be 75, but bankroll only has 30 left.
    bot = TightAggressiveBot(raise_sizing=0.75)
    action = bot.decide(equity=0.9, pot_size=100, bet_to_call=20, bankroll=30)
    assert action == Action('raise', 30)


def test_raise_is_not_capped_when_bankroll_not_provided():
    bot = TightAggressiveBot(raise_sizing=0.75)
    action = bot.decide(equity=0.9, pot_size=100, bet_to_call=20, bankroll=None)
    assert action == Action('raise', 75.0)


def test_base_bot_decide_is_not_implemented():
    with pytest.raises(NotImplementedError):
        Bot().decide(equity=0.5, pot_size=100, bet_to_call=20)


def test_decide_from_hand_integration_with_equity_calculator():
    # Pocket aces heads-up have ~85% equity -- comfortably above TAG's
    # raise threshold of 0.65, so this should recommend raising, having
    # gone through the real Monte Carlo equity calculator (Part 3), not a
    # hand-fed equity number.
    bot = TightAggressiveBot()
    hole_cards = [Card.from_str('Ah'), Card.from_str('Ac')]

    action = bot.decide_from_hand(
        hole_cards, board=(), pot_size=100, bet_to_call=20, num_opponents=1,
        num_simulations=3000, seed=5,
    )
    assert action.action == 'raise'
