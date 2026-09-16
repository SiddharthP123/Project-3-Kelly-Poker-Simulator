import pytest

from backend.models import GameSession, HandAction, HandHistory, HandPlayer, User


_DEFAULT_PLAYERS = [
    {'seat_index': 0, 'is_hero': True, 'hole_cards': 'Ah,Ac', 'folded': False, 'is_winner': True, 'net_result': 10.0},
    {
        'seat_index': 1, 'persona': 'tight-aggressive', 'hole_cards': 'Kh,Kc',
        'folded': False, 'is_winner': False, 'net_result': -5.0,
    },
    {
        'seat_index': 2, 'persona': 'loose-passive', 'hole_cards': 'Qh,Qc',
        'folded': True, 'is_winner': False, 'net_result': -5.0,
    },
]


def _insert_complete_hand(db_session, game_session, button_seat, actions, players=None, board_cards=None):
    """Directly constructs one complete hand's rows (HandHistory,
    HandPlayers, and whatever HandActions the caller wants), bypassing
    the live game engine and its bot decisions entirely.

    Needed specifically for scenarios that are genuinely rare (or need
    exact multi-street control) through the live bot-decision pipeline
    -- see test_three_bet_rate_reflects_reraising_an_existing_preflop_raise
    for the confirmed, structural reason an opponent's real preflop raise
    before hero's turn is hard to hit live: poker/hand_flow.py's
    default_bot_action sizes a persona's raise as a fraction of the
    CURRENT pot, almost always below the legal minimum raise at a
    blinds-only pot, and even KellyOptimalBot (sizing isn't
    pot-fraction-based) needs ~40% equity against a 2-into-3 pot that a
    random 3-4-way hand only averages ~25% for.

    `players`: list of dicts (seat_index, is_hero, persona, hole_cards,
    folded, is_winner, net_result) -- defaults to a 3-seat hero-wins/one
    opponent-folds shape (_DEFAULT_PLAYERS) when the scenario doesn't
    care about the exact player rows, only the action log.
    `actions`: list of (seat_index, street, action, amount) tuples, in
    the order they happened.
    """
    hand = HandHistory(
        game_session_id=game_session.id, hand_number=1,
        hero_hole_cards='Ah,Ac', pot_size=0.0, button_seat=button_seat, street='complete',
        board_cards=board_cards,
    )
    db_session.add(hand)
    db_session.flush()

    for player in (players if players is not None else _DEFAULT_PLAYERS):
        db_session.add(HandPlayer(
            hand_history_id=hand.id,
            seat_index=player['seat_index'],
            is_hero=player.get('is_hero', False),
            persona=player.get('persona'),
            starting_stack=1000.0,
            hole_cards=player.get('hole_cards', 'Kh,Kc'),
            folded=player.get('folded', False),
            is_winner=player.get('is_winner', False),
            net_result=player.get('net_result', 0.0),
        ))

    for seq, (seat_index, street, action, amount) in enumerate(actions):
        db_session.add(HandAction(
            hand_history_id=hand.id, seq=seq, street=street, seat_index=seat_index,
            action=action, amount=amount, pot_size_after=0.0,
        ))

    db_session.commit()
    return hand


def _create_raw_session(db_session, num_opponents=2, starting_bankroll=1000.0):
    """A GameSession row inserted directly (no live API call), for tests
    that build their hand data via _insert_complete_hand rather than
    playing it out through the live engine."""
    user = db_session.query(User).filter_by(email='hero@example.com').first()
    session = GameSession(
        user_id=user.id, starting_bankroll=starting_bankroll, current_bankroll=starting_bankroll,
        bot_persona='placeholder', num_opponents=num_opponents, small_blind=1.0, big_blind=2.0, status='active',
    )
    db_session.add(session)
    db_session.commit()
    return session


def _signup_and_get_headers(client, email):
    response = client.post('/api/auth/signup', json={'email': email, 'password': 'correct-horse-battery'})
    token = response.json()['access_token']
    return {'Authorization': f'Bearer {token}'}


