---
description: Compare code edits against stored rules to detect violations
---

# Correction Analysis

Compare before/after code content against stored rules to detect rule violations and track repeated mistakes.

## When to Use

Run immediately after the user corrects your work:
- User says "no", "wrong", "not that" followed by the fix
- User edits your code and shows the corrected version
- User provides feedback that reveals a missed rule

## Usage

```
analyze_corrections(
  before_content="[original code that was wrong]",
  after_content="[corrected code]"
)
```

## What It Does

1. Extracts all stored rules from memory (memory_type = "rule")
2. Analyzes before_content for rule violations using trigger keywords
3. Checks if after_content fixes those violations
4. Logs violations to rule_violations table with frequency tracking
5. Returns JSON with detected violations

## Output Format

```json
{
  "status": "violations_found" | "no_violations",
  "count": 3,
  "violations": [
    {
      "rule_id": "abc123",
      "rule_trigger": "before adding features",
      "violation_id": "viol_xxx"
    }
  ]
}
```

## Related Tools

- `get_rule_violations()` — View all tracked violations
- `resolve_rule_violation(violation_id)` — Mark a violation as resolved
- `/correct` — Review active violations before starting work

## Pattern

This implements the correction cycle from claude-memory-engine:
1. User corrects you → run `/analyze` to log the mistake
2. Before next task → violations auto-load as reminder
3. Same mistake 3+ times → consider upgrading to a hard rule
