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

-- Canonical build-specific function inventory. This records L0 only; presence
-- in an index never implies that a function was semantically understood.
CREATE TABLE IF NOT EXISTS function_inventory (
    id INTEGER PRIMARY KEY,
    build_id INTEGER NOT NULL REFERENCES game_build(id) ON DELETE CASCADE,
    module TEXT NOT NULL,
    va INTEGER NOT NULL CHECK (va >= 0),
    rva INTEGER NOT NULL CHECK (rva >= 0),
    image_base INTEGER NOT NULL CHECK (image_base >= 0),
    name TEXT NOT NULL,
    signature TEXT NOT NULL DEFAULT '',
    size_bytes INTEGER NOT NULL CHECK (size_bytes > 0),
    index_source TEXT NOT NULL,
    index_sha256 TEXT NOT NULL CHECK (length(index_sha256) = 64),
    UNIQUE (build_id, module, va)
);

-- Tool output coverage (L1) is distinct from semantic claims (L2).
-- cache_key includes build/input hash, exact function address, tool version,
-- analysis kind and options hash so changed inputs do not reuse stale results.
CREATE TABLE IF NOT EXISTS function_analysis_runs (
    id INTEGER PRIMARY KEY,
    function_id INTEGER NOT NULL REFERENCES function_inventory(id) ON DELETE CASCADE,
    analysis_kind TEXT NOT NULL CHECK (analysis_kind IN (
        'decompile', 'manual_body_review', 'callgraph', 'xref', 'strings',
        'vtable', 'dataflow', 'runtime_trace', 'other'
    )),
    tool_name TEXT NOT NULL,
    tool_version TEXT,
    status TEXT NOT NULL CHECK (status IN ('complete', 'partial', 'failed', 'not_run')),
    input_sha256 TEXT NOT NULL CHECK (length(input_sha256) = 64),
    options_sha256 TEXT CHECK (options_sha256 IS NULL OR length(options_sha256) = 64),
    cache_key TEXT NOT NULL UNIQUE CHECK (length(cache_key) = 64),
    source_ref TEXT NOT NULL,
    source_sha256 TEXT CHECK (source_sha256 IS NULL OR length(source_sha256) = 64),
    summary TEXT NOT NULL DEFAULT '',
    is_current INTEGER NOT NULL DEFAULT 1 CHECK (is_current IN (0, 1)),
    recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Claims are evidence-backed and keep the project's claim vocabulary.
CREATE TABLE IF NOT EXISTS function_claims (
    id INTEGER PRIMARY KEY,
    function_id INTEGER NOT NULL REFERENCES function_inventory(id) ON DELETE CASCADE,
    claim_kind TEXT NOT NULL CHECK (claim_kind IN (
        'role', 'owner', 'field_read', 'field_write', 'side_effect',
        'dataflow', 'runtime_behavior', 'other'
    )),
    claim_status TEXT NOT NULL CHECK (claim_status IN (
        'confirmed', 'observed', 'inferred', 'unknown', 'superseded', 'rejected'
    )),
    statement TEXT NOT NULL,
    confidence REAL CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1)),
    evidence_va INTEGER CHECK (evidence_va IS NULL OR evidence_va >= 0),
    evidence_rva INTEGER CHECK (evidence_rva IS NULL OR evidence_rva >= 0),
    evidence_ref TEXT NOT NULL,
    evidence_sha256 TEXT CHECK (evidence_sha256 IS NULL OR length(evidence_sha256) = 64),
    experiment_key TEXT,
    pointer_provenance TEXT NOT NULL DEFAULT '',
    claim_key TEXT NOT NULL UNIQUE CHECK (length(claim_key) = 64),
    is_current INTEGER NOT NULL DEFAULT 1 CHECK (is_current IN (0, 1)),
    recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- A caller edge is not automatically a dataflow edge. Keep relation kinds and
