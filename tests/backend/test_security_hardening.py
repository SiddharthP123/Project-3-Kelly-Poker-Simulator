"""Tests for the security-audit fixes: response headers, Retry-After on
429s, per-user rate-limit key derivation, bounded list inputs, and
security-event logging."""

import logging

import pytest
from starlette.requests import Request

from backend.rate_limit import user_id_or_ip_key
from backend.security import create_access_token


def _make_request(headers=None):
    headers = headers or {}
    scope = {
        'type': 'http',
        'headers': [(key.lower().encode(), value.encode()) for key, value in headers.items()],
        'client': ('127.0.0.1', 12345),
    }
    return Request(scope)


def test_security_headers_present_on_every_response(client):
    response = client.get('/health')
    assert response.headers['x-content-type-options'] == 'nosniff'
    assert response.headers['x-frame-options'] == 'DENY'
    assert response.headers['referrer-policy'] == 'strict-origin-when-cross-origin'
    assert response.headers['permissions-policy'] == 'camera=(), microphone=(), geolocation=()'
    assert response.headers['content-security-policy'] == "default-src 'none'"
    assert 'strict-transport-security' in response.headers


def test_429_response_includes_retry_after_header(client):
    # AUTH_LIMIT is 5/15min -- the 6th login attempt in a row exceeds it.
    for _ in range(5):
        client.post('/api/auth/login', json={'email': 'ratelimit@example.com', 'password': 'x'})

    response = client.post('/api/auth/login', json={'email': 'ratelimit@example.com', 'password': 'x'})
    assert response.status_code == 429
    assert 'retry-after' in response.headers
    assert int(response.headers['retry-after']) > 0


def test_user_id_or_ip_key_uses_user_id_for_a_valid_token():
    token = create_access_token(user_id=42)
    request = _make_request({'Authorization': f'Bearer {token}'})
    assert user_id_or_ip_key(request) == 'user:42'


def test_user_id_or_ip_key_falls_back_to_ip_with_no_token():
    request = _make_request()
    assert user_id_or_ip_key(request) == '127.0.0.1'


def test_user_id_or_ip_key_falls_back_to_ip_with_an_invalid_token():
    request = _make_request({'Authorization': 'Bearer not-a-real-token'})
    assert user_id_or_ip_key(request) == '127.0.0.1'


def test_equity_endpoint_rejects_oversized_board(client):
    response = client.post(
        '/api/equity', json={'hole_cards': ['Ah', 'Ac'], 'board': ['2c', '3d', '4h', '5s', '6c', '7d']}
    )
    assert response.status_code == 422


def test_bot_decide_endpoint_rejects_oversized_board(client):
    response = client.post(
        '/api/bots/decide',
        json={
            'persona': 'random', 'hole_cards': ['Ah', 'Ac'],
            'board': ['2c', '3d', '4h', '5s', '6c', '7d'], 'pot_size': 100, 'bet_to_call': 20,
        },
    )
    assert response.status_code == 422


def test_compare_hands_endpoint_rejects_too_many_hands(client):
    board = ['2c', '3d', '4h', '5s', '6c']
    eleven_hands = [['Ah', 'Ad'] + board for _ in range(11)]
    response = client.post('/api/hand-evaluator/compare', json={'hands': eleven_hands})
    assert response.status_code == 422


def test_compare_hands_endpoint_rejects_oversized_single_hand(client):
    oversized_hand = ['2c', '3d', '4h', '5s', '6c', '7d', '8h', '9s']  # 8 cards, max is 7
    response = client.post(
        '/api/hand-evaluator/compare', json={'hands': [oversized_hand, ['Ah', 'Ad', '2c', '3d', '4h']]}
    )
    assert response.status_code == 422


def test_failed_login_is_logged(client, caplog):
    with caplog.at_level(logging.WARNING, logger='backend.routers.auth'):
        client.post('/api/auth/login', json={'email': 'logtest@example.com', 'password': 'wrong'})

    assert any('Failed login attempt' in record.message for record in caplog.records)
    assert not any('wrong' in record.message for record in caplog.records)  # never log the password


def test_rejected_token_is_logged(client, caplog):
    with caplog.at_level(logging.WARNING, logger='backend.security'):
        client.get('/api/auth/me', headers={'Authorization': 'Bearer garbage-token'})

    assert any('Rejected invalid or expired access token' in record.message for record in caplog.records)
    assert not any('garbage-token' in record.message for record in caplog.records)  # never log the token
