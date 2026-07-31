# Manual migrations

This project deliberately has no Alembic yet (see `backend/database.py`'s docstring) --
`backend/create_tables.py`'s `Base.metadata.create_all()` is the only schema tool, and it only
ever creates tables that don't exist yet. It never alters an existing table, so a new nullable
column on a table that's already live (with real rows in it) needs one manual step outside that
normal flow.

A fresh database (a new local SQLite test db, a brand new Postgres instance) never needs this --
`create_all()` already creates every table with every column defined on the model today, including
these. This only matters for a database that already has `game_sessions`/`hand_histories` rows in
it from before the column was added (in practice: the live Render Postgres).

## `0001_part12_multi_opponent_columns.sql`

Adds the Part 12 columns to the two existing tables (`game_sessions`, `hand_histories`) that
`poker/hand_flow.py`'s multi-opponent, multi-street hands need. All four columns are nullable, so
this is purely additive -- existing rows just get `NULL` in the new columns, nothing is rewritten
or dropped. Run once, manually, against the real database, before Phase 5 (backend wiring) needs
these columns to exist:

```bash
psql "$DATABASE_URL" -f backend/migrations/0001_part12_multi_opponent_columns.sql
```

The new tables Part 12 also introduces (`game_session_opponents`, `hand_players`, `hand_actions`)
need **no manual step** -- they're brand new tables, so `create_tables.py`'s existing
`create_all()` already creates them the next time it's run (or the next time the backend process
starts, if that's wired to call it).
