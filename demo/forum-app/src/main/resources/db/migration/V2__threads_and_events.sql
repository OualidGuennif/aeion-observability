-- Feature 010 (threads) and 011 (events leave the request path).
-- The outbox is written in the same transaction as the thread, so a broker outage cannot lose an
-- event and a crash cannot publish one that was never stored. The log makes the consumer
-- idempotent: the same event id twice is applied once.

CREATE TABLE IF NOT EXISTS thread_outbox (
    event_id     TEXT PRIMARY KEY,
    topic        TEXT NOT NULL,
    payload      TEXT NOT NULL,
    created_ns   INTEGER NOT NULL,
    attempts     INTEGER NOT NULL DEFAULT 0,
    published_ns INTEGER,
    last_error   TEXT
);

CREATE INDEX IF NOT EXISTS idx_outbox_pending ON thread_outbox(published_ns, created_ns);

CREATE TABLE IF NOT EXISTS thread_event_log (
    event_id    TEXT PRIMARY KEY,
    topic       TEXT NOT NULL,
    received_ns INTEGER NOT NULL,
    payload     TEXT NOT NULL
);
