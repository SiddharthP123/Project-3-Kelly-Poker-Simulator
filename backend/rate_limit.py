"""Shared rate limiter instance.

Kept in its own module (rather than defined in main.py) so router modules
can `from backend.rate_limit import limiter` and apply `@limiter.limit(...)`
without a circular import back to main.py, which is what wires this same
instance into the FastAPI app via `app.state.limiter`.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# Calculator endpoints are POST but compute-only (no DB writes) -- treated
# as "reads" per the standing rate-limit policy. Game endpoints that
# persist to the DB use WRITES_LIMIT instead.
READS_LIMIT = '100/15minute'
WRITES_LIMIT = '50/15minute'
