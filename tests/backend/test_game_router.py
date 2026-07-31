import pytest


def _signup_and_get_headers(client, email):
    response = client.post('/api/auth/signup', json={'email': email, 'password': 'correct-horse-battery'})
    token = response.json()['access_token']
    return {'Authorization': f'Bearer {token}'}


def _create_session(client, headers, num_opponents=2, starting_bankroll=1000.0, **overrides):
    # num_opponents=2 (3 seats) by default: with button=hero on hand 1,
    # first_to_act = (button + 3) % 3 = 0 -- hero is guaranteed to act
    # first preflop, deterministically, with no need to seed a bot's
    # actual decision (which real personas don't support -- they use live
    # Monte Carlo equity every time).
    body = {'starting_bankroll': starting_bankroll, 'num_opponents': num_opponents, **overrides}
    response = client.post('/api/game/sessions', json=body, headers=headers)
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


def _hero(hand):
    return next(p for p in hand['players'] if p['is_hero'])


def _play_to_completion(client, headers, session_id, hand, action='call'):
    """Keeps acting (default: call) until the hand reaches 'complete'.
    Real personas decide with live Monte Carlo equity, not a seedable
    stub, so a hand can resolve after any number of hero decisions
    (including zero, if every bot already folded before hero's turn)."""
    guard = 0
    while hand['street'] != 'complete':
        guard += 1
        assert guard < 20, 'hand did not resolve within 20 actions -- likely a real bug'
        response = _act(client, headers, session_id, hand['id'], action)
        assert response.status_code == 200
        hand = response.json()
    return hand


def test_create_session_requires_authentication(client):
    response = client.post('/api/game/sessions', json={'starting_bankroll': 1000.0, 'num_opponents': 1})
    assert response.status_code == 401


