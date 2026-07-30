# Lessons Learned

## Template:

- **Date:** YYYY-MM-DD
- **Mistake:** [What went wrong]
- **Correction:** [What was done to fix it]
- **Lesson:** [Rule to prevent this in the future]
- **Applied To:** [Where this lesson applies]

---

- **Date:** 2026-07-30
- **Mistake:** Added `slowapi` rate limiting (Part 8) without accounting for the `Limiter` being a
  process-wide singleton. Once Part 9's auth tests started hitting the 5/15min auth bucket
  repeatedly (every `TestClient` request shares a fake IP), later tests calling `/api/auth/signup`
  or `/login` started failing with 429s that had nothing to do with what they were actually testing.
- **Correction:** Added an `autouse` `reset_rate_limiter` fixture in `tests/backend/conftest.py`
  that calls `limiter.reset()` before and after every test.
- **Lesson:** Any shared/global piece of state introduced for a cross-cutting concern (rate
  limiters, caches, in-memory counters) needs an explicit test-isolation story from the moment
  it's added — don't wait for a strict bucket to actually start failing tests to notice.
- **Applied To:** `backend/rate_limit.py`, `tests/backend/conftest.py` — relevant again if any
  future part adds another global limiter/cache/singleton.
- **Date:** 2026-07-30
- **Mistake:** `tests/backend/__init__.py` was created out of habit (mirroring `tests/backend`
  looking like a package), which silently made `backend` resolve to `tests/backend` instead of the
  real top-level `backend/` package inside `conftest.py` -- `import backend.models` failed with a
  confusing `ModuleNotFoundError` that looked unrelated to the actual cause.
- **Correction:** Deleted `tests/backend/__init__.py`. The existing `tests/` convention in this
  project has no `__init__.py` files anywhere; pytest's rootdir-based discovery doesn't need them.
- **Lesson:** Don't add `__init__.py` to a test directory just because it "looks like" it should be
  a package, especially when its name matches a real top-level package name -- check what pytest
  actually needs (usually nothing) before assuming Python package conventions apply the same way
  inside `tests/`.
- **Applied To:** Any new subdirectory under `tests/` in this project.
