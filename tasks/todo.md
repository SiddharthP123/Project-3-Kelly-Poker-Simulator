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
  - [x] Phase 4: database schema (multi-street/multi-opponent hands)
  - [x] Phase 5a: backend wiring, heads-up-focused (`game_engine.py` + `routers/game.py`)
  - [x] Phase 5b: multi-way side-pot testing through the API
  - [x] Phase 6a: modern poker table, static (frontend)
  - [x] Phase 6b: dealing/flip/chip animations (Framer Motion sign-off given 2026-09-13)
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
- **Part 12 Phase 4** — new tables `game_session_opponents`/`hand_players`/`hand_actions`, all
  additive under `create_tables.py`'s existing `create_all()`. `hand_players.hole_cards` always
  stores real cards for every seat (redaction moves to the response-schema layer in Phase 5,
  replacing Part 10's hidden-column pattern, which doesn't scale to 5 seats x 4 streets). Also adds
  4 nullable columns to the *existing* `game_sessions`/`hand_histories` tables -- NOT
  `create_all()`-safe, needs one manual `ALTER TABLE` against the live Render Postgres before
  Phase 5 (see `backend/migrations/README.md`), not yet run. 263 tests total (11 new).
- **Part 12 Phase 5a** — rewrote `backend/services/game_engine.py` + `backend/routers/game.py` on
  `poker/hand_flow.py`, replacing the fixed-pot/one-opponent model. Required two small changes to
  already-merged Phase 1/2 code (re-verified against their full existing suites afterward): the
  whole board is now dealt upfront (behaviorally identical for a given seed, just removes the need
  to keep a live `Deck` around across streets), and `BettingAction` now carries `pot_size_after`.
  Added `poker.hand_flow.rebuild_hand_state` (reconstructs a hand from persisted data by replaying
  it through the real engine) plus `_load_and_sync_state` in `game_engine.py` -- a real bug was
  found and fixed here (reconstruction alone can land one `advance_hand` cascade behind reality; see
  `lessons.md` for the full account, including why only a loop of many real-persona playthroughs,
  not a stub-bot unit test, surfaced it). 270 tests total (7 new: `pot_size_after`,
  `rebuild_hand_state` x3, plus the router suite fully rewritten for the new API). Manual migration
  step against live Render Postgres still not run -- needed before this is usable there.
- **Part 12 Phase 5b** — added an API-level test proving a genuine multi-layer side pot forms and
  resolves correctly end-to-end (deal -> shove all-in -> persist -> reconstruct -> showdown), using
  randomized real-valued bot stacks instead of Phase 1's clean textbook numbers. This surfaced a
  real (if small) rounding bug in `poker/betting.py`'s `build_pots` -- grouping contributors by
  rounding each one's `committed_total` to the nearest cent independently let those roundings
  compound into a multi-cent total drift on realistic stacks (never visible with round numbers).
  Fixed by grouping by proximity (`_EPSILON`) instead; verified via a 3000-trial repro (max error
  0.023 -> 1.5e-11) plus a new regression test with the exact failing values. 272 tests total (1
  new API test + 1 regression test). Full account in `lessons.md`.
- **Part 12 Phase 6a** — rewrote the game screen for 1-4 opponents/multi-street play against Phase
  5's API: new `Seat`/`getSeatPosition` components, an oval table with a progressively-revealed
  5-slot board, `ActionControls` rewritten around the backend's own `legal_action_bounds` object,
  `HandResultBanner` rewritten for a `winners[]` list instead of one fixed label. Adapted (not
  redesigned) the existing per-session dashboard/hand-history-table to the new `players[]`/
  `winners[]` shape so the app keeps working end-to-end; dropped its "Equity" column (not in the
  new API response, matching the Kelly UI's deferral). Deliberately black/white/red regardless of
  the app's own theme toggle -- a felt table doesn't "go light mode." No animations yet (Phase 6b,
  needs a Framer Motion dependency sign-off first). Verified via the full component suite (33
  tests) + oxlint + a production build -- **not** visually verified in a real browser this session
  (no browser tooling available); worth a manual pass before calling this phase fully done, per the
  Part 10 lesson that unit tests alone missed two real UI bugs.
- **Part 12 Phase 6b** — added Framer Motion (~42KB gzipped; only 3 new packages, none flagged by
  `npm audit` -- the flagged issues are pre-existing dev-tooling transitive deps, unaffected by this
  addition), signed off explicitly before the phase started. New `AnimatedCard` (deal-in entrance +
  a 3D flip specifically for an opponent's showdown reveal, built around two deliberately separate
  `dealt`/`card` props rather than one nullable prop). `Seat`'s hole-card slots are now keyed by
  position, not card value, so a reveal updates the same element in place instead of remounting a
  different one. `PokerTable`'s felt/seats/board subtree is now keyed by `hand.id` so a genuinely
  new hand replays deal-in animations while actions within the same hand don't re-trigger them. Pot
  amount pulses on change; winning seat(s) pulse instead of a static highlight; a small chip visibly
  travels from the pot to each winner at showdown. 38 tests total (5 new, `AnimatedCard`'s own
  dealt/card/flip states) + oxlint + a production build -- same "not visually verified in a browser"
  caveat as Phase 6a still applies.
