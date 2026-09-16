import pytest

from backend.models import GameSession, HandAction, HandHistory, HandPlayer, User


def _insert_complete_hand(db_session, game_session, button_seat, hero_folded, actions):
    """Directly constructs one complete hand's rows (HandHistory,
    3 HandPlayers, and whatever HandActions the caller wants), bypassing
    the live game engine and its bot decisions entirely.

    Needed specifically for 3-bet% scenarios: an opponent making a real
    preflop RAISE before hero's turn turns out to be genuinely rare
    through the live pipeline, for two structural reasons confirmed by
    direct experimentation, not a bug in this project's own code --
    (1) poker/hand_flow.py's default_bot_action sizes a persona's raise
    as a fraction of the CURRENT pot, which at the blinds-only pot a
    hand starts with is almost always below the legal minimum raise, so
    it silently downgrades to a call; (2) even when a bot's persona
    calls for a raise (e.g. KellyOptimalBot, whose sizing isn't
    pot-fraction-based), the pot odds of a 2-into-3 blinds-only pot need
    roughly 40% equity to justify it, and a 3-4-way random hand's
    average equity is only ~25% -- so most real deals simply don't
    clear the bar. Retrying live deals for this specific condition would
    need a very large attempt budget to be reliable; constructing the
    scenario directly is deterministic and fast instead.

    `actions`: list of (seat_index, street, action, amount) tuples, in
    the order they happened.
    """
    hand = HandHistory(
        game_session_id=game_session.id, hand_number=1,
        hero_hole_cards='Ah,Ac', pot_size=0.0, button_seat=button_seat, street='complete',
    )
    db_session.add(hand)
    db_session.flush()

    db_session.add(HandPlayer(
        hand_history_id=hand.id, seat_index=0, is_hero=True, starting_stack=1000.0,
        hole_cards='Ah,Ac', folded=hero_folded, is_winner=not hero_folded,
        net_result=10.0 if not hero_folded else -5.0,
    ))
    db_session.add(HandPlayer(
        hand_history_id=hand.id, seat_index=1, is_hero=False, persona='tight-aggressive',
        starting_stack=1000.0, hole_cards='Kh,Kc', folded=False, is_winner=False, net_result=-5.0,
    ))
    db_session.add(HandPlayer(
        hand_history_id=hand.id, seat_index=2, is_hero=False, persona='loose-passive',
        starting_stack=1000.0, hole_cards='Qh,Qc', folded=True, is_winner=False, net_result=-5.0,
    ))

    for seq, (seat_index, street, action, amount) in enumerate(actions):
        db_session.add(HandAction(
            hand_history_id=hand.id, seq=seq, street=street, seat_index=seat_index,
            action=action, amount=amount, pot_size_after=0.0,
        ))

    db_session.commit()
    return hand


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
    user = db_session.query(User).filter_by(email='hero@example.com').first()
    session = GameSession(
        user_id=user.id, starting_bankroll=1000.0, current_bankroll=1000.0,
        bot_persona='placeholder', num_opponents=2, small_blind=1.0, big_blind=2.0, status='active',
    )
    db_session.add(session)
    db_session.commit()

    _insert_complete_hand(
        db_session, session, button_seat=1, hero_folded=False,
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
    user = db_session.query(User).filter_by(email='hero@example.com').first()
    session = GameSession(
        user_id=user.id, starting_bankroll=1000.0, current_bankroll=1000.0,
        bot_persona='placeholder', num_opponents=2, small_blind=1.0, big_blind=2.0, status='active',
    )
    db_session.add(session)
    db_session.commit()

    # Hero's only preflop action just calls the big blind -- nobody
    # raised before hero, so there was no 3-bet opportunity at all.
    _insert_complete_hand(
        db_session, session, button_seat=0, hero_folded=False,
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
