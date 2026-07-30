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


def test_cannot_access_another_users_session(client, auth_headers):
    session = _create_session(client, auth_headers)
    other_user_headers = _signup_and_get_headers(client, 'other@example.com')

    for method, path in [
        ('get', f"/api/game/sessions/{session['id']}"),
        ('post', f"/api/game/sessions/{session['id']}/hands"),
        ('get', f"/api/game/sessions/{session['id']}/hands"),
        ('get', f"/api/game/sessions/{session['id']}/bankroll-history"),
        ('post', f"/api/game/sessions/{session['id']}/end"),
    ]:
        response = getattr(client, method)(path, headers=other_user_headers)
        assert response.status_code == 404, f'{method.upper()} {path} should 404 for a non-owner'


def test_play_hand_with_fold_leaves_bankroll_unchanged_and_hides_opponent_cards(client, auth_headers):
    # seed=0 deterministically produces a hero fold against these fixed
    # stakes (equity ~0.497, just below the 50% breakeven point).
    session = _create_session(client, auth_headers)
    response = client.post(
        f"/api/game/sessions/{session['id']}/hands", json={'seed': 0}, headers=auth_headers
    )
    assert response.status_code == 200

    hand = response.json()
    assert hand['hero_action'] == 'fold'
    assert hand['hero_bankroll_delta'] == 0.0
    assert hand['winner'] == 'opponent'
    assert hand['board_cards'] is None  # never revealed -- the hand never reached showdown
    assert hand['opponent_hole_cards'] is None

    updated_session = client.get(f"/api/game/sessions/{session['id']}", headers=auth_headers).json()
    assert updated_session['current_bankroll'] == 1000.0


def test_play_hand_with_call_reaches_showdown(client, auth_headers):
    # seed=1 deterministically produces a hero call.
    session = _create_session(client, auth_headers)
    response = client.post(
        f"/api/game/sessions/{session['id']}/hands", json={'seed': 1}, headers=auth_headers
    )
    assert response.status_code == 200

    hand = response.json()
    assert hand['hero_action'] == 'call'
    assert hand['board_cards'] is not None
    assert hand['opponent_hole_cards'] is not None
    assert hand['winner'] in {'hero', 'opponent', 'split'}
    assert hand['equity_at_decision'] == pytest.approx(0.5403, abs=1e-3)


def test_play_hand_with_raise_records_bot_response(client, auth_headers):
    # seed=54 deterministically produces a hero raise.
    session = _create_session(client, auth_headers)
    response = client.post(
        f"/api/game/sessions/{session['id']}/hands", json={'seed': 54}, headers=auth_headers
    )
    assert response.status_code == 200

    hand = response.json()
    assert hand['hero_action'] == 'raise'
    assert hand['bot_action'] in {'fold', 'call', 'raise'}


def test_bankroll_updates_consistently_across_a_hand(client, auth_headers):
    session = _create_session(client, auth_headers, starting_bankroll=1000.0)
    hand = client.post(
        f"/api/game/sessions/{session['id']}/hands", json={'seed': 1}, headers=auth_headers
    ).json()

    updated_session = client.get(f"/api/game/sessions/{session['id']}", headers=auth_headers).json()
    assert updated_session['current_bankroll'] == pytest.approx(1000.0 + hand['hero_bankroll_delta'])

    history = client.get(
        f"/api/game/sessions/{session['id']}/bankroll-history", headers=auth_headers
    ).json()
    assert len(history) == 2  # session-start row + this hand's row
    assert history[-1]['bankroll_after'] == pytest.approx(updated_session['current_bankroll'])


def test_hand_history_lists_hands_in_order(client, auth_headers):
    session = _create_session(client, auth_headers)
    client.post(f"/api/game/sessions/{session['id']}/hands", json={'seed': 0}, headers=auth_headers)
    client.post(f"/api/game/sessions/{session['id']}/hands", json={'seed': 1}, headers=auth_headers)

    hands = client.get(
        f"/api/game/sessions/{session['id']}/hands", headers=auth_headers
    ).json()
    assert [hand['hand_number'] for hand in hands] == [1, 2]


def test_cannot_play_a_hand_in_an_ended_session(client, auth_headers):
    session = _create_session(client, auth_headers)
    end_response = client.post(f"/api/game/sessions/{session['id']}/end", headers=auth_headers)
    assert end_response.status_code == 200
    assert end_response.json()['status'] == 'ended'

    play_response = client.post(f"/api/game/sessions/{session['id']}/hands", headers=auth_headers)
    assert play_response.status_code == 400


def test_create_session_rejects_unknown_persona(client, auth_headers):
    response = client.post(
        '/api/game/sessions',
        json={'starting_bankroll': 1000.0, 'bot_persona': 'super-shark'},
        headers=auth_headers,
    )
    assert response.status_code == 422
