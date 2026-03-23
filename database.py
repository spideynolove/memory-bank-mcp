import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from models import (
    Memory,
    Collection,
    MemorySession,
    PackageAPI,
    CodebasePattern,
    CodingSession,
    ValidationCheck,
    ToolError,
    RuleViolation,
)


class DatabaseAdapter:

    def __init__(self, project_path: Optional[str] = None):
        self.project_path = project_path or self._detect_project_root()
        self.db_path = Path(self.project_path) / "memory.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _detect_project_root(self) -> str:
        current_dir = Path.cwd()
        markers = [
            ".git",
            "package.json",
            "requirements.txt",
            "Cargo.toml",
            "go.mod",
            "composer.json",
        ]
        for path in [current_dir] + list(current_dir.parents):
            for marker in markers:
                if (path / marker).exists():
                    return str(path)
        return str(current_dir)

    def _init_database(self):
        schema_path = Path(__file__).parent / "schema.sql"
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'"
            )
            if not cursor.fetchone():
                with open(schema_path, "r") as f:
                    schema_sql = f.read()
                conn.executescript(schema_sql)
            else:
                existing = {
                    row[0]
                    for row in cursor.execute(
                        "PRAGMA table_info(memories)"
                    ).fetchall()
                }
                for col, defn in [
                    ("trigger", "TEXT"),
                    ("memory_type", "TEXT"),
                    ("has_user_correction", "BOOLEAN DEFAULT 0"),
                    ("priority", "INTEGER DEFAULT 2"),
                    ("disclosure", "TEXT"),
                ]:
                    if col not in existing:
                        conn.execute(
                            f"ALTER TABLE memories ADD COLUMN {col} {defn}"
                        )

                tables = {
                    row[0]
                    for row in cursor.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    ).fetchall()
                }
                if "tool_errors" not in tables:
                    conn.execute("""
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
                        )
                    """)
                    conn.execute("""
                        CREATE INDEX idx_tool_errors_session ON tool_errors(session_id)
                    """)
                    conn.execute("""
                        CREATE INDEX idx_tool_errors_tool ON tool_errors(tool_name)
                    """)
                    conn.execute("""
                        CREATE INDEX idx_tool_errors_frequency ON tool_errors(frequency DESC)
                    """)
                    conn.execute("""
                        CREATE TRIGGER update_tool_errors_timestamp
                        AFTER UPDATE ON tool_errors
                        FOR EACH ROW
                        BEGIN
                            UPDATE tool_errors SET last_seen = CURRENT_TIMESTAMP WHERE id = NEW.id;
                        END
                    """)

                if "rule_violations" not in tables:
                    conn.execute("""
                        CREATE TABLE rule_violations (
                            id TEXT PRIMARY KEY,
                            session_id TEXT NOT NULL,
                            rule_id TEXT NOT NULL,
                            rule_content TEXT NOT NULL,
                            violation_type TEXT NOT NULL,
                            before_content TEXT,
                            after_content TEXT,
                            detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            frequency INTEGER DEFAULT 1,
                            resolved BOOLEAN DEFAULT 0,
                            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
                        )
                    """)
                    conn.execute("""
                        CREATE INDEX idx_rule_violations_session ON rule_violations(session_id)
                    """)
                    conn.execute("""
                        CREATE INDEX idx_rule_violations_rule ON rule_violations(rule_id)
                    """)
                    conn.execute("""
                        CREATE INDEX idx_rule_violations_frequency ON rule_violations(frequency DESC)
                    """)

    def create_session(self, session: MemorySession) -> str:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO sessions (id, problem_statement, success_criteria, constraints_json, started, last_updated)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    session.id,
                    session.problem_statement,
                    session.success_criteria,
                    json.dumps(session.constraints),
                    session.started,
                    session.last_updated,
                ),
            )
            conn.commit()
        return session.id

    def get_session(self, session_id: str) -> Optional[MemorySession]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, problem_statement, success_criteria, constraints_json, started, last_updated
                FROM sessions WHERE id = ?
            """,
                (session_id,),
            )
            row = cursor.fetchone()

            if not row:
                return None

            cursor.execute(
                """
                SELECT id FROM memories
                WHERE session_id = ? AND collection_id IS NULL
                ORDER BY number
            """,
                (session_id,),
            )
            main_thread = [row[0] for row in cursor.fetchall()]

            collections = self._get_collections_for_session(session_id)
            patterns = self._get_patterns_for_session(session_id)

            return MemorySession(
                id=row[0],
                problem_statement=row[1],
                success_criteria=row[2],
                constraints=json.loads(row[3]),
                main_thread=main_thread,
                collections=collections,
                patterns=patterns,
                started=row[4],
                last_updated=row[5],
            )

    def add_memory(self, memory: Memory) -> str:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO memories (
                    id, session_id, content, number, total_estimated, timestamp,
                    confidence, dependencies_json, contradictions_json, tags_json,
                    collection_id, revision_of, is_checkpoint,
                    trigger, memory_type, has_user_correction, priority, disclosure
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    memory.id,
                    self._get_current_session_id(),
                    memory.content,
                    memory.number,
                    memory.total_estimated,
                    memory.timestamp,
                    memory.confidence,
                    json.dumps(memory.dependencies),
                    json.dumps(memory.contradictions),
                    json.dumps(memory.tags),
                    memory.collection_id,
                    memory.revision_of,
                    memory.is_checkpoint,
                    memory.trigger,
                    memory.memory_type,
                    memory.has_user_correction,
                    memory.priority,
                    memory.disclosure,
                ),
            )
            conn.commit()
        return memory.id

    def get_memory(self, memory_id: str) -> Optional[Memory]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, content, number, total_estimated, timestamp, confidence,
                       dependencies_json, contradictions_json, tags_json,
                       collection_id, revision_of, is_checkpoint,
                       trigger, memory_type, has_user_correction, priority, disclosure
                FROM memories WHERE id = ?
            """,
                (memory_id,),
            )
            row = cursor.fetchone()

            if not row:
                return None

            return Memory(
                id=row[0],
                content=row[1],
                number=row[2],
                total_estimated=row[3],
                timestamp=row[4],
                confidence=row[5],
                dependencies=json.loads(row[6]),
                contradictions=json.loads(row[7]),
                tags=json.loads(row[8]),
                collection_id=row[9],
                revision_of=row[10],
                is_checkpoint=bool(row[11]),
                trigger=row[12],
                memory_type=row[13],
                has_user_correction=(
                    bool(row[14]) if row[14] is not None else False
                ),
                priority=row[15] if row[15] is not None else 2,
                disclosure=row[16],
            )

    def update_memory(self, memory: Memory) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE memories SET
                    content = ?, confidence = ?, dependencies_json = ?,
                    contradictions_json = ?, tags_json = ?, collection_id = ?,
                    revision_of = ?, is_checkpoint = ?,
                    trigger = ?, memory_type = ?, has_user_correction = ?,
                    priority = ?, disclosure = ?
                WHERE id = ?
            """,
                (
                    memory.content,
                    memory.confidence,
                    json.dumps(memory.dependencies),
                    json.dumps(memory.contradictions),
                    json.dumps(memory.tags),
                    memory.collection_id,
                    memory.revision_of,
                    memory.is_checkpoint,
                    memory.trigger,
                    memory.memory_type,
                    memory.has_user_correction,
                    memory.priority,
                    memory.disclosure,
                    memory.id,
                ),
            )
            conn.commit()
            return cursor.rowcount > 0

    def create_collection(self, collection: Collection) -> str:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO collections (id, session_id, name, created_from, purpose, memories_json, merged, merge_target)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    collection.id,
                    self._get_current_session_id(),
                    collection.name,
                    collection.created_from,
                    collection.purpose,
                    json.dumps(collection.memories),
                    collection.merged,
                    collection.merge_target,
                ),
            )
            conn.commit()
        return collection.id

    def get_collection(self, collection_id: str) -> Optional[Collection]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, name, created_from, purpose, memories_json, merged, merge_target
                FROM collections WHERE id = ?
            """,
                (collection_id,),
            )
            row = cursor.fetchone()

            if not row:
                return None

            return Collection(
                id=row[0],
                name=row[1],
                created_from=row[2],
                purpose=row[3],
                memories=json.loads(row[4]),
                merged=bool(row[5]),
                merge_target=row[6],
            )

    def update_collection(self, collection: Collection) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE collections SET
                    name = ?, purpose = ?, memories_json = ?, merged = ?, merge_target = ?
                WHERE id = ?
            """,
                (
                    collection.name,
                    collection.purpose,
                    json.dumps(collection.memories),
                    collection.merged,
                    collection.merge_target,
                    collection.id,
                ),
            )
            conn.commit()
            return cursor.rowcount > 0

    def update_patterns(self, patterns: Dict[str, int], session_id: str):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for pattern, count in patterns.items():
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO patterns (session_id, pattern, count)
                    VALUES (?, ?, ?)
                """,
                    (session_id, pattern, count),
                )
            conn.commit()

    def get_active_session_id(self) -> Optional[str]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id FROM sessions WHERE is_active = 1 ORDER BY last_updated DESC LIMIT 1
            """
            )
            row = cursor.fetchone()
            return row[0] if row else None

    def set_active_session(self, session_id: str):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE sessions SET is_active = 0")
            cursor.execute(
                "UPDATE sessions SET is_active = 1 WHERE id = ?", (session_id,)
            )
            conn.commit()

    def _get_collections_for_session(
        self, session_id: str
    ) -> Dict[str, Collection]:
        collections = {}
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, name, created_from, purpose, memories_json, merged, merge_target
                FROM collections WHERE session_id = ?
            """,
                (session_id,),
            )

            for row in cursor.fetchall():
                collection = Collection(
                    id=row[0],
                    name=row[1],
                    created_from=row[2],
                    purpose=row[3],
                    memories=json.loads(row[4]),
                    merged=bool(row[5]),
                    merge_target=row[6],
                )
                collections[collection.id] = collection

        return collections

    def _get_patterns_for_session(self, session_id: str) -> List[str]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT pattern FROM patterns WHERE session_id = ? ORDER BY count DESC
            """,
                (session_id,),
            )
            return [row[0] for row in cursor.fetchall()]

    def _get_current_session_id(self) -> str:
        session_id = self.get_active_session_id()
        if not session_id:
            raise ValueError("No active session found")
        return session_id

    def migrate_from_json(self, json_data: Dict[str, Any]) -> bool:
        return True

    def create_coding_session(self, coding_session: CodingSession) -> str:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO coding_sessions (
                    session_id, session_type, project_path, language, framework,
                    packages_discovered, patterns_stored, validation_checks
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    coding_session.session_id,
                    coding_session.session_type,
                    coding_session.project_path,
                    coding_session.language,
                    coding_session.framework,
                    coding_session.packages_discovered,
                    coding_session.patterns_stored,
                    coding_session.validation_checks,
                ),
            )
            conn.commit()
        return coding_session.session_id

    def add_package_api(self, package_api: PackageAPI) -> str:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO package_apis (
                    id, session_id, package_name, api_signature, usage_example,
                    documentation, discovered_at, last_used, usage_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    package_api.id,
                    package_api.session_id,
                    package_api.package_name,
                    package_api.api_signature,
                    package_api.usage_example,
                    package_api.documentation,
                    package_api.discovered_at,
                    package_api.last_used,
                    package_api.usage_count,
                ),
            )
            conn.commit()
        return package_api.id

    def get_package_apis(self, session_id: str) -> List[PackageAPI]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, session_id, package_name, api_signature, usage_example,
                       documentation, discovered_at, last_used, usage_count
                FROM package_apis WHERE session_id = ?
            """,
                (session_id,),
            )

            apis = []
            for row in cursor.fetchall():
                apis.append(
                    PackageAPI(
                        id=row[0],
                        session_id=row[1],
                        package_name=row[2],
                        api_signature=row[3],
                        usage_example=row[4],
                        documentation=row[5],
                        discovered_at=row[6],
                        last_used=row[7],
                        usage_count=row[8],
                    )
                )
            return apis

    def add_codebase_pattern(self, pattern: CodebasePattern) -> str:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO codebase_patterns (
                    id, session_id, pattern_type, code_snippet, description,
                    language, file_path, created_at, updated_at, tags_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    pattern.id,
                    pattern.session_id,
                    pattern.pattern_type,
                    pattern.code_snippet,
                    pattern.description,
                    pattern.language,
                    pattern.file_path,
                    pattern.created_at,
                    pattern.updated_at,
                    json.dumps(pattern.tags),
                ),
            )
            conn.commit()
        return pattern.id

    def get_codebase_patterns(
        self, session_id: str, pattern_type: str = None
    ) -> List[CodebasePattern]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if pattern_type:
                cursor.execute(
                    """
                    SELECT id, session_id, pattern_type, code_snippet, description,
                           language, file_path, created_at, updated_at, tags_json
                    FROM codebase_patterns WHERE session_id = ? AND pattern_type = ?
                """,
                    (session_id, pattern_type),
                )
            else:
                cursor.execute(
                    """
                    SELECT id, session_id, pattern_type, code_snippet, description,
                           language, file_path, created_at, updated_at, tags_json
                    FROM codebase_patterns WHERE session_id = ?
                """,
                    (session_id,),
                )

            patterns = []
            for row in cursor.fetchall():
                patterns.append(
                    CodebasePattern(
                        id=row[0],
                        session_id=row[1],
                        pattern_type=row[2],
                        code_snippet=row[3],
                        description=row[4],
                        language=row[5],
                        file_path=row[6],
                        created_at=row[7],
                        updated_at=row[8],
                        tags=json.loads(row[9]),
                    )
                )
            return patterns

    def add_validation_check(self, validation_check: ValidationCheck) -> str:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO validation_checks (
                    id, session_id, check_type, target_code, result,
                    message, suggestions_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    validation_check.id,
                    validation_check.session_id,
                    validation_check.check_type,
                    validation_check.target_code,
                    validation_check.result,
                    validation_check.message,
                    json.dumps(validation_check.suggestions),
                    validation_check.created_at,
                ),
            )
            conn.commit()
        return validation_check.id

    def get_validation_checks(self, session_id: str) -> List[ValidationCheck]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, session_id, check_type, target_code, result,
                       message, suggestions_json, created_at
                FROM validation_checks WHERE session_id = ?
            """,
                (session_id,),
            )

            checks = []
            for row in cursor.fetchall():
                checks.append(
                    ValidationCheck(
                        id=row[0],
                        session_id=row[1],
                        check_type=row[2],
                        target_code=row[3],
                        result=row[4],
                        message=row[5],
                        suggestions=json.loads(row[6]),
                        created_at=row[7],
                    )
                )
            return checks

    def add_or_update_tool_error(self, error: ToolError) -> str:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, frequency FROM tool_errors
                WHERE session_id = ? AND tool_name = ? AND error_message = ?
                LIMIT 1
            """,
                (error.session_id, error.tool_name, error.error_message),
            )
            existing = cursor.fetchone()

            if existing:
                error_id, freq = existing
                cursor.execute(
                    """
                    UPDATE tool_errors
                    SET frequency = frequency + 1, last_seen = CURRENT_TIMESTAMP
                    WHERE id = ?
                """,
                    (error_id,),
                )
                conn.commit()
                return error_id
            else:
                cursor.execute(
                    """
                    INSERT INTO tool_errors (
                        id, session_id, tool_name, error_message, error_context,
                        frequency, first_seen, last_seen, resolved, resolution_note
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        error.id,
                        error.session_id,
                        error.tool_name,
                        error.error_message,
                        error.error_context,
                        error.frequency,
                        error.first_seen,
                        error.last_seen,
                        error.resolved,
                        error.resolution_note,
                    ),
                )
                conn.commit()
                return error.id

    def get_tool_errors(
        self, session_id: str, tool_name: str = None, unresolved_only: bool = False
    ) -> List[ToolError]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            query = """
                SELECT id, session_id, tool_name, error_message, error_context,
                       frequency, first_seen, last_seen, resolved, resolution_note
                FROM tool_errors WHERE session_id = ?
            """
            params = [session_id]

            if tool_name:
                query += " AND tool_name = ?"
                params.append(tool_name)

            if unresolved_only:
                query += " AND resolved = 0"

            query += " ORDER BY frequency DESC, last_seen DESC"

            cursor.execute(query, params)

            errors = []
            for row in cursor.fetchall():
                errors.append(
                    ToolError(
                        id=row[0],
                        session_id=row[1],
                        tool_name=row[2],
                        error_message=row[3],
                        error_context=row[4],
                        frequency=row[5],
                        first_seen=row[6],
                        last_seen=row[7],
                        resolved=bool(row[8]),
                        resolution_note=row[9],
                    )
                )
            return errors

    def resolve_tool_error(self, error_id: str, resolution_note: str = None) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE tool_errors SET resolved = 1, resolution_note = ?
                WHERE id = ?
            """,
                (resolution_note, error_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    def get_frequent_errors(self, session_id: str, min_frequency: int = 3) -> List[ToolError]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, session_id, tool_name, error_message, error_context,
                       frequency, first_seen, last_seen, resolved, resolution_note
                FROM tool_errors
                WHERE session_id = ? AND frequency >= ? AND resolved = 0
                ORDER BY frequency DESC
                """,
                (session_id, min_frequency),
            )

            errors = []
            for row in cursor.fetchall():
                errors.append(
                    ToolError(
                        id=row[0],
                        session_id=row[1],
                        tool_name=row[2],
                        error_message=row[3],
                        error_context=row[4],
                        frequency=row[5],
                        first_seen=row[6],
                        last_seen=row[7],
                        resolved=bool(row[8]),
                        resolution_note=row[9],
                    )
                )
            return errors

    def add_or_update_rule_violation(self, violation: RuleViolation) -> str:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, frequency FROM rule_violations
                WHERE session_id = ? AND rule_id = ? AND violation_type = ?
                LIMIT 1
                """,
                (violation.session_id, violation.rule_id, violation.violation_type),
            )
            existing = cursor.fetchone()

            if existing:
                v_id, freq = existing
                cursor.execute(
                    """
                    UPDATE rule_violations
                    SET frequency = frequency + 1, after_content = ?, detected_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (violation.after_content, v_id),
                )
                conn.commit()
                return v_id
            else:
                cursor.execute(
                    """
                    INSERT INTO rule_violations (
                        id, session_id, rule_id, rule_content, violation_type,
                        before_content, after_content, detected_at, frequency, resolved
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        violation.id,
                        violation.session_id,
                        violation.rule_id,
                        violation.rule_content,
                        violation.violation_type,
                        violation.before_content,
                        violation.after_content,
                        violation.detected_at,
                        violation.frequency,
                        violation.resolved,
                    ),
                )
                conn.commit()
                return violation.id

    def get_rule_violations(
        self, session_id: str, unresolved_only: bool = False
    ) -> List[RuleViolation]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            query = """
                SELECT id, session_id, rule_id, rule_content, violation_type,
                       before_content, after_content, detected_at, frequency, resolved
                FROM rule_violations WHERE session_id = ?
            """
            params = [session_id]

            if unresolved_only:
                query += " AND resolved = 0"

            query += " ORDER BY frequency DESC, detected_at DESC"

            cursor.execute(query, params)

            violations = []
            for row in cursor.fetchall():
                violations.append(
                    RuleViolation(
                        id=row[0],
                        session_id=row[1],
                        rule_id=row[2],
                        rule_content=row[3],
                        violation_type=row[4],
                        before_content=row[5],
                        after_content=row[6],
                        detected_at=row[7],
                        frequency=row[8],
                        resolved=bool(row[9]),
                    )
                )
            return violations

    def resolve_rule_violation(self, violation_id: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE rule_violations SET resolved = 1 WHERE id = ?",
                (violation_id,),
            )
            conn.commit()
            return cursor.rowcount > 0

    def get_database_info(self) -> Dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sessions")
            sessions_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM memories")
            memories_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM collections")
            collections_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM package_apis")
            package_apis_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM codebase_patterns")
            patterns_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM validation_checks")
            validation_checks_count = cursor.fetchone()[0]

            return {
                "database_path": str(self.db_path),
                "project_path": self.project_path,
                "sessions_count": sessions_count,
                "memories_count": memories_count,
                "collections_count": collections_count,
                "package_apis_count": package_apis_count,
                "codebase_patterns_count": patterns_count,
                "validation_checks_count": validation_checks_count,
                "database_size": (
                    self.db_path.stat().st_size if self.db_path.exists() else 0
                ),
                "rule_violations_count": self._count_table("rule_violations"),
            }

    def _count_table(self, table_name: str) -> int:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                return cursor.fetchone()[0]
        except Exception:
            return 0

    def get_all_rules(self) -> List[Memory]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, content, number, total_estimated, timestamp, confidence,
                       dependencies_json, contradictions_json, tags_json,
                       collection_id, revision_of, is_checkpoint,
                       trigger, memory_type, has_user_correction, priority, disclosure
                FROM memories WHERE memory_type = 'rule'
                ORDER BY priority ASC, timestamp DESC
                """
            )

            rules = []
            for row in cursor.fetchall():
                rules.append(
                    Memory(
                        id=row[0],
                        content=row[1],
                        number=row[2],
                        total_estimated=row[3],
                        timestamp=row[4],
                        confidence=row[5],
                        dependencies=json.loads(row[6]),
                        contradictions=json.loads(row[7]),
                        tags=json.loads(row[8]),
                        collection_id=row[9],
                        revision_of=row[10],
                        is_checkpoint=bool(row[11]),
                        trigger=row[12],
                        memory_type=row[13],
                        has_user_correction=bool(row[14]) if row[14] is not None else False,
                        priority=row[15] if row[15] is not None else 2,
                        disclosure=row[16],
                    )
                )
            return rules

    def get_all_memories_for_analysis(self) -> List[Memory]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, content, number, total_estimated, timestamp, confidence,
                       dependencies_json, contradictions_json, tags_json,
                       collection_id, revision_of, is_checkpoint,
                       trigger, memory_type, has_user_correction, priority, disclosure
                FROM memories ORDER BY priority ASC, timestamp DESC
                """
            )

            memories = []
            for row in cursor.fetchall():
                memories.append(
                    Memory(
                        id=row[0],
                        content=row[1],
                        number=row[2],
                        total_estimated=row[3],
                        timestamp=row[4],
                        confidence=row[5],
                        dependencies=json.loads(row[6]),
                        contradictions=json.loads(row[7]),
                        tags=json.loads(row[8]),
                        collection_id=row[9],
                        revision_of=row[10],
                        is_checkpoint=bool(row[11]),
                        trigger=row[12],
                        memory_type=row[13],
                        has_user_correction=bool(row[14]) if row[14] is not None else False,
                        priority=row[15] if row[15] is not None else 2,
                        disclosure=row[16],
                    )
                )
            return memories