def _create_session(client, headers, num_opponents=1, starting_bankroll=1000.0):
    response = client.post(
        '/api/game/sessions',
        json={'starting_bankroll': starting_bankroll, 'num_opponents': num_opponents},
        headers=headers,
    )
    assert response.status_code == 200
    return response.json()


def _deal(client, headers, session_id, seed=None):
    body = {'seed': seed} if seed is not None else {}
    response = client.post(f'/api/game/sessions/{session_id}/hands/deal', json=body, headers=headers)
    assert response.status_code == 200
    return response.json()


def _act(client, headers, session_id, hand_id, action, raise_to=None):
    body = {'action': action}
    if raise_to is not None:
        body['raise_to'] = raise_to
    return client.post(f'/api/game/sessions/{session_id}/hands/{hand_id}/act', json=body, headers=headers)


def _play_to_completion(client, headers, session_id, hand, action='call'):
    """Same helper pattern as test_game_router.py: real personas decide
    with live, unseeded equity, so a hand can resolve after any number of
    hero decisions."""
    guard = 0
    while hand['street'] != 'complete':
        guard += 1
        assert guard < 20, 'hand did not resolve within 20 actions -- likely a real bug'
        response = _act(client, headers, session_id, hand['id'], action)
        assert response.status_code == 200
        hand = response.json()
    return hand


def _get_stats(client, headers):
    response = client.get('/api/users/me/stats', headers=headers)
    assert response.status_code == 200
    return response.json()


def test_stats_requires_authentication(client):
    response = client.get('/api/users/me/stats')
    assert response.status_code == 401


def test_stats_are_all_zero_with_no_sessions_played(client, auth_headers):
    stats = _get_stats(client, auth_headers)

    assert stats['total_sessions'] == 0
    assert stats['total_hands'] == 0
    assert stats['win_count'] == stats['loss_count'] == stats['split_count'] == stats['fold_count'] == 0
    assert stats['win_rate'] == stats['loss_rate'] == stats['split_rate'] == stats['fold_rate'] == 0.0
    assert stats['cumulative_bankroll_change'] == 0.0
    assert stats['biggest_win'] is None
    assert stats['biggest_loss'] is None
    assert stats['vpip_rate'] == 0.0
    assert stats['aggression_factor'] is None
    assert stats['pfr_rate'] == 0.0
    assert stats['three_bet_rate'] is None
    assert stats['ats_rate'] is None
    assert stats['wtsd_rate'] == 0.0
    assert stats['won_at_showdown_rate'] is None
    assert stats['won_when_saw_flop_rate'] is None
    assert stats['fold_frequency_by_street'] == {
        'preflop': None, 'flop': None, 'turn': None, 'river': None,
    }
    assert stats['aggression_frequency_by_street'] == {
        'preflop': None, 'flop': None, 'turn': None, 'river': None,
    }
    assert stats['hands_won'] == 0
    assert stats['sessions_won'] == 0
    assert stats['bankroll_history'] == []


def test_stats_count_a_session_with_no_hands_played_yet(client, auth_headers):
    _create_session(client, auth_headers, starting_bankroll=500.0)

    stats = _get_stats(client, auth_headers)
    assert stats['total_sessions'] == 1
    assert stats['total_hands'] == 0
    assert stats['cumulative_bankroll_change'] == 0.0
    assert stats['vpip_rate'] == 0.0
    assert stats['aggression_factor'] is None
    assert stats['pfr_rate'] == 0.0
    assert stats['three_bet_rate'] is None
    assert stats['ats_rate'] is None
    assert stats['wtsd_rate'] == 0.0
    assert stats['won_at_showdown_rate'] is None
    assert stats['won_when_saw_flop_rate'] is None
    assert stats['hands_won'] == 0
    assert stats['sessions_won'] == 0
    # A session's own creation already writes an initial BankrollLog row
    # (bankroll_after == starting_bankroll), independent of any hand ever
    # being played -- see test_create_session_writes_starting_bankroll_log.
    assert stats['bankroll_history'] == [{'bankroll_after': 500.0, 'logged_at': stats['bankroll_history'][0]['logged_at']}]


