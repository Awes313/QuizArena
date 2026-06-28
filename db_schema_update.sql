-- QuizArena  –  DB schema additions
-- Run this ONCE against quiz_app.db to add new tables.
-- sqlite3 quiz_app.db < db_schema_update.sql

PRAGMA journal_mode=WAL;   -- prevents locking issues

-- Scores table (one row per completed quiz)
CREATE TABLE IF NOT EXISTS scores (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category    TEXT    NOT NULL,          -- 'gaming', 'tech', … 'champion'
    difficulty  TEXT    NOT NULL,          -- 'easy' | 'hard'
    score       INTEGER NOT NULL DEFAULT 0,
    total       INTEGER NOT NULL DEFAULT 10,
    accuracy    INTEGER NOT NULL DEFAULT 0, -- 0-100 (%)
    time_taken  INTEGER NOT NULL DEFAULT 0, -- seconds
    played_at   TEXT    NOT NULL           -- ISO datetime UTC
);

CREATE INDEX IF NOT EXISTS idx_scores_user     ON scores(user_id);
CREATE INDEX IF NOT EXISTS idx_scores_category ON scores(category);
CREATE INDEX IF NOT EXISTS idx_scores_score    ON scores(score DESC);

-- User badges / achievements
CREATE TABLE IF NOT EXISTS user_badges (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id   INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    badge_id  TEXT    NOT NULL,           -- matches BADGES list in leaderboard_routes.py
    earned_at TEXT    NOT NULL,
    UNIQUE(user_id, badge_id)
);

CREATE INDEX IF NOT EXISTS idx_badges_user ON user_badges(user_id);

-- Ensure users table has created_at (add if missing)
-- SQLite ALTER TABLE only supports ADD COLUMN
-- Safe to run even if column already exists (will fail silently via Python, 
-- or you can wrap in a try block in create_db.py)
-- ALTER TABLE users ADD COLUMN created_at TEXT DEFAULT (datetime('now'));