def test_create_session_uses_users_own_starting_bankroll_when_not_specified(client, auth_headers):
    response = client.post('/api/game/sessions', json={'num_opponents': 1}, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()['current_bankroll'] == 1000.0


def test_create_session_assigns_one_distinct_persona_per_opponent(client, auth_headers):
    session = _create_session(client, auth_headers, num_opponents=3)
    assert session['num_opponents'] == 3
    assert len(session['opponents']) == 3
    seats = {o['seat_index'] for o in session['opponents']}
    assert seats == {1, 2, 3}
    personas = {o['persona'] for o in session['opponents']}
    assert len(personas) == 3  # no repeats


def test_create_session_writes_starting_bankroll_log(client, auth_headers):
    session = _create_session(client, auth_headers, starting_bankroll=1000.0)
    assert session['current_bankroll'] == 1000.0
    assert session['status'] == 'active'

    history = client.get(
        f"/api/game/sessions/{session['id']}/bankroll-history", headers=auth_headers
    ).json()
    assert len(history) == 1
    assert history[0]['bankroll_after'] == 1000.0


@pytest.mark.parametrize('num_opponents', [0, 5])
def test_create_session_rejects_out_of_range_num_opponents(client, auth_headers, num_opponents):
    response = client.post(
        '/api/game/sessions', json={'starting_bankroll': 1000.0, 'num_opponents': num_opponents},
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_create_session_rejects_big_blind_not_exceeding_small_blind(client, auth_headers):
    response = client.post(
        '/api/game/sessions',
        json={'starting_bankroll': 1000.0, 'num_opponents': 1, 'small_blind': 2.0, 'big_blind': 2.0},
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_get_session_returns_404_for_unknown_id(client, auth_headers):
    response = client.get('/api/game/sessions/999999', headers=auth_headers)
    assert response.status_code == 404


def test_cannot_access_another_users_session_or_hand(client, auth_headers):
    session = _create_session(client, auth_headers)
    hand = _deal(client, auth_headers, session['id'], seed=1)
    other_headers = _signup_and_get_headers(client, 'other@example.com')

    assert client.get(f"/api/game/sessions/{session['id']}", headers=other_headers).status_code == 404
    assert client.post(
        f"/api/game/sessions/{session['id']}/hands/deal", json={}, headers=other_headers
    ).status_code == 404
    assert client.get(
        f"/api/game/sessions/{session['id']}/hands/pending", headers=other_headers
    ).status_code == 404
    assert _act(client, other_headers, session['id'], hand['id'], 'fold').status_code == 404
    assert client.get(f"/api/game/sessions/{session['id']}/hands", headers=other_headers).status_code == 404
    assert client.get(
        f"/api/game/sessions/{session['id']}/hands/{hand['id']}", headers=other_headers
    ).status_code == 404
    assert client.get(
        f"/api/game/sessions/{session['id']}/bankroll-history", headers=other_headers
    ).status_code == 404
    assert client.post(f"/api/game/sessions/{session['id']}/end", headers=other_headers).status_code == 404


def test_deal_returns_heros_cards_and_hides_opponents_cards(client, auth_headers):
    session = _create_session(client, auth_headers)
    hand = _deal(client, auth_headers, session['id'], seed=0)

    assert hand['street'] == 'preflop'
    hero = _hero(hand)
    assert hero['hole_cards'] is not None
    assert len(hero['hole_cards'].split(',')) == 2

    opponents = [p for p in hand['players'] if not p['is_hero']]
    assert len(opponents) == 2
    assert all(o['hole_cards'] is None for o in opponents)  # never dealt to the client
    assert all(o['persona'] is not None for o in opponents)

    # Hero is guaranteed to act first here (see _create_session) -- bounds
    # for hero's own turn should already be present.
    assert hand['legal_action_bounds'] is not None
    assert hand['legal_action_bounds']['can_fold'] is True


def test_dealing_twice_is_idempotent(client, auth_headers):
    session = _create_session(client, auth_headers)
    first = _deal(client, auth_headers, session['id'], seed=1)
    second = _deal(client, auth_headers, session['id'], seed=99)  # different seed, must be ignored

    assert first['id'] == second['id']
    assert _hero(first)['hole_cards'] == _hero(second)['hole_cards']


def test_get_pending_hand_returns_the_dealt_hand(client, auth_headers):
    session = _create_session(client, auth_headers)
    dealt = _deal(client, auth_headers, session['id'], seed=1)

    response = client.get(f"/api/game/sessions/{session['id']}/hands/pending", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()['id'] == dealt['id']


def test_get_pending_hand_404s_when_nothing_pending(client, auth_headers):
    session = _create_session(client, auth_headers)
    response = client.get(f"/api/game/sessions/{session['id']}/hands/pending", headers=auth_headers)
    assert response.status_code == 404


def test_fold_out_never_reveals_any_cards(client, auth_headers):
    # Heads-up specifically: with only 2 seats, any single fold (hero's or
    # the bot's) is necessarily a fold-out -- with 3+ seats a fold just
    # removes one seat and the rest keep playing, so it wouldn't reliably
    # prove this. Real personas decide with live equity, not a seedable
    # stub, so which side folds first isn't something this test can force
    # -- it handles either: if the bot folds before hero's turn, hero
    # already won uncontested and there's nothing left to fold; otherwise
    # hero folds explicitly.
    session = _create_session(client, auth_headers, num_opponents=1)
    hand = _deal(client, auth_headers, session['id'], seed=0)

    if hand['street'] != 'complete':
        response = _act(client, auth_headers, session['id'], hand['id'], 'fold')
        assert response.status_code == 200
        hand = response.json()

    non_folded = [p for p in hand['players'] if not p['folded']]
    if hand['street'] == 'complete' and len(non_folded) < 2:
        # Hero always sees their own cards regardless -- only the
        # OPPONENT's cards are the actual redaction check here.
        assert all(p['hole_cards'] is None for p in hand['players'] if not p['is_hero'])
        assert sum(p['is_winner'] for p in hand['players']) == 1


def test_playing_to_completion_conserves_chips_and_resolves_the_hand(client, auth_headers):
    session = _create_session(client, auth_headers, starting_bankroll=1000.0, num_opponents=3)
    dealt = _deal(client, auth_headers, session['id'], seed=2)
    # 'stack' only counts chips not yet committed to the pot -- pot_size
    # holds the rest until the hand resolves and it's paid back into
    # winners' stacks, so the true invariant mid-hand is stack+pot, not
    # stack alone (stack alone only matches the grand total again once
    # the hand is complete and everything's been paid back out).
    total_before = sum(p['stack'] for p in dealt['players']) + dealt['pot_size']

    hand = _play_to_completion(client, auth_headers, session['id'], dealt)

    assert hand['street'] == 'complete'
    assert hand['winners']  # at least one seat won something
    total_after = sum(p['stack'] for p in hand['players'])
    assert total_after == pytest.approx(total_before, abs=0.01)

    non_folded = [p for p in hand['players'] if not p['folded']]
    if len(non_folded) >= 2:
        # A genuine multi-way showdown -- every non-folded seat's cards
        # (including opponents') are now visible.
        assert all(p['hole_cards'] is not None for p in non_folded)
    else:
        # Everyone but one player folded -- a fold-out, nobody's cards shown.
        assert all(p['hole_cards'] is None for p in hand['players'] if not p['is_hero'])


def test_acting_on_an_already_resolved_hand_returns_400(client, auth_headers):
    session = _create_session(client, auth_headers)
    dealt = _deal(client, auth_headers, session['id'], seed=0)
    _act(client, auth_headers, session['id'], dealt['id'], 'fold')

    second_attempt = _act(client, auth_headers, session['id'], dealt['id'], 'fold')
    assert second_attempt.status_code == 400


def test_acting_on_unknown_hand_returns_404(client, auth_headers):
    session = _create_session(client, auth_headers)
    response = _act(client, auth_headers, session['id'], 999999, 'fold')
    assert response.status_code == 404


def test_act_rejects_raise_to_supplied_without_raise_action(client, auth_headers):
    session = _create_session(client, auth_headers)
    dealt = _deal(client, auth_headers, session['id'], seed=1)
    response = _act(client, auth_headers, session['id'], dealt['id'], 'call', raise_to=200)
    assert response.status_code == 422


def test_act_rejects_raise_action_without_raise_to(client, auth_headers):
    session = _create_session(client, auth_headers)
    dealt = _deal(client, auth_headers, session['id'], seed=1)
    response = _act(client, auth_headers, session['id'], dealt['id'], 'raise')
    assert response.status_code == 422


def test_raise_below_minimum_legal_amount_is_rejected(client, auth_headers):
    session = _create_session(client, auth_headers)
    dealt = _deal(client, auth_headers, session['id'], seed=1)
    bounds = dealt['legal_action_bounds']

    response = _act(
        client, auth_headers, session['id'], dealt['id'], 'raise', raise_to=bounds['min_raise_to'] - 0.5,
    )
    assert response.status_code == 400


def test_raise_within_legal_bounds_is_accepted(client, auth_headers):
    session = _create_session(client, auth_headers)
    dealt = _deal(client, auth_headers, session['id'], seed=1)
    bounds = dealt['legal_action_bounds']

    response = _act(client, auth_headers, session['id'], dealt['id'], 'raise', raise_to=bounds['min_raise_to'])
    assert response.status_code == 200
    hand = response.json()
    assert any(a['action'] == 'raise_to' and a['seat_index'] == _hero(dealt)['seat_index'] for a in hand['actions'])


def test_bankroll_updates_only_once_hand_completes(client, auth_headers):
    session = _create_session(client, auth_headers, starting_bankroll=1000.0)
    dealt = _deal(client, auth_headers, session['id'], seed=2)
    hand = _play_to_completion(client, auth_headers, session['id'], dealt)

    updated_session = client.get(f"/api/game/sessions/{session['id']}", headers=auth_headers).json()
    hero_net_result = _hero(hand)['net_result']
    assert updated_session['current_bankroll'] == pytest.approx(1000.0 + hero_net_result, abs=0.01)

    history = client.get(
        f"/api/game/sessions/{session['id']}/bankroll-history", headers=auth_headers
    ).json()
    assert len(history) == 2  # session-start row + this hand's row
    assert history[-1]['bankroll_after'] == pytest.approx(updated_session['current_bankroll'], abs=0.01)


def test_hand_history_lists_hands_in_order(client, auth_headers):
    session = _create_session(client, auth_headers)
    dealt_1 = _deal(client, auth_headers, session['id'], seed=0)
    _play_to_completion(client, auth_headers, session['id'], dealt_1)
    dealt_2 = _deal(client, auth_headers, session['id'], seed=1)
    _play_to_completion(client, auth_headers, session['id'], dealt_2)

    hands = client.get(f"/api/game/sessions/{session['id']}/hands", headers=auth_headers).json()
    assert [hand['hand_number'] for hand in hands] == [1, 2]
    assert all(hand['street'] == 'complete' for hand in hands)


def test_get_hand_detail_endpoint_returns_full_action_log(client, auth_headers):
    session = _create_session(client, auth_headers)
    dealt = _deal(client, auth_headers, session['id'], seed=0)
    _play_to_completion(client, auth_headers, session['id'], dealt)

    response = client.get(f"/api/game/sessions/{session['id']}/hands/{dealt['id']}", headers=auth_headers)
    assert response.status_code == 200
    detail = response.json()
    assert detail['id'] == dealt['id']
    assert len(detail['actions']) >= 2  # at least both blinds


def test_cannot_deal_a_hand_in_an_ended_session(client, auth_headers):
    session = _create_session(client, auth_headers)
    end_response = client.post(f"/api/game/sessions/{session['id']}/end", headers=auth_headers)
    assert end_response.status_code == 200
    assert end_response.json()['status'] == 'ended'

    deal_response = client.post(
        f"/api/game/sessions/{session['id']}/hands/deal", json={}, headers=auth_headers
    )
    assert deal_response.status_code == 400
