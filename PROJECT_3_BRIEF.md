# Project 3: Kelly Criterion Poker Simulator — Project Brief

Hand this file to Claude Code in VS Code to kick off the build. It has the full plan so Claude Code doesn't need to guess at scope.

## What this project is

A progressive, self-taught project (same style as "Project 1: Learning Python with Finance") that builds a full-stack poker simulator with AI opponents and a virtual bankroll manager, using the Kelly Criterion to size bets. The Kelly Criterion is the direct bridge to finance: it was developed for gambling/poker bankroll management and is the same formula used for position-sizing in real investment portfolios (Ed Thorp is the classic example — professional card counter turned quant hedge fund manager).

No real money is involved anywhere — it's a simulator/game against AI opponents with a virtual bankroll only.

## Goals

- Learn the math: hand equity, expected value, pot odds, the Kelly Criterion, risk of ruin.
- Learn full-stack web development: Python backend, React frontend, a real database, authentication.
- End up with a public GitHub repo worth showcasing, following the same "Part 1, Part 2, ... Part N" progressive structure as Project 1.

## Tech stack

- **Backend:** FastAPI (Python)
- **Frontend:** React
- **Database:** PostgreSQL
- **Auth:** JWT-based authentication (password hashing, protected routes)

## Repo

New public GitHub repo: `Project-3-Kelly-Poker-Simulator` (or similar — Claude Code can suggest final naming). Owner: SiddharthP123. Same account as `Project-1-Monte-Carlo-Simulation-Model` and `Project-2-SafeLink-Mobile-App`.

## Roadmap (progressive parts, like Project 1)

Build and commit these roughly in order. Early parts are plain Python (no web stack needed yet) so the core game/math logic is solid and tested before any web app is built on top of it.

1. **Cards, Deck & Dealing** — represent a 52-card deck, shuffle, deal hole cards + board for Texas Hold'em without duplicating cards.
2. **Hand Evaluator** — rank 5-7 card poker hands (pair, straight, flush, etc.) and compare hands to find a winner.
3. **Monte Carlo Equity Calculator** — given hole cards (and optionally a partial board), simulate thousands of run-outs to estimate win probability. Mirrors the Monte Carlo approach from Project 1.
4. **Expected Value & Pot Odds** — compute the breakeven equity needed to call a bet, and EV of calling/folding/raising given estimated equity.
5. **The Kelly Criterion** — implement the Kelly formula for optimal bet sizing given edge and odds. Explain the finance parallel explicitly in this part's README/comments (position sizing in a portfolio uses the identical formula).
6. **Bankroll Simulator** — Monte Carlo simulate many sessions/hands under different staking strategies (fixed stake, full Kelly, fractional Kelly, all-in) and plot bankroll growth curves and risk of ruin for each.
7. **Simple AI Opponents** — rule-based bot personas (e.g., tight-aggressive, loose-passive, random, Kelly-optimal) that make call/fold/raise decisions using the equity calculator and EV logic from earlier parts.
8. **Backend API (FastAPI)** — expose the game engine, equity calculator, Kelly calculator, and AI opponents as REST endpoints. Set up database models: User, GameSession, HandHistory, BankrollLog.
9. **Authentication & Security** — user signup/login, password hashing (e.g., bcrypt/passlib), JWT issuing and validation, protected routes.
10. **Frontend (React)** — poker table UI to play hands against the AI opponents, a bankroll dashboard showing virtual bankroll over time, live Kelly-recommended bet sizing shown during play, and charts (bankroll growth, win rate).
11. **Deployment** — deploy backend (e.g., Render/Railway) and frontend (e.g., Vercel) so there's a live demo link, same as Project 1's Streamlit Cloud deployment.

## Learning style

Progressive and explained, not just generated. For each part: explain the concept briefly (in code comments and/or a short README section) before or alongside the implementation, the way Project 1 documents "Key insight" for each part. The user wants to actually learn the math and the full-stack concepts along the way, not just receive finished code.

## Suggested first prompt to Claude Code

> Read PROJECT_3_BRIEF.md in this repo. Let's start with Part 1: Cards, Deck & Dealing. Set up a new git repo locally, create the file structure, implement it in Python, explain the key concepts as we go, and test that it works before moving on.