def test_folding_the_only_hand_counts_as_a_fold_not_a_loss(client, auth_headers):
    # num_opponents=2 (3 seats): hero is guaranteed to act first preflop
    # (see the identical reasoning in test_a_pending_unresolved_hand_is_
    # not_counted_yet below) -- heads-up can't guarantee hero ever gets a
    # turn to explicitly fold, since the opponent might fold first.
    session = _create_session(client, auth_headers, num_opponents=2, starting_bankroll=1000.0)
    dealt = _deal(client, auth_headers, session['id'], seed=0)
    assert dealt['street'] != 'complete'
    response = _act(client, auth_headers, session['id'], dealt['id'], 'fold')
    assert response.status_code == 200

    stats = _get_stats(client, auth_headers)
    assert stats['total_hands'] == 1
    assert stats['fold_count'] == 1
    assert stats['loss_count'] == 0
    assert stats['fold_rate'] == 1.0
    # With num_opponents=2 (3 seats), hero is the button and posts no
    # blind -- folding here costs hero exactly nothing (net_result == 0),
    # so cumulative_bankroll_change is 0 and biggest_loss stays None
    # (there's no NEGATIVE net_result in the data, only a zero one).
    assert stats['cumulative_bankroll_change'] == 0.0
    assert stats['biggest_loss'] is None
    assert stats['biggest_win'] is None
    # Folding preflop is the textbook non-voluntary case -- never counted
    # toward VPIP, and contributes no call/raise toward aggression_factor
    # (still None: hero has made zero real calls across any hand so far).
    assert stats['vpip_rate'] == 0.0
    assert stats['aggression_factor'] is None


def test_biggest_win_or_loss_reflects_a_real_nonzero_net_result(client, auth_headers):
    # Calling (not folding) means hero genuinely risks chips -- exactly
    # one of biggest_win/biggest_loss should end up populated with a real
    # nonzero value depending on the outcome, and the other stays None
    # (only one hand was played, so there's nothing on the other side).
    session = _create_session(client, auth_headers, num_opponents=2, starting_bankroll=1000.0)
    dealt = _deal(client, auth_headers, session['id'], seed=1)
    hand = dealt
    guard = 0
    while hand['street'] != 'complete':
        guard += 1
        assert guard < 20
        response = _act(client, auth_headers, session['id'], hand['id'], 'call')
        assert response.status_code == 200
        hand = response.json()

    stats = _get_stats(client, auth_headers)
    assert stats['total_hands'] == 1
    assert stats['fold_count'] == 0

    if stats['win_count'] == 1:
        assert stats['biggest_win'] is not None and stats['biggest_win'] > 0
        assert stats['biggest_loss'] is None
    elif stats['loss_count'] == 1:
        assert stats['biggest_loss'] is not None and stats['biggest_loss'] < 0
        assert stats['biggest_win'] is None
    else:
        # A split pot -- net_result can legitimately be 0 (an even chop)
        # or a genuine nonzero value if stacks/contributions weren't equal.
        assert stats['split_count'] == 1


def test_a_pending_unresolved_hand_is_not_counted_yet(client, auth_headers):
    # num_opponents=2 (3 seats): with button=hero on hand 1, hero is
    # guaranteed to act first preflop (see test_game_router.py's own
    # _create_session for the same reasoning) -- so the freshly-dealt hand
    # is guaranteed to still be pending, not resolved by a bot folding
    # before hero ever gets a turn (which heads-up can't rule out).
    session = _create_session(client, auth_headers, num_opponents=2, starting_bankroll=1000.0)
    dealt = _deal(client, auth_headers, session['id'], seed=0)
    assert dealt['street'] != 'complete'

    stats = _get_stats(client, auth_headers)
    assert stats['total_hands'] == 0


