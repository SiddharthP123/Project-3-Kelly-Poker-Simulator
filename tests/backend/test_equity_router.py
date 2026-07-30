def test_equity_endpoint_returns_expected_shape(client):
    response = client.post(
        '/api/equity',
        json={'hole_cards': ['Ah', 'Ac'], 'num_opponents': 1, 'num_simulations': 2000, 'seed': 1},
    )
    assert response.status_code == 200

    body = response.json()
    assert set(body.keys()) == {'win', 'tie', 'lose', 'equity'}
    assert 0.75 < body['win'] < 0.92  # AA heads-up benchmark, same band as Part 3's test


def test_equity_endpoint_accepts_a_board(client):
    response = client.post(
        '/api/equity',
        json={
            'hole_cards': ['Ah', 'Kh'],
            'board': ['Qh', 'Jh', 'Th'],
            'num_opponents': 2,
            'num_simulations': 500,
            'seed': 2,
        },
    )
    assert response.status_code == 200
    assert response.json()['equity'] == 1.0  # royal flush already made, can't lose or tie


def test_equity_endpoint_rejects_malformed_card(client):
    response = client.post('/api/equity', json={'hole_cards': ['Zx', 'Ac']})
    assert response.status_code == 422


def test_equity_endpoint_rejects_wrong_hole_card_count(client):
    response = client.post('/api/equity', json={'hole_cards': ['Ah']})
    assert response.status_code == 422


def test_equity_endpoint_rejects_invalid_board_length(client):
    response = client.post('/api/equity', json={'hole_cards': ['Ah', 'Ac'], 'board': ['2c', '3d']})
    assert response.status_code == 400


def test_equity_endpoint_rejects_unexpected_fields(client):
    response = client.post(
        '/api/equity', json={'hole_cards': ['Ah', 'Ac'], 'not_a_real_field': 123}
    )
    assert response.status_code == 422


def test_equity_endpoint_rejects_excessive_simulations(client):
    response = client.post(
        '/api/equity', json={'hole_cards': ['Ah', 'Ac'], 'num_simulations': 1_000_000}
    )
    assert response.status_code == 422
