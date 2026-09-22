# Project 3: Kelly Poker Simulator.

A progressive, self-taught, full-stack project that builds a Texas Hold'em simulator with AI
opponents and a virtual bankroll manager sized using the **Kelly Criterion**.

No real money is involved anywhere — this is a simulator/game against AI opponents using a
virtual bankroll only.

## Live Demo:

**[project-3-kelly-poker-simulator.vercel.app](https://project-3-kelly-poker-simulator.vercel.app)**
— open it directly; no invite or waitlist needed.

Watch this demo: **[▶ Watch the demo (2x speed)](https://github.com/user-attachments/assets/680900bb-272d-4c26-8678-bddfadda9c3e)**



Sign up with any email + password to play (real authentication, not a shared demo login). The
backend (Render's free tier) spins down after ~15 minutes idle, so the very first request after
a break can take 10-30 seconds to respond — that's expected, not a bug. Full deployment
architecture and runbook: see [Part 11](#part-11-deployment).

## Why poker?

The Kelly Criterion was originally developed for gambling/bankroll management and is the exact
same formula used for position-sizing in real investment portfolios (Ed Thorp — professional
card counter turned quant hedge fund manager — is the classic example). Poker gives a clean,
self-contained environment (known edge, known odds, discrete bets) to learn the formula before
applying the same thinking to a portfolio.

## Tech Stack:

- **Backend:** FastAPI (Python)
- **Frontend:** React
- **Database:** PostgreSQL
- **Auth:** JWT-based authentication (password hashing, protected routes)

Early parts (1–7) are plain Python with no web stack — the goal is to get the game/math logic
solid and tested before any API or UI is built on top of it.

## Progress:

| Part: | Topic: | Status: |
|---|---|---|
| 1 | Cards, Deck & Dealing | ✅ Done |
| 2 | Hand Evaluator | ✅ Done |
| 3 | Monte Carlo Equity Calculator | ✅ Done |
| 4 | Expected Value & Pot Odds | ✅ Done |
| 5 | The Kelly Criterion | ✅ Done |
| 6 | Bankroll Simulator | ✅ Done |
| 7 | Simple AI Opponents | ✅ Done |
| 8 | Backend API (FastAPI) | ✅ Done |
| 9 | Authentication & Security | ✅ Done |
| 10 | Frontend (React) | ✅ Done |
| 11 | Deployment | ✅ Done |
| 12 | Real Poker Engine (multi-street, multi-opponent, side pots) | ✅ Done |
| 13 | Table Redesign, Balance/Performance Tuning, Profile & Play-Style Analytics | ✅ Done |
| 14 | Player Education, Advanced Stats & Table Polish | ✅ Done |
| 15 | Illustrated Education, Dark-Mode Pages, Stat Tooltips & Table Layout Fixes | ✅ Done |

## Setup:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pytest
```

One-time, to enable local pre-commit checks (pytest + frontend lint/tests before every commit,
see `.pre-commit-config.yaml`):

```bash
pre-commit install
```

---

## Part 1: Cards, Deck & Dealing:

**Key insight:** a deck is just 52 unique `(rank, suit)` pairs. Treat it as a mutable pool you
*remove* cards from as you deal — once a card is dealt it physically leaves the deck, so no
explicit "already dealt?" check is needed.

- `poker/cards.py` — `Suit`/`Rank` enums and an immutable `Card`, with compact string notation
  (`Ah` = Ace of hearts, `Tc` = Ten of clubs — `T` avoids `10` taking two characters).
- `poker/deck.py` — `Deck` builds all 52 cards, `shuffle()`s, and deals via `deal(n)`,
  `deal_hole_cards(num_players)`, and `deal_community(n)` (flop/turn/river).

```bash
pytest tests/test_cards.py tests/test_deck.py -v
```

---

## Part 2: Hand Evaluator:

**Key insight:** every 5-card hand reduces to one sortable tuple: `(category, tiebreakers)`.
Once every hand is a tuple, deciding a winner is just Python's `max()` — no special-cased "flush
beats straight" logic anywhere, since tuple comparison checks category first and only falls
through to tiebreakers within the same category.

Tiebreakers come from one trick: group the 5 ranks by frequency, then sort groups by `(count,
rank)` descending. That single ordering produces the correct tiebreak order for every category
with duplicate ranks (e.g. two pair → `high_pair, low_pair, kicker`).

Two cases need special-casing: straights (5 distinct consecutive ranks, including the wheel
A-2-3-4-5 where the Ace plays low) and flushes (5 cards, same suit). A straight flush is both.

- `poker/hand_evaluator.py` — `HandCategory` (ordered enum), `evaluate_5(cards)`,
  `best_hand(cards)` for 5-7 cards (brute-forces all `C(7,5) = 21` combinations), and
  `compare_hands(hands)` (returns winning index/indices — more than one means a split pot).

```bash
pytest tests/test_hand_evaluator.py -v
```

---

## Part 3: Monte Carlo Equity Calculator:

**Key insight:** we don't know opponents' hole cards or the rest of the board, but we know the
pool they could come from. Instead of solving win probability analytically, repeatedly deal the
unknown cards at random and check who wins with Part 2's `compare_hands` — thousands of times,
letting the win rate converge to the true probability. Same idea as Project 1's Monte Carlo, just
applied to cards.

`calculate_equity(hole_cards, num_opponents, board, num_simulations, seed)` returns an
`EquityResult` with `win`/`tie`/`lose` shares plus `equity` (expected pot share — 1 per win, 1/n
per n-way tie, 0 per loss). `equity` is what later parts (EV, Kelly) actually need.

Sanity-checked against a known benchmark: pocket Aces heads-up wins **85.2%** over 20,000
simulations, matching the commonly cited ~85% figure.

- `poker/equity.py` — `EquityResult` dataclass, `calculate_equity(...)`. Opponents are assumed
  to hold uniformly random hole cards (no modelled range) — the standard baseline calculation.

```bash
pytest tests/test_equity.py -v
```

---

## Part 4: Expected Value & Pot Odds:

**Key insight:** pot odds convert a bet size into a probability threshold. Facing pot `P` and bet
`B`, calling breaks even when `equity * P == (1 - equity) * B` — solving for equity gives `B / (P
+ B)`, the minimum win probability needed to call profitably. Comparing Part 3's simulated equity
against that number tells you whether to call, no dollar EV required. Same "probability vs.
break-even threshold" logic used to judge whether an investment's expected return justifies its
risk.

Raising is modelled as a probability-weighted mix: opponent folds (win the pot as-is) or calls
(same call-EV formula, using the raise size). No full game-tree solving — just one extra input,
an assumed fold probability.

- `poker/ev.py` — `pot_odds_breakeven_equity(pot_size, bet_to_call)`, `ev_fold()` (always 0),
  `ev_call(equity, pot_size, bet_to_call)`, `ev_raise(equity, pot_size, raise_amount,
  fold_probability)`, and `best_action(...)` (picks highest-EV action, returns a `Decision`
  showing every option's EV).

```bash
pytest tests/test_ev.py -v
```

---

## Part 5: The Kelly Criterion:

**The finance parallel the whole project is built around.** Kelly answers "what fraction of your
bankroll to stake on a repeatable bet with a known edge" — the identical formula sizes positions
in a real investment portfolio. Given an edge and known odds, Kelly gives the capital fraction
that maximises long-run *compound* growth. Ed Thorp used this exact reasoning to go from
blackjack card counting to running a hedge fund.

**Key insight:** Kelly is the fraction `f` that maximises expected *log*-growth per bet, `g(f) =
p·ln(1 + f·b) + q·ln(1 - f)`, not plain expected value. Log-growth is correct for a bet repeated
many times because bankroll compounds multiplicatively — maximising raw EV instead pushes toward
betting the whole bankroll every time, which guarantees eventual ruin. Setting `g'(f) = 0` gives
the closed form: `f* = (p·b − q) / b`. The test suite proves this directly: for several `(p, b)`
pairs, it checks `expected_log_growth` at the Kelly fraction is never beaten by any nearby
fraction.

A negative `f*` means no edge — bet nothing, not a negative amount. `fractional_kelly` clips this
to 0, and also supports "half Kelly" etc. — growth near the Kelly peak is flat, but variance keeps
rising linearly with bet size, so trading a little growth for lower drawdowns is common practice.
Part 6 compares these strategies directly.

- `poker/kelly.py` — `kelly_fraction(win_probability, odds)`, `fractional_kelly(...,
  fraction=1.0)`, `kelly_fraction_from_pot_odds(equity, pot_size, bet_to_call,
  kelly_multiplier=1.0)` (bridges Parts 3 & 4), and `expected_log_growth(...)`.

```bash
pytest tests/test_kelly.py -v
```

---

## Part 6: Bankroll Simulator:

**Key insight:** the "aggressive growth vs. safety" trade-off in bet sizing is a direct
mathematical consequence of how the same sequence of wins/losses compounds under different stake
sizes — not a matter of risk tolerance. Past the Kelly fraction, both risk of ruin **and**
long-run growth get worse together, since a big loss erases gains faster than wins rebuild them.
Kelly betting can never hit exactly zero (every stake is a fraction below 1 of what remains — it
"can't go broke"), while all-in betting means any single loss is total. Part 5 proved the
growth-maximising property algebraically; this part demonstrates the ruin side empirically,
simulating a modest edge (55% win probability, even-money) under four staking strategies over 200
hands:

![Bankroll growth curves by staking strategy](docs/part-6-plots/bankroll_growth_curves.png)

![Risk of ruin and median final bankroll by strategy](docs/part-6-plots/risk_of_ruin_comparison.png)

Full Kelly has both the **highest median outcome** and **zero risk of ruin** — it strictly
dominates every less-adapted strategy tested, not a trade-off. All-in has the same edge but 100%
risk of ruin: surviving 200 hands undefeated at 55% is astronomically unlikely, and one loss is
unrecoverable at an all-in stake.

- `poker/bankroll.py` — `fixed_stake_strategy`, `kelly_strategy(kelly_multiplier)`,
  `all_in_strategy`, `simulate_session`, and `simulate_many_sessions` (Monte Carlo over bankroll
  trajectories, reporting risk of ruin and mean/median final bankroll).
- `scripts/plot_bankroll_comparison.py` — generates the two plots above via matplotlib.

```bash
pytest tests/test_bankroll.py -v

# Regenerate the plots:
PYTHONPATH=. python3 scripts/plot_bankroll_comparison.py
```

---

## Part 7: Simple AI Opponents:

**Key insight:** every persona differs only in *which numbers* it plugs into the same
fold/call/raise vocabulary. `TightAggressiveBot` and `LoosePassiveBot` are the same
`ThresholdBot` logic (fold below one equity bar, raise above another, call in between) with
different constants — tight-aggressive folds most hands but raises big with the few it plays;
loose-passive ("calling station") folds almost nothing but rarely raises. `RandomBot` ignores
equity entirely, as a baseline the smarter personas are judged against.

`KellyOptimalBot` sizes every decision straight from Part 5's Kelly Criterion, and doesn't need a
separate Part 4 pot-odds check to decide whether to fold: Kelly's numerator (`p·b − q`) is
positive exactly when calling is +EV under pot odds, since Part 4's breakeven equity (`bet /
(pot + bet)`) and Kelly's "no edge" point (`1 / (b + 1)`) are algebraically the same number. So
for this bot, "Kelly recommends staking nothing" and "folding is correct" are one condition —
Parts 3, 4, and 5 collapse into a single Kelly-stake calculation.

- `poker/bots.py` — `Action` (fold/call/raise + amount), `Bot` base class (bankroll-capping +
  `decide_from_hand`, running Part 3's real Monte Carlo equity calculator end-to-end),
  `ThresholdBot` → `TightAggressiveBot`/`LoosePassiveBot`, `RandomBot`, `KellyOptimalBot`.

```bash
pytest tests/test_bots.py -v
```

---

## Part 8: Backend API (FastAPI):

**Key insight:** turning the engine into a service is mostly translation, not new logic — every
calculator endpoint (`/api/equity`, `/api/ev`, `/api/kelly/*`, `/api/hand-evaluator/*`,
`/api/bots/decide`) is a thin Pydantic-in → `poker/` call → Pydantic-out wrapper. The one
genuinely new piece is `services/game_engine.py::play_hand`, which settles a hand's outcome by
feeding the *realized* result (win=1, split=1/n, loss=0) back into Part 4's `ev_call` — the same
call-EV math now computes actual bankroll change too.

Hero is auto-played by a fixed `KellyOptimalBot` in this part (no interactive UI yet — that's
Part 10). A hand here is a single fixed-stakes decision (pot-sized bet, 1:1 odds, 50% breakeven),
not a full multi-street engine — enough to prove deal → decide → showdown → persist end-to-end.

`backend/` is a new top-level package, sibling to `poker/` (never nested inside it):

- `backend/models/` — SQLAlchemy models: `User`, `GameSession`, `HandHistory` (one row per hand;
  a folded opponent's cards are never revealed), `BankrollLog` (append-only time series, separate
  from `HandHistory` so a growth chart is a plain ordered `SELECT`).
- `backend/routers/` + `backend/schemas/` — calculator endpoints above, plus stateful
  `/api/game/sessions/*` endpoints (create session, play a hand, list history, fetch bankroll
  history, end session). Every request schema uses `extra='forbid'`; card strings validate
  through `Card.from_str` at the schema layer, so bad notation 422s instead of 500ing.
- Rate limiting via `slowapi`: calculator endpoints get a 100/15min "reads" bucket;
  `/api/game/sessions/*` writes get 50/15min — IP-based until Part 9 adds JWT-keyed limits.
- **Testing runs entirely on SQLite** (`tests/backend/conftest.py` overrides `get_db` with a
  per-test temp-file database) — no Postgres needed for `pytest`. Real Postgres is dev/run only.

Three defaults were set without a full stop (each easily revisited later): Alembic deferred in
favour of `Base.metadata.create_all()` (no production data to protect yet); `User` rows optional
this part (`GameSession.user_id` nullable, Part 9 owns signup); plain SQLAlchemy + separate
Pydantic schemas (not SQLModel), Postgres via Docker Desktop + docker-compose.

### Running It Locally:

```bash
# One-time: install Docker Desktop, then from the project root:
docker compose up -d          # starts Postgres on localhost:5432
cp .env.example .env          # fill in real values if you changed docker-compose.yml
source venv/bin/activate
PYTHONPATH=. python3 backend/create_tables.py   # stands up the schema (no Alembic yet)
uvicorn backend.main:app --reload
# Then visit http://localhost:8000/docs for the interactive Swagger UI.
```

```bash
pytest tests/backend/ -v   # no Docker/Postgres needed
```

---

## Part 9: Authentication & Security:

**Key insight:** JWTs are stateless — the server never stores issued tokens, only verifies
signature and expiry per request, so `get_current_user` is a fast dependency with no DB round
trip to validate the token itself. Auth is two pieces bolted onto Part 8: `backend/security.py`
(bcrypt password hashing, JWT issue/decode) and `Depends(get_current_user)` on every
`/api/game/sessions/*` endpoint.

Two security details worth calling out:
- **Login failures are indistinguishable.** Unknown email and wrong password both return the
  same 401 + generic message — separating them would let an attacker enumerate accounts.
- **A session belonging to someone else 404s, not 403s** — 403 would confirm the ID is real; 404
  leaks nothing, matching the project's "verify ownership before allowing modifications" rule.

Auth endpoints (`/api/auth/signup`, `/api/auth/login`) get a tight 5/15min rate-limit bucket,
separate from general reads/writes — credential endpoints are the classic brute-force target.
`User.starting_bankroll` gets its first real use: creating a session without specifying it falls
back to the signed-up user's own default.

One bug fixed while testing: `slowapi`'s rate limiter is a process-wide singleton, so without
resetting it between tests, exhausting the 5/15min bucket in one test starved every later test
hitting the same endpoint. Fixed with an `autouse` `reset_rate_limiter` fixture.

- `backend/security.py` — `hash_password`/`verify_password` (bcrypt), `create_access_token`/
  `get_current_user` (PyJWT, `HS256`, configurable expiry).
- `backend/routers/auth.py` — `POST /api/auth/signup`, `POST /api/auth/login`, `GET
  /api/auth/me`.
- `backend/routers/game.py` — every endpoint requires `Depends(get_current_user)`;
  `_get_owned_session_or_404` enforces ownership.
- Chose bcrypt + PyJWT over passlib/python-jose (both showing their age); login is required for
  game sessions (not anonymous), confirmed with the project owner before implementation.

Smoke-tested end-to-end against a real Postgres container: signup → `/me` → create session
(correct default bankroll) → play a hand → a second user gets a clean 404 on the first user's
session → login with correct/wrong credentials.

```bash
pytest tests/backend/test_auth_router.py -v
```

### Security Hardening Pass:

Before Part 10, the backend was audited against this project's standing
`CLAUDE-CODE-INSTRUCTIONS.md` security checklist (Firebase/Next.js items translated to their
FastAPI/Postgres equivalents). Already compliant: ORM-only (no raw SQL), no hardcoded secrets,
debug off, strict schema validation everywhere, rate limits on every endpoint except `/health`
(intentionally unthrottled — a trivial, no-DB liveness check). Five gaps found and fixed:

- **`Retry-After` missing from 429s** — `slowapi`'s `Limiter` needed `headers_enabled=True`,
  which requires every rate-limited endpoint to accept a `response: Response` param — added to
  all 16.
- **No per-user rate limiting** — added `USER_HOURLY_LIMIT` (1000/hour) stacked on top of the
  existing IP limits on `/api/game/sessions/*`, keyed by `user_id_or_ip_key` (bearer token → user
  id, else IP). Protects against a single compromised/shared token spread across many source IPs.
- **No security response headers** — added `backend/middleware.py`
  (`SecurityHeadersMiddleware`): `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`,
  `Permissions-Policy`, `X-XSS-Protection`, `Content-Security-Policy: default-src 'none'` (JSON
  API only), `Strict-Transport-Security`.
- **Three unbounded list fields** — `EquityRequest.board`/`BotDecideRequest.board` had no
  `max_length`, `CompareHandsRequest.hands` had no cap on hand/card count. All now enforce
  `poker/`'s own bounds at the schema layer (422 instead of after partial work).
- **Zero logging** — failed logins vanished silently. Added stdlib logging: failed
  logins/duplicate signups log email + IP (never password), rejected tokens log failure type
  (never the token), rate-limit breaches log IP + path.

Re-verified end-to-end after the fixes: security headers present on a live response, gameplay
unaffected, oversized input still 422s, a 6th rapid login returns a real `Retry-After`.

```bash
pytest tests/backend/test_security_hardening.py -v
```

---

## Part 10: Frontend (React):

**Key insight:** the backend from Parts 8-9 couldn't actually be *played* — `play_hand`
auto-decided hero's action with a hardcoded bot, since there was no UI to ask a human. Before any
frontend code, `services/game_engine.py::play_hand` was split into `deal_hand` (deals hero's
cards, computes equity and live Kelly stake, hand stays pending) and `resolve_hand` (settles the
human's real decision — everything downstream is unchanged from Part 8/9). Two new
internal-only columns (`dealt_board_cards`, `dealt_opponent_hole_cards` on `HandHistory`)
remember what was dealt across the two separate requests this now takes; neither is ever declared
in `HandHistoryResponse`, so a human hasn't structurally earned the right to see them yet.

`GET /api/game/sessions/{id}/hands/pending` lets the frontend recover a hand-in-progress after a
refresh — verified live: refreshing mid-decision reloads the same hole cards and equity rather
than losing or silently redealing the hand.

### Stack:

Plain React (not Next.js, per the brief) + Vite + JavaScript + Tailwind CSS v4 + shadcn/ui (Radix
base, Nova preset) + `react-router-dom` + Recharts (via shadcn's `chart.jsx`) + Vitest + React
Testing Library — following the project's standing conventions wherever stack-agnostic
(kebab-case files, `cn()`, functional components, hooks in `hooks/`), translating Next.js-specific
ones (ESLint → `oxlint`, the faster Rust-based linter Vite scaffolds by default).

### What's Built:

- **Auth** — `lib/api-client.js` (fetch-based, no axios; 401 → clear token + redirect, 422 →
  flattens FastAPI's validation error shape, 429 → surfaces `Retry-After`),
  `context/auth-context.jsx` + `hooks/use-auth.js`, login/signup pages, `ProtectedRoute`.
- **Lobby & session setup** — no "list my sessions" backend endpoint, so resuming a session is
  client-side: the last-created session id lives in `localStorage`, checked against `GET
  /sessions/{id}` on load (same-browser only, avoids expanding backend scope).
- **Interactive poker table** (`components/poker/poker-table.jsx`) — a 3-stage state machine
  (idle → awaiting decision → resolved) driven by the pending-hand endpoint. The Kelly-recommended
  stake shows live next to the equity it's derived from; the raise input pre-fills with that
  suggestion floored at the minimum valid raise — a real bug caught in manual testing, since Kelly
  can recommend staking *less* than a call, which had pre-filled a guaranteed-invalid number.
- **Dashboard** — bankroll growth chart, win-rate KPI tiles + stacked bar, hand history table.
  Built with the `dataviz` skill: the bankroll line uses one consistent color (signed delta lives
  in a separate stat tile, not diverging red/green by magnitude); win/loss/split/fold use
  status tokens (green/red/neutral/amber). **Caught live**: shadcn's Nova preset `--chart-1` is
  near-white grayscale (that palette is meant for multi-series charts), making a single
  highlighted line nearly invisible — fixed with an explicit blue (`#2a78d6` light / `#3987e5`
  dark) instead of the theme token.

### Testing:

Vitest + React Testing Library, no Playwright/E2E yet (deferred to Part 11, once there's a real
deployed URL). 28 tests: API client auth/401/422/429 handling, auth context, protected-route
redirects, the poker table's full state-machine against a mocked API client, action validation,
and two pure aggregation functions (`compute-win-rate.js`, `compute-bankroll-series.js`) tested
directly rather than only through chart components (Recharts' SVG output is brittle under jsdom).

One environment quirk: this Node version ships a native but non-functional `localStorage` global
that shadows jsdom's own, breaking any test touching it — fixed via
`NODE_OPTIONS="--localstorage-file=..."` in the `test` npm script.

Smoke-tested end-to-end in a real browser against the live API: signup → create session → deal →
fold (bankroll unchanged, cards hidden) → deal again → call → showdown (board + opponent cards
revealed, bankroll updated) → dashboard showing accurate win rate and a correctly-colored chart.

```bash
cd frontend && npm run test

# Run locally (backend already running per Part 8):
cd frontend
cp .env.example .env
npm install
npm run dev
# Visit http://localhost:3000
```

---

## Part 11: Deployment:

**Key insight:** the two services deploy independently — backend to Render (Docker container,
portable, mirrors local exactly), frontend to Vercel (native Vite build) — but have a real
chicken-and-egg dependency: the frontend needs the backend's URL (`VITE_API_BASE_URL`), the
backend needs the frontend's URL (`CORS_ALLOWED_ORIGINS`). Neither exists until the other is
deployed once, so going live takes two passes.

This part adds no application code, only deployment config (`Dockerfile`, `.dockerignore`,
`render.yaml`, `frontend/vercel.json`) and CI (`.github/workflows/ci.yml`, mirroring
`.pre-commit-config.yaml`'s three checks so local and CI enforcement never drift). The Dockerfile
was built and run locally first — confirmed it serves `/health` with no live DB connection (by
design) and picks up a runtime-injected `$PORT`, matching Render's behavior.

### Usage (Once Deployed):

Visit the Vercel URL, sign up, start a session (pick an opponent persona and starting bankroll),
and play: deal a hand, see equity and the live Kelly-recommended stake, fold/call/raise, see the
resolution, check the dashboard for bankroll growth and win rate. First request after 15 minutes
of inactivity is slow (10-30s) — Render's free tier cold-starts on idle. Expected, not a bug.

### Testing:

```bash
pytest -q                                    # 182 tests, no Postgres needed (SQLite-backed)
cd frontend && npm run lint && npm run test && npm run build   # 28 tests + production build
pre-commit run --all-files                   # all three checks, same as CI
```

`.github/workflows/ci.yml` runs the same three checks on every push and PR targeting `main`.

### Deployment Runbook:

Creating the Render/Vercel accounts needs your own browser session and credentials, so this part
is prepared and verified but not something that runs itself. Steps to go live:

1. **Merge this PR** (or deploy from the feature branch directly — Render/Vercel can point at a
   specific branch).

2. **Supabase — database.** Postgres is hosted on Supabase, not Render's own (Render's free tier
   deletes the whole database after 30 days; Supabase's free tier only pauses, resuming with one
   dashboard click). Create a free project at [supabase.com](https://supabase.com), grab its
   connection string from **Project Settings → Database → Connection string → URI**.

3. **Render — backend.** Dashboard → **New → Blueprint** → connect this repo. Render reads
   `render.yaml` and prompts for:
   - `DATABASE_URL` — the Supabase connection string from step 2.
   - `JWT_SECRET_KEY` — generate your own, don't reuse the local dev default:
     ```bash
     python3 -c "import secrets; print(secrets.token_hex(32))"
     ```
   Deploy the Blueprint and note the resulting URL (this project's live backend:
   `https://kelly-poker-backend.onrender.com`).

4. **Stand up the production schema.** Still no Alembic — `create_all()` is additive and safe to
   run once, directly against the externally-reachable Supabase database:
   ```bash
   DATABASE_URL="<your Supabase connection string>" PYTHONPATH=. python3 backend/create_tables.py
   ```

5. **Vercel — frontend.** Dashboard → **Add New → Project** → import this repo → set **Root
   Directory** to `frontend` (monorepo) → add env var `VITE_API_BASE_URL` = your Render URL +
   `/api` → Deploy. This project's live frontend:
   `https://project-3-kelly-poker-simulator.vercel.app`.

6. **Close the loop.** Back in Render, set `CORS_ALLOWED_ORIGINS` to your real Vercel URL from
   step 5 (comma-separate for more than one, e.g. a preview URL too). Render redeploys
   automatically on env var change.

7. **Smoke test the live URL:** sign up, start a session, deal a hand, act on it, check the
   dashboard.

**Free-tier caveats** (verify current terms before relying on these long-term): Supabase's free
project pauses on inactivity and needs a manual "restore" click before it accepts connections
again; Render's free web service cold-starts after ~15 min idle; Vercel's Hobby tier is
non-commercial/single-developer only. All fine for a portfolio demo — upgrade whichever tier
matters if this needs to stay reliably live.

---

## Part 12: Real Poker Engine (multi-street, multi-opponent, side pots):

**Why this part exists:** Parts 8-10 deliberately simplified the game to one fixed $100 pot/bet,
one opponent, and one hero decision resolving the whole hand instantly — enough to prove the
pipeline end-to-end before a UI existed. Part 12 replaces that with the real thing: blinds,
no-limit betting with side pots, 1-4 opponents from an expanded 10-persona roster, and a genuine
flop → turn → river progression with a betting round per street. Built and shipped incrementally,
same pattern as Parts 1-11 — each phase its own branch/PR.

**Key insight:** side-pot math only needs one number per player — their total contribution
(`committed_total`) — and whether they folded. Sort the distinct contribution levels; each gap
between levels is one pot "layer," sized `(gap × players who reached that level)`, eligible to
non-folded players who reached it. Worked example: three players all-in for $50/$120/$200 splits
into a $150 main pot (all three eligible), a $140 side pot, and an $80 side pot (only the $200
player, uncontested). Checksum: `150+140+80 = 370 = 50+120+200`.

A second trick: the human-facing 5-verb vocabulary (fold/check/call/bet/raise) collapses to 3
engine primitives — `fold`/`match`/`raise_to`. Check is "match a bet of $0"; bet is "raise from
$0." One comparison validates any action; friendlier verbs are just an API-layer label.

### Phase 1: `poker/betting.py` — pure Python, no DB/HTTP:

Built and unit-tested standalone before touching a database or endpoint, same pattern as every
`poker/` module.

- `PlayerState` — per-seat state (`stack`, `committed_street`, `committed_total`, `status`).
  `.commit(amount)` keeps street/total in sync.
- `BettingRound` — one street's betting for N players. `legal_action_bounds(seat)` gives call
  amount and min/max raise; `apply(seat, action, raise_to)` validates and applies
  `fold`/`match`/`raise_to`, reopening action correctly on a raise (an undersized all-in doesn't
  reopen action for others — official poker's exception, deliberately not implemented, flagged
  in the docstring).
- `refund_uncalled_bet()` — refunds the excess when a street closes with nobody matching the
  largest bet, so chip totals stay balanced and no pot layer ends up with zero eligible winners.
- `build_pots(players)`/`award_pots(pots, hands)` — the side-pot algorithm above, reusing
  `poker/hand_evaluator.py`'s `compare_hands` unchanged to award each contested layer.

```bash
pytest tests/test_betting.py -v
```

### Phase 2: `poker/hand_flow.py` — the orchestrator:

Ties Phase 1's betting engine to real bot decisions across a full hand, still pure Python.

- `create_hand(...)` — deals hole cards to hero + 1-4 opponents, rotates the button by hand
  number (uniform rule, including heads-up), posts blinds.
- `advance_hand(state, decide_bot_action)` — loops resolving bot turns and street transitions
  until it's hero's turn or the hand is complete — the resumability boundary an HTTP request
  needs, since hero now acts across multiple requests.
- `apply_hero_action(state, action, raise_to)` — applies hero's decision; caller re-runs
  `advance_hand` afterward.
- `default_bot_action` — translates `poker/bots.py`'s vocabulary into fold/match/raise_to:
  recomputes live opponent count each decision, suppresses folding when checking is free, clamps
  a bot's raise against `legal_action_bounds`. `poker/bots.py` itself needed no interface change.
- A fold-out and a genuine showdown resolve through the same function — `build_pots`/`award_pots`
  already handle a single eligible seat as a trivial one-seat pot.

```bash
pytest tests/test_hand_flow.py -v
```

### Phase 3: `poker/bots.py` — 10 opponent personas:

Expands 4 personas to 10, all reusing `ThresholdBot(fold_below, raise_above, raise_sizing)`
unchanged — every new persona is just different threshold values:

| Persona | fold_below | raise_above | raise_sizing |
|---|---|---|---|
| Very-Tight-Passive ("Rock") | 0.65 | 0.90 | 0.35 |
| Tight-Aggressive | 0.55 | 0.65 | 0.75 |
| Very-Tight-Aggressive ("Nit-Shark") | 0.70 | 0.80 | 0.90 |
| Balanced (GTO-ish) | 0.45 | 0.60 | 0.65 |
| Loose-Passive | 0.15 | 0.85 | 0.40 |
| Very-Loose-Passive ("Weak-Loose") | 0.05 | 0.95 | 0.30 |
| Loose-Aggressive ("LAG") | 0.25 | 0.45 | 0.85 |
| Very-Loose-Aggressive ("Maniac") | 0.10 | 0.30 | 1.10 |
| Random | — | — | — |
| Kelly-Optimal | — | — | — |

`assign_opponent_personas(num_opponents, rng)` samples distinct personas per opponent seat (any
of the 10 eligible, no repeats), taking an explicit `random.Random` for reproducibility.

```bash
pytest tests/test_bots.py -v
```

### Phase 4: database schema for multi-street, multi-opponent hands:

Three new tables, purely additive (safe under `create_tables.py`'s `create_all()`):

- **`game_session_opponents`** — one row per opponent seat's persona, replacing the old single
  `bot_persona` column which couldn't hold 1-4 opponents.
- **`hand_players`** — one row per seat per hand: stacks, fold/all-in status, net result, and
  real hole cards for every seat, always. Redaction moved from storage to serialization — cards
  are always stored real, only ever *shown* once a seat has earned the right (built in Phase 5).
- **`hand_actions`** — full replayable action log (street, seat, action, amount, running pot
  size), reusing `poker.betting.BettingAction`'s vocabulary directly. What Phase 6's frontend
  animates through, street by street. Hero's `equity_at_decision`/`kelly_recommended_stake` move
  here too, since a decision now happens per street, not per hand.

Two small nullable columns land on the existing `game_sessions`/`hand_histories` tables — safe
for a fresh database, but a genuine manual migration step against the live production database
(see `backend/migrations/README.md`), run deliberately before Phase 5 needs them.

`GameSession.bot_persona` and the old single-opponent card columns are left untouched (vestigial
for new sessions, still valid for old ones) — cleanup is a future step, not part of this one.

### Phase 5a: backend wiring (heads-up-focused):

Rewrites `backend/services/game_engine.py` and `backend/routers/game.py` on `poker/hand_flow.py`,
replacing the single fixed-pot/one-opponent model. A hand now spans multiple HTTP requests, so
`HandState` can't just live in a Python variable between them.

- `POST /sessions` takes `num_opponents` (1-4), `small_blind`/`big_blind` — personas assigned
  randomly via `assign_opponent_personas`, stored in `game_session_opponents`. Bots get a
  randomized per-hand stack, reset every hand — only hero's `current_bankroll` persists.
- Two load-bearing changes to already-merged Phase 1/2 code (re-verified against their full test
  suites): `hand_flow.py` now deals the whole 5-card board upfront (`HandState.board` slices it
  by street) — behaviorally identical for a given seed, but nothing needs a live mutating `Deck`
  past hand creation. `betting.py`'s `BettingAction` now carries `pot_size_after`.
- `poker.hand_flow.rebuild_hand_state` (new) reconstructs a hand's state purely from persisted
  data by *replaying* it through the same primitives that produced it — proven byte-identical to
  never having paused.
- Redaction happens at response-assembly time: `HandPlayer.hole_cards` is always real; a seat's
  cards serialize only once earned (hero's own always, everyone's at a genuine showdown, nobody's
  at a fold-out).
- A subtle bug fixed here (full account in `tasks/lessons.md`): reconstructing state and
  immediately applying hero's next action isn't enough — nothing records for a fresh street until
  someone acts on it, so reconstruction alone can land one cascade behind. `_load_and_sync_state`
  completes and persists that catch-up first — critical since bot decisions use live, unseeded
  equity, so silently discarding an unpersisted catch-up could resolve a bot turn differently on
  a second read.

```bash
pytest tests/backend/test_game_router.py -v
```

**Manual step still needed on the live production database:** run
`backend/migrations/run_migrations.py` (see `backend/migrations/README.md`) — the new columns
don't exist on the already-live tables until then.

### Phase 5b: multi-way side-pot testing through the API:

Proves a genuine multi-layer side pot forms and resolves end-to-end through the HTTP API — deal →
hero shoves all-in → persistence → reconstruction → showdown.

Bot stacks are randomized and not directly controllable, and bots decide with live, unseeded
equity, so a specific side-pot shape can't be forced deterministically. The test gives hero an
enormous stack (guaranteeing any calling bot goes all-in for less), shoves preflop every hand,
and retries fresh sessions/seeds until at least two differently-stacked opponents are both
observed all-in at showdown.

This surfaced a genuine bug in Phase 1's `build_pots`, found only because this phase finally uses
realistic non-round amounts: it grouped contributors by rounding `committed_total` to the nearest
cent independently, and those roundings didn't cancel out — the reconstructed total could drift a
couple cents from what was actually committed. Fixed by grouping by proximity (the same
`_EPSILON` every float comparison in `betting.py` uses) instead of rounding — the same repro now
drifts by ~1.5e-11 (ordinary float64 noise). Full account in `tasks/lessons.md`.

```bash
pytest tests/backend/test_game_router.py::test_multiway_all_in_produces_a_genuine_side_pot_end_to_end -v
```

### Phase 6a: modern poker table (frontend, static):

Rewrites the game screen for 1-4 opponents and real multi-street play. Deliberately
black/white — only suit glyphs use color, everything else on the table stays grayscale regardless
of the app's light/dark toggle, since a felt table doesn't "go light mode." No animations yet —
that's Phase 6b, a separate signed-off phase (new Framer Motion dependency).

- **`PokerTable`** — an oval felt (seats via `getSeatPosition`, keyed by opponent count), 5 board
  slots always rendered, undealt ones shown as dashed placeholders. A single `hand` object is the
  only state that matters — its `street` field distinguishes "hero has a decision" from "hand is
  over."
- **`Seat`** (new) — persona label, live stack, hole cards. Redaction is entirely the backend's
  job (`hole_cards` is `null` until earned) — this component only decides *how* to render what
  it's given: face-down for a hidden seat, nothing for a folded one (mucked, not face-down).
- **`ActionControls`** — rewritten around the backend's `legal_action_bounds` object directly
  (`can_fold`/`can_check`/`can_call`/`call_amount`/`can_raise`/`min_raise_to`/`max_raise_to`)
  instead of a single fixed bet-to-call. An "All-in" shortcut fills the raise field with
  `max_raise_to`.
- **`HandResultBanner`** — rewritten for `winners: [seat_index, ...]`, since 1-4 opponents means
  any number of winners (a split, or an uncontested side pot).
- The per-session dashboard is adapted (not redesigned) to the new `players[]`/`winners[]` shape;
  its "Equity" column is dropped (not in the new response, matching the Kelly UI's deferral).
- `SessionSetupForm`/`useGameSession` send `num_opponents` instead of `bot_persona`.

```bash
cd frontend && npm run test
```

Verified via the full component test suite (33 tests), `oxlint`, and a production build — not by
looking at a rendered browser this session. Worth a manual visual pass, per this project's own
lesson (Part 10's two real UI bugs both passed unit tests and were only caught manually).

### Phase 6b: dealing/flip/chip animations:

Adds Framer Motion (~42KB gzipped, signed off before this phase started) and animates the
transitions Phase 6a only ever snapped between:

- **`AnimatedCard`** (new) — built around two separate props (`dealt`, `card`) rather than one
  nullable card, since "not dealt" and "dealt face-down" need different treatment. A `dealt:
  false → true` transition plays a deal-in entrance once, face-down or face-up. A `card: null →
  <value>` transition on an already-dealt card plays a 3D flip — the showdown-reveal moment.
- **`Seat`** — hole-card slots are keyed by position, not card value, so a showdown reveal
  updates the same element in place (letting it flip) instead of remounting.
- **`PokerTable`** — the felt/seats/board subtree is keyed by `hand.id`, so a new hand replays
  every deal-in while actions within the same hand only update mounted elements. Board cards
  stagger in; the pot pulses on change; a glowing chip travels from pot to winning seat(s).

```bash
cd frontend && npm run test -- animated-card poker-table
```

## Part 12 Phase 7: account-wide statistics page:

An aggregation across every session a user has ever played, distinct from the per-session
dashboard (Part 10).

- **`GET /api/users/me/stats`** (new) — `compute_user_stats` fetches every completed-hand
  `HandPlayer` row in two flat queries (not N+1), groups by `hand_history_id` in Python (knowing
  hero won isn't enough to know outright win vs. split — needs every seat's row).
  `cumulative_bankroll_change` sums each session's own persisted `(current_bankroll -
  starting_bankroll)` directly rather than re-deriving from hand deltas. `biggest_win`/
  `biggest_loss` are `None` (not `0`) when there's no hand of that kind yet.
- **`StatsPage`** (new, `/stats`, linked from the header) — reshapes the backend's flat fields
  into the nested shape the existing `WinRateSummary` component already expects, reused as-is.

```bash
pytest tests/backend/test_user_stats_router.py -v
cd frontend && npm run test -- stats-page
```

## Part 12 Phase 8: re-polish Kelly-recommended-stake UI:

Wires hero's live equity and Kelly-recommended stake into the multi-street flow — the columns
Phase 4 added were real but nothing populated them; every hero decision from Phase 5 onward went
straight through `legal_action_bounds` with no equity computed for hero.

- **`_compute_hero_kelly_info`** (new) — hero's equity via `calculate_equity` (3000 simulations,
  more than bots' 750, since this is shown to a human) and Kelly-recommended stake via
  `kelly_fraction_from_pot_odds`. `kelly_recommended_stake` is `None` whenever hero can check for
  free.
- **`HandResponse`** gains top-level `equity_at_decision`/`kelly_recommended_stake`. Same two
  fields land per-action on `HandActionLogEntry`, populated only on hero's own persisted rows.
- Values are computed **before** applying hero's decision, so they reflect what was actually true
  at that moment, not a later recompute with different Monte Carlo noise.
- **`KellyStakePanel`** (built in Part 10, unwired since Phase 6a) is back, restyled to match the
  game screen, showing "Free to check" instead of a nonsensical number when there's nothing to
  call.

**Real, accepted cost**: every hero decision now runs a 3000-simulation equity calculation
(previously only bots paid this). Backend suite wall-clock roughly tripled (~45s → ~140s).

```bash
pytest tests/backend/test_game_router.py -k "equity or kelly_stake" -v
cd frontend && npm run test -- poker-table
```

Part 12 (all 8 phases) is now complete — the full multi-street, multi-opponent engine, backend
wiring, animated frontend, account-wide stats, and live Kelly sizing are built and tested
end-to-end.

## Part 13: Table Redesign, Balance/Performance Tuning, Profile & Play-Style Analytics:

Driven by hands-on feedback from the deployed Part 12 app: table visual/layout requests, a
missing "what did the opponent just do" indicator, interaction latency, a game-balance question
about starting stacks, and two new features (a deeper profile, richer stats with a play-style
spider chart).

### Phase 1: table redesign + opponent action display:

Frontend only.

- **`PokerTable`** — green felt (was black/zinc), a smaller fixed corner radius (was a full pill
  shape), wider container (`max-w-3xl` → `max-w-6xl`). Felt/seats/board now render before any
  hand is dealt, as outlined placeholders, so the table reads as waiting rather than blank.
  Restructured into two columns: felt on the left, a right panel with hero's cards enlarged,
  stack, `KellyStakePanel`, and `ActionControls`.
- **`Seat`** — a transient per-seat action label ("Folds"/"Checks"/"Calls $X"/"Raises +$X"/"Posts
  $X"), sourced from `hand.actions`, cleared after ~1.5s. A brand-new hand doesn't flash its own
  setup/blind actions — only a later response for the *same* hand does.

```bash
cd frontend && npm run test -- poker-table
```

### Phase 2: bot stack balancing + performance:

Both in `backend/services/game_engine.py`.

- **Bot stack balancing** — `_sample_opponent_stack_bb` (new) centers each bot's per-hand stack
  sample on hero's own current bankroll in big blinds, instead of a fixed 50-150bb band unrelated
  to hero. Floor/ceiling clamp the *baseline* being sampled from, not the final stack directly —
  clamping the final value would collapse every bot to the same number once hero is deep enough,
  defeating the point of randomization.
- **Performance** — `HERO_NUM_SIMULATIONS` lowered from 3000 to 1000. Bots' own 750 is untouched.

```bash
pytest tests/backend/test_game_router.py -v
```

### Phase 3: profile page:

- **`users` table** gains nullable `bio`/`avatar_url` (see
  `backend/migrations/0002_part13_profile_columns.sql` for the live-database step). `avatar_url`
  is a pasted image URL, not a real upload — no file/object storage exists in this project, and
  adding one is out of scope for a profile page.
- **`PATCH /auth/me`** (new) updates `display_name`/`bio`/`avatar_url` as a full-form save — a
  blank field clears that column (`blank_to_none` turns empty string into `NULL`).
- **`ProfilePage`** (new, `/profile`) — edits via a new `updateProfile` action on `AuthContext`
  (also refreshes the shared `user`), plus a read-only snapshot of the same account-wide stats
  `/stats` shows. Avatar preview falls back to an initials circle when no URL is set or a set URL
  fails to load.

```bash
pytest tests/backend/test_auth_router.py -v
cd frontend && npm run test -- profile-page use-auth
```

### Phase 4: play-style analytics, spider chart, account-wide bankroll chart:

- **`compute_user_stats`** gains two play-style metrics computed from hero's own persisted
  `HandAction` rows (hero is always `seat_index == 0`):
  - **`vpip_rate`** — fraction of hands hero voluntarily called or raised preflop (a forced blind
    or free check don't count).
  - **`aggression_factor`** — raises-to-calls ratio across every street (checks excluded). `None`
    until hero has made a real call.
  - **`bankroll_history`** — every `BankrollLog` row across every session, chronologically. A
    session boundary shows as a real jump back to that session's `starting_bankroll`, not
    smoothed over.
- **`PlayStyleRadarChart`** (new) — a `recharts` `RadarChart` combining the two new metrics with
  `win_rate`/`fold_rate` (Part 12 Phase 7), normalized to a shared 0-100 scale.
  `aggression_factor` is capped for display only (`AGGRESSION_FACTOR_DISPLAY_CAP = 3`); the raw
  ratio is shown unclamped elsewhere. Rendered on `StatsPage` and `ProfilePage`.
- **`BankrollGrowthChart`**'s `startingBankroll` prop is now optional — the account-wide chart
  has no single "starting" value to mark, so it omits the prop rather than picking one arbitrarily.
- **Fixed a flaky test bug**: `NODE_OPTIONS="--localstorage-file=..."` backs `localStorage` with
  one real file shared across parallel worker threads, letting two test files race on it.
  `vitest.config.js` now sets `fileParallelism: false` — confirmed across 6 repeated full suite
  runs (0 failures vs. intermittent before).

```bash
pytest tests/backend/test_user_stats_router.py -v
cd frontend && npm run test -- play-style-radar-chart stats-page profile-page
```

Part 13 (all 4 phases) is now complete.

## Part 14: Player Education, Advanced Stats & Table Polish:

Driven by feedback on the deployed Part 13 app: a first-time-player tutorial and Kelly education
page, a much richer stat set (PFR, 3-bet%, ATS%, per-street fold/aggression frequency, showdown
stats), and visual polish.

### Phase 1: header + table visual polish:

Frontend only.

- **`AppHeader`** — "Kelly Poker Simulator" goes to `text-xl font-bold`.
- **`PokerTable`** — felt border changes to a solid 8px `border-amber-900` (wood-rail look);
  table widens (`max-w-6xl` → `max-w-7xl`, matched in `GamePage`'s header row).
- **Hero hand panel** — `AnimatedCard` gains an `lg` size (`h-28 w-20`) for hero's own cards; the
  right-side panel widens (`380px` → `440px`) with more padding.

```bash
cd frontend && npm run test -- poker-table animated-card
```

### Phase 2: "How to Play" tutorial page:

New public page (`/how-to-play`), registered outside `ProtectedRoute` so a new visitor can read
it before signing up. Static content: hole cards vs. the board, the four streets, check/call/
fold/raise in plain language, showdown/split pots, and a glossary. The glossary uses a new shared
`GlossaryEntry` component, reused as-is by Phase 3.

`AppHeader` gains a "How to Play" link visible whether or not a user is logged in (previously
every nav link was gated behind `user &&`); Login/Signup also link to it.

```bash
cd frontend && npm run test -- how-to-play
```

### Phase 3: Kelly Criterion education page:

New public page (`/kelly-criterion`), same treatment as Phase 2. Content: the formula explained
term by term, two worked examples (from `poker/kelly.py`'s own tests), a small hand-rolled bar
diagram (no chart library) showing expected log-growth at several stake fractions computed
directly from `expected_log_growth`, and a "beyond poker" section connecting back to the README's
Ed Thorp framing. Reuses Phase 2's `GlossaryEntry`.

```bash
cd frontend && npm run test -- kelly-criterion
```

### Phase 4: position/sequence-aware preflop stats — PFR, 3-bet%, ATS%:

Backend only. These need to know how much action happened before hero's own preflop decision — a
different, sequence-aware computation from Phase 4 (Part 13)'s flat filters, so it gets a shared
helper, `_hero_preflop_decisions`, walking each hand's full action log once.

- **PFR** — fraction of hands where hero's first preflop entry was itself a raise.
- **3-bet%** — of hands hero faced an existing preflop raise ("opportunity"), the fraction hero
  re-raised.
- **ATS%** — hero on the button with action folded to them ("opportunity"); fraction hero raised.
  Only meaningful for 2+ opponents.

**A real finding**: a genuine opponent preflop raise before hero's turn is structurally rare
through the live bot pipeline — not a bug, just how existing bot sizing behaves (raise sizing is
a fraction of the current pot, almost always below the legal minimum at a blinds-only pot). The
3-bet% test constructs its scenario directly (a new `_insert_complete_hand` helper writing rows
straight to the test DB) rather than retrying live deals.

```bash
pytest tests/backend/test_user_stats_router.py -v
```

### Phase 5: showdown, per-street, and volume stats:

Backend only, same file.

- **WTSD%** — fraction of all hands where more than one seat was non-folded at completion.
- **W$SD%** — of showdown hands, the fraction hero won. `None` until hero reaches a showdown.
- **WWSF%** — of hands hero saw a flop, the fraction hero won.
- **Per-street fold/aggression frequency** — folds/raises over hero's own real decisions per
  street (excludes blinds). `None` for a street with no decisions yet.
- **`hands_won`** and **`sessions_won`** (ended sessions where `current_bankroll >
  starting_bankroll`).

The `_insert_complete_hand` test helper is generalized to accept an arbitrary player list and
board, since these scenarios need exact multi-seat/multi-street control.

```bash
pytest tests/backend/test_user_stats_router.py -v
```

### Phase 6: stats dashboard overhaul — charts + performance coloring:

Frontend only, the final phase of Part 14.

- **New `stat-classifier.js`** — `classifyStat(statKey, value)` maps a raw stat to `'good' |
  'critical' | 'neutral'` against standard poker HUD guidance, reusing `StatTile`'s existing
  color tokens. `null` or an uncovered stat resolves to `'neutral'`.
- **`PlayStyleRadarChart`** extended to 5 axes (adds PFR); each axis dot is colored via
  `classifyStat` through a custom SVG renderer (recharts has no per-vertex fill by default).
- **New `StatRadialGauge`** — a single-stat circular gauge (`recharts` `RadialBarChart`), colored
  the same way. Rendered per headline stat on `StatsPage`; a trimmed pair on `ProfilePage`.
- **`StatsPage`** also gains a per-street fold/aggression section (plain tiles, not classified —
  thresholds are context-dependent), `sessions_won`/`hands_won` tiles, and relabels "Cumulative
  change" to "All-time winnings."

```bash
cd frontend && npm run test -- stat-classifier stat-radial-gauge play-style-radar-chart stats-page profile-page
```

Part 14 (all 6 phases) is now complete.

## Part 15: Illustrated Education, Dark-Mode Pages, Stat Tooltips & Table Layout Fixes:

Driven by feedback on the deployed Part 14 app: text-only education content (no illustrated hand
rankings, no visual street example, no starting-hand chart), stats abbreviations with no in-app
explanation, and two table layout bugs (a seat rendering off the felt, hero panel misaligned with
the table bottom). A separate ask (animations via the `magic` MCP server) is on hold pending a
working API key.

### Phase 1: table layout fixes — seat position, bottom alignment, glow border:

Frontend only.

- **Left-side seat clipping the felt** — 3/4-opponent layouts placed the leftmost seat at `left:
  6%`, which combined with the seat's own width put its edge past the felt's left border. Moved
  to `10%` (mirrored right seat `94%` → `90%`) so the full seat stays inside the felt.
- **Hero panel bottom vs. table bottom** — the two-column row was `lg:items-start` (top-aligned
  only); changed to `lg:items-end` so both columns' bottoms line up.
- **Glow border** — the felt's inset shadow is now combined with a soft outward emerald glow
  matching the felt's own gradient.

```bash
cd frontend && npm run test -- poker-table
```

### Phase 2: dark mode for Login, Signup, How to Play, and Kelly Criterion:

Frontend only. No global theme toggle needed: `index.css` already shipped a complete, unused
`.dark { ... }` token override as shadcn boilerplate, and all four pages were already built from
semantic tokens. Each page's root now carries `className="dark bg-background text-foreground
..."`, cascading the existing dark tokens to that page's subtree without touching any other page.

```bash
cd frontend && npm run test -- login-page signup-page how-to-play kelly-criterion
```

**Addendum**: extended the same wrapper to `lobby-page.jsx`, `profile-page.jsx`, and
`stats-page.jsx` after using the deployed app showed these should read dark too. `StatRadialGauge`
also gained an explicit `background={{ fill: 'var(--muted)' }}`, since it isn't wrapped in the
shared `ChartContainer` that neutralizes recharts' hardcoded light-gray default elsewhere.

### Phase 3: illustrated hand rankings + illustrated preflop/flop/turn/river example:

Frontend only, reusing the existing static `PlayingCard` rather than `AnimatedCard`'s deal/flip
machinery, which this content doesn't need.

- **New `hand-rankings.jsx`** — the 10 standard categories, worst to best, each with a concrete
  5-card example and one-line description.
- **New `street-progression.jsx`** — a single worked hand across all 4 streets, board building 0
  → 3 → 4 → 5 cards, undealt slots as dashed placeholders matching the live table. Replaces the
  previous plain-text bullet list.

```bash
cd frontend && npm run test -- how-to-play
```

### Phase 4: 13x13 starting-hand matrix, color-coded worst to best:

Frontend only. New `starting-hand-strength.js` scores all 169 starting-hand classes with the
standard **Chen Formula** (highest-card value, doubled for pairs, +2 suited, gap penalty, +1
straight-making bonus) — famously scores 7-2 offsuit among the worst hands, matching its folklore
reputation. `strengthColor(score)` interpolates a continuous red → amber → green scale across the
table's own min/max (a full ranking, not a threshold split).

New `starting-hand-matrix.jsx` renders the classic 13x13 grid (pairs diagonal, suited above,
offsuit below), wrapped in `overflow-x-auto`. Inserted after "The four streets."

```bash
cd frontend && npm run test -- starting-hand how-to-play
```

### Phase 5: stat tooltips on the Stats page:

Frontend only. New `tooltip.jsx` — a thin wrapper around `radix-ui`'s `Tooltip` primitives
(already a dependency), styled to match the other shadcn components. New `stat-descriptions.js` —
full-name + one-sentence definitions for every abbreviation on the page.

Both `StatTile` and `StatRadialGauge` gain an optional `tooltip` prop — a hover-info icon renders
next to the label when passed, so the affordance lives in those two components once.
`WinRateSummary` and `StatsPage` now pass a tooltip for every stat.

```bash
cd frontend && npm run test -- stat-tile stat-radial-gauge stats-page
```

Phases 1-5 of Part 15 are now complete. A 6th, deferred phase (animations/UI polish via the
`magic`/`21st` MCP tools) is on hold pending a working connection.
