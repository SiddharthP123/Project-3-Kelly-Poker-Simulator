import pytest

from poker.betting import PlayerStatus
from poker.bots import PERSONA_REGISTRY, Action
from poker.hand_flow import (
    advance_hand,
    apply_hero_action,
    create_hand,
    default_bot_action,
    rebuild_hand_state,
)


def _always_match(state, seat):
    """Stub decide_bot_action: check/call whatever is legal, never raise or
    fold. Used to drive deterministic multi-street playthroughs without
    depending on real equity/persona randomness."""
    bounds = state.betting_round.legal_action_bounds(seat)
    if bounds.can_check or bounds.can_call:
        return 'match', None
    return 'fold', None


def _always_fold(state, seat):
    return 'fold', None


def _total_chips(state):
    return sum(player.stack for player in state.players.values())


def _make_fake_persona(monkeypatch, key, canned_action):
    """Registers a fake persona under `key` whose .decide() always returns
    canned_action regardless of equity/pot/bet -- lets default_bot_action's
    translation logic be tested precisely, without depending on real
    Monte Carlo equity or a real persona's threshold values."""

    class _FakeBot:
        def decide(self, equity, pot_size, bet_to_call, bankroll=None):
            return canned_action

    monkeypatch.setitem(PERSONA_REGISTRY, key, _FakeBot)


# --- create_hand ---------------------------------------------------------


def test_create_hand_deals_two_hole_cards_per_seat():
    state = create_hand(
        num_opponents=2, hero_stack=200, opponent_stacks=[200, 200],
        personas=['random', 'random'], seed=1,
    )

    assert set(state.hole_cards.keys()) == {0, 1, 2}
    for cards in state.hole_cards.values():
        assert len(cards) == 2
    all_cards = [card for cards in state.hole_cards.values() for card in cards]
    assert len(set(all_cards)) == 6  # no duplicates dealt


def test_create_hand_posts_blinds_and_sets_current_bet():
    state = create_hand(
        num_opponents=1, hero_stack=200, opponent_stacks=[200],
        personas=['random'], small_blind=1, big_blind=2, hand_number=1, seed=1,
    )

    # Heads-up (2 seats), uniform rule: button posts BB, non-button posts SB.
    assert state.button_seat == 0
    assert state.players[0].committed_street == 2  # hero/button = BB
    assert state.players[1].committed_street == 1  # SB
    assert state.betting_round.current_bet == 2
    assert _total_chips(state) == 200 + 200 - 3  # 3 already moved into the pot


def test_create_hand_button_rotates_with_hand_number():
    make = lambda hand_number: create_hand(
        num_opponents=1, hero_stack=200, opponent_stacks=[200],
        personas=['random'], hand_number=hand_number, seed=1,
    )

    assert make(1).button_seat == 0
    assert make(2).button_seat == 1
    assert make(3).button_seat == 0  # wraps at num_seats=2


@pytest.mark.parametrize('num_opponents', [0, 5])
def test_create_hand_rejects_out_of_range_opponent_count(num_opponents):
    with pytest.raises(ValueError):
        create_hand(
            num_opponents=num_opponents, hero_stack=200,
            opponent_stacks=[200] * max(num_opponents, 1), personas=['random'] * max(num_opponents, 1),
        )


def test_create_hand_rejects_mismatched_stacks_or_personas_length():
    with pytest.raises(ValueError):
        create_hand(num_opponents=2, hero_stack=200, opponent_stacks=[200], personas=['random', 'random'])

    with pytest.raises(ValueError):
        create_hand(num_opponents=2, hero_stack=200, opponent_stacks=[200, 200], personas=['random'])


# --- advance_hand: full playthroughs with a stub bot ----------------------


