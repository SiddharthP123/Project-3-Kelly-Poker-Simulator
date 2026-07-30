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
    assert 'hashed_password' not in body
