# Project 3: Kelly Poker Simulator

A progressive, self-taught, full-stack project that builds a Texas Hold'em simulator with AI
opponents and a virtual bankroll manager sized using the **Kelly Criterion**.

No real money is involved anywhere — this is a simulator/game against AI opponents using a
virtual bankroll only.

## Why poker?

The Kelly Criterion was originally developed for gambling/bankroll management and is the exact
same formula used for position-sizing in real investment portfolios (Ed Thorp — professional
card counter turned quant hedge fund manager — is the classic example). Poker gives a clean,
self-contained environment (known edge, known odds, discrete bets) to learn the formula before
applying the same thinking to a portfolio.

## Tech stack

- **Backend:** FastAPI (Python)
- **Frontend:** React
- **Database:** PostgreSQL
- **Auth:** JWT-based authentication (password hashing, protected routes)

Early parts (1–7) are plain Python with no web stack — the goal is to get the game/math logic
solid and tested before any API or UI is built on top of it.

## Progress

| Part | Topic | Status |
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
| 10 | Frontend (React) | ⬜ Not started |
| 11 | Deployment | ⬜ Not started |

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pytest
```

---

## Part 1: Cards, Deck & Dealing

**Key insight:** A deck is just 52 unique `(rank, suit)` pairs. Dealing without duplicating cards
is trivial if you treat the deck as a mutable pool you *remove* cards from — once a card is dealt,
it physically leaves the deck, so there is no way to deal it twice. That single design decision
(deal = pop from the deck) is what guarantees no-duplicate dealing, rather than any explicit
"has this card already been dealt?" check.

- `poker/cards.py` — `Suit` and `Rank` enums, and an immutable `Card` (rank + suit), with a
  compact string form (e.g. `Ah` = Ace of hearts, `Tc` = Ten of clubs — standard poker notation,
  `T` for ten avoids confusion with `10` taking two characters).
- `poker/deck.py` — `Deck` builds all 52 cards, `shuffle()`s them, and deals via `deal(n)`
  (generic), `deal_hole_cards(num_players)` (2 cards per player, one at a time in dealing order),
  and `deal_community(n)` (flop/turn/river).

Run just this part's tests:

```bash
pytest tests/test_cards.py tests/test_deck.py -v
```

---

## Part 2: Hand Evaluator

**Key insight:** every 5-card hand can be reduced to one sortable tuple:
`(category, tiebreakers)`. Once every hand is turned into one of these tuples, deciding a winner
is just Python's `max()` over tuples — no special-cased "if flush beats straight" logic is
needed anywhere, because tuple comparison already checks the category first and only falls
through to tiebreakers when two hands share a category.

The tiebreakers themselves come from one trick: group the 5 ranks by how often each appears,
then sort those groups by `(count, rank)` descending. That single ordering produces the correct
tiebreak order for every category that involves duplicate ranks — e.g. for two pair the result is
`(high_pair, low_pair, kicker)`, which is exactly the order poker rules say to compare in (higher
pair first, even if the other hand's low pair or kicker is better).

Two things need special-casing on top of that: straights (need 5 *distinct*, consecutive ranks —
including the "wheel", A-2-3-4-5, where the Ace plays low and the straight is 5-high, not
Ace-high) and flushes (all 5 cards share a suit). A straight flush is just a hand that is both.

- `poker/hand_evaluator.py` — `HandCategory` (ordered enum, high card through straight flush),
  `evaluate_5(cards)` for exactly 5 cards, `best_hand(cards)` for 5-7 cards (checks all `C(7,5) =
  21` five-card combinations and keeps the best — simple brute force, fast enough at this scale),
  and `compare_hands(hands)` which returns the winning player index/indices (more than one index
  means a split pot).

Run just this part's tests:

```bash
pytest tests/test_hand_evaluator.py -v
```

---

## Part 3: Monte Carlo Equity Calculator

**Key insight:** we don't know the opponents' hole cards or the rest of the board, but we do
know the pool of cards they could possibly be. Rather than solving the win probability
analytically (the exact combinatorics get messy fast), we repeatedly guess a plausible
reality — deal the unknown cards at random, see who wins with Part 2's `compare_hands` — thousands
of times, and let the win rate converge to the true probability. Same Monte Carlo idea as
Project 1, just applied to cards instead of price paths.

`calculate_equity(hole_cards, num_opponents, board, num_simulations, seed)` returns an
`EquityResult` with `win` / `tie` / `lose` shares plus `equity` — the expected pot share (1 per
outright win, 1/n per n-way tie, 0 per loss). `equity` is the number later parts (EV, Kelly)
actually need, since a tie only wins back a fraction of the pot, not the whole thing.

Sanity-checked against a well-known benchmark: pocket Aces heads-up against one random hand wins
**85.2%** of the time over 20,000 simulations, matching the commonly cited ~85% figure almost
exactly.

- `poker/equity.py` — `EquityResult` dataclass, `calculate_equity(...)`. Opponents are assumed to
  hold uniformly random hole cards (no modelled "range") — the standard, simplest equity
  calculation, and the one the AI opponents in Part 7 will call directly.

Run just this part's tests:

```bash
pytest tests/test_equity.py -v
```

---

## Part 4: Expected Value & Pot Odds

**Key insight:** pot odds convert a bet size into a probability threshold. Given a pot of size
`P` facing a bet of `B`, calling breaks even when `equity * P == (1 - equity) * B` — solving for
equity gives `B / (P + B)`, the minimum win probability needed to call profitably. Comparing
Part 3's simulated equity against that single number tells you whether to call, without ever
computing a dollar EV. This is the exact same "compare an estimated probability to a break-even
threshold" logic used to judge whether an investment's expected return justifies its risk.

Raising is modelled as a probability-weighted mix of two outcomes: the opponent folds now (you
win the pot as it stands) or they call (it goes to showdown, and the math collapses back to the
same call-EV formula, just using the raise size as the bet). No full game-tree solving needed —
just one extra input, an assumed fold probability.

- `poker/ev.py` — `pot_odds_breakeven_equity(pot_size, bet_to_call)`, `ev_fold()` (always 0 —
  folding risks and wins nothing further), `ev_call(equity, pot_size, bet_to_call)`,
  `ev_raise(equity, pot_size, raise_amount, fold_probability)`, and `best_action(...)` which picks
  the highest-EV action out of fold/call/(optional) raise and returns a `Decision` showing the EV
  of every option considered.

Run just this part's tests:

```bash
pytest tests/test_ev.py -v
```

---

## Part 5: The Kelly Criterion

**This is the finance parallel the whole project is built around.** Kelly was developed for
exactly this kind of gambling problem — what fraction of your bankroll to stake on a repeatable
bet with a known edge — but the identical formula is used to size positions in a real investment
portfolio. If you have an edge (expected return better than break-even) and know the "odds" (the
payoff structure of the bet/trade), Kelly gives the fraction of capital to allocate that
maximises long-run *compound* growth. Ed Thorp used this exact reasoning to go from card
counting in blackjack to running a hedge fund.

**Key insight:** Kelly isn't derived by guesswork — it's the fraction `f` that maximises expected
*log*-growth per bet, `g(f) = p·ln(1 + f·b) + q·ln(1 - f)`, not expected value. Log-growth (not
plain EV) is the right thing to maximise for a bet you repeat many times, because bankroll
compounds multiplicatively — maximising raw EV instead would push you toward betting your whole
bankroll every time, which guarantees eventual ruin. Setting `g'(f) = 0` and solving gives the
closed-form formula: `f* = (p·b − q) / b`. The test suite proves this directly — for several
`(p, b)` pairs, it checks that `expected_log_growth` at the computed Kelly fraction is never
beaten by any nearby fraction, confirming the formula really is the calculus-derived optimum, not
just a memorised expression.

