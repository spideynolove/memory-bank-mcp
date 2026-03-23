---
name: xia-claude-reflect-hook-based-automatic-capture
source: https://github.com/BayramAnnakov/claude-reflect
extracted: 2026-03-24
---

# Hook-based Automatic Capture — Xỉa from claude-reflect

**Source**: [BayramAnnakov/claude-reflect](https://github.com/BayramAnnakov/claude-reflect)
**Extracted**: 2026-03-24
**Gap filled**: No automatic trigger mechanism for learning from user corrections

## What this is

A `UserPromptSubmit` hook that automatically detects learning patterns (corrections, preferences, guardrails) in user messages and queues them for memory storage. Uses regex pattern matching to identify correction events and tool errors, then queues them to `.claude/learnings/` for later processing.

## Why it fills A's gap

Memory Bank MCP had storage tools (`store_memory`) but no automatic trigger mechanism. AI only stored memories when explicitly prompted. This hook creates an automatic capture loop: user corrections → pattern detection → learning queue → memory storage.

## The pattern

```python
CORRECTION_PATTERNS = [
    r"not\s+that", r"don't\s+do\s+that", r"wrong", r"incorrect",
    r"stop", r"fix\s+this", r"undo", r"revert"
]

def detect_correction_patterns(content: str) -> list:
    matches = []
    for pattern in CORRECTION_PATTERNS:
        if re.search(pattern, content.lower()):
            matches.append(("correction", pattern))
    return matches

def process_transcript(records: list) -> dict:
    for i, record in enumerate(records):
        if record.get("role") == "user":
            patterns = detect_correction_patterns(record.get("content", ""))
            if patterns:
                queue_learning(extract_learning_event(records, i))
    return {"corrections_found": len(corrections_found)}
```

## How to apply here

**Location**: `.claude/hooks/user_prompt_submit.py` (already created)

**Integration points**:
- Hook runs on every `UserPromptSubmit` event via Claude Code settings.json
- Queues learning events to `.claude/learnings/learnings_queue.jsonl`
- Call `extract_tool_errors()` MCP tool to process queue into database
- Tool errors automatically detected and queued separately to `tool_errors.jsonl`

**Usage**:
1. Configure hook in settings.json: `"UserPromptSubmit": ["python", ".claude/hooks/user_prompt_submit.py"]`
2. Hook automatically captures corrections and tool errors
3. Call `extract_tool_errors()` MCP tool to import queued events into database
4. Memories created with `memory_type=correction`, `priority=1`, `trigger=user_correction_event`

## Original context

`claude-reflect` uses this hook to power its `/reflect` workflow, which aggregates correction events across sessions and proposes CLAUDE.md updates. Memory Bank MCP adapts this for its `store_memory` workflow, storing corrections as `memory_type=correction` with `priority=1` for high-priority recall.