def test_full_playthrough_reaches_showdown_and_conserves_chips():
    state = create_hand(
        num_opponents=2, hero_stack=200, opponent_stacks=[200, 200],
        personas=['random', 'random'], small_blind=1, big_blind=2, hand_number=1, seed=42,
    )

    state = advance_hand(state, decide_bot_action=_always_match)
    while state.street != 'complete':
        state = apply_hero_action(state, 'call')
        state = advance_hand(state, decide_bot_action=_always_match)

    assert state.result is not None
    assert len(state.board) == 5
    assert _total_chips(state) == 600  # hero_stack + 2*opponent_stack, nothing created or destroyed
    assert set(state.result['reveal'].keys()) == {0, 1, 2}  # genuine 3-way showdown, all revealed


def test_hero_fold_ends_hand_immediately_without_revealing_cards():
    state = create_hand(
        num_opponents=1, hero_stack=100, opponent_stacks=[100],
        personas=['random'], small_blind=1, big_blind=2, hand_number=1, seed=7,
    )
    state = advance_hand(state, decide_bot_action=_always_match)
    state = apply_hero_action(state, 'fold')
    state = advance_hand(state, decide_bot_action=_always_match)

    assert state.street == 'complete'
    assert state.result['reveal'] == {}
    assert state.result['winners'] == [1]
    assert _total_chips(state) == 200


def test_all_opponents_fold_to_hero_wins_uncontested():
    state = create_hand(
        num_opponents=2, hero_stack=200, opponent_stacks=[200, 200],
        personas=['random', 'random'], small_blind=1, big_blind=2, hand_number=1, seed=3,
    )
    # 3-handed, button=0=hero: hero acts first preflop, so hero must raise
    # before there's anything for the stub bots to fold to.
    state = advance_hand(state, decide_bot_action=_always_fold)
    assert state.betting_round.next_to_act() == state.hero_seat
    state = apply_hero_action(state, 'raise', raise_to=10)
    state = advance_hand(state, decide_bot_action=_always_fold)

    assert state.street == 'complete'
    assert state.result['winners'] == [0]
    assert state.result['reveal'] == {}
    assert _total_chips(state) == 600


def test_side_pot_forms_when_a_short_stack_is_all_in_and_others_keep_betting():
    raised_once = {'done': False}

    def stub(state, seat):
        bounds = state.betting_round.legal_action_bounds(seat)
        if seat == 1 and state.street == 'preflop' and not raised_once['done']:
            raised_once['done'] = True
            return 'raise_to', min(60, bounds.max_raise_to)
        if bounds.can_check or bounds.can_call:
            return 'match', None
        return 'fold', None

    state = create_hand(
        num_opponents=2, hero_stack=15, opponent_stacks=[100, 100],
        personas=['random', 'random'], small_blind=1, big_blind=2, hand_number=1, seed=99,
    )
    state = advance_hand(state, decide_bot_action=stub)
    state = apply_hero_action(state, 'raise', raise_to=15)  # hero's whole stack
    while state.street != 'complete':
        state = advance_hand(state, decide_bot_action=stub)

    assert len(state.result['pots']) == 2
    main_pot, side_pot = state.result['pots']
    assert main_pot.eligible_seats == frozenset({0, 1, 2})
    assert side_pot.eligible_seats == frozenset({1, 2})  # hero (all-in for less) excluded
    assert main_pot.amount + side_pot.amount == pytest.approx(45 + 90)
    assert _total_chips(state) == pytest.approx(215)  # 15 + 100 + 100


def test_advance_hand_is_a_no_op_once_hand_is_complete():
    state = create_hand(
        num_opponents=1, hero_stack=100, opponent_stacks=[100], personas=['random'], seed=1,
    )
    state = advance_hand(state, decide_bot_action=_always_match)
    state = apply_hero_action(state, 'fold')
    state = advance_hand(state, decide_bot_action=_always_match)
    assert state.street == 'complete'

    result_before = state.result
    state = advance_hand(state, decide_bot_action=_always_match)
    assert state.result is result_before  # untouched, no exception


# --- apply_hero_action validation -----------------------------------------


