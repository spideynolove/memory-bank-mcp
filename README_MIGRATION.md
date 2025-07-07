# Memory Bank MCP - SQLite Migration Guide

## Overview

This guide explains how to migrate your Memory Bank MCP from in-memory storage to persistent SQLite database with Docker Compose support.

## Key Changes

### 1. Project Isolation
- Each project now gets its own `memory.db` SQLite database
- Database is automatically detected in project root (looks for `.git`, `package.json`, etc.)
- No more shared state between different Claude Code projects

### 2. Persistent Storage
- All memories, sessions, and collections are now stored in SQLite
- Data survives MCP server restarts
- Automatic backup of old JSON files during migration

### 3. Docker Compose Support
- Simple `docker-compose up` to start the MCP server
- Optional SQLite browser for database inspection
- Project-specific volume mounting for isolation

## Quick Start

### 1. Standard Setup
```bash
# Install dependencies with uv
uv sync

# Start MCP server (auto-migration will occur if needed)
uv run python main.py
```

### 2. Docker Setup
```bash
# Copy environment file
cp .env.example .env

# Start with Docker Compose
docker-compose up -d

# Optional: Start with SQLite browser for debugging
docker-compose --profile debug up -d
```

### 3. Manual Migration
```bash
# Check migration status
uv run python migration.py --status

# Force migration (if needed)
uv run python migration.py --migrate --force

# Migrate specific project
uv run python migration.py --project-path /path/to/project --migrate
```

## Database Schema

### Tables Created
- `sessions` - Memory session metadata
- `memories` - Individual memory entries
- `collections` - Memory collections within sessions
- `patterns` - Detected thinking patterns

### Project Detection
The system automatically detects project root by looking for:
- `.git` directory
- `package.json`
- `requirements.txt`
- `Cargo.toml`
- `go.mod`
- `composer.json`

## Migration Process

### Automatic Migration
1. On MCP server startup, checks for existing `memory_storage.json`
2. If found and SQLite database is empty, automatically migrates
3. Creates backup of JSON file with timestamp
4. Preserves all memory relationships and session data

### Manual Migration
```bash
# Get detailed migration status
uv run python migration.py --status

# Example output:
{
  "project_path": "/home/user/my-project",
  "json_file_exists": true,
  "sqlite_data_exists": false,
  "json_file_path": "/home/user/my-project/memory_storage.json",
  "sqlite_db_path": "/home/user/my-project/memory.db",
  "database_info": {
    "sessions_count": 0,
    "memories_count": 0,
    "collections_count": 0
  }
}
```

## Docker Compose Services

### Core Service
- `memory-bank-mcp` - Main MCP server
- Mounts project directory for database isolation
- Auto-restarts on failure

### Optional Services
- `sqlite-browser` - Web-based database inspection
- Available on `http://localhost:8080`
- Start with `--profile debug`

## Environment Variables

```bash
# Project path (auto-detected if not set)
PROJECT_PATH=./

# Database file name
SQLITE_DB_PATH=memory.db

# Enable debug logging
MCP_DEBUG=false
```

## File Structure

```
your-project/
├── memory.db                    # SQLite database (auto-created)
├── memory_storage.json.backup_* # Backup of old JSON (if migrated)
└── docker-compose.yml          # Docker setup (if using)
```

## Troubleshooting

### Migration Issues
```bash
# Check what's preventing migration
uv run python migration.py --status

# Force migration even if SQLite has data
uv run python migration.py --migrate --force
```

### Database Inspection
```bash
# Using SQLite CLI
sqlite3 memory.db .tables

# Using Docker browser
docker-compose --profile debug up sqlite-browser
# Visit http://localhost:8080
```

### Starting Fresh
```bash
# Remove existing database
rm memory.db

# Restart MCP server for auto-migration
uv run python main.py
```

## Performance Notes

- SQLite provides much better performance than JSON for large datasets
- Database includes indexes for fast memory and session lookups
- Automatic maintenance of timestamps and relationships
- Concurrent access support for multiple MCP clients

## Backup Strategy

1. **JSON Backup**: Original files are automatically backed up during migration
2. **SQLite Backup**: Use standard SQLite backup commands
3. **Docker Volumes**: Persistent volumes ensure data survives container restarts

```bash
# Backup SQLite database
cp memory.db memory.db.backup.$(date +%Y%m%d_%H%M%S)

# Restore from backup
cp memory.db.backup.20240101_120000 memory.db
```

## Compatibility

- **Existing JSON data**: Automatically migrated on first run
- **MCP tool interface**: Unchanged - all existing tools work identically
- **Claude Code integration**: Seamless - no changes needed in Claude Code configuration

## Next Steps

After migration, you can:
1. Use all existing MCP tools exactly as before
2. Benefit from persistent storage across sessions
3. Inspect your memory database using the web browser
4. Scale to larger datasets without performance issues
5. Share project databases with team members