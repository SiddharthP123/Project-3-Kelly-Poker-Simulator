def test_bot_decide_endpoint_tight_aggressive_raises_with_pocket_aces(client):
    response = client.post(
        '/api/bots/decide',
        json={
            'persona': 'tight-aggressive', 'hole_cards': ['Ah', 'Ac'],
            'pot_size': 100, 'bet_to_call': 20, 'num_opponents': 1,
            'num_simulations': 3000, 'seed': 5,
        },
    )
    assert response.status_code == 200
    assert response.json()['action'] == 'raise'


def test_bot_decide_endpoint_kelly_optimal_requires_bankroll(client):
    response = client.post(
        '/api/bots/decide',
        json={
            'persona': 'kelly-optimal', 'hole_cards': ['Ah', 'Ac'],
            'pot_size': 100, 'bet_to_call': 20, 'num_simulations': 500, 'seed': 1,
        },
    )
    assert response.status_code == 400


def test_bot_decide_endpoint_kelly_optimal_with_bankroll(client):
    response = client.post(
        '/api/bots/decide',
        json={
            'persona': 'kelly-optimal', 'hole_cards': ['Ah', 'Ac'],
            'pot_size': 100, 'bet_to_call': 20, 'bankroll': 10_000,
            'num_simulations': 3000, 'seed': 1,
        },
    )
    assert response.status_code == 200
    assert response.json()['action'] in {'call', 'raise'}


def test_bot_decide_endpoint_rejects_unknown_persona(client):
    response = client.post(
        '/api/bots/decide',
        json={
            'persona': 'super-shark', 'hole_cards': ['Ah', 'Ac'],
            'pot_size': 100, 'bet_to_call': 20,
        },
    )
    assert response.status_code == 422
