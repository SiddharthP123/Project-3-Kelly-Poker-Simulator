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

---

- **Date:** 2026-07-30
- **Mistake:** Two Part 10 frontend bugs shipped past 28 passing unit tests and only surfaced
  during manual browser testing: (1) `ActionControls` pre-filled the raise input with the raw
  Kelly-recommended stake, which can legitimately be *below* the minimum valid raise (that's
  exactly the "call, don't raise" zone) -- so the suggested default was sometimes a guaranteed-invalid
  number. (2) `BankrollGrowthChart` used the shadcn theme's `--chart-1` token for its line color,
  which for the Nova preset is a near-white grayscale value (that palette is monochrome, meant for
  multi-series charts) -- the line was nearly invisible against a white background.
- **Correction:** Floored the raise suggestion at `betToCall + 1`; replaced the theme token with an
  explicit, deliberately visible color (`#2a78d6`/`#3987e5`) for the single-line chart.
- **Lesson:** Component unit tests with mocked data verify *logic*, not *appearance* or
  *real-world value ranges* -- a test can pass with `suggestedRaiseAmount=250` (comfortably valid)
  while the actual API returns `13.50` in a real scenario, and a snapshot test wouldn't catch a
  color that resolves but is visually wrong. Manually driving the actual app end-to-end with real
  data (not just running the test suite) is what caught both -- worth doing before considering a
  UI part done, especially for anything involving theme tokens or derived numeric ranges.
- **Applied To:** `frontend/src/components/poker/action-controls.jsx`,
  `frontend/src/components/dashboard/bankroll-growth-chart.jsx` -- and any future chart using a
  shadcn preset's `--chart-N` tokens should verify the actual rendered color, not assume the token
  name implies a sensible visible color.

---

- **Date:** 2026-07-30
- **Mistake:** A full audit against this project's own `CLAUDE-CODE-INSTRUCTIONS.md` (requested
  after Part 10, covering every section, not just security) found process gaps that had been
  accumulating silently across all 10 parts: every commit went straight to `main` with no
  branches/PRs ever used; `tasks/todo.md` never got the "Review section" the workflow calls for
  after each part; `email-validator` (Part 9) was added without ever being flagged or documented
  anywhere, unlike every other dependency in the project; `oxlint` was defined in
  `frontend/package.json` but nothing ever actually ran it (no hook, no CI).
- **Correction:** Added `.pre-commit-config.yaml` (pytest + oxlint + vitest, installed via
  `pre-commit install`) so lint/tests are enforced locally before every commit; documented
  `email-validator` in `requirements.txt`; added the missing review section to `tasks/todo.md`
  retroactively; agreed to use feature branches + PRs from Part 11 onward instead of committing
  straight to `main`.
- **Lesson:** Following a governing instructions file well on the *content* dimensions (tests,
  docs, security, code quality) doesn't guarantee the *process* dimensions (branching, dependency
  sign-off paper trail, review checkpoints) are being followed too -- they're easy to silently
  drop since nothing breaks when they're skipped, unlike a failing test. A standing instructions
  file needs an occasional full pass, not just a security-focused one, to catch this category of
  drift.
- **Applied To:** Git workflow starting Part 11; `.pre-commit-config.yaml`; any future new
  dependency should get an explicit one-line justification in the commit message or a code
  comment, not just quietly added to `requirements.txt`/`package.json`.