A negative `f*` means there's no edge at all — the correct action is to bet nothing, not to bet a
negative amount (you can't take the other side of a poker hand you're already holding).
`fractional_kelly` clips this to 0. It also supports betting less than full Kelly ("half Kelly"
etc.) — growth near the Kelly peak is flat, but variance keeps rising linearly with bet size, so
practitioners commonly trade a little growth for meaningfully lower drawdowns. Part 6 compares
these strategies directly.

- `poker/kelly.py` — `kelly_fraction(win_probability, odds)` (raw formula), `fractional_kelly(...,
  fraction=1.0)` (clipped, scalable), `kelly_fraction_from_pot_odds(equity, pot_size,
  bet_to_call, kelly_multiplier=1.0)` (bridges Parts 3 & 4 — calling risks `bet_to_call` to win
  `pot_size`, i.e. "b to 1" odds of `pot_size / bet_to_call`), and `expected_log_growth(...)` (the
  theoretical justification, and the same function real position-sizing math uses).

Run just this part's tests:

```bash
pytest tests/test_kelly.py -v
```

---

## Part 6: Bankroll Simulator

**Key insight:** the "aggressive growth vs. safety" trade-off in bet sizing isn't a matter of risk
tolerance — it's a direct mathematical consequence of how the *same* sequence of wins and losses
compounds under different stake sizes. Past the Kelly fraction, both risk of ruin **and** long-run
growth get worse together, because a big loss erases gains faster than wins can rebuild them.
Kelly betting can never hit exactly zero from a finite run of bets (every stake is a fraction
below 1 of whatever remains — "Kelly can't go broke"), while all-in betting means any single loss
is total, immediate ruin. Part 5 proved the growth-maximising property algebraically; this part
demonstrates the ruin side of the story empirically, simulating the same modest edge
(55% win probability, even-money odds) under four staking strategies over 200 hands:

