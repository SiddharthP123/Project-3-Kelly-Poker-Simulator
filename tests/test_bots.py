import random

import pytest

from poker.bots import (
    PERSONA_REGISTRY,
    Action,
    BalancedBot,
    Bot,
    KellyOptimalBot,
    LooseAggressiveBot,
    LoosePassiveBot,
    RandomBot,
    TightAggressiveBot,
    VeryLooseAggressiveBot,
    VeryLoosePassiveBot,
    VeryTightAggressiveBot,
    VeryTightPassiveBot,
    assign_opponent_personas,
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


# --- expanded persona roster (Part 12 Phase 3) ----------------------------


def test_very_tight_passive_folds_where_tight_aggressive_would_still_call():
    # TAG's fold_below is 0.55, so 0.6 is comfortably in its calling range.
    # The Rock's fold_below is 0.65 -- 0.6 should still be a fold for it.
    bot = VeryTightPassiveBot()
    action = bot.decide(equity=0.6, pot_size=100, bet_to_call=20)
    assert action == Action('fold')


def test_very_tight_passive_raises_smaller_than_tight_aggressive():
    tag = TightAggressiveBot()
    rock = VeryTightPassiveBot()

    tag_action = tag.decide(equity=0.95, pot_size=100, bet_to_call=20)
    rock_action = rock.decide(equity=0.95, pot_size=100, bet_to_call=20)

    assert tag_action.action == rock_action.action == 'raise'
    assert rock_action.raise_amount < tag_action.raise_amount


def test_very_tight_aggressive_folds_more_but_raises_bigger_than_tight_aggressive():
    tag = TightAggressiveBot()
    nit_shark = VeryTightAggressiveBot()

    # 0.6 is a call for TAG (fold_below=0.55) but a fold for the Nit-Shark
    # (fold_below=0.70).
    assert tag.decide(equity=0.6, pot_size=100, bet_to_call=20) == Action('call')
    assert nit_shark.decide(equity=0.6, pot_size=100, bet_to_call=20) == Action('fold')

    tag_raise = tag.decide(equity=0.95, pot_size=100, bet_to_call=20)
    nit_shark_raise = nit_shark.decide(equity=0.95, pot_size=100, bet_to_call=20)
    assert nit_shark_raise.raise_amount > tag_raise.raise_amount


def test_balanced_bot_sits_between_tight_and_loose_thresholds():
    bot = BalancedBot()
    # 0.5 is below TAG's fold_below (0.55) but above loose-passive's
    # (0.15) and above Balanced's own (0.45) -- should call, not fold.
    action = bot.decide(equity=0.5, pot_size=100, bet_to_call=20)
    assert action == Action('call')


def test_very_loose_passive_calls_where_loose_passive_would_fold():
    # LoosePassiveBot's fold_below is 0.15 -- 0.1 is a fold for it.
    # Very-Loose-Passive's fold_below is 0.05 -- 0.1 should still call.
    loose_passive = LoosePassiveBot()
    weak_loose = VeryLoosePassiveBot()

    assert loose_passive.decide(equity=0.1, pot_size=100, bet_to_call=20) == Action('fold')
    assert weak_loose.decide(equity=0.1, pot_size=100, bet_to_call=20) == Action('call')


def test_loose_aggressive_raises_where_loose_passive_would_call():
    # Both play equity=0.5 (well within both personas' non-fold range),
    # but LAG's raise_above (0.45) means it raises here while
    # loose-passive's raise_above (0.85) means it just calls.
    lag = LooseAggressiveBot()
    loose_passive = LoosePassiveBot()

    assert lag.decide(equity=0.5, pot_size=100, bet_to_call=20).action == 'raise'
    assert loose_passive.decide(equity=0.5, pot_size=100, bet_to_call=20).action == 'call'


def test_very_loose_aggressive_raises_the_biggest_of_any_persona():
    maniac = VeryLooseAggressiveBot()
    lag = LooseAggressiveBot()

    maniac_action = maniac.decide(equity=0.9, pot_size=100, bet_to_call=20)
    lag_action = lag.decide(equity=0.9, pot_size=100, bet_to_call=20)

    assert maniac_action.action == lag_action.action == 'raise'
    assert maniac_action.raise_amount > lag_action.raise_amount
    assert maniac_action.raise_amount > 100  # bets more than the pot itself


def test_persona_registry_has_all_ten_personas():
    assert len(PERSONA_REGISTRY) == 10
    assert set(PERSONA_REGISTRY.keys()) == {
        'very-tight-passive', 'tight-aggressive', 'very-tight-aggressive',
        'balanced', 'loose-passive', 'very-loose-passive', 'loose-aggressive',
        'very-loose-aggressive', 'random', 'kelly-optimal',
    }


def test_persona_registry_entries_are_all_instantiable_bots():
    for persona_class in PERSONA_REGISTRY.values():
        bot = persona_class()
        assert isinstance(bot, Bot)


# --- assign_opponent_personas ----------------------------------------------


def test_assign_opponent_personas_returns_requested_count_with_no_repeats():
    rng = random.Random(1)
    personas = assign_opponent_personas(4, rng)

    assert len(personas) == 4
    assert len(set(personas)) == 4  # no seat gets the same persona twice
    assert set(personas) <= set(PERSONA_REGISTRY.keys())


def test_assign_opponent_personas_is_reproducible_with_same_seeded_rng():
    first = assign_opponent_personas(3, random.Random(42))
    second = assign_opponent_personas(3, random.Random(42))
    assert first == second


def test_assign_opponent_personas_can_use_all_ten_at_once():
    rng = random.Random(1)
    personas = assign_opponent_personas(10, rng)
    assert set(personas) == set(PERSONA_REGISTRY.keys())


@pytest.mark.parametrize('num_opponents', [0, 11])
def test_assign_opponent_personas_rejects_out_of_range_count(num_opponents):
    with pytest.raises(ValueError):
        assign_opponent_personas(num_opponents, random.Random(1))
