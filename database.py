"""
Database adapter layer for Memory Bank MCP
Handles SQLite operations and project-specific database management
"""

import sqlite3
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import asdict

from main import Memory, Collection, MemorySession


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
            
            return {
                "database_path": str(self.db_path),
                "project_path": self.project_path,
                "sessions_count": sessions_count,
                "memories_count": memories_count,
                "collections_count": collections_count,
                "database_size": self.db_path.stat().st_size if self.db_path.exists() else 0
            }