![Bankroll growth curves by staking strategy](docs/part-6-plots/bankroll_growth_curves.png)

![Risk of ruin and median final bankroll by strategy](docs/part-6-plots/risk_of_ruin_comparison.png)

Full Kelly has both the **highest median outcome** and **zero risk of ruin** — it isn't a
trade-off between the two, it strictly dominates every less-adapted strategy tested. All-in has
the same edge but a 100% risk of ruin, because surviving 200 hands undefeated at 55% is
astronomically unlikely, and a single loss with an all-in stake is unrecoverable.

- `poker/bankroll.py` — `fixed_stake_strategy`, `kelly_strategy(kelly_multiplier)`,
  `all_in_strategy` (three staking strategies, each a function of `(initial_bankroll,
  current_bankroll, win_probability, odds) -> stake_amount`), `simulate_session` (one sequence of
  hands under a strategy), and `simulate_many_sessions` (the Monte Carlo layer — same idea as
  Part 3's equity calculator, applied to bankroll trajectories instead of single hands),
  reporting risk of ruin and mean/median final bankroll.
- `scripts/plot_bankroll_comparison.py` — generates the two plots above via matplotlib (added as a
  dependency specifically for this part).

Run just this part's tests:

```bash
pytest tests/test_bankroll.py -v
```

Regenerate the plots:

```bash
PYTHONPATH=. python3 scripts/plot_bankroll_comparison.py
```

---

## Part 7: Simple AI Opponents

**Key insight:** every persona differs only in *which numbers* it uses to turn the same equity
estimate into a decision — the fold/call/raise vocabulary, and the "never raise more than your
bankroll" rule, are shared by all of them. `TightAggressiveBot` and `LoosePassiveBot` are the same
`ThresholdBot` logic (fold below one equity bar, raise above another, call in between) with
different constants plugged in — tight-aggressive folds most hands but raises big with the few it
plays; loose-passive ("calling station") folds almost nothing but rarely raises even with a
monster. `RandomBot` ignores equity entirely, as a control/baseline the smarter personas can be
judged against.

`KellyOptimalBot` is the "textbook" persona, sizing every decision straight from Part 5's Kelly
Criterion instead of fixed heuristics — and it doesn't need to separately re-run Part 4's pot-odds
check to decide whether to fold. Kelly's numerator (`p·b − q`) is positive exactly when calling is
+EV under pot odds, because Part 4's breakeven equity (`bet / (pot + bet)`) and Kelly's "no edge"
point (`1 / (b + 1)`, where `b = pot/bet`) are algebraically the same number. So for this bot,
"Kelly recommends staking nothing" and "folding is correct" are one condition, not two — Parts 3,
4, and 5 collapse into a single Kelly-stake calculation.

- `poker/bots.py` — `Action` (fold/call/raise + amount), `Bot` base class (bankroll-capping +
  `decide_from_hand`, which runs Part 3's real Monte Carlo equity calculator end-to-end),
  `ThresholdBot` → `TightAggressiveBot` / `LoosePassiveBot`, `RandomBot`, `KellyOptimalBot`.

Run just this part's tests:

```bash
pytest tests/test_bots.py -v
```

---

## Part 8: Backend API (FastAPI)

**Key insight:** turning the engine into a service is mostly about translation, not new logic —
every "calculator" endpoint (`/api/equity`, `/api/ev`, `/api/kelly/*`, `/api/hand-evaluator/*`,
`/api/bots/decide`) is a thin Pydantic-schema-in → `poker/` function call → Pydantic-schema-out
wrapper. The one genuinely new piece is `services/game_engine.py::play_hand`, which settles a
real hand's outcome by feeding the *realized* result (win = 1, n-way split = 1/n, loss = 0) back
into Part 4's `ev_call` formula — the exact same call-EV math used for decision-making now
computes the actual bankroll change too, so no separate settlement formula was needed.

Hero is auto-played by a fixed `KellyOptimalBot` in this part — there's no interactive UI yet for
a human to submit a decision from (that's Part 10). `GameSession.bot_persona` is the actual named
opponent. A hand is a single fixed-stakes decision (pot-sized bet, 1:1 odds, 50% breakeven) rather
than a full multi-street betting engine — enough to prove deal → decide → showdown → persist
end-to-end without building a complete rules engine this part doesn't need yet.

`backend/` is a new top-level package, sibling to `poker/` (never nested inside it — `poker/`
stays a framework-agnostic library `backend/` imports from, never the reverse):

- `backend/models/` — SQLAlchemy models: `User` (minimal, `user_id` is nullable everywhere until
  Part 9 adds real auth), `GameSession`, `HandHistory` (one row per hand; `opponent_hole_cards`
  is only ever populated at showdown — a folded opponent's cards are never revealed, matching real
  poker), `BankrollLog` (a dedicated append-only time series, separate from `HandHistory`
  specifically so a Part-6-style growth chart is a plain ordered `SELECT`, not an aggregation
  query).
- `backend/routers/` + `backend/schemas/` — the calculator endpoints above, plus the stateful
  `/api/game/sessions/*` endpoints (create session, play a hand, list hand history, fetch bankroll
  history, end session). Every request schema inherits `extra='forbid'` (the Pydantic/Zod-strict
  equivalent), and card strings are validated through `Card.from_str` at the schema layer so bad
  notation 422s cleanly instead of 500ing inside `poker/`.
- Rate limiting via `slowapi`: calculator endpoints (compute-only, even though POST) get a
  100/15min "reads" bucket; `/api/game/sessions/*` writes get 50/15min — IP-based only until
  Part 9 has a JWT to key per-user limits off.
- **Testing runs entirely on SQLite** (`tests/backend/conftest.py` overrides FastAPI's `get_db`
  dependency with a per-test temp-file database) — no Postgres needs to be running for `pytest` to
  pass. Real Postgres is only used for actual local dev/run.

Three implementation defaults were set without a full stop to ask, since each is easily revisited
later without redoing work: **Alembic deferred** in favour of `Base.metadata.create_all()` (no
production data to protect yet); **`User` rows are optional** in this part (`GameSession.user_id`
nullable, no user-management endpoint — Part 9 owns signup); and the ORM/schema pairing is plain
**SQLAlchemy + separate Pydantic schemas** (not SQLModel) and local Postgres runs via **Docker
Desktop + docker-compose** — both confirmed with the project owner before implementation, since
they shape a lot of downstream code and neither Docker nor Postgres was already installed on this
machine.

### Running it locally

```bash
# One-time: install Docker Desktop (github.com/docker/docker-compose is bundled),
# then from the project root:
docker compose up -d          # starts Postgres on localhost:5432
cp .env.example .env          # fill in real values if you changed docker-compose.yml
source venv/bin/activate
PYTHONPATH=. python3 backend/create_tables.py   # stands up the schema (no Alembic yet)
uvicorn backend.main:app --reload
# Then visit http://localhost:8000/docs for the interactive Swagger UI.
```

Run just this part's tests (no Docker/Postgres needed):

```bash
pytest tests/backend/ -v
```

---

## Part 9: Authentication & Security

**Key insight:** JWTs are stateless — the server never stores issued tokens anywhere; it just
verifies the signature and expiry on each request. That's what makes `get_current_user` a single
fast dependency with no database round trip needed to validate the token itself (only to load the
user row it names). The whole auth layer is really just two small pieces bolted onto what Part 8
already built: `backend/security.py` (hash/verify passwords with bcrypt, issue/decode JWTs) and one
`Depends(get_current_user)` added to every `/api/game/sessions/*` endpoint.

Two security details worth calling out explicitly:
- **Login failures are indistinguishable.** An unknown email and a correct email with the wrong
  password both return the exact same 401 + generic message — separating them would let an
  attacker enumerate which emails have accounts.
- **A session belonging to someone else 404s, not 403s.** Returning 403 would confirm the session
  ID is real; 404 (session not found, full stop) leaks nothing about what exists behind the
  ownership check, matching the project's standing "verify ownership before allowing
  modifications" convention.

Auth endpoints (`/api/auth/signup`, `/api/auth/login`) get their own tight rate-limit bucket
(5/15min) — separate from the general reads/writes buckets — since credential endpoints are the
classic brute-force target. `User.starting_bankroll` (added in Part 8, unused until now) gets its
first real use: creating a game session without specifying `starting_bankroll` falls back to the
signed-up user's own default.

One real bug surfaced and fixed while testing this: the `slowapi` rate limiter is a
process-wide singleton, so without resetting it between tests, exhausting the 5/15min auth bucket
in one test starved every later test hitting the same endpoint (all `TestClient` requests share a
fake IP). Fixed with an `autouse` `reset_rate_limiter` fixture in `tests/backend/conftest.py`.

- `backend/security.py` — `hash_password`/`verify_password` (bcrypt), `create_access_token`/
  `get_current_user` (PyJWT, `HS256`, configurable expiry).
- `backend/routers/auth.py` — `POST /api/auth/signup` (creates the user, returns a token
  immediately), `POST /api/auth/login`, `GET /api/auth/me`.
- `backend/routers/game.py` — every endpoint now requires `Depends(get_current_user)`;
  `_get_owned_session_or_404` enforces the ownership check described above.
- Chose **bcrypt + PyJWT** over the brief's originally-named passlib/python-jose (both showing
  their age maintenance-wise) and confirmed **login is required** for game sessions (not
  optional/anonymous) with the project owner before implementation.

Smoke-tested end-to-end against the real Postgres container (not just SQLite tests): signup →
`/me` → create session (defaulting bankroll correctly) → play a hand → a second user gets a clean
404 trying to touch the first user's session → login with correct/wrong credentials.

Run just this part's tests (no Docker/Postgres needed):

```bash
pytest tests/backend/test_auth_router.py -v
```

### Security hardening pass

Before moving on to Part 10, the backend was audited against every item in this project's
standing `CLAUDE-CODE-INSTRUCTIONS.md` security checklist (translating Firebase/Next.js-specific
items to their FastAPI/Postgres equivalents). Already-compliant: no raw SQL anywhere (ORM-only),
no hardcoded real secrets, debug mode off, strict schema validation (`extra='forbid'`) everywhere,
rate-limit buckets on every endpoint except `/health` (intentionally unthrottled — a trivial,
no-DB liveness check). Five real gaps were found and fixed:

- **`Retry-After` was missing from 429 responses** — `slowapi`'s `Limiter` needed
  `headers_enabled=True` explicitly. That setting has a real consequence: slowapi then tries to
  inject rate-limit headers into *every* response, success or not, which requires each rate-limited
  endpoint to accept a `response: Response` parameter (FastAPI's mutable response object) — added
  to all 16 rate-limited routes.
- **No per-user rate limiting** — only IP-based existed. Added `USER_HOURLY_LIMIT` (1000/hour),
  stacked on top of (not instead of) the existing IP-based limits on every `/api/game/sessions/*`
  route, keyed by `user_id_or_ip_key` (decodes the bearer token to key by user id when present,
  falling back to IP otherwise). This protects against a single compromised/shared token being
  used across many different source IPs — a threat IP-based limiting alone can't see.
- **No security response headers at all** — added `backend/middleware.py`
  (`SecurityHeadersMiddleware`): `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`,
  `Permissions-Policy`, `X-XSS-Protection`, `Content-Security-Policy: default-src 'none'` (this API
  only ever returns JSON), and `Strict-Transport-Security` (harmless over local HTTP, takes effect
  once deployed over HTTPS in Part 11).
- **Three unbounded list fields** — `EquityRequest.board` / `BotDecideRequest.board` had no
  `max_length` (a board is never more than 5 cards), and `CompareHandsRequest.hands` had no cap on
  either the number of hands *or* cards per hand. All three now enforce the same bounds
  `poker/`'s own functions expect, rejecting oversized input at the schema layer (422) instead of
  after partial validation work.
- **Zero logging anywhere** — failed logins vanished silently. Added stdlib `logging` (no new
  dependency): failed login attempts and duplicate-signup attempts log the email + IP (never the
  password), rejected tokens log the failure type (never the token itself), and rate-limit
  breaches log the IP + path.

Re-verified end-to-end against the real Postgres container after the fixes: security headers
present on a live response, gameplay still works unaffected, oversized input still 422s, and a
6th rapid login attempt returns a real `Retry-After` value.

Run just the hardening tests:

```bash
pytest tests/backend/test_security_hardening.py -v
```
