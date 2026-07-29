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
| 4 | Expected Value & Pot Odds | ⬜ Not started |
| 5 | The Kelly Criterion | ⬜ Not started |
| 6 | Bankroll Simulator | ⬜ Not started |
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
