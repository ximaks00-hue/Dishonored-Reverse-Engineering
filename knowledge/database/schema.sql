PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS game_build (
    id INTEGER PRIMARY KEY,
    app_id TEXT NOT NULL,
    build_id TEXT NOT NULL,
    executable_sha256 TEXT NOT NULL,
    architecture TEXT NOT NULL,
    recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (app_id, build_id, executable_sha256)
);

CREATE TABLE IF NOT EXISTS functions (
    id INTEGER PRIMARY KEY,
    module TEXT NOT NULL,
    name TEXT,
    address TEXT NOT NULL,
    signature TEXT NOT NULL DEFAULT '',
    summary TEXT NOT NULL DEFAULT '',
    source TEXT NOT NULL DEFAULT '',
    confidence REAL NOT NULL DEFAULT 0.5 CHECK (confidence >= 0 AND confidence <= 1),
    status TEXT NOT NULL DEFAULT 'observed',
    experiment_key TEXT,
    UNIQUE (module, address)
);

CREATE TABLE IF NOT EXISTS structures (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    fields_json TEXT NOT NULL DEFAULT '{}',
    source TEXT NOT NULL DEFAULT '',
    confidence REAL NOT NULL DEFAULT 0.5 CHECK (confidence >= 0 AND confidence <= 1),
    status TEXT NOT NULL DEFAULT 'observed',
    experiment_key TEXT
);

CREATE TABLE IF NOT EXISTS hypotheses (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    claim TEXT NOT NULL,
    scope TEXT NOT NULL DEFAULT '',
    confidence REAL NOT NULL DEFAULT 0.25 CHECK (confidence >= 0 AND confidence <= 1),
    status TEXT NOT NULL DEFAULT 'open',
    experiment_key TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS evidence (
    id INTEGER PRIMARY KEY,
    hypothesis_id INTEGER REFERENCES hypotheses(id) ON DELETE CASCADE,
    source_type TEXT NOT NULL,
    source_ref TEXT NOT NULL,
    observation TEXT NOT NULL,
    confidence REAL NOT NULL DEFAULT 0.5 CHECK (confidence >= 0 AND confidence <= 1),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS experiments (
    id INTEGER PRIMARY KEY,
    experiment_key TEXT UNIQUE,
    title TEXT NOT NULL,
    procedure TEXT NOT NULL DEFAULT '',
    result TEXT NOT NULL DEFAULT '',
    game_build TEXT NOT NULL DEFAULT '',
    save_id TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'observed',
    experiment_status TEXT NOT NULL DEFAULT 'done',
    claim_status TEXT NOT NULL DEFAULT 'observed',
    path TEXT NOT NULL DEFAULT '',
    recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS evidence_edges (
    id INTEGER PRIMARY KEY,
    edge_key TEXT NOT NULL UNIQUE,
    source_node TEXT NOT NULL,
    target_node TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('confirmed', 'observed', 'inferred', 'unknown', 'rejected', 'open')),
    summary TEXT NOT NULL DEFAULT '',
    experiment_key TEXT,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_evidence_hypothesis ON evidence(hypothesis_id);
CREATE INDEX IF NOT EXISTS idx_functions_address ON functions(module, address);
-- experiment_key / evidence_edges indexes are applied after migration in
-- tools/knowledge/sync_from_experiments.py so older DBs without those columns
-- do not fail CREATE INDEX during executescript.
