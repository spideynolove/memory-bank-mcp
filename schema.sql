CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    problem_statement TEXT NOT NULL,
    success_criteria TEXT NOT NULL,
    constraints_json TEXT DEFAULT '[]',
    started TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);
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
    trigger TEXT,
    memory_type TEXT,
    has_user_correction BOOLEAN DEFAULT 0,
    priority INTEGER DEFAULT 2,
    disclosure TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (collection_id) REFERENCES collections(id) ON DELETE SET NULL,
    FOREIGN KEY (revision_of) REFERENCES memories(id) ON DELETE SET NULL
);
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
CREATE TABLE patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    pattern TEXT NOT NULL,
    count INTEGER DEFAULT 1,
    last_detected TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);
CREATE INDEX idx_memories_session ON memories(session_id);
CREATE INDEX idx_memories_collection ON memories(collection_id);
CREATE INDEX idx_memories_timestamp ON memories(timestamp);
CREATE INDEX idx_collections_session ON collections(session_id);
CREATE INDEX idx_patterns_session ON patterns(session_id);
CREATE INDEX idx_sessions_active ON sessions(is_active);
CREATE TABLE package_apis (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    package_name TEXT NOT NULL,
    api_signature TEXT NOT NULL,
    usage_example TEXT,
    documentation TEXT,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usage_count INTEGER DEFAULT 0,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);
CREATE TABLE codebase_patterns (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    pattern_type TEXT NOT NULL,
    code_snippet TEXT NOT NULL,
    description TEXT,
    language TEXT,
    file_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tags_json TEXT DEFAULT '[]',
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);
CREATE TABLE coding_sessions (
    session_id TEXT PRIMARY KEY,
    session_type TEXT NOT NULL,
    project_path TEXT,
    language TEXT,
    framework TEXT,
    packages_discovered INTEGER DEFAULT 0,
    patterns_stored INTEGER DEFAULT 0,
    validation_checks INTEGER DEFAULT 0,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);
CREATE TABLE validation_checks (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    check_type TEXT NOT NULL,
    target_code TEXT NOT NULL,
    result TEXT NOT NULL,
    message TEXT,
    suggestions_json TEXT DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);
CREATE INDEX idx_package_apis_session ON package_apis(session_id);
CREATE INDEX idx_package_apis_package ON package_apis(package_name);
CREATE INDEX idx_codebase_patterns_session ON codebase_patterns(session_id);
CREATE INDEX idx_codebase_patterns_type ON codebase_patterns(pattern_type);
CREATE INDEX idx_coding_sessions_type ON coding_sessions(session_type);
CREATE INDEX idx_validation_checks_session ON validation_checks(session_id);
CREATE INDEX idx_validation_checks_type ON validation_checks(check_type);
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
CREATE TRIGGER update_package_apis_timestamp
    AFTER UPDATE ON package_apis
    FOR EACH ROW
    BEGIN
        UPDATE package_apis SET last_used = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;
CREATE TRIGGER update_codebase_patterns_timestamp
    AFTER UPDATE ON codebase_patterns
    FOR EACH ROW
    BEGIN
        UPDATE codebase_patterns SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;
CREATE TABLE tool_errors (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    tool_name TEXT NOT NULL,
    error_message TEXT NOT NULL,
    error_context TEXT,
    frequency INTEGER DEFAULT 1,
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved BOOLEAN DEFAULT 0,
    resolution_note TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);
CREATE INDEX idx_tool_errors_session ON tool_errors(session_id);
CREATE INDEX idx_tool_errors_tool ON tool_errors(tool_name);
CREATE INDEX idx_tool_errors_frequency ON tool_errors(frequency DESC);
CREATE TRIGGER update_tool_errors_timestamp
    AFTER UPDATE ON tool_errors
    FOR EACH ROW
    BEGIN
        UPDATE tool_errors SET last_seen = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;