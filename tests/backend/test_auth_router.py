def test_signup_returns_an_access_token(client):
    response = client.post(
        '/api/auth/signup', json={'email': 'new@example.com', 'password': 'correct-horse'}
    )
    assert response.status_code == 200
    body = response.json()
    assert body['token_type'] == 'bearer'
    assert isinstance(body['access_token'], str) and len(body['access_token']) > 0


def test_signup_rejects_duplicate_email(client):
    client.post('/api/auth/signup', json={'email': 'dup@example.com', 'password': 'correct-horse'})
    response = client.post('/api/auth/signup', json={'email': 'dup@example.com', 'password': 'another-pw'})
    assert response.status_code == 409


def test_signup_rejects_short_password(client):
    response = client.post('/api/auth/signup', json={'email': 'short@example.com', 'password': 'abc'})
    assert response.status_code == 422


def test_signup_rejects_invalid_email(client):
    response = client.post('/api/auth/signup', json={'email': 'not-an-email', 'password': 'correct-horse'})
    assert response.status_code == 422


def test_login_succeeds_with_correct_credentials(client):
    client.post('/api/auth/signup', json={'email': 'login@example.com', 'password': 'correct-horse'})
    response = client.post('/api/auth/login', json={'email': 'login@example.com', 'password': 'correct-horse'})
    assert response.status_code == 200
    assert 'access_token' in response.json()


def test_login_fails_with_wrong_password(client):
    client.post('/api/auth/signup', json={'email': 'wrongpw@example.com', 'password': 'correct-horse'})
    response = client.post('/api/auth/login', json={'email': 'wrongpw@example.com', 'password': 'nope'})
    assert response.status_code == 401


def test_login_fails_with_unknown_email_using_same_generic_message(client):
    known_wrong = client.post(
        '/api/auth/login', json={'email': 'unknown-entirely@example.com', 'password': 'whatever'}
    )
    client.post('/api/auth/signup', json={'email': 'exists@example.com', 'password': 'correct-horse'})
    wrong_password = client.post('/api/auth/login', json={'email': 'exists@example.com', 'password': 'wrong'})

    assert known_wrong.status_code == wrong_password.status_code == 401
    assert known_wrong.json()['detail'] == wrong_password.json()['detail']


def test_me_requires_a_token(client):
    response = client.get('/api/auth/me')
    assert response.status_code == 401  # HTTPBearer rejects a missing Authorization header


def test_me_rejects_an_invalid_token(client):
    response = client.get('/api/auth/me', headers={'Authorization': 'Bearer not-a-real-token'})
    assert response.status_code == 401


def test_me_returns_the_authenticated_user(client):
    signup = client.post(
        '/api/auth/signup',
        json={'email': 'me@example.com', 'password': 'correct-horse', 'display_name': 'Sid'},
    )
    token = signup.json()['access_token']

    response = client.get('/api/auth/me', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    body = response.json()
    assert body['email'] == 'me@example.com'
    assert body['display_name'] == 'Sid'
    assert body['bio'] is None
    assert body['avatar_url'] is None
    assert 'hashed_password' not in body


def test_update_me_requires_a_token(client):
    response = client.patch('/api/auth/me', json={'display_name': 'New Name'})
    assert response.status_code == 401


def test_update_me_persists_display_name_bio_and_avatar_url(client):
    signup = client.post('/api/auth/signup', json={'email': 'profile@example.com', 'password': 'correct-horse'})
    token = signup.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}

    response = client.patch(
        '/api/auth/me',
        headers=headers,
        json={
            'display_name': 'New Name',
            'bio': 'I like poker and the Kelly Criterion.',
            'avatar_url': 'https://example.com/avatar.png',
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body['display_name'] == 'New Name'
    assert body['bio'] == 'I like poker and the Kelly Criterion.'
    assert body['avatar_url'] == 'https://example.com/avatar.png'

    # Persisted, not just echoed back -- a fresh GET sees the same values.
    refetched = client.get('/api/auth/me', headers=headers)
    assert refetched.json()['display_name'] == 'New Name'
    assert refetched.json()['bio'] == 'I like poker and the Kelly Criterion.'


def test_update_me_treats_blank_strings_as_clearing_the_field(client):
    signup = client.post(
        '/api/auth/signup',
        json={'email': 'clear@example.com', 'password': 'correct-horse', 'display_name': 'Sid'},
    )
    token = signup.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    client.patch('/api/auth/me', headers=headers, json={'bio': 'temporary bio'})

    response = client.patch('/api/auth/me', headers=headers, json={'display_name': '  ', 'bio': ''})
    assert response.status_code == 200
    body = response.json()
    assert body['display_name'] is None
    assert body['bio'] is None


def test_update_me_rejects_an_over_length_bio(client):
    signup = client.post('/api/auth/signup', json={'email': 'longbio@example.com', 'password': 'correct-horse'})
    token = signup.json()['access_token']

    response = client.patch(
        '/api/auth/me', headers={'Authorization': f'Bearer {token}'}, json={'bio': 'x' * 501},
    )
    assert response.status_code == 422


def test_update_me_rejects_unknown_fields(client):
    signup = client.post('/api/auth/signup', json={'email': 'strict@example.com', 'password': 'correct-horse'})
    token = signup.json()['access_token']

    response = client.patch(
        '/api/auth/me', headers={'Authorization': f'Bearer {token}'}, json={'email': 'new@example.com'},
    )
    assert response.status_code == 422
