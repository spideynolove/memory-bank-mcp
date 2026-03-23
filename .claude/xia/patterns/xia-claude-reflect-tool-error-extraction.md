---
name: xia-claude-reflect-tool-error-extraction
source: https://github.com/BayramAnnakov/claude-reflect
extracted: 2026-03-24
---

# Tool Error Extraction and Aggregation — Xỉa from claude-reflect

**Source**: [BayramAnnakov/claude-reflect](https://github.com/BayramAnnakov/claude-reflect)
**Extracted**: 2026-03-24
**Gap filled**: No systematic tracking of tool errors for learning from mistakes

## What this is

A system for extracting tool errors from transcript data, aggregating by error signature, and tracking frequency over time. Supports querying frequent errors, resolving errors with notes, and identifying recurring problems.

## Why it fills A's gap

Memory Bank MCP had no way to track or learn from tool errors. When MCP tools failed, the context was lost. This system creates a feedback loop: tool errors → extraction → aggregation → frequent error reporting → resolution tracking.

## The pattern

```python
def extract_tool_errors(records: list) -> list:
    errors = []
    for record in records:
        content = record.get("content") or []
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    tool_name = block.get("name", "unknown")
                    result = block.get("result", {})
                    if isinstance(result, dict) and result.get("isError"):
                        errors.append({
                            "tool": tool_name,
                            "error": result.get("error", "Unknown error")
                        })
    return errors

def add_or_update_tool_error(error: ToolError) -> str:
    existing = db.query(
        "SELECT id, frequency FROM tool_errors
         WHERE session_id = ? AND tool_name = ? AND error_message = ?"
    )
    if existing:
        db.execute("UPDATE tool_errors SET frequency = frequency + 1")
    else:
        db.execute("INSERT INTO tool_errors ...")
```

## How to apply here

**Database**: `tool_errors` table (added to schema.sql)
- `id`, `session_id`, `tool_name`, `error_message`, `error_context`
- `frequency` (auto-increments on duplicate errors)
- `first_seen`, `last_seen` (timestamps)
- `resolved`, `resolution_note`

**MCP Tools**:
- `extract_tool_errors()` - Process queued errors from learnings directory
- `get_tool_errors(tool_name, unresolved_only)` - Query errors
- `resolve_tool_error(error_id, resolution_note)` - Mark error as resolved
- `get_frequent_errors(min_frequency)` - Report recurring problems

**MCP Resource**:
- `memory://tool-errors` - JSON dump of all errors for session

**Usage**:
1. Hook automatically captures tool errors to `.claude/learnings/tool_errors.jsonl`
2. Call `extract_tool_errors()` to import into database
3. Call `get_frequent_errors(min_frequency=3)` to see recurring issues
4. Use `resolve_tool_error()` to mark resolved issues

## Original context

`claude-reflect` uses tool error extraction as part of its multi-dimensional `/extract` command, aggregating errors to identify patterns of failures. Memory Bank MCP adapts this as a standalone tool set for tracking tool reliability issues across sessions.
