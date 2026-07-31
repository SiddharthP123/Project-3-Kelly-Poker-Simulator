"""Applies every .sql file in this directory, in filename order, against
whatever DATABASE_URL points at.

Still not Alembic (see backend/database.py's docstring) -- these are
one-off, hand-written, idempotent ALTER TABLE scripts for the handful of
columns create_all() can't add to an already-live table (it only creates
missing tables, never alters existing ones). This script just removes the
need to run `psql -f ...` by hand; it's still something you run
yourself, deliberately, the same way you already run create_tables.py --
nothing in the app or deploy process calls this automatically.

Run from the project root:
    source venv/bin/activate
    PYTHONPATH=. python3 backend/migrations/run_migrations.py
"""

from pathlib import Path

from sqlalchemy import text

from backend.database import engine

MIGRATIONS_DIR = Path(__file__).parent


def run_migrations():
    sql_files = sorted(MIGRATIONS_DIR.glob('*.sql'))
    if not sql_files:
        print('No .sql migration files found.')
        return

    with engine.begin() as connection:
        for sql_file in sql_files:
            statements = [s.strip() for s in sql_file.read_text().split(';') if s.strip()]
            for statement in statements:
                connection.execute(text(statement))
            print(f'Applied {sql_file.name} ({len(statements)} statement(s))')

    print(f'Migrations applied against {engine.url}')


if __name__ == '__main__':
    run_migrations()