def test_stats_aggregate_across_multiple_sessions(client, auth_headers):
    session_a = _create_session(client, auth_headers, starting_bankroll=1000.0)
    hand_a = _deal(client, auth_headers, session_a['id'], seed=1)
    _play_to_completion(client, auth_headers, session_a['id'], hand_a)

    session_b = _create_session(client, auth_headers, starting_bankroll=1000.0)
    hand_b = _deal(client, auth_headers, session_b['id'], seed=2)
    _play_to_completion(client, auth_headers, session_b['id'], hand_b)

    stats = _get_stats(client, auth_headers)
    assert stats['total_sessions'] == 2
    assert stats['total_hands'] == 2
    assert stats['win_count'] + stats['loss_count'] + stats['split_count'] + stats['fold_count'] == 2
    assert stats['win_rate'] + stats['loss_rate'] + stats['split_rate'] + stats['fold_rate'] == pytest.approx(1.0)

    # cumulative_bankroll_change is the authoritative sum of each session's
    # own persisted (current_bankroll - starting_bankroll), not re-derived
    # from individual hand deltas -- cross-check it matches that directly.
    session_a_after = client.get(f"/api/game/sessions/{session_a['id']}", headers=auth_headers).json()
    session_b_after = client.get(f"/api/game/sessions/{session_b['id']}", headers=auth_headers).json()
    expected_delta = (session_a_after['current_bankroll'] - session_a_after['starting_bankroll']) + (
        session_b_after['current_bankroll'] - session_b_after['starting_bankroll']
    )
    assert stats['cumulative_bankroll_change'] == pytest.approx(expected_delta)


def test_calling_the_only_hand_counts_as_vpip_but_not_aggression(client, auth_headers):
    # num_opponents=2 (3 seats): hero is the button, acting first preflop
    # and facing exactly the live big blind (a real amount > 0) -- same
    # setup as test_folding_the_only_hand_counts_as_a_fold_not_a_loss,
    # just calling instead of folding.
    session = _create_session(client, auth_headers, num_opponents=2, starting_bankroll=1000.0)
    dealt = _deal(client, auth_headers, session['id'], seed=1)
    _play_to_completion(client, auth_headers, session['id'], dealt, action='call')

    stats = _get_stats(client, auth_headers)
    assert stats['total_hands'] == 1
    assert stats['vpip_rate'] == 1.0
    # At least one real call and zero raises -- a defined, non-None ratio.
    assert stats['aggression_factor'] == 0.0
    # Hero's first preflop action was a call, not a raise -- not PFR.
    assert stats['pfr_rate'] == 0.0
    # Hero (button) faced 0 entries preflop -- an ATS opportunity -- but
    # called instead of raising, so the opportunity wasn't taken.
    assert stats['ats_rate'] == 0.0


