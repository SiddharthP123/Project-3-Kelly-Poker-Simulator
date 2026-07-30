import pytest


def test_kelly_from_odds_matches_classic_example(client):
    response = client.post(
        '/api/kelly/from-odds', json={'win_probability': 0.6, 'odds': 1}
    )
    assert response.status_code == 200
    assert response.json()['stake_fraction'] == pytest.approx(0.2)


def test_kelly_from_odds_clips_negative_edge_to_zero(client):
    response = client.post(
        '/api/kelly/from-odds', json={'win_probability': 0.3, 'odds': 1}
    )
    assert response.status_code == 200
    assert response.json()['stake_fraction'] == 0.0


def test_kelly_from_pot_odds_matches_known_example(client):
    response = client.post(
        '/api/kelly/from-pot-odds', json={'equity': 0.6, 'pot_size': 100, 'bet_to_call': 50}
    )
    assert response.status_code == 200
    assert response.json()['stake_fraction'] == pytest.approx(0.4)


def test_kelly_from_pot_odds_rejects_non_positive_bet(client):
    response = client.post(
        '/api/kelly/from-pot-odds', json={'equity': 0.6, 'pot_size': 100, 'bet_to_call': 0}
    )
    assert response.status_code == 422  # gt=0 constraint catches this at the schema layer
