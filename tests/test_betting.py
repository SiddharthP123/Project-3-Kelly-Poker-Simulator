import pytest

from poker.betting import (
    ActionBounds,
    BettingRound,
    Pot,
    PlayerState,
    PlayerStatus,
    award_pots,
    build_pots,
)
from poker.cards import Card


def cards(text):
    return [Card.from_str(token) for token in text.split()]


# --- PlayerState -------------------------------------------------------


def test_commit_moves_chips_from_stack_to_pot():
    player = PlayerState(seat=0, stack=100.0)
    actual = player.commit(30.0)

    assert actual == 30.0
    assert player.stack == 70.0
    assert player.committed_street == 30.0
    assert player.committed_total == 30.0
    assert player.status == PlayerStatus.ACTIVE


def test_commit_caps_at_available_stack_and_flips_to_all_in():
    player = PlayerState(seat=0, stack=50.0)
    actual = player.commit(80.0)  # tries to commit more than the stack has

    assert actual == 50.0
    assert player.stack == 0.0
    assert player.status == PlayerStatus.ALL_IN


def test_commit_exactly_draining_stack_flips_to_all_in():
    player = PlayerState(seat=0, stack=25.0)
    player.commit(25.0)

    assert player.stack == 0.0
    assert player.status == PlayerStatus.ALL_IN


def test_committed_total_persists_across_streets_but_committed_street_resets():
    player = PlayerState(seat=0, stack=100.0)
    player.commit(20.0)
    player.start_new_street()
    player.commit(15.0)

    assert player.committed_street == 15.0
    assert player.committed_total == 35.0


# --- BettingRound: basic heads-up flow ----------------------------------


def _heads_up_players(stack=1000.0):
    return [PlayerState(seat=0, stack=stack), PlayerState(seat=1, stack=stack)]


def test_blinds_set_current_bet_and_committed_amounts():
    players = _heads_up_players()
    round_ = BettingRound(players, order=[0, 1], current_bet=0.0, min_raise=10.0)
    round_.post_blind(0, 5.0)   # small blind
    round_.post_blind(1, 10.0)  # big blind

    assert players[0].committed_street == 5.0
    assert players[1].committed_street == 10.0
    assert round_.current_bet == 10.0


def test_pot_size_after_reflects_the_whole_hand_not_just_the_current_street():
    players = _heads_up_players()
    round_ = BettingRound(players, order=[0, 1], current_bet=0.0, min_raise=10.0)
    blind_record = round_.post_blind(0, 5.0)
    assert blind_record.pot_size_after == 5.0

    call_record = round_.apply(1, 'match')  # matches seat 0's 5 (only blind posted)
    assert call_record.pot_size_after == 10.0  # 5 + 5

    # A later street's BettingRound is a different object, but reuses the
    # SAME PlayerState instances -- pot_size_after should keep accumulating
    # across streets, not reset with committed_street.
    for player in players:
        player.start_new_street()
    flop_round = BettingRound(players, order=[0, 1], current_bet=0.0, min_raise=10.0, street='flop')
    flop_record = flop_round.apply(0, 'raise_to', raise_to=20.0)
    assert flop_record.pot_size_after == 10.0 + 20.0


def test_both_players_matching_closes_the_round():
    players = _heads_up_players()
    round_ = BettingRound(players, order=[0, 1], current_bet=0.0, min_raise=10.0)
    round_.post_blind(0, 5.0)
    round_.post_blind(1, 10.0)

    assert not round_.is_closed()
    round_.apply(0, 'match')  # small blind calls up to 10
    assert not round_.is_closed()
    round_.apply(1, 'match')  # big blind checks (already at 10)
    assert round_.is_closed()


def test_fold_ends_the_round_when_only_one_player_remains():
    players = _heads_up_players()
    round_ = BettingRound(players, order=[0, 1], current_bet=10.0, min_raise=10.0)

    round_.apply(0, 'fold')

    assert players[0].status == PlayerStatus.FOLDED
    assert round_.is_closed()


def test_cannot_act_out_of_turn_or_twice():
    players = _heads_up_players()
    round_ = BettingRound(players, order=[0, 1], current_bet=10.0, min_raise=10.0)
    round_.apply(0, 'match')

    with pytest.raises(ValueError):
        round_.apply(0, 'match')  # already acted, no longer eligible


def test_cannot_apply_once_round_is_closed():
    players = _heads_up_players()
    round_ = BettingRound(players, order=[0, 1], current_bet=10.0, min_raise=10.0)
    round_.apply(0, 'match')
    round_.apply(1, 'match')

    with pytest.raises(ValueError):
        round_.apply(0, 'fold')


# --- Raising, min-raise enforcement, reopening action -------------------


