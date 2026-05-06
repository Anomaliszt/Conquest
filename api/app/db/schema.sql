PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS operators (
    id TEXT PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'disabled')),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS operator_registration_tokens (
    token_hash TEXT PRIMARY KEY,
    used INTEGER NOT NULL DEFAULT 0
        CHECK (used IN (0, 1)),
    expires_at TEXT,
    created_at TEXT NOT NULL,
    used_at TEXT,
    used_by_operator_id TEXT,

    FOREIGN KEY (used_by_operator_id)
        REFERENCES operators(id)
        ON DELETE SET NULL
);