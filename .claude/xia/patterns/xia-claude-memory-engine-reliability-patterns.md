---
name: xia-claude-memory-engine-reliability-patterns
source: https://github.com/HelloRuru/claude-memory-engine
extracted: 2026-03-24
---

# Mid-Session Checkpoint + Correction Cycle + Health Checks — Xỉa from claude-memory-engine

**Source**: [HelloRuru/claude-memory-engine](https://github.com/HelloRuru/claude-memory-engine)
**Extracted**: 2026-03-24
**Gap filled**: No mid-session save points, no systematic rule violation tracking, no system health monitoring

## What this is

Three reliability patterns borrowed from claude-memory-engine:
1. **Mid-session checkpoint** — Every 20 messages, save a checkpoint with the last few records
2. **Correction cycle** — `/analyze` compares user edits against stored rules, logs violations
3. **Health checks** — `/check` (daily) and `/full-check` (weekly) for system monitoring

## Why it fills A's gap

Memory Bank MCP had `pre_compact.py` hook but no mid-session checkpoints. If a session crashed or the window closed unexpectedly, recent work could be lost. It also had no systematic way to detect when stored rules were being violated, and no visibility into system health.

## The pattern

### Mid-session checkpoint (user_prompt_submit.py)

```python
CHECKPOINT_INTERVAL = 20
MESSAGE_COUNT_FILE = CHECKPOINT_DIR / "message_count.json"

def increment_message_count() -> int:
    count = get_message_count()
    new_count = count + 1
    MESSAGE_COUNT_FILE.write_text(json.dumps({"count": new_count}))
    return new_count

def save_checkpoint(records: list) -> dict:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    checkpoint_file = CHECKPOINT_DIR / f"checkpoint_{timestamp}.jsonl"
    summary = {
        "timestamp": datetime.now().isoformat(),
        "message_count": get_message_count() + 1,
        "records_count": len(records),
        "last_few_records": records[-5:] if len(records) >= 5 else records
    }
    with open(checkpoint_file, "w") as f:
        f.write(json.dumps(summary) + "\n")
    return {"checkpoint_file": str(checkpoint_file), "message_count": summary["message_count"], "records_saved": summary["records_count"]}

# In main():
current_count = increment_message_count()
is_checkpoint = current_count % CHECKPOINT_INTERVAL == 0
if is_checkpoint:
    checkpoint_info = save_checkpoint(records)
```

### Correction cycle (main.py)

```python
@dataclass
class RuleViolation:
    id: str
    session_id: str
    rule_id: str
    rule_content: str
    violation_type: str
    before_content: str
    after_content: str
    detected_at: str
    frequency: int = 1
    resolved: bool = False

@mcp.tool()
def analyze_corrections(before_content: str, after_content: str, ctx: Context = None) -> str:
    rules = engine.db_adapter.get_all_rules()
    violations = []
    for memory in memories:
        if memory.memory_type == "rule" and memory.trigger:
            rule_keywords = re.findall(r'\w+', memory.trigger.lower())
            before_violates = any(kw in before_content.lower() for kw in rule_keywords if len(kw) > 3)
            after_fixed = not any(kw in after_content.lower() for kw in rule_keywords if len(kw) > 3)
            if before_violates and after_fixed:
                violation = RuleViolation(...)
                engine.db_adapter.add_or_update_rule_violation(violation)
                violations.append(...)
    return json.dumps({"status": "violations_found", "violations": violations})

@mcp.tool()
def get_rule_violations(unresolved_only: bool = True, ctx: Context = None) -> str:
    violations = engine.db_adapter.get_rule_violations(engine.current_session, unresolved_only)
    return json.dumps({"count": len(violations), "violations": violations})
```

### Health checks (commands)

`/check` — Calls `get_database_info()` for quick stats
`/full-check` — Calls `get_database_info()` + `get_frequent_errors()` + `get_rule_violations()` + `get_attention_state()`

## How to apply here

The implementation is already integrated:
- `user_prompt_submit.py` — Added checkpoint logic (message counter, checkpoint file)
- `models.py` — Added `RuleViolation` dataclass
- `database.py` — Added `rule_violations` table and methods (`add_or_update_rule_violation`, `get_rule_violations`, `resolve_rule_violation`, `get_all_rules`)
- `main.py` — Added MCP tools: `analyze_corrections()`, `get_rule_violations()`, `resolve_rule_violation()`
- `.claude/commands/` — Added `analyze.md`, `correct.md`, `check.md`, `full-check.md`

## Original context

claude-memory-engine uses pure JS hooks + markdown files. This implementation adapts the patterns to Python + SQLite:
- Checkpoints stored as JSON in `.claude/checkpoints/` instead of markdown
- Rule violations stored in SQLite `rule_violations` table with frequency aggregation
- Health checks use existing `get_database_info()` method instead of separate file scans
