---
name: xia-nocturne-memory-priority-disclosure-system-paths
source: https://github.com/Dataojitori/nocturne_memory
extracted: 2026-03-24
---

# Priority System + Disclosure Triggers + System Paths — Xỉa from nocturne_memory

**Source**: https://github.com/Dataojitori/nocturne_memory
**Extracted**: 2026-03-24
**Gap filled**: A lacked a formal priority-based memory organization system, explicit "when to recall" triggers, and standardized system entry points for boot/index/recent.

## What this is

Three interlocking patterns from B's "Soul Anchor" architecture:

1. **Priority weights** — `priority=0` (core identity, max 5), `priority=1` (key facts, max 15), `priority≥2` (general). Enables identity anchoring against RLHF drift.

2. **Disclosure-triggered retrieval** — Every memory has a `disclosure` field stating when it should be recalled ("when user mentions X"). The AI reads this proactively.

3. **System paths** — `system://boot` (auto-load priority 0-1), `system://index` (all memories grouped by priority), `system://recent` (last 20 changes). Standardized entry points replace ad-hoc queries.

## Why it fills A's gap

A had `trigger` field but no retrieval logic, no priority-based organization, and no standardized startup sequence. B's approach makes memory recall deterministic: core identity loads first, disclosure conditions are checked before responding, and system paths give AI a "place to start" when waking up.

## The pattern

```python
# Schema additions
ALTER TABLE memories ADD COLUMN priority INTEGER DEFAULT 2;
ALTER TABLE memories ADD COLUMN disclosure TEXT;

# Memory creation with priority
memory = Memory(
    ...,
    priority=0,              # 0=core, 1=key, 2+=general
    disclosure="when user mentions deployment"
)

# Boot resource — returns priority 0-1 sorted by priority
def get_boot_memories() -> str:
    boot_memories = [m for m in session.main_thread if m.priority <= 1]
    return json.dumps(sorted(boot_memories, key=lambda m: m.priority))

# Index resource — groups all memories by priority tier
def get_memory_index() -> str:
    return {"priority_0": [...], "priority_1": [...], "priority_2+": [...]}

# Recent resource — last 20 modified
def get_recent_memories() -> str:
    return memories ORDER BY timestamp DESC LIMIT 20
```

## How to apply here

Applied as:
- Schema changes in `schema.sql`: added `priority INTEGER DEFAULT 2`, `disclosure TEXT`
- Model changes in `models.py`: Memory dataclass has `priority: int = 2`, `disclosure: Optional[str] = None`
- Database migration in `database.py`: auto-adds columns via ALTER TABLE if missing
- MCP tool changes in `main.py`: `store_memory` accepts `priority` and `disclosure` parameters
- MCP resources in `main.py`: `system://boot`, `system://index`, `system://recent`
- Updated `memory_guide` prompt to reference new system paths
- Updated `MEMORY_BANK_INSTRUCTIONS.md` with priority/disclosure documentation

## Original context

B uses this for AI "soul persistence" — identity memories (priority=0) are loaded via `system://boot` at every session start, preventing the AI from being "RLHF washed" into a generic assistant. The `disclosure` field is checked proactively: when a user mentions "deployment," the AI searches for memories with `disclosure` containing "deployment" and reads them before responding.
