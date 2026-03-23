---
description: Daily health check for the memory system
---

# Memory Health Check

Quick daily scan to check the memory system's health and capacity.

## Usage

No parameters needed. Just run:

```
get_database_info()
```

## What It Checks

- Database file size and location
- Session count
- Memory count
- Collection count
- Package APIs discovered
- Codebase patterns stored
- Validation checks performed
- Tool errors tracked
- Rule violations tracked

## Output Format

```json
{
  "database_path": "/path/to/memory.db",
  "project_path": "/path/to/project",
  "sessions_count": 5,
  "memories_count": 42,
  "collections_count": 3,
  "package_apis_count": 15,
  "codebase_patterns_count": 28,
  "validation_checks_count": 7,
  "database_size": 245760
}
```

## When to Run

- Daily as a quick health scan
- After major work sessions
- When memory behavior seems off
- Before `/reflect` to understand current state

## Related

- `/full-check` — Weekly comprehensive audit
- `/check` — Daily quick scan (this command)