def test_raising_counts_toward_vpip_and_produces_a_positive_aggression_factor(client, auth_headers):
    # Two separate sessions, not two hands in one session: button_seat
    # rotates by hand_number (poker/hand_flow.py: button_seat = (hand_number
    # - 1) % num_seats), so hero (seat 0) is only guaranteed to be the
    # button -- and thus act first preflop -- on a session's FIRST hand.
    # On a session's second hand, hero would become the big blind and
    # could win an uncontested walk with no decision at all if the other
    # two seats both fold before hero ever acts, leaving
    # legal_action_bounds None. A fresh session per hand keeps every deal
    # at hand_number=1, the same guarantee every other test here relies on.

    # First session/hand: hero calls (contributes to the aggression_factor
    # denominator) -- same shape as the VPIP-only test above.
    calling_session = _create_session(client, auth_headers, num_opponents=2, starting_bankroll=1000.0)
    called_hand = _deal(client, auth_headers, calling_session['id'], seed=1)
    _play_to_completion(client, auth_headers, calling_session['id'], called_hand, action='call')

    # Second session/hand: hero shoves all-in preflop (the numerator) --
    # same pattern as test_game_router.py's multiway side-pot test.
    raising_session = _create_session(client, auth_headers, num_opponents=2, starting_bankroll=1000.0)
    raised_hand = _deal(client, auth_headers, raising_session['id'], seed=2)
    bounds = raised_hand['legal_action_bounds']
    response = _act(
        client, auth_headers, raising_session['id'], raised_hand['id'], 'raise', raise_to=bounds['max_raise_to'],
    )
    assert response.status_code == 200
    hand = response.json()
    guard = 0
    while hand['street'] != 'complete':
        # Hero is all-in and can never be asked to act again -- this
        # branch should be unreachable, but acts as a harmless fallback.
        guard += 1
        assert guard < 20
        response = _act(client, auth_headers, raising_session['id'], hand['id'], 'call')
        assert response.status_code == 200
        hand = response.json()

    stats = _get_stats(client, auth_headers)
    assert stats['total_hands'] == 2
    assert stats['vpip_rate'] == 1.0  # neither hand was folded preflop
    assert stats['aggression_factor'] is not None
    assert stats['aggression_factor'] > 0
    # Exactly one of the two hands was a preflop raise -- both hands had
    # hero as the button facing 0 entries (an ATS opportunity each time),
    # so both rates land on the same 1-of-2 = 0.5.
    assert stats['pfr_rate'] == 0.5
    assert stats['ats_rate'] == 0.5


def test_three_bet_rate_reflects_reraising_an_existing_preflop_raise(client, auth_headers, db_session):
    # See _insert_complete_hand's own docstring for why this scenario is
    # built directly rather than played out through the live API: an
    # opponent's real preflop raise before hero's turn is genuinely rare
    # through the live bot-decision pipeline, confirmed by direct
    # experimentation, not just bad luck worth retrying past.
    session = _create_raw_session(db_session)

    _insert_complete_hand(
        db_session, session, button_seat=1,
        actions=[
            (1, 'preflop', 'post_blind', 1.0),
            (2, 'preflop', 'post_blind', 2.0),
            (1, 'preflop', 'raise_to', 6.0),  # opponent opens for a raise
            (0, 'preflop', 'raise_to', 20.0),  # hero re-raises -- a 3-bet
            (2, 'preflop', 'fold', 0.0),
            (1, 'preflop', 'match', 14.0),
        ],
    )

    stats = _get_stats(client, auth_headers)
    assert stats['total_hands'] == 1
    assert stats['three_bet_rate'] == 1.0


def test_three_bet_rate_is_none_when_hero_never_faced_an_existing_preflop_raise(client, auth_headers, db_session):
    session = _create_raw_session(db_session)

    # Hero's only preflop action just calls the big blind -- nobody
    # raised before hero, so there was no 3-bet opportunity at all.
    _insert_complete_hand(
        db_session, session, button_seat=0,
        actions=[
            (1, 'preflop', 'post_blind', 1.0),
            (2, 'preflop', 'post_blind', 2.0),
            (0, 'preflop', 'match', 2.0),
            (1, 'preflop', 'fold', 0.0),
        ],
    )

    stats = _get_stats(client, auth_headers)
    assert stats['total_hands'] == 1
    assert stats['three_bet_rate'] is None


def test_wtsd_and_won_at_showdown_reflect_a_genuine_multiway_showdown(client, auth_headers, db_session):
    session = _create_raw_session(db_session, num_opponents=2)

    # Hero and opp1 both stay in to the end (a genuine showdown); opp2
    # folded along the way, so only 2 of 3 seats are non-folded.
    _insert_complete_hand(
        db_session, session, button_seat=0,
        players=[
            {'seat_index': 0, 'is_hero': True, 'folded': False, 'is_winner': True, 'net_result': 10.0},
            {'seat_index': 1, 'folded': False, 'is_winner': False, 'net_result': -10.0},
            {'seat_index': 2, 'folded': True, 'is_winner': False, 'net_result': 0.0},
        ],
        actions=[(0, 'preflop', 'match', 2.0)],
    )

    stats = _get_stats(client, auth_headers)
    assert stats['total_hands'] == 1
    assert stats['wtsd_rate'] == 1.0
    assert stats['won_at_showdown_rate'] == 1.0


