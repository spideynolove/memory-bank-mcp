"""
Database adapter layer for Memory Bank MCP
Handles SQLite operations and project-specific database management
"""

import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from models import Memory, Collection, MemorySession, PackageAPI, CodebasePattern, CodingSession, ValidationCheck


class DatabaseAdapter:
    """SQLite database adapter for Memory Bank MCP with project isolation"""
    
    def __init__(self, project_path: Optional[str] = None):
        self.project_path = project_path or self._detect_project_root()
        self.db_path = Path(self.project_path) / "memory.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _detect_project_root(self) -> str:
        """Detect project root by looking for common project markers"""
        current_dir = Path.cwd()
        markers = ['.git', 'package.json', 'requirements.txt', 'Cargo.toml', 'go.mod', 'composer.json']
        
        # Check current directory and parents
        for path in [current_dir] + list(current_dir.parents):
            for marker in markers:
                if (path / marker).exists():
                    return str(path)
        
        # Fallback to current directory
        return str(current_dir)
    
    def _init_database(self):
        """Initialize database with schema if it doesn't exist"""
        schema_path = Path(__file__).parent / "schema.sql"
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")
        
        with sqlite3.connect(self.db_path) as conn:
            # Check if tables exist
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'")
            if not cursor.fetchone():
                # Database is empty, create schema
                with open(schema_path, 'r') as f:
                    schema_sql = f.read()
                conn.executescript(schema_sql)
    
    def create_session(self, session: MemorySession) -> str:
        """Create a new memory session"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sessions (id, problem_statement, success_criteria, constraints_json, started, last_updated)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                session.id,
                session.problem_statement,
                session.success_criteria,
                json.dumps(session.constraints),
                session.started,
                session.last_updated
            ))
            conn.commit()
        return session.id
    
    def get_session(self, session_id: str) -> Optional[MemorySession]:
        """Retrieve a memory session by ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, problem_statement, success_criteria, constraints_json, started, last_updated
                FROM sessions WHERE id = ?
            """, (session_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            # Get main thread memories
            cursor.execute("""
                SELECT id FROM memories 
                WHERE session_id = ? AND collection_id IS NULL 
                ORDER BY number
            """, (session_id,))
            main_thread = [row[0] for row in cursor.fetchall()]
            
            # Get collections
            collections = self._get_collections_for_session(session_id)
            
            # Get patterns
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
                last_updated=row[5]
            )
    
    def add_memory(self, memory: Memory) -> str:
        """Add a new memory to the database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO memories (
                    id, session_id, content, number, total_estimated, timestamp,
                    confidence, dependencies_json, contradictions_json, tags_json,
                    collection_id, revision_of, is_checkpoint
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
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
                memory.is_checkpoint
            ))
            conn.commit()
        return memory.id
    
    def get_memory(self, memory_id: str) -> Optional[Memory]:
        """Retrieve a memory by ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, content, number, total_estimated, timestamp, confidence,
                       dependencies_json, contradictions_json, tags_json,
                       collection_id, revision_of, is_checkpoint
                FROM memories WHERE id = ?
            """, (memory_id,))
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
                is_checkpoint=bool(row[11])
            )
    
    def update_memory(self, memory: Memory) -> bool:
        """Update an existing memory"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE memories SET
                    content = ?, confidence = ?, dependencies_json = ?,
                    contradictions_json = ?, tags_json = ?, collection_id = ?,
                    revision_of = ?, is_checkpoint = ?
                WHERE id = ?
            """, (
                memory.content,
                memory.confidence,
                json.dumps(memory.dependencies),
                json.dumps(memory.contradictions),
                json.dumps(memory.tags),
                memory.collection_id,
                memory.revision_of,
                memory.is_checkpoint,
                memory.id
            ))
            conn.commit()
            return cursor.rowcount > 0
    
    def create_collection(self, collection: Collection) -> str:
        """Create a new collection"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO collections (id, session_id, name, created_from, purpose, memories_json, merged, merge_target)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                collection.id,
                self._get_current_session_id(),
                collection.name,
                collection.created_from,
                collection.purpose,
                json.dumps(collection.memories),
                collection.merged,
                collection.merge_target
            ))
            conn.commit()
        return collection.id
    
    def get_collection(self, collection_id: str) -> Optional[Collection]:
        """Retrieve a collection by ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, created_from, purpose, memories_json, merged, merge_target
                FROM collections WHERE id = ?
            """, (collection_id,))
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
                merge_target=row[6]
            )
    
    def update_collection(self, collection: Collection) -> bool:
        """Update an existing collection"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE collections SET
                    name = ?, purpose = ?, memories_json = ?, merged = ?, merge_target = ?
                WHERE id = ?
            """, (
                collection.name,
                collection.purpose,
                json.dumps(collection.memories),
                collection.merged,
                collection.merge_target,
                collection.id
            ))
            conn.commit()
            return cursor.rowcount > 0
    
    def update_patterns(self, patterns: Dict[str, int], session_id: str):
        """Update detected patterns for a session"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for pattern, count in patterns.items():
                cursor.execute("""
                    INSERT OR REPLACE INTO patterns (session_id, pattern, count)
                    VALUES (?, ?, ?)
                """, (session_id, pattern, count))
            conn.commit()
    
    def get_active_session_id(self) -> Optional[str]:
        """Get the currently active session ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id FROM sessions WHERE is_active = 1 ORDER BY last_updated DESC LIMIT 1
            """)
            row = cursor.fetchone()
            return row[0] if row else None
    
    def set_active_session(self, session_id: str):
        """Set the active session and deactivate others"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Deactivate all sessions
            cursor.execute("UPDATE sessions SET is_active = 0")
            # Activate the specified session
            cursor.execute("UPDATE sessions SET is_active = 1 WHERE id = ?", (session_id,))
            conn.commit()
    
    def _get_collections_for_session(self, session_id: str) -> Dict[str, Collection]:
        """Get all collections for a session"""
        collections = {}
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, created_from, purpose, memories_json, merged, merge_target
                FROM collections WHERE session_id = ?
            """, (session_id,))
            
            for row in cursor.fetchall():
                collection = Collection(
                    id=row[0],
                    name=row[1],
                    created_from=row[2],
                    purpose=row[3],
                    memories=json.loads(row[4]),
                    merged=bool(row[5]),
                    merge_target=row[6]
                )
                collections[collection.id] = collection
        
        return collections
    
    def _get_patterns_for_session(self, session_id: str) -> List[str]:
        """Get all patterns for a session"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT pattern FROM patterns WHERE session_id = ? ORDER BY count DESC
            """, (session_id,))
            return [row[0] for row in cursor.fetchall()]
    
    def _get_current_session_id(self) -> str:
        """Get current session ID from database"""
        session_id = self.get_active_session_id()
        if not session_id:
            raise ValueError("No active session found")
        return session_id
    
    def migrate_from_json(self, json_data: Dict[str, Any]) -> bool:
        """Migrate existing JSON data to SQLite database"""
        # Implementation depends on JSON structure
        # This is a placeholder for migration logic
        return True
    
    def create_coding_session(self, coding_session: CodingSession) -> str:
        """Create a coding-specific session extension"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO coding_sessions (
                    session_id, session_type, project_path, language, framework,
                    packages_discovered, patterns_stored, validation_checks
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                coding_session.session_id,
                coding_session.session_type,
                coding_session.project_path,
                coding_session.language,
                coding_session.framework,
                coding_session.packages_discovered,
                coding_session.patterns_stored,
                coding_session.validation_checks
            ))
            conn.commit()
        return coding_session.session_id

    def add_package_api(self, package_api: PackageAPI) -> str:
        """Add a package API to the database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO package_apis (
                    id, session_id, package_name, api_signature, usage_example,
                    documentation, discovered_at, last_used, usage_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                package_api.id,
                package_api.session_id,
                package_api.package_name,
                package_api.api_signature,
                package_api.usage_example,
                package_api.documentation,
                package_api.discovered_at,
                package_api.last_used,
                package_api.usage_count
            ))
            conn.commit()
        return package_api.id

    def get_package_apis(self, session_id: str) -> List[PackageAPI]:
        """Get all package APIs for a session"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, session_id, package_name, api_signature, usage_example,
                       documentation, discovered_at, last_used, usage_count
                FROM package_apis WHERE session_id = ?
            """, (session_id,))
            
            apis = []
            for row in cursor.fetchall():
                apis.append(PackageAPI(
                    id=row[0],
                    session_id=row[1],
                    package_name=row[2],
                    api_signature=row[3],
                    usage_example=row[4],
                    documentation=row[5],
                    discovered_at=row[6],
                    last_used=row[7],
                    usage_count=row[8]
                ))
            return apis

    def add_codebase_pattern(self, pattern: CodebasePattern) -> str:
        """Add a codebase pattern to the database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO codebase_patterns (
                    id, session_id, pattern_type, code_snippet, description,
                    language, file_path, created_at, updated_at, tags_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                pattern.id,
                pattern.session_id,
                pattern.pattern_type,
                pattern.code_snippet,
                pattern.description,
                pattern.language,
                pattern.file_path,
                pattern.created_at,
                pattern.updated_at,
                json.dumps(pattern.tags)
            ))
            conn.commit()
        return pattern.id

    def get_codebase_patterns(self, session_id: str, pattern_type: str = None) -> List[CodebasePattern]:
        """Get codebase patterns for a session"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if pattern_type:
                cursor.execute("""
                    SELECT id, session_id, pattern_type, code_snippet, description,
                           language, file_path, created_at, updated_at, tags_json
                    FROM codebase_patterns WHERE session_id = ? AND pattern_type = ?
                """, (session_id, pattern_type))
            else:
                cursor.execute("""
                    SELECT id, session_id, pattern_type, code_snippet, description,
                           language, file_path, created_at, updated_at, tags_json
                    FROM codebase_patterns WHERE session_id = ?
                """, (session_id,))
            
            patterns = []
            for row in cursor.fetchall():
                patterns.append(CodebasePattern(
                    id=row[0],
                    session_id=row[1],
                    pattern_type=row[2],
                    code_snippet=row[3],
                    description=row[4],
                    language=row[5],
                    file_path=row[6],
                    created_at=row[7],
                    updated_at=row[8],
                    tags=json.loads(row[9])
                ))
            return patterns

    def add_validation_check(self, validation_check: ValidationCheck) -> str:
        """Add a validation check to the database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO validation_checks (
                    id, session_id, check_type, target_code, result,
                    message, suggestions_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                validation_check.id,
                validation_check.session_id,
                validation_check.check_type,
                validation_check.target_code,
                validation_check.result,
                validation_check.message,
                json.dumps(validation_check.suggestions),
                validation_check.created_at
            ))
            conn.commit()
        return validation_check.id

    def get_validation_checks(self, session_id: str) -> List[ValidationCheck]:
        """Get validation checks for a session"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, session_id, check_type, target_code, result,
                       message, suggestions_json, created_at
                FROM validation_checks WHERE session_id = ?
            """, (session_id,))
            
            checks = []
            for row in cursor.fetchall():
                checks.append(ValidationCheck(
                    id=row[0],
                    session_id=row[1],
                    check_type=row[2],
                    target_code=row[3],
                    result=row[4],
                    message=row[5],
                    suggestions=json.loads(row[6]),
                    created_at=row[7]
                ))
            return checks

    def get_database_info(self) -> Dict[str, Any]:
        """Get database information and statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get counts
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
                "database_size": self.db_path.stat().st_size if self.db_path.exists() else 0
            }