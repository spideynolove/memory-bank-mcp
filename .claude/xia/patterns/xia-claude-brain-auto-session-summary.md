---
name: xia-claude-brain-auto-session-summary
source: https://github.com/memvid/claude-brain
extracted: 2026-03-24
---

# Auto Session Summary — Xỉa from claude-brain

**Source**: [memvid/claude-brain](https://github.com/memvid/claude-brain)
**Extracted**: 2026-03-24
**Gap filled**: No automatic end-of-session synthesis

## What this is

A session-end hook that automatically generates a structured summary including: key decisions made, files modified, user request count, and a concise summary sentence. Stored as JSON for future retrieval and analysis.

## Why it fills A's gap

Memory Bank MCP has manual `/diary` command for narrative capture, but no automatic way to synthesize session outcomes into a structured format that can be easily queried later.

## The pattern

```python
def generate_session_summary(records: list, file_changes: Dict[str, Any]) -> Dict[str, Any]:
    key_decisions = []
    files_modified = set()

    for record in records:
        role = record.get("role")
        content = record.get("content", "")

        if role == "assistant" and has_decision_keywords(content):
            key_decisions.append(content[:100])

        if has_file_path(content):
            files_modified.add(extract_file_path(content))

    summary_parts = []
    if user_messages: summary_parts.append(f"Addressed {len(user_messages)} requests")
    if files_modified: summary_parts.append(f"Modified {len(files_modified)} files")
    if key_decisions: summary_parts.append(f"Made {len(key_decisions)} decisions")

    return {
        "key_decisions": key_decisions[:10],
        "files_modified": sorted(list(files_modified))[:20],
        "summary": ". ".join(summary_parts)
    }

def save_session_summary(summary: Dict[str, Any]) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_file = SUMMARY_DIR / f"summary_{timestamp}.json"
    summary["timestamp"] = datetime.now().isoformat()
    summary["id"] = f"summary_{timestamp}"
    json.dump(summary, open(summary_file, "w"), indent=2)
    return str(summary_file)
```

## How to apply here

Implemented in `.claude/hooks/stop.py`:
- Runs at session end via Stop hook
- Extracts: key decisions (by keyword), files modified (from git diff)
- Stores to `.claude/summaries/summary_{timestamp}.json`
- Includes: summary sentence, decisions list, files list, counts

## Original context

claude-brain's `stop.ts` generates session summaries from observations and stores them in the memvid file. This enables quick retrieval of "what happened in this session" without loading all observations.