def test_apply_hero_action_raises_if_not_heros_turn():
    state = create_hand(
        num_opponents=1, hero_stack=100, opponent_stacks=[100], personas=['random'], seed=1,
    )
    # Heads-up: seat 1 (SB) acts first preflop, not hero -- hero hasn't been
    # given the turn yet since advance_hand hasn't run.
    with pytest.raises(ValueError):
        apply_hero_action(state, 'call')


def test_apply_hero_action_raises_on_unknown_action():
    state = create_hand(
        num_opponents=1, hero_stack=100, opponent_stacks=[100], personas=['random'], seed=1,
    )
    state = advance_hand(state, decide_bot_action=_always_match)
    with pytest.raises(ValueError):
        apply_hero_action(state, 'all-in-for-the-lulz')


def test_apply_hero_action_raises_if_raise_missing_raise_to():
    state = create_hand(
        num_opponents=1, hero_stack=100, opponent_stacks=[100], personas=['random'], seed=1,
    )
    state = advance_hand(state, decide_bot_action=_always_match)
    with pytest.raises(ValueError):
        apply_hero_action(state, 'raise')


def test_apply_hero_action_raises_once_hand_is_complete():
    state = create_hand(
        num_opponents=1, hero_stack=100, opponent_stacks=[100], personas=['random'], seed=1,
    )
    state = advance_hand(state, decide_bot_action=_always_match)
    state = apply_hero_action(state, 'fold')
    state = advance_hand(state, decide_bot_action=_always_match)

    with pytest.raises(ValueError):
        apply_hero_action(state, 'call')


# --- default_bot_action translation logic ---------------------------------


def test_default_bot_action_checks_when_nothing_to_call_and_bot_would_fold_or_call(monkeypatch):
    _make_fake_persona(monkeypatch, 'fake-fold', Action('fold'))
    state = create_hand(
        num_opponents=1, hero_stack=100, opponent_stacks=[100], personas=['fake-fold'], seed=1,
    )
    # Advance past preflop (blinds committed, one street of betting) to reach
    # a street where the acting seat faces no bet yet.
    state = advance_hand(state, decide_bot_action=_always_match)
    state = apply_hero_action(state, 'call')
    state = advance_hand(state, decide_bot_action=_always_match)

    assert state.street == 'flop'
    action, raise_to = default_bot_action(state, seat=1)
    assert action == 'match'
    assert raise_to is None


def test_default_bot_action_bets_when_nothing_to_call_and_bot_would_raise(monkeypatch):
    _make_fake_persona(monkeypatch, 'fake-raise', Action('raise', 10.0))
    state = create_hand(
        num_opponents=1, hero_stack=100, opponent_stacks=[100], personas=['fake-raise'], seed=1,
    )
    state = advance_hand(state, decide_bot_action=_always_match)
    state = apply_hero_action(state, 'call')
    state = advance_hand(state, decide_bot_action=_always_match)

    assert state.street == 'flop'
    action, raise_to = default_bot_action(state, seat=1)
    assert action == 'raise_to'
    assert raise_to == pytest.approx(10.0)


def test_default_bot_action_folds_when_facing_a_bet_and_bot_folds(monkeypatch):
    _make_fake_persona(monkeypatch, 'fake-fold', Action('fold'))
    state = create_hand(
        num_opponents=1, hero_stack=100, opponent_stacks=[100], personas=['fake-fold'], seed=1,
    )
    # Preflop: seat 1 (SB) faces the BB's forced bet -- a real bet to call.
    action, raise_to = default_bot_action(state, seat=1)
    assert action == 'fold'
    assert raise_to is None


def test_default_bot_action_calls_when_facing_a_bet_and_bot_calls(monkeypatch):
    _make_fake_persona(monkeypatch, 'fake-call', Action('call'))
    state = create_hand(
        num_opponents=1, hero_stack=100, opponent_stacks=[100], personas=['fake-call'], seed=1,
    )
    action, raise_to = default_bot_action(state, seat=1)
    assert action == 'match'
    assert raise_to is None