def test_legal_action_bounds_reflects_call_amount_and_raise_range():
    players = _heads_up_players(stack=1000.0)
    round_ = BettingRound(players, order=[0, 1], current_bet=10.0, min_raise=10.0)

    bounds = round_.legal_action_bounds(0)
    assert bounds.can_call
    assert bounds.call_amount == 10.0
    assert bounds.can_raise
    assert bounds.min_raise_to == 20.0  # current_bet(10) + min_raise_increment(10)
    assert bounds.max_raise_to == 1000.0  # committed_street(0) + stack(1000)


def test_raise_updates_current_bet_and_reopens_action_for_others():
    players = [
        PlayerState(seat=0, stack=1000.0),
        PlayerState(seat=1, stack=1000.0),
        PlayerState(seat=2, stack=1000.0),
    ]
    round_ = BettingRound(players, order=[0, 1, 2], current_bet=10.0, min_raise=10.0)

    round_.apply(0, 'match')  # seat 0 calls the 10, done acting
    assert round_.needs_to_act == {1, 2}

    round_.apply(1, 'raise_to', raise_to=30.0)  # seat 1 raises to 30
    # Seat 0 already matched but the bar moved -- must act again.
    assert round_.needs_to_act == {0, 2}
    assert round_.current_bet == 30.0
    assert round_.last_raise_increment == 20.0  # 30 - 10


def test_raise_below_minimum_is_rejected_unless_its_an_all_in():
    players = _heads_up_players(stack=1000.0)
    round_ = BettingRound(players, order=[0, 1], current_bet=10.0, min_raise=10.0)

    with pytest.raises(ValueError):
        round_.apply(0, 'raise_to', raise_to=15.0)  # below min_raise_to of 20


def test_all_in_for_less_than_min_raise_is_allowed():
    players = [PlayerState(seat=0, stack=15.0), PlayerState(seat=1, stack=1000.0)]
    round_ = BettingRound(players, order=[0, 1], current_bet=10.0, min_raise=10.0)

    # seat 0 only has 15 total -- a full min-raise would need 20, but an
    # all-in for everything they have (15) is still legal.
    bounds = round_.legal_action_bounds(0)
    assert bounds.min_raise_to == 15.0  # capped down to their max
    action = round_.apply(0, 'raise_to', raise_to=15.0)

    assert action.action == 'raise_to'
    assert players[0].status == PlayerStatus.ALL_IN
    assert players[0].stack == 0.0


def test_raise_amount_exceeding_stack_is_rejected():
    players = _heads_up_players(stack=100.0)
    round_ = BettingRound(players, order=[0, 1], current_bet=10.0, min_raise=10.0)

    with pytest.raises(ValueError):
        round_.apply(0, 'raise_to', raise_to=500.0)


def test_betting_round_closes_correctly_for_multiple_players_with_a_late_fold():
    players = [
        PlayerState(seat=0, stack=1000.0),
        PlayerState(seat=1, stack=1000.0),
        PlayerState(seat=2, stack=1000.0),
        PlayerState(seat=3, stack=1000.0),
    ]
    round_ = BettingRound(players, order=[0, 1, 2, 3], current_bet=10.0, min_raise=10.0)

    round_.apply(0, 'match')
    round_.apply(1, 'fold')
    round_.apply(2, 'raise_to', raise_to=30.0)
    # seat 0 already matched at 10 but must respond to the new raise;
    # seat 1 folded and is permanently out; seat 3 hasn't acted yet.
    assert round_.needs_to_act == {0, 3}

    round_.apply(3, 'fold')
    assert round_.needs_to_act == {0}
    round_.apply(0, 'match')
    assert round_.is_closed()


def test_round_closes_when_fewer_than_two_non_folded_players_remain_even_mid_action():
    players = [
        PlayerState(seat=0, stack=1000.0),
        PlayerState(seat=1, stack=1000.0),
        PlayerState(seat=2, stack=1000.0),
    ]
    round_ = BettingRound(players, order=[0, 1, 2], current_bet=10.0, min_raise=10.0)

    round_.apply(0, 'fold')
    round_.apply(1, 'fold')
    # seat 2 never even acted, but only one non-folded player remains.
    assert round_.is_closed()
    assert round_.next_to_act() is None


# --- Uncalled-bet refund -------------------------------------------------


