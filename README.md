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
| 7 | Simple AI Opponents | ⬜ Not started |
| 8 | Backend API (FastAPI) | ⬜ Not started |
| 9 | Authentication & Security | ⬜ Not started |
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
