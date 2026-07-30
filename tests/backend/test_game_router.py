import pytest


def _signup_and_get_headers(client, email):
    response = client.post('/api/auth/signup', json={'email': email, 'password': 'correct-horse-battery'})
    token = response.json()['access_token']
    return {'Authorization': f'Bearer {token}'}


def _create_session(client, headers, bot_persona='random', starting_bankroll=1000.0):
    response = client.post(
        '/api/game/sessions',
        json={'starting_bankroll': starting_bankroll, 'bot_persona': bot_persona},
        headers=headers,
    )
    assert response.status_code == 200
    return response.json()


def _deal(client, headers, session_id, seed=None):
    body = {'seed': seed} if seed is not None else {}
    response = client.post(f'/api/game/sessions/{session_id}/hands/deal', json=body, headers=headers)
    assert response.status_code == 200
    return response.json()


def _act(client, headers, session_id, hand_id, action, raise_amount=None, seed=None):
    body = {'action': action}
    if raise_amount is not None:
        body['raise_amount'] = raise_amount
    if seed is not None:
        body['seed'] = seed
    return client.post(f'/api/game/sessions/{session_id}/hands/{hand_id}/act', json=body, headers=headers)


def test_create_session_requires_authentication(client):
    response = client.post('/api/game/sessions', json={'starting_bankroll': 1000.0, 'bot_persona': 'random'})
    assert response.status_code == 401


def test_create_session_uses_users_own_starting_bankroll_when_not_specified(client, auth_headers):
    # No starting_bankroll in the request -> falls back to the User row's
    # own default (1000.0, set at signup), which is the first real use of
    # that field.
    response = client.post(
        '/api/game/sessions', json={'bot_persona': 'random'}, headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()['current_bankroll'] == 1000.0


def test_create_session_writes_starting_bankroll_log(client, auth_headers):
    session = _create_session(client, auth_headers, starting_bankroll=1000.0)
    assert session['current_bankroll'] == 1000.0
    assert session['status'] == 'active'

    history = client.get(
        f"/api/game/sessions/{session['id']}/bankroll-history", headers=auth_headers
    ).json()
    assert len(history) == 1
    assert history[0]['bankroll_after'] == 1000.0


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
        f"/api/game/sessions/{session['id']}/bankroll-history", headers=other_headers
    ).status_code == 404
    assert client.post(f"/api/game/sessions/{session['id']}/end", headers=other_headers).status_code == 404


def test_deal_returns_a_pending_hand_with_no_outcome_yet(client, auth_headers):
    session = _create_session(client, auth_headers)
    # seed=0 deterministically produces equity ~0.497, just below the 50%
    # breakeven point for these fixed stakes.
    dealt = _deal(client, auth_headers, session['id'], seed=0)

    assert dealt['hero_action'] is None
    assert dealt['hero_bankroll_delta'] is None
    assert dealt['winner'] is None
    assert dealt['board_cards'] is None
    assert dealt['opponent_hole_cards'] is None
    assert dealt['equity_at_decision'] == pytest.approx(0.497, abs=1e-3)
    assert dealt['bet_to_call'] == 100.0


def test_dealing_twice_is_idempotent(client, auth_headers):
    session = _create_session(client, auth_headers)
    first = _deal(client, auth_headers, session['id'], seed=1)
    second = _deal(client, auth_headers, session['id'], seed=99)  # different seed, must be ignored

    assert first['id'] == second['id']
    assert first['hero_hole_cards'] == second['hero_hole_cards']


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


def test_fold_leaves_bankroll_unchanged_and_hides_opponent_cards(client, auth_headers):
    session = _create_session(client, auth_headers)
    dealt = _deal(client, auth_headers, session['id'], seed=0)

    response = _act(client, auth_headers, session['id'], dealt['id'], 'fold')
    assert response.status_code == 200

    hand = response.json()
    assert hand['hero_action'] == 'fold'
    assert hand['hero_bankroll_delta'] == 0.0
    assert hand['winner'] == 'opponent'
    assert hand['board_cards'] is None  # never revealed -- the hand never reached showdown
    assert hand['opponent_hole_cards'] is None

    updated_session = client.get(f"/api/game/sessions/{session['id']}", headers=auth_headers).json()
    assert updated_session['current_bankroll'] == 1000.0


