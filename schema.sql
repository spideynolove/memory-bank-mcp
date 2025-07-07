-- Memory Bank MCP SQLite Schema
-- Project-isolated database for persistent memory storage

-- Sessions table - stores memory session metadata
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    problem_statement TEXT NOT NULL,
    success_criteria TEXT NOT NULL,
    constraints_json TEXT DEFAULT '[]',
    started TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);

-- Memories table - stores individual memory entries
CREATE TABLE memories (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    content TEXT NOT NULL,
    number INTEGER NOT NULL,
    total_estimated INTEGER NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confidence REAL DEFAULT 0.8,
    dependencies_json TEXT DEFAULT '[]',
    contradictions_json TEXT DEFAULT '[]',
    tags_json TEXT DEFAULT '[]',
    collection_id TEXT,
    revision_of TEXT,
    is_checkpoint BOOLEAN DEFAULT 0,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (collection_id) REFERENCES collections(id) ON DELETE SET NULL,
    FOREIGN KEY (revision_of) REFERENCES memories(id) ON DELETE SET NULL
);

-- Collections table - stores memory collections within sessions
CREATE TABLE collections (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    name TEXT NOT NULL,
    created_from TEXT NOT NULL,
    purpose TEXT NOT NULL,
    memories_json TEXT DEFAULT '[]',
    merged BOOLEAN DEFAULT 0,
    merge_target TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (created_from) REFERENCES memories(id) ON DELETE CASCADE
);

-- Patterns table - stores detected thinking patterns
CREATE TABLE patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    pattern TEXT NOT NULL,
    count INTEGER DEFAULT 1,
    last_detected TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX idx_memories_session ON memories(session_id);
CREATE INDEX idx_memories_collection ON memories(collection_id);
CREATE INDEX idx_memories_timestamp ON memories(timestamp);
CREATE INDEX idx_collections_session ON collections(session_id);
CREATE INDEX idx_patterns_session ON patterns(session_id);
CREATE INDEX idx_sessions_active ON sessions(is_active);

-- Triggers to maintain last_updated timestamps
CREATE TRIGGER update_sessions_timestamp 
    AFTER UPDATE ON sessions
    FOR EACH ROW
    BEGIN
        UPDATE sessions SET last_updated = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

CREATE TRIGGER update_patterns_timestamp
    AFTER UPDATE ON patterns
    FOR EACH ROW
    BEGIN
        UPDATE patterns SET last_detected = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;