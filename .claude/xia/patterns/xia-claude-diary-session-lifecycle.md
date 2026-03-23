---
name: xia-claude-diary-session-lifecycle
source: https://github.com/rlancemartin/claude-diary
extracted: 2026-03-23
---

# Session Lifecycle Pattern — Xỉa from claude-diary

**Source**: https://github.com/rlancemartin/claude-diary
**Extracted**: 2026-03-23
**Gap filled**: Memory Bank MCP had no session narrative capture, no cross-session synthesis, and no automatic pre-compact capture — only explicit per-fact `store_memory` calls.

## What this is

Three interlocking patterns that close the session lifecycle loop: (1) `/diary` — capture what happened in a session as a narrative markdown entry, (2) `/reflect` — synthesize N diary entries into pattern analysis and CLAUDE.md rule proposals, (3) `pre_compact.py` hook — automatically write a diary stub before context is compacted.

## Why it fills A's gap

A (Memory Bank MCP) requires explicit `store_memory` calls per fact. It has no narrative capture, no cross-session synthesis, and `analyze_memories` loses all detected patterns on server restart. B's session lifecycle provides the missing outer loop: human-readable capture → durable synthesis → self-improving config.

## The pattern

```
session → /diary (markdown in .claude/diary/) → /reflect (reads N entries, updates CLAUDE.md)
                ↑
pre-compact hook (auto-stub if diary not manually called)
```

Storage layout (project-local, no ~/.claude):
```
.claude/
├── commands/diary.md       ← /diary slash command
├── commands/reflect.md     ← /reflect slash command
├── diary/                  ← YYYY-MM-DD-session-N.md entries
├── reflections/
│   ├── processed.log       ← deduplication: diary-file | date | reflection-file
│   └── YYYY-MM-reflection-N.md
├── hooks/pre_compact.py    ← auto-capture before context compaction
└── settings.json           ← PreCompact hook config
```

## How to apply here

- `/diary` → `.claude/commands/diary.md` (auto-discovered by Claude Code)
- `/reflect` → `.claude/commands/reflect.md`
- Pre-compact → `.claude/hooks/pre_compact.py` + `.claude/settings.json`
- Reflection target: `CLAUDE.md` at project root (project-specific rules, not global)
- Optional MCP bridge: diary command calls `store_memory` for hybrid markdown + SQLite queryability

## Original context

B stored everything in `~/.claude/memory/` (global, not project-local). B's reflect updated `~/.claude/CLAUDE.md` (global config). The key adaptation: everything moved to `.claude/` inside the project so it travels with the git repo and stays project-scoped.