def test_wtsd_is_zero_and_won_at_showdown_is_none_for_a_fold_out(client, auth_headers, db_session):
    session = _create_raw_session(db_session, num_opponents=2)

    # Everyone but hero folds -- hero wins uncontested, never a showdown.
    _insert_complete_hand(
        db_session, session, button_seat=0,
        players=[
            {'seat_index': 0, 'is_hero': True, 'folded': False, 'is_winner': True, 'net_result': 3.0},
            {'seat_index': 1, 'folded': True, 'is_winner': False, 'net_result': -1.0},
            {'seat_index': 2, 'folded': True, 'is_winner': False, 'net_result': -2.0},
        ],
        actions=[(0, 'preflop', 'raise_to', 6.0)],
    )

    stats = _get_stats(client, auth_headers)
    assert stats['total_hands'] == 1
    assert stats['wtsd_rate'] == 0.0
    assert stats['won_at_showdown_rate'] is None


def test_won_when_saw_flop_excludes_preflop_folds_and_no_flop_hands(client, auth_headers, db_session):
    session = _create_raw_session(db_session, num_opponents=1)

    # Hand A: hero doesn't fold preflop, a flop is dealt, hero wins --
    # counts toward won_when_saw_flop_rate.
    _insert_complete_hand(
        db_session, session, button_seat=0, board_cards='2c,3d,4h',
        players=[
            {'seat_index': 0, 'is_hero': True, 'folded': False, 'is_winner': True, 'net_result': 4.0},
            {'seat_index': 1, 'folded': True, 'is_winner': False, 'net_result': -4.0},
        ],
        actions=[(0, 'preflop', 'match', 2.0)],
    )
    # Hand B: hero folds preflop, even though a flop was dealt for the
    # players who continued -- excluded (hero never saw it).
    _insert_complete_hand(
        db_session, session, button_seat=1, board_cards='5s,6s,7s',
        players=[
            {'seat_index': 0, 'is_hero': True, 'folded': True, 'is_winner': False, 'net_result': -2.0},
            {'seat_index': 1, 'folded': False, 'is_winner': True, 'net_result': 2.0},
        ],
        actions=[(0, 'preflop', 'fold', 0.0)],
    )
    # Hand C: hero doesn't fold preflop, but no flop was ever dealt (a
    # preflop fold-out) -- excluded (there was no flop to see).
    _insert_complete_hand(
        db_session, session, button_seat=0, board_cards=None,
        players=[
            {'seat_index': 0, 'is_hero': True, 'folded': False, 'is_winner': True, 'net_result': 2.0},
            {'seat_index': 1, 'folded': True, 'is_winner': False, 'net_result': -2.0},
        ],
        actions=[(0, 'preflop', 'raise_to', 6.0)],
    )

    stats = _get_stats(client, auth_headers)
    assert stats['total_hands'] == 3
    # Only hand A qualifies, and hero won it.
    assert stats['won_when_saw_flop_rate'] == 1.0


