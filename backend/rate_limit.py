"""Shared rate limiter instance.

Kept in its own module (rather than defined in main.py) so router modules
can `from backend.rate_limit import limiter` and apply `@limiter.limit(...)`
without a circular import back to main.py, which is what wires this same
instance into the FastAPI app via `app.state.limiter`.
"""

import jwt
from slowapi import Limiter
from slowapi.util import get_remote_address

from backend.config import settings

# headers_enabled=True is what makes a 429 response actually include
# Retry-After / X-RateLimit-* headers -- without it, slowapi's handler
# silently skips adding them, leaving a client with no idea when to retry.
limiter = Limiter(key_func=get_remote_address, headers_enabled=True)

# Calculator endpoints are POST but compute-only (no DB writes) -- treated
# as "reads" per the standing rate-limit policy. Game endpoints that
# persist to the DB use WRITES_LIMIT instead. Auth endpoints get a much
# tighter bucket -- they're the classic brute-force/credential-stuffing
# target, so 5/15min matches the project's standing security policy for
# auth endpoints specifically (distinct from the general read/write split).
READS_LIMIT = '100/15minute'
WRITES_LIMIT = '50/15minute'
AUTH_LIMIT = '5/15minute'

# Applied ON TOP OF (not instead of) the IP-based limits above, on the
# authenticated /api/game/sessions/* endpoints only. This protects against
# a single compromised/shared token being used to make excessive requests
# across many different IPs -- a threat IP-based limiting alone can't see,
# since it buckets by source address, not by who's actually authenticated.
USER_HOURLY_LIMIT = '1000/hour'


def user_id_or_ip_key(request):
    """Rate-limit key: the authenticated user's id when a valid bearer
    token is present, falling back to IP address otherwise.

    Deliberately tolerant of a missing/invalid token here -- this is a
    rate-limiting key function, not an auth check (get_current_user still
    enforces that separately); a malformed token should degrade to
    IP-based limiting, not raise an error of its own.
    """
    auth_header = request.headers.get('Authorization', '')
    if auth_header.lower().startswith('bearer '):
        token = auth_header[len('Bearer '):]
        try:
            payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
            return f'user:{payload["sub"]}'
        except jwt.PyJWTError:
            pass
    return get_remote_address(request)
