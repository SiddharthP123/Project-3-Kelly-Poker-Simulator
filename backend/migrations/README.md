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
or dropped.

Run it with `backend/migrations/run_migrations.py` (applies every `.sql` file in this directory,
in filename order, via SQLAlchemy against whatever `DATABASE_URL` points at -- no `psql` needed):

```bash
source venv/bin/activate
DATABASE_URL="<the real database URL>" PYTHONPATH=. python3 backend/migrations/run_migrations.py
```

This is still a command **you** run deliberately, once, before Phase 5 needs these columns --
nothing in the app or deploy process calls it automatically (same as `create_tables.py`). Each
statement uses `IF NOT EXISTS`, so running it more than once (or against a database that already
has these columns) is a safe no-op -- confirmed by running it twice in a row against a real local
Postgres container during development.

The new tables Part 12 also introduces (`game_session_opponents`, `hand_players`, `hand_actions`)
need **no manual step** -- they're brand new tables, so `create_tables.py`'s existing
`create_all()` already creates them the next time it's run.