def test_call_reaches_showdown(client, auth_headers):
    session = _create_session(client, auth_headers)
    # seed=1 -> equity ~0.5403, above breakeven.
    dealt = _deal(client, auth_headers, session['id'], seed=1)
    assert dealt['equity_at_decision'] == pytest.approx(0.5403, abs=1e-3)

    response = _act(client, auth_headers, session['id'], dealt['id'], 'call')
    assert response.status_code == 200

    hand = response.json()
    assert hand['hero_action'] == 'call'
    assert hand['board_cards'] is not None
    assert hand['opponent_hole_cards'] is not None
    assert hand['winner'] in {'hero', 'opponent', 'split'}


def test_raise_records_opponents_response(client, auth_headers):
    session = _create_session(client, auth_headers)
    dealt = _deal(client, auth_headers, session['id'], seed=54)

    response = _act(client, auth_headers, session['id'], dealt['id'], 'raise', raise_amount=200)
    assert response.status_code == 200

    hand = response.json()
    assert hand['hero_action'] == 'raise'
    assert hand['bot_action'] in {'fold', 'call', 'raise'}


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


def test_raise_at_or_below_bet_to_call_is_rejected(client, auth_headers):
    session = _create_session(client, auth_headers)
    dealt = _deal(client, auth_headers, session['id'], seed=54)
    response = _act(client, auth_headers, session['id'], dealt['id'], 'raise', raise_amount=100)
    assert response.status_code == 400


def test_raise_exceeding_bankroll_is_rejected(client, auth_headers):
    session = _create_session(client, auth_headers, starting_bankroll=150.0)
    dealt = _deal(client, auth_headers, session['id'], seed=54)
    response = _act(client, auth_headers, session['id'], dealt['id'], 'raise', raise_amount=500)
    assert response.status_code == 400


def test_act_rejects_raise_amount_supplied_without_raise_action(client, auth_headers):
    session = _create_session(client, auth_headers)
    dealt = _deal(client, auth_headers, session['id'], seed=1)
    response = _act(client, auth_headers, session['id'], dealt['id'], 'call', raise_amount=200)
    assert response.status_code == 422


def test_act_rejects_raise_action_without_raise_amount(client, auth_headers):
    session = _create_session(client, auth_headers)
    dealt = _deal(client, auth_headers, session['id'], seed=54)
    response = _act(client, auth_headers, session['id'], dealt['id'], 'raise')
    assert response.status_code == 422


def test_bankroll_updates_consistently_across_a_hand(client, auth_headers):
    session = _create_session(client, auth_headers, starting_bankroll=1000.0)
    dealt = _deal(client, auth_headers, session['id'], seed=1)
    hand = _act(client, auth_headers, session['id'], dealt['id'], 'call').json()

    updated_session = client.get(f"/api/game/sessions/{session['id']}", headers=auth_headers).json()
    assert updated_session['current_bankroll'] == pytest.approx(1000.0 + hand['hero_bankroll_delta'])

    history = client.get(
        f"/api/game/sessions/{session['id']}/bankroll-history", headers=auth_headers
    ).json()
    assert len(history) == 2  # session-start row + this hand's row
    assert history[-1]['bankroll_after'] == pytest.approx(updated_session['current_bankroll'])


def test_hand_history_lists_hands_in_order(client, auth_headers):
    session = _create_session(client, auth_headers)
    dealt_1 = _deal(client, auth_headers, session['id'], seed=0)
    _act(client, auth_headers, session['id'], dealt_1['id'], 'fold')
    dealt_2 = _deal(client, auth_headers, session['id'], seed=1)
    _act(client, auth_headers, session['id'], dealt_2['id'], 'call')

    hands = client.get(f"/api/game/sessions/{session['id']}/hands", headers=auth_headers).json()
    assert [hand['hand_number'] for hand in hands] == [1, 2]
    assert all(hand['bet_to_call'] == 100.0 for hand in hands)


def test_cannot_deal_a_hand_in_an_ended_session(client, auth_headers):
    session = _create_session(client, auth_headers)
    end_response = client.post(f"/api/game/sessions/{session['id']}/end", headers=auth_headers)
    assert end_response.status_code == 200
    assert end_response.json()['status'] == 'ended'

    deal_response = client.post(
        f"/api/game/sessions/{session['id']}/hands/deal", json={}, headers=auth_headers
    )
    assert deal_response.status_code == 400


def test_create_session_rejects_unknown_persona(client, auth_headers):
    response = client.post(
        '/api/game/sessions',
        json={'starting_bankroll': 1000.0, 'bot_persona': 'super-shark'},
        headers=auth_headers,
    )
    assert response.status_code == 422