def test_refund_when_everyone_folds_to_a_bet():
    players = [
        PlayerState(seat=0, stack=900.0, committed_street=100.0, committed_total=100.0),
        PlayerState(seat=1, stack=950.0, committed_street=50.0, committed_total=50.0,
                    status=PlayerStatus.FOLDED),
        PlayerState(seat=2, stack=1000.0, committed_street=0.0, committed_total=0.0,
                    status=PlayerStatus.FOLDED),
    ]
    round_ = BettingRound(players, order=[0, 1, 2], current_bet=100.0, min_raise=10.0)

    refund = round_.refund_uncalled_bet()

    assert refund == 50.0  # 100 - the next-highest commitment (seat 1's 50)
    assert players[0].committed_street == 50.0
    assert players[0].committed_total == 50.0
    assert players[0].stack == 950.0


def test_refund_when_remaining_opponent_can_only_call_for_less():
    players = [
        PlayerState(seat=0, stack=900.0, committed_street=100.0, committed_total=100.0),
        PlayerState(seat=1, stack=0.0, committed_street=60.0, committed_total=60.0,
                    status=PlayerStatus.ALL_IN),
    ]
    round_ = BettingRound(players, order=[0, 1], current_bet=100.0, min_raise=10.0)

    refund = round_.refund_uncalled_bet()

    assert refund == 40.0  # 100 - 60
    assert players[0].committed_street == 60.0
    assert players[0].stack == 940.0


def test_refund_is_a_noop_when_top_two_commitments_are_equal():
    players = [
        PlayerState(seat=0, stack=900.0, committed_street=100.0, committed_total=100.0),
        PlayerState(seat=1, stack=900.0, committed_street=100.0, committed_total=100.0),
    ]
    round_ = BettingRound(players, order=[0, 1], current_bet=100.0, min_raise=10.0)

    refund = round_.refund_uncalled_bet()

    assert refund is None
    assert players[0].committed_street == 100.0
    assert players[1].committed_street == 100.0


def test_refund_can_return_an_all_in_player_to_active_status():
    # seat 0 posted their whole (tiny) stack as a bet; seat 1 folded
    # without ever matching any of it. Since NOBODY matched any part of
    # seat 0's bet, the whole thing is uncalled and refunded -- which
    # means seat 0 isn't really "all-in" anymore, they have chips again.
    players = [
        PlayerState(seat=0, stack=0.0, committed_street=5.0, committed_total=5.0,
                    status=PlayerStatus.ALL_IN),
        PlayerState(seat=1, stack=995.0, committed_street=0.0, committed_total=0.0,
                    status=PlayerStatus.FOLDED),
    ]
    round_ = BettingRound(players, order=[0, 1], current_bet=5.0, min_raise=5.0)

    refund = round_.refund_uncalled_bet()

    assert refund == 5.0
    assert players[0].committed_street == 0.0
    assert players[0].stack == 5.0
    assert players[0].status == PlayerStatus.ACTIVE


# --- Side pots: build_pots ------------------------------------------------


def test_single_pot_when_everyone_has_equal_commitment():
    players = [
        PlayerState(seat=0, stack=0.0, committed_total=100.0),
        PlayerState(seat=1, stack=0.0, committed_total=100.0),
    ]
    pots = build_pots(players)

    assert len(pots) == 1
    assert pots[0].amount == 200.0
    assert pots[0].eligible_seats == frozenset({0, 1})


def test_worked_example_three_way_all_in_50_120_200():
    players = [
        PlayerState(seat=0, stack=0.0, committed_total=50.0, status=PlayerStatus.ALL_IN),
        PlayerState(seat=1, stack=0.0, committed_total=120.0, status=PlayerStatus.ALL_IN),
        PlayerState(seat=2, stack=0.0, committed_total=200.0, status=PlayerStatus.ALL_IN),
    ]
    pots = build_pots(players)

    assert len(pots) == 3
    assert pots[0] == Pot(150.0, frozenset({0, 1, 2}))
    assert pots[1] == Pot(140.0, frozenset({1, 2}))
    assert pots[2] == Pot(80.0, frozenset({2}))
    # Checksum: every dollar committed is accounted for across the layers.
    assert sum(pot.amount for pot in pots) == 50.0 + 120.0 + 200.0


def test_folded_players_contribute_to_pot_amount_but_are_never_eligible():
    # seat 0's folded $50 is less than seats 1/2's $100 -- a real
    # threshold split, so this is two layers, not one. Both layers share
    # the same eligible set ({1,2}), so they still pay out identically to
    # a single $250 pot would -- the folded contribution stays in the
    # money, seat 0 just can never win any of it.
    players = [
        PlayerState(seat=0, stack=0.0, committed_total=50.0, status=PlayerStatus.FOLDED),
        PlayerState(seat=1, stack=0.0, committed_total=100.0),
        PlayerState(seat=2, stack=0.0, committed_total=100.0),
    ]
    pots = build_pots(players)

    assert len(pots) == 2
    assert all(pot.eligible_seats == frozenset({1, 2}) for pot in pots)
    assert sum(pot.amount for pot in pots) == 250.0