-- confidence separate; only confirmed dataflow links qualify for the L3 gate.
CREATE TABLE IF NOT EXISTS function_edges (
    id INTEGER PRIMARY KEY,
    source_function_id INTEGER NOT NULL REFERENCES function_inventory(id) ON DELETE CASCADE,
    target_function_id INTEGER NOT NULL REFERENCES function_inventory(id) ON DELETE CASCADE,
    relation_kind TEXT NOT NULL CHECK (relation_kind IN (
        'direct_call', 'virtual_dispatch', 'dataflow', 'ownership', 'xref', 'other'
    )),
    claim_status TEXT NOT NULL CHECK (claim_status IN (
        'confirmed', 'observed', 'inferred', 'unknown', 'superseded', 'rejected'
    )),
    evidence_ref TEXT NOT NULL,
    evidence_sha256 TEXT CHECK (evidence_sha256 IS NULL OR length(evidence_sha256) = 64),
    source_va INTEGER,
    source_rva INTEGER,
    pointer_provenance TEXT NOT NULL DEFAULT '',
    experiment_key TEXT,
    edge_key TEXT NOT NULL UNIQUE CHECK (length(edge_key) = 64),
    recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS function_runtime_evidence (
    id INTEGER PRIMARY KEY,
    function_id INTEGER NOT NULL REFERENCES function_inventory(id) ON DELETE CASCADE,
    status TEXT NOT NULL CHECK (status IN ('not_run', 'observed', 'replicated', 'failed', 'blocked')),
    claim_status TEXT NOT NULL CHECK (claim_status IN (
        'confirmed', 'observed', 'inferred', 'unknown', 'superseded', 'rejected'
    )),
    baseline_id TEXT NOT NULL,
    capture_ref TEXT NOT NULL,
    capture_sha256 TEXT CHECK (capture_sha256 IS NULL OR length(capture_sha256) = 64),
    build_sha256 TEXT NOT NULL CHECK (length(build_sha256) = 64),
    inputs_json TEXT NOT NULL DEFAULT '[]',
    outputs_json TEXT NOT NULL DEFAULT '[]',
    experiment_key TEXT,
    recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_function_inventory_build_rva
    ON function_inventory(build_id, rva);
CREATE INDEX IF NOT EXISTS idx_function_analysis_function_status
    ON function_analysis_runs(function_id, status);
CREATE INDEX IF NOT EXISTS idx_function_claim_function_kind_status
    ON function_claims(function_id, claim_kind, claim_status);
CREATE INDEX IF NOT EXISTS idx_function_edges_source
    ON function_edges(source_function_id, relation_kind, claim_status);
CREATE INDEX IF NOT EXISTS idx_function_edges_target
    ON function_edges(target_function_id, relation_kind, claim_status);
CREATE INDEX IF NOT EXISTS idx_function_runtime_function_status
    ON function_runtime_evidence(function_id, status, claim_status);

-- Per-function axes remain visible even when the sequential L0-L4 gate is low.
DROP VIEW IF EXISTS function_research_progress;
CREATE VIEW function_research_progress AS
WITH evidence AS (
    SELECT
        f.id AS function_id,
        EXISTS (
            SELECT 1 FROM function_analysis_runs a
            WHERE a.function_id = f.id AND a.is_current = 1 AND a.status IN ('complete', 'partial')
        ) AS has_analysis,
        EXISTS (
            SELECT 1 FROM function_claims c
            WHERE c.function_id = f.id AND c.is_current = 1 AND c.claim_kind = 'role' AND c.claim_status = 'confirmed'
        ) AS has_confirmed_role,
        EXISTS (
            SELECT 1 FROM function_claims c
            WHERE c.function_id = f.id AND c.is_current = 1 AND c.claim_kind = 'role'
        ) AS has_role_claim,
        EXISTS (
            SELECT 1 FROM function_edges e
            WHERE (e.source_function_id = f.id OR e.target_function_id = f.id)
              AND e.relation_kind = 'dataflow' AND e.claim_status = 'confirmed'
        ) AS has_confirmed_dataflow,
        EXISTS (
            SELECT 1 FROM function_edges e
            WHERE e.source_function_id = f.id OR e.target_function_id = f.id
        ) AS has_any_edge,
        EXISTS (
            SELECT 1 FROM function_runtime_evidence r
            WHERE r.function_id = f.id AND r.status = 'replicated' AND r.claim_status = 'confirmed'
        ) AS has_replicated_runtime,
        EXISTS (
            SELECT 1 FROM function_runtime_evidence r WHERE r.function_id = f.id
        ) AS has_runtime_record
    FROM function_inventory f
)
SELECT
    f.id AS function_id,
    b.build_id AS build_id,
    b.executable_sha256 AS executable_sha256,
    f.module,
    f.va,
    f.rva,
    f.name,
    f.size_bytes,
    CASE WHEN e.has_analysis THEN 'analyzed' ELSE 'indexed' END AS analysis_axis,
    CASE
        WHEN EXISTS (SELECT 1 FROM function_claims c WHERE c.function_id=f.id AND c.is_current=1 AND c.claim_kind='role' AND c.claim_status='confirmed') THEN 'confirmed'
        WHEN e.has_role_claim THEN 'claim_recorded'
        ELSE 'unknown'
    END AS semantic_axis,
    CASE
        WHEN e.has_confirmed_dataflow THEN 'confirmed_dataflow'
        WHEN e.has_any_edge THEN 'edge_recorded'
        ELSE 'unconnected'
    END AS connectivity_axis,
    CASE
        WHEN e.has_replicated_runtime THEN 'replicated_verified'
        WHEN e.has_runtime_record THEN 'runtime_recorded'
        ELSE 'unverified'
    END AS runtime_axis,
    CASE
        WHEN e.has_analysis AND e.has_confirmed_role AND e.has_confirmed_dataflow AND e.has_replicated_runtime THEN 'L4'
        WHEN e.has_analysis AND e.has_confirmed_role AND e.has_confirmed_dataflow THEN 'L3'
        WHEN e.has_analysis AND e.has_confirmed_role THEN 'L2'
        WHEN e.has_analysis THEN 'L1'
        ELSE 'L0'
    END AS gated_level
FROM function_inventory f
JOIN game_build b ON b.id = f.build_id
JOIN evidence e ON e.function_id = f.id;

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
