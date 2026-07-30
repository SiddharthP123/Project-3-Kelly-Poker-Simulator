"""Security response headers, applied to every response.

Key insight: these aren't a substitute for the same protections on the
frontend (Part 10 should set equivalent headers there too) -- but for a
pure JSON API they still cost nothing and add real defense-in-depth. If a
browser is ever tricked into loading an API response directly,
Content-Security-Policy stops it from being treated as active content and
X-Content-Type-Options stops MIME-sniffing from reinterpreting a JSON
payload as something executable.
"""

from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)

        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        # This API only ever returns JSON -- never HTML/JS -- so it can be
        # maximally restrictive here.
        response.headers['Content-Security-Policy'] = "default-src 'none'"
        # Harmless over plain HTTP (browsers ignore it there); takes effect
        # once this API is actually served over HTTPS (Part 11 deployment).
        response.headers['Strict-Transport-Security'] = 'max-age=63072000; includeSubDomains; preload'

        return response
