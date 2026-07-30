def test_ev_endpoint_recommends_fold_below_breakeven(client):
    response = client.post(
        '/api/ev', json={'equity': 0.1, 'pot_size': 100, 'bet_to_call': 50}
    )
    assert response.status_code == 200
    body = response.json()
    assert body['action'] == 'fold'
    assert body['evs']['fold'] == 0.0


def test_ev_endpoint_recommends_call_above_breakeven(client):
    response = client.post(
        '/api/ev', json={'equity': 0.9, 'pot_size': 100, 'bet_to_call': 50}
    )
    assert response.status_code == 200
    assert response.json()['action'] == 'call'


def test_ev_endpoint_considers_raise_when_supplied(client):
    response = client.post(
        '/api/ev',
        json={
            'equity': 0.8, 'pot_size': 100, 'bet_to_call': 50,
            'raise_amount': 60, 'fold_probability': 0.6,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert set(body['evs'].keys()) == {'fold', 'call', 'raise'}


def test_ev_endpoint_rejects_raise_amount_without_fold_probability(client):
    response = client.post(
        '/api/ev', json={'equity': 0.8, 'pot_size': 100, 'bet_to_call': 50, 'raise_amount': 60}
    )
    assert response.status_code == 400


def test_ev_endpoint_rejects_equity_out_of_range(client):
    response = client.post(
        '/api/ev', json={'equity': 1.5, 'pot_size': 100, 'bet_to_call': 50}
    )
    assert response.status_code == 422