def test_per_street_fold_and_aggression_frequency_reflect_heros_own_decisions(client, auth_headers, db_session):
    session = _create_raw_session(db_session, num_opponents=1)

    # Hero calls preflop, raises the flop, then folds the turn -- never
    # reaches the river at all.
    _insert_complete_hand(
        db_session, session, button_seat=0,
        players=[
            {'seat_index': 0, 'is_hero': True, 'folded': True, 'is_winner': False, 'net_result': -12.0},
            {'seat_index': 1, 'folded': False, 'is_winner': True, 'net_result': 12.0},
        ],
        actions=[
            (0, 'preflop', 'match', 2.0),
            (0, 'flop', 'raise_to', 10.0),
            (0, 'turn', 'fold', 0.0),
        ],
    )

    stats = _get_stats(client, auth_headers)
    assert stats['fold_frequency_by_street'] == {
        'preflop': 0.0, 'flop': 0.0, 'turn': 1.0, 'river': None,
    }
    assert stats['aggression_frequency_by_street'] == {
        'preflop': 0.0, 'flop': 1.0, 'turn': 0.0, 'river': None,
    }


def test_hands_won_counts_wins_and_splits(client, auth_headers, db_session):
    session = _create_raw_session(db_session, num_opponents=2)

    # Hand A: an outright win (the default players shape).
    _insert_complete_hand(db_session, session, button_seat=0, actions=[(0, 'preflop', 'match', 2.0)])
    # Hand B: a split pot -- hero and opp1 both is_winner.
    _insert_complete_hand(
        db_session, session, button_seat=0,
        players=[
            {'seat_index': 0, 'is_hero': True, 'folded': False, 'is_winner': True, 'net_result': 5.0},
            {'seat_index': 1, 'folded': False, 'is_winner': True, 'net_result': 5.0},
            {'seat_index': 2, 'folded': True, 'is_winner': False, 'net_result': -10.0},
        ],
        actions=[(0, 'preflop', 'match', 2.0)],
    )

    stats = _get_stats(client, auth_headers)
    assert stats['total_hands'] == 2
    assert stats['win_count'] == 1
    assert stats['split_count'] == 1
    assert stats['hands_won'] == 2


def test_sessions_won_counts_only_ended_sessions_with_a_profit(client, auth_headers, db_session):
    losing_session = _create_session(client, auth_headers, starting_bankroll=1000.0)
    client.post(f"/api/game/sessions/{losing_session['id']}/end", headers=auth_headers)

    winning_session = _create_session(client, auth_headers, starting_bankroll=1000.0)
    winning_row = db_session.query(GameSession).filter_by(id=winning_session['id']).one()
    winning_row.current_bankroll = 1200.0
    db_session.commit()
    client.post(f"/api/game/sessions/{winning_session['id']}/end", headers=auth_headers)

    # Also profitable right now, but never ended -- shouldn't count yet.
    still_active_session = _create_session(client, auth_headers, starting_bankroll=1000.0)
    active_row = db_session.query(GameSession).filter_by(id=still_active_session['id']).one()
    active_row.current_bankroll = 1500.0
    db_session.commit()

    stats = _get_stats(client, auth_headers)
    assert stats['total_sessions'] == 3
    assert stats['sessions_won'] == 1


def test_bankroll_history_spans_every_session_chronologically(client, auth_headers):
    _create_session(client, auth_headers, starting_bankroll=500.0)
    _create_session(client, auth_headers, starting_bankroll=750.0)

    stats = _get_stats(client, auth_headers)
    assert len(stats['bankroll_history']) >= 2
    bankroll_values = [point['bankroll_after'] for point in stats['bankroll_history']]
    assert 500.0 in bankroll_values
    assert 750.0 in bankroll_values
    # Chronological, matching each session's own creation order.
    assert bankroll_values.index(500.0) < bankroll_values.index(750.0)


def test_stats_are_isolated_per_user(client, auth_headers):
    session = _create_session(client, auth_headers, starting_bankroll=1000.0)
    dealt = _deal(client, auth_headers, session['id'], seed=0)
    _act(client, auth_headers, session['id'], dealt['id'], 'fold')

    other_headers = _signup_and_get_headers(client, 'stats-other@example.com')
    other_stats = _get_stats(client, other_headers)

    assert other_stats['total_sessions'] == 0
    assert other_stats['total_hands'] == 0
