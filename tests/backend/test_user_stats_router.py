import pytest


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
    assert stats['bankroll_history'] == []


def test_stats_count_a_session_with_no_hands_played_yet(client, auth_headers):
    _create_session(client, auth_headers, starting_bankroll=500.0)

    stats = _get_stats(client, auth_headers)
    assert stats['total_sessions'] == 1
    assert stats['total_hands'] == 0
    assert stats['cumulative_bankroll_change'] == 0.0
    assert stats['vpip_rate'] == 0.0
    assert stats['aggression_factor'] is None
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


def test_raising_counts_toward_vpip_and_produces_a_positive_aggression_factor(client, auth_headers):
    session = _create_session(client, auth_headers, num_opponents=2, starting_bankroll=1000.0)

    # First hand: hero calls (contributes to the aggression_factor
    # denominator) -- same shape as the VPIP-only test above.
    called_hand = _deal(client, auth_headers, session['id'], seed=1)
    _play_to_completion(client, auth_headers, session['id'], called_hand, action='call')

    # Second hand: hero shoves all-in preflop (the numerator) -- same
    # pattern as test_game_router.py's multiway side-pot test.
    raised_hand = _deal(client, auth_headers, session['id'], seed=2)
    bounds = raised_hand['legal_action_bounds']
    response = _act(
        client, auth_headers, session['id'], raised_hand['id'], 'raise', raise_to=bounds['max_raise_to'],
    )
    assert response.status_code == 200
    hand = response.json()
    guard = 0
    while hand['street'] != 'complete':
        # Hero is all-in and can never be asked to act again -- this
        # branch should be unreachable, but acts as a harmless fallback.
        guard += 1
        assert guard < 20
        response = _act(client, auth_headers, session['id'], hand['id'], 'call')
        assert response.status_code == 200
        hand = response.json()

    stats = _get_stats(client, auth_headers)
    assert stats['total_hands'] == 2
    assert stats['vpip_rate'] == 1.0  # neither hand was folded preflop
    assert stats['aggression_factor'] is not None
    assert stats['aggression_factor'] > 0


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