def test_side_pot_with_a_fold_mixed_in():
    # seat 0 folds after committing 30, seat 1 is all-in for 80, seat 2
    # covers the full 150.
    #   threshold 30:  contributors {0,1,2} -> 30*3=90,  eligible {1,2} (0 folded)
    #   threshold 80:  contributors {1,2}   -> 50*2=100, eligible {1,2}
    #   threshold 150: contributors {2}     -> 70*1=70,  eligible {2}
    players = [
        PlayerState(seat=0, stack=0.0, committed_total=30.0, status=PlayerStatus.FOLDED),
        PlayerState(seat=1, stack=0.0, committed_total=80.0, status=PlayerStatus.ALL_IN),
        PlayerState(seat=2, stack=0.0, committed_total=150.0),
    ]
    pots = build_pots(players)

    assert len(pots) == 3
    assert pots[0] == Pot(90.0, frozenset({1, 2}))
    assert pots[1] == Pot(100.0, frozenset({1, 2}))
    assert pots[2] == Pot(70.0, frozenset({2}))
    assert sum(pot.amount for pot in pots) == 30.0 + 80.0 + 150.0


def test_build_pots_raises_if_a_layer_has_no_eligible_winners():
    # Deliberately construct an invalid state (everyone contributing to
    # the top layer folded) that should never occur if the uncalled-bet
    # refund ran correctly -- confirms the defensive guard actually fires
    # rather than silently dropping money.
    players = [
        PlayerState(seat=0, stack=0.0, committed_total=100.0, status=PlayerStatus.FOLDED),
        PlayerState(seat=1, stack=0.0, committed_total=50.0, status=PlayerStatus.FOLDED),
    ]

    with pytest.raises(ValueError):
        build_pots(players)


def test_build_pots_returns_empty_list_when_nobody_committed_anything():
    players = [PlayerState(seat=0, stack=1000.0), PlayerState(seat=1, stack=1000.0)]
    assert build_pots(players) == []


# --- Awarding pots (integration with poker/hand_evaluator.py) ------------


def test_award_pots_single_layer_single_winner():
    pots = [Pot(200.0, frozenset({0, 1}))]
    board = cards('2c 5d 9s Jh 3h')
    hands = {
        0: cards('Ah Ad') + board,  # pair of aces
        1: cards('Kh Kd') + board,  # pair of kings, loses
    }

    payouts = award_pots(pots, hands)

    assert payouts == {0: 200.0}


def test_award_pots_splits_a_tied_layer_evenly():
    pots = [Pot(200.0, frozenset({0, 1}))]
    board = cards('5h 6d 7c 8s 9h')  # straight on the board, hole cards don't improve it
    hands = {
        0: cards('2c 3d') + board,
        1: cards('2h 3s') + board,
    }

    payouts = award_pots(pots, hands)

    assert payouts == {0: 100.0, 1: 100.0}


def test_award_pots_awards_a_single_eligible_seat_uncontested_no_comparison_needed():
    # Seat 2 is the only one eligible for this layer (the earlier side-pot
    # layers already accounted for seats 0/1) -- must not require a hand
    # comparison to award it.
    pots = [Pot(80.0, frozenset({2}))]
    hands = {2: cards('2c 7d 9s Jh 3h')}  # garbage hand, doesn't matter, wins by default

    payouts = award_pots(pots, hands)

    assert payouts == {2: 80.0}


def test_award_pots_across_multiple_layers_matches_the_worked_side_pot_example():
    # Full end-to-end: the $50/$120/$200 worked example, but now actually
    # awarded based on real hands.
    pots = [
        Pot(150.0, frozenset({0, 1, 2})),
        Pot(140.0, frozenset({1, 2})),
        Pot(80.0, frozenset({2})),
    ]
    board = cards('2c 5d 9s Jh 3h')
    hands = {
        0: cards('Kh Kd') + board,   # pair of kings -- only eligible for the main pot
        1: cards('Ah Ad') + board,   # pair of aces -- best hand among {0,1,2}, but only eligible up to side pot 1
        2: cards('7h 7d') + board,   # pair of sevens -- worst hand, but the only one eligible for side pot 2
    }

    payouts = award_pots(pots, hands)

    # Seat 1 has the best hand and wins both the main pot and side pot 1
    # (everywhere they're eligible); seat 2 wins side pot 2 uncontested
    # despite having the worst hand overall, because nobody else was
    # eligible for it -- this is the entire point of side pots.
    assert payouts == {1: 150.0 + 140.0, 2: 80.0}
    assert sum(payouts.values()) == 150.0 + 140.0 + 80.0
