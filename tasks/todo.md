# Project Tasks

## Current Sprint:

- [x] Repo scaffolding (gitignore, requirements, README, tasks folder)
- [x] Part 1: Cards, Deck & Dealing
- [x] Part 2: Hand Evaluator
- [x] Part 3: Monte Carlo Equity Calculator
- [x] Part 4: Expected Value & Pot Odds
- [x] Part 5: The Kelly Criterion
- [x] Part 6: Bankroll Simulator
- [x] Part 7: Simple AI Opponents
- [x] Part 8: Backend API (FastAPI)
- [x] Part 9: Authentication & Security
- [x] Part 10: Frontend (React)
- [x] Part 11: Deployment
- [ ] Part 12: Real Poker Engine (multi-street, multi-opponent, side pots)
  - [x] Phase 1: `poker/betting.py` -- betting rounds + side pots, pure Python
  - [x] Phase 2: `poker/hand_flow.py` -- orchestrator (streets, bot turns)
  - [x] Phase 3: expand `poker/bots.py` to 10 personas
  - [ ] Phase 4: database schema (multi-street/multi-opponent hands)
  - [ ] Phase 5: backend wiring (`game_engine.py` + `routers/game.py`)
  - [ ] Phase 6: modern animated poker table (frontend)
  - [ ] Phase 7: account-wide statistics page
  - [ ] Phase 8 (deprioritized): re-polish Kelly-recommended-stake UI

## Completed:

- [x] Project setup

## Backlog:

- [ ] Future task

## Review (Parts 1-10):

Retroactive summary added 2026-07-30 after a full compliance audit against
`CLAUDE-CODE-INSTRUCTIONS.md` surfaced that this section had never been kept,
despite the workflow calling for it after each part.

- **Parts 1-7** (`poker/`) — pure-Python engine: cards/deck, hand evaluator,
  Monte Carlo equity, EV/pot odds, Kelly Criterion, bankroll simulator,
  rule-based AI opponents. 108 tests, all green. Each part's Monte Carlo/
  formula-derived output was sanity-checked against a known real-world
  benchmark or a numerical proof (e.g. AA-vs-random equity ~85.2% vs. the
  textbook ~85%; Kelly's fraction verified as the actual local maximum of
  `expected_log_growth`, not just an algebraic transcription).
- **Part 8** (`backend/`) — FastAPI + PostgreSQL. Calculator endpoints
  wrapping `poker/` directly; game-session endpoints backed by real DB
  models. 148 tests (SQLite-based, no live Postgres needed). Smoke-tested
  against the real Docker Postgres container.
- **Part 9** — JWT auth (bcrypt + PyJWT, chosen over the brief's
  passlib/python-jose for maintenance reasons), ownership checks (404 not
  403) on every game route. 161 tests. Caught and fixed a real cross-test
  bug (slowapi's rate limiter is a process-wide singleton) — see
  `lessons.md`. Separate security audit against the project's own
  standing checklist found and fixed 5 real gaps (Retry-After headers,
  per-user rate limiting, security response headers, unbounded input
  fields, zero logging) — 172 tests after.
- **Part 10** — split the single auto-played `play_hand` into
  `deal_hand`/`resolve_hand` so a real human decides fold/call/raise
  (the original Part 8 design had a fixed bot playing hero's side, since
  no UI existed yet). Built the full React frontend (Vite + Tailwind +
  shadcn + Recharts). 182 backend + 28 frontend tests. Two real UI bugs
  (raise-suggestion floor, invisible chart line) were only caught by
  manually driving the app in a browser against live data — see
  `lessons.md`.
- **Process gaps found in the 2026-07-30 audit** (see chat history for
  full detail): all 10 parts committed straight to `main` with no
  branches/PRs; `oxlint` was defined but never enforced (now wired into
  `.pre-commit-config.yaml`); `email-validator` was added in Part 9
  without ever being flagged (now documented in `requirements.txt`);
  `COMMON-ISSUES.md` in the global dev-docs was never populated (this
  project logged bugs in its own `tasks/lessons.md` instead).
- **Going forward (Part 11+):** use a `feature/part-11-deployment`-style
  branch and open a PR for review before merging, instead of committing
  straight to `main` — confirmed with the project owner during the
  compliance audit.
- **Part 11** — deployment config only, no application code changes.
  Backend deploys to Render as a Docker container (`Dockerfile` +
  `.dockerignore` + `render.yaml` Blueprint wiring a free web service to a
  free Postgres); frontend deploys to Vercel via its native Vite build
  (`frontend/vercel.json` for React Router's SPA rewrite). Added
  `.github/workflows/ci.yml` mirroring `.pre-commit-config.yaml`'s three
  checks, closing the "no CI" gap from the compliance audit. This is the
  first part built on a feature branch with an opened PR rather than a
  direct push to `main`, per the process change agreed above. The
  Dockerfile was built and run locally (confirmed `/health` responds with
  no live DB, and `$PORT` is correctly picked up at runtime) before ever
  being pointed at Render. Actually creating the Render/Vercel
  accounts/resources is the project owner's step — see README's "Part 11:
  Deployment" runbook.
- **Part 12 Phase 1-2** — `poker/betting.py` (blinds, no-limit betting rounds, side-pot
  construction/awarding) and `poker/hand_flow.py` (the multi-street orchestrator tying it to real
  bot decisions). Both pure Python, no DB/HTTP, each on its own branch/PR per the process agreed
  after Part 10's audit. 238 tests total (56 new). `poker/bots.py` needed no interface change for
  Phase 2 -- the fold/call/raise-to-engine-primitive translation (including clamping a bot's
  proposed raise against `legal_action_bounds`, and suppressing folding when checking is free)
  lives entirely in the new orchestrator, confirmed by a design pass before implementation started.
- **Part 12 Phase 3** — expanded `poker/bots.py` from 4 to 10 personas, all reusing the existing
  `ThresholdBot` base with no new decision logic -- just 6 new threshold-value combinations plus
  `assign_opponent_personas(num_opponents, rng)` to randomly seat distinct personas. 252 tests
  total (14 new). `backend/services/game_engine.py`'s own persona dict is untouched -- backend
  wiring is Phase 5, not this phase.
