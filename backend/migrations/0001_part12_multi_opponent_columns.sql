-- Part 12 (Real Poker Engine): nullable columns needed on two tables that
-- already exist in production, so create_all() can't add them on its own.
-- See backend/migrations/README.md for when/how to run this.
--
-- All four columns are nullable -- existing rows simply get NULL, no
-- backfill required. Safe to run more than once (IF NOT EXISTS guards).

ALTER TABLE game_sessions ADD COLUMN IF NOT EXISTS num_opponents INTEGER;
ALTER TABLE game_sessions ADD COLUMN IF NOT EXISTS small_blind DOUBLE PRECISION;
ALTER TABLE game_sessions ADD COLUMN IF NOT EXISTS big_blind DOUBLE PRECISION;

ALTER TABLE hand_histories ADD COLUMN IF NOT EXISTS button_seat INTEGER;
ALTER TABLE hand_histories ADD COLUMN IF NOT EXISTS street VARCHAR(10);