def test_default_bot_action_treats_undersized_raise_as_a_call(monkeypatch):
    # Facing the big blind (2), a "raise" to only 3 is below the minimum
    # legal raise-to (2 + big_blind = 4) -- should collapse to a call.
    _make_fake_persona(monkeypatch, 'fake-small-raise', Action('raise', 3.0))
    state = create_hand(
        num_opponents=1, hero_stack=100, opponent_stacks=[100],
        personas=['fake-small-raise'], big_blind=2, seed=1,
    )
    action, raise_to = default_bot_action(state, seat=1)
    assert action == 'match'
    assert raise_to is None


def test_default_bot_action_caps_an_oversized_raise_at_the_stack():
    class _AllInBot:
        def decide(self, equity, pot_size, bet_to_call, bankroll=None):
            return Action('raise', 10_000.0)

    import poker.bots as bots_module
    original = dict(bots_module.PERSONA_REGISTRY)
    bots_module.PERSONA_REGISTRY['fake-huge-raise'] = _AllInBot
    try:
        state = create_hand(
            num_opponents=1, hero_stack=100, opponent_stacks=[50],
            personas=['fake-huge-raise'], big_blind=2, seed=1,
        )
        action, raise_to = default_bot_action(state, seat=1)
        assert action == 'raise_to'
        assert raise_to == pytest.approx(50.0)  # seat 1's whole stack
    finally:
        bots_module.PERSONA_REGISTRY.clear()
        bots_module.PERSONA_REGISTRY.update(original)


# --- integration with real personas (no stub) -----------------------------


@pytest.mark.parametrize('seed', [1, 2, 3, 4, 5])
def test_full_playthrough_with_real_personas_conserves_chips(seed):
    state = create_hand(
        num_opponents=3, hero_stack=150, opponent_stacks=[80, 120, 200],
        personas=['tight-aggressive', 'loose-passive', 'kelly-optimal'],
        small_blind=1, big_blind=2, hand_number=1, seed=seed,
    )
    total = 150 + 80 + 120 + 200

    state = advance_hand(state)  # real default_bot_action, no stub
    while state.street != 'complete':
        state = apply_hero_action(state, 'call')
        state = advance_hand(state)

    assert state.result is not None
    assert _total_chips(state) == pytest.approx(total)
    assert sum(state.result['payouts'].values()) > 0


# --- rebuild_hand_state ----------------------------------------------------


def _extract_persisted_data(state, starting_stacks):
    """Mimics exactly what a DB layer would have stored so far -- one row
    per seat (its STARTING stack, not its current one) and the action log
    in the plain {seq, street, seat, action, amount} shape a real
    HandAction row would round-trip through."""
    seat_data = [
        {
            'seat': seat, 'stack': starting_stacks[seat],
            'persona': state.personas.get(seat), 'hole_cards': state.hole_cards[seat],
        }
        for seat in sorted(state.players.keys())
    ]
    action_log = [
        {'seq': i, 'street': a.street, 'seat': a.seat, 'action': a.action, 'amount': a.amount}
        for i, a in enumerate(state.action_log)
    ]
    return seat_data, action_log


def test_rebuild_hand_state_matches_a_freshly_dealt_hand_before_any_action():
    original = create_hand(
        num_opponents=1, hero_stack=200, opponent_stacks=[200],
        personas=['random'], small_blind=1, big_blind=2, hand_number=1, seed=5,
    )
    seat_data, action_log = _extract_persisted_data(original, starting_stacks={0: 200, 1: 200})

    rebuilt = rebuild_hand_state(
        hero_seat=0, button_seat=original.button_seat, small_blind=1, big_blind=2,
        hand_number=1, seat_data=seat_data, full_board=original.full_board, action_log=action_log,
    )

    assert rebuilt.street == original.street == 'preflop'
    assert rebuilt.betting_round.current_bet == original.betting_round.current_bet
    assert rebuilt.betting_round.next_to_act() == original.betting_round.next_to_act()
    for seat in original.players:
        assert rebuilt.players[seat].stack == original.players[seat].stack
        assert rebuilt.players[seat].committed_street == original.players[seat].committed_street
        assert rebuilt.players[seat].committed_total == original.players[seat].committed_total
    assert rebuilt.hole_cards == original.hole_cards
    assert rebuilt.board == original.board


