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
| 2 | Hand Evaluator | ⬜ Not started |
| 3 | Monte Carlo Equity Calculator | ⬜ Not started |
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
