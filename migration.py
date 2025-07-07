"""
Migration utilities for Memory Bank MCP
Handles migration from JSON file storage to SQLite database
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

from database import DatabaseAdapter
from main import Memory, Collection, MemorySession


class MigrationManager:
    """Manages migration from JSON storage to SQLite database"""
    
    def __init__(self, project_path: Optional[str] = None):
        self.db_adapter = DatabaseAdapter(project_path)
        self.project_path = self.db_adapter.project_path
        self.json_file_path = Path(self.project_path) / "memory_storage.json"
    
    def has_json_data(self) -> bool:
        """Check if there's existing JSON data to migrate"""
        return self.json_file_path.exists() and self.json_file_path.stat().st_size > 0
    
    def has_sqlite_data(self) -> bool:
        """Check if SQLite database already has data"""
        info = self.db_adapter.get_database_info()
        return info["sessions_count"] > 0 or info["memories_count"] > 0
    
    def load_json_data(self) -> Dict[str, Any]:
        """Load existing JSON data"""
        if not self.has_json_data():
            return {}
        
        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading JSON data: {e}")
            return {}
    
    def migrate_to_sqlite(self) -> Dict[str, Any]:
        """Migrate JSON data to SQLite database"""
        if not self.has_json_data():
            return {"status": "no_json_data", "message": "No JSON data found to migrate"}
        
        if self.has_sqlite_data():
            return {"status": "sqlite_exists", "message": "SQLite database already contains data"}
        
        json_data = self.load_json_data()
        if not json_data:
            return {"status": "empty_json", "message": "JSON file is empty or corrupted"}
        
        try:
            migration_stats = self._perform_migration(json_data)
            self._backup_json_file()
            return {
                "status": "success",
                "message": "Migration completed successfully",
                "stats": migration_stats
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Migration failed: {str(e)}",
                "error": str(e)
            }
    
    def _perform_migration(self, json_data: Dict[str, Any]) -> Dict[str, int]:
        """Perform the actual migration from JSON to SQLite"""
        stats = {
            "sessions_migrated": 0,
            "memories_migrated": 0,
            "collections_migrated": 0,
            "patterns_migrated": 0
        }
        
        # Migrate sessions
        sessions = json_data.get("sessions", {})
        for session_id, session_data in sessions.items():
            session = self._convert_json_session(session_id, session_data)
            self.db_adapter.create_session(session)
            stats["sessions_migrated"] += 1
        
        # Migrate memories
        memories = json_data.get("memories", {})
        for memory_id, memory_data in memories.items():
            memory = self._convert_json_memory(memory_id, memory_data)
            self.db_adapter.add_memory(memory)
            stats["memories_migrated"] += 1
        
        # Migrate collections (stored within sessions)
        for session_id, session_data in sessions.items():
            collections = session_data.get("collections", {})
            for collection_id, collection_data in collections.items():
                collection = self._convert_json_collection(collection_id, collection_data)
                self.db_adapter.create_collection(collection)
                stats["collections_migrated"] += 1
        
        # Migrate patterns
        patterns = json_data.get("patterns", {})
        if patterns and sessions:
            # Associate patterns with the most recent session
            latest_session = max(sessions.keys(), key=lambda x: sessions[x].get("last_updated", ""))
            self.db_adapter.update_patterns(patterns, latest_session)
            stats["patterns_migrated"] = len(patterns)
        
        return stats
    
    def _convert_json_session(self, session_id: str, session_data: Dict[str, Any]) -> MemorySession:
        """Convert JSON session data to MemorySession object"""
        return MemorySession(
            id=session_id,
            problem_statement=session_data.get("problem_statement", ""),
            success_criteria=session_data.get("success_criteria", ""),
            constraints=session_data.get("constraints", []),
            main_thread=session_data.get("main_thread", []),
            collections={},  # Will be populated separately
            patterns=session_data.get("patterns", []),
            started=session_data.get("started", datetime.now().isoformat()),
            last_updated=session_data.get("last_updated", datetime.now().isoformat())
        )
    
    def _convert_json_memory(self, memory_id: str, memory_data: Dict[str, Any]) -> Memory:
        """Convert JSON memory data to Memory object"""
        return Memory(
            id=memory_id,
            content=memory_data.get("content", ""),
            number=memory_data.get("number", 1),
            total_estimated=memory_data.get("total_estimated", 5),
            timestamp=memory_data.get("timestamp", datetime.now().isoformat()),
            confidence=memory_data.get("confidence", 0.8),
            dependencies=memory_data.get("dependencies", []),
            contradictions=memory_data.get("contradictions", []),
            tags=memory_data.get("tags", []),
            collection_id=memory_data.get("collection_id"),
            revision_of=memory_data.get("revision_of"),
            is_checkpoint=memory_data.get("is_checkpoint", False)
        )
    
    def _convert_json_collection(self, collection_id: str, collection_data: Dict[str, Any]) -> Collection:
        """Convert JSON collection data to Collection object"""
        return Collection(
            id=collection_id,
            name=collection_data.get("name", ""),
            created_from=collection_data.get("created_from", ""),
            purpose=collection_data.get("purpose", ""),
            memories=collection_data.get("memories", []),
            merged=collection_data.get("merged", False),
            merge_target=collection_data.get("merge_target")
        )
    
    def _backup_json_file(self):
        """Create a backup of the original JSON file"""
        if not self.json_file_path.exists():
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.json_file_path.with_suffix(f".backup_{timestamp}.json")
        
        try:
            import shutil
            shutil.copy2(self.json_file_path, backup_path)
            print(f"JSON backup created: {backup_path}")
        except Exception as e:
            print(f"Warning: Could not create backup: {e}")
    
    def get_migration_status(self) -> Dict[str, Any]:
        """Get current migration status"""
        return {
            "project_path": self.project_path,
            "json_file_exists": self.has_json_data(),
            "sqlite_data_exists": self.has_sqlite_data(),
            "json_file_path": str(self.json_file_path),
            "sqlite_db_path": str(self.db_adapter.db_path),
            "database_info": self.db_adapter.get_database_info()
        }
    
    def auto_migrate_if_needed(self) -> Optional[Dict[str, Any]]:
        """Automatically migrate if JSON exists and SQLite is empty"""
        if self.has_json_data() and not self.has_sqlite_data():
            return self.migrate_to_sqlite()
        return None


def main():
    """CLI interface for migration"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Memory Bank MCP Migration Tool")
    parser.add_argument("--project-path", help="Project path (auto-detected if not provided)")
    parser.add_argument("--status", action="store_true", help="Show migration status")
    parser.add_argument("--migrate", action="store_true", help="Perform migration")
    parser.add_argument("--force", action="store_true", help="Force migration even if SQLite has data")
    
    args = parser.parse_args()
    
    migrator = MigrationManager(args.project_path)
    
    if args.status:
        status = migrator.get_migration_status()
        print(json.dumps(status, indent=2))
    
    elif args.migrate:
        if not args.force and migrator.has_sqlite_data():
            print("SQLite database already has data. Use --force to override.")
            return
        
        result = migrator.migrate_to_sqlite()
        print(json.dumps(result, indent=2))
    
    else:
        # Auto-migration
        result = migrator.auto_migrate_if_needed()
        if result:
            print("Auto-migration performed:")
            print(json.dumps(result, indent=2))
        else:
            print("No migration needed.")


if __name__ == "__main__":
    main()