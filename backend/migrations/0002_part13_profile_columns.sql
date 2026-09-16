-- Part 13 Phase 3 (Profile page): nullable columns on the existing `users`
-- table, which already has real rows in production. See
-- backend/migrations/README.md for when/how to run this.
--
-- Both columns are nullable -- existing rows simply get NULL until their
-- owner fills their profile in. Safe to run more than once (IF NOT EXISTS
-- guards).

ALTER TABLE users ADD COLUMN IF NOT EXISTS bio VARCHAR(500);
ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(2048);
