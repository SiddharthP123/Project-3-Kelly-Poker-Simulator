def test_best_hand_endpoint_finds_a_flush_in_seven_cards(client):
    response = client.post(
        '/api/hand-evaluator/best-hand',
        json={'cards': ['Ah', 'Ad', '2h', '5h', '9h', 'Jh', 'Qd']},
    )
    assert response.status_code == 200
    body = response.json()
    assert body['category'] == 'Flush'
    assert len(body['best_five']) == 5
    assert all(card.endswith('h') for card in body['best_five'])


def test_best_hand_endpoint_rejects_wrong_card_count(client):
    response = client.post('/api/hand-evaluator/best-hand', json={'cards': ['Ah', 'Kh', 'Qh', 'Jh']})
    assert response.status_code == 422  # min_length=5 constraint


def test_compare_hands_endpoint_finds_single_winner(client):
    board = ['2c', '5d', '9s', 'Jh', '3h']
    response = client.post(
        '/api/hand-evaluator/compare',
        json={'hands': [['Ah', 'Ad'] + board, ['Kh', 'Kd'] + board]},
    )
    assert response.status_code == 200
    assert response.json()['winners'] == [0]


def test_compare_hands_endpoint_finds_split_pot(client):
    board = ['5h', '6d', '7c', '8s', '9h']
    response = client.post(
        '/api/hand-evaluator/compare',
        json={'hands': [['2c', '3d'] + board, ['2h', '3s'] + board]},
    )
    assert response.status_code == 200
    assert response.json()['winners'] == [0, 1]
