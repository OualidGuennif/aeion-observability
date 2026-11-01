-- Feature 001 (app skeleton and settings), 002 (schema and migration runner), 003 (test harness).
-- The forum's own tables arrive in later migrations; this one is the base every feature builds on.

CREATE TABLE IF NOT EXISTS settings (
    name       TEXT PRIMARY KEY,
    value      TEXT NOT NULL,
    updated_ns INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS accounts (
    id          TEXT PRIMARY KEY,
    username    TEXT NOT NULL UNIQUE,
    password    TEXT NOT NULL,          -- Argon2id encoded, never the clear text
    role        TEXT NOT NULL DEFAULT 'member',
    created_ns  INTEGER NOT NULL,
    locked_ns   INTEGER,
    failures    INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS sessions (
    id          TEXT PRIMARY KEY,       -- SHA-256 of the cookie value, never the cookie itself
    account_id  TEXT NOT NULL REFERENCES accounts(id),
    issued_ns   INTEGER NOT NULL,
    expires_ns  INTEGER NOT NULL,
    revoked_ns  INTEGER
);

CREATE TABLE IF NOT EXISTS threads (
    id          TEXT PRIMARY KEY,
    title       TEXT NOT NULL,
    body        TEXT NOT NULL,
    author_id   TEXT NOT NULL REFERENCES accounts(id),
    created_ns  INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS schema_events (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    at_ns      INTEGER NOT NULL,
    migration  TEXT NOT NULL,
    detail     TEXT
);

CREATE INDEX IF NOT EXISTS idx_threads_created ON threads(created_ns DESC);
CREATE INDEX IF NOT EXISTS idx_sessions_account ON sessions(account_id);