def test_rebuild_hand_state_resumes_mid_hand_to_an_identical_showdown():
    starting_stacks = {0: 200, 1: 200, 2: 200}

    def build_and_play_to_flop():
        state = create_hand(
            num_opponents=2, hero_stack=200, opponent_stacks=[200, 200],
            personas=['random', 'random'], small_blind=1, big_blind=2, hand_number=1, seed=42,
        )
        state = advance_hand(state, decide_bot_action=_always_match)
        state = apply_hero_action(state, 'call')
        state = advance_hand(state, decide_bot_action=_always_match)
        return state

    # Reference: keep playing the same, never-interrupted state to a finish.
    reference = build_and_play_to_flop()
    while reference.street != 'complete':
        reference = apply_hero_action(reference, 'call')
        reference = advance_hand(reference, decide_bot_action=_always_match)

    # Now redo it, but "pause" at the exact same midpoint (flop, hero's
    # turn), extract what a DB would have persisted by then, rebuild a
    # fresh HandState from only that data, and resume from the rebuild.
    paused = build_and_play_to_flop()
    seat_data, action_log = _extract_persisted_data(paused, starting_stacks)
    resumed = rebuild_hand_state(
        hero_seat=0, button_seat=paused.button_seat, small_blind=1, big_blind=2,
        hand_number=1, seat_data=seat_data, full_board=paused.full_board, action_log=action_log,
    )
    while resumed.street != 'complete':
        resumed = apply_hero_action(resumed, 'call')
        resumed = advance_hand(resumed, decide_bot_action=_always_match)

    assert resumed.result == reference.result
    assert {s: p.stack for s, p in resumed.players.items()} == {
        s: p.stack for s, p in reference.players.items()
    }


def test_rebuild_hand_state_reconstructs_across_a_street_boundary_with_no_actions_on_it():
    # Force an all-in preflop so flop/turn/river close instantly with zero
    # recorded actions on them -- proves the replay's street-transition
    # loop (_advance_street called in a `while`, not just once) correctly
    # cascades through streets a persisted action log can legitimately skip.
    def stub_shove_then_call(state, seat):
        bounds = state.betting_round.legal_action_bounds(seat)
        if state.street == 'preflop' and bounds.can_raise:
            return 'raise_to', bounds.max_raise_to
        if bounds.can_check or bounds.can_call:
            return 'match', None
        return 'fold', None

    original = create_hand(
        num_opponents=1, hero_stack=20, opponent_stacks=[20],
        personas=['random'], small_blind=1, big_blind=2, hand_number=1, seed=11,
    )
    original = advance_hand(original, decide_bot_action=stub_shove_then_call)
    if original.street != 'complete':
        # Hero's remaining stack exactly covers the call -- there's no
        # legal "raise" left once it only matches, not exceeds, the bet.
        original = apply_hero_action(original, 'call')
        original = advance_hand(original, decide_bot_action=stub_shove_then_call)
    assert original.street == 'complete'  # both all-in preflop -> instant showdown

    seat_data, action_log = _extract_persisted_data(original, starting_stacks={0: 20, 1: 20})
    rebuilt = rebuild_hand_state(
        hero_seat=0, button_seat=original.button_seat, small_blind=1, big_blind=2,
        hand_number=1, seat_data=seat_data, full_board=original.full_board, action_log=action_log,
    )

    # The persisted log only ever covers 'preflop' -- rebuild_hand_state
    # itself doesn't resolve the showdown (that's advance_hand's job on
    # whatever the caller does next), so it should stop exactly there.
    assert rebuilt.street == 'preflop'
    assert rebuilt.board == []
