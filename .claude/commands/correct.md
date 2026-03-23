---
description: Review tracked rule violations before starting work
---

# Review Rule Violations

Display all tracked rule violations from the correction analysis system.

## When to Use

- Before starting a new task (automatic reminder)
- After running `/reflect` to see what was cleaned up
- Manually anytime with `/correct`

## Usage

```
get_rule_violations(unresolved_only=true)
```

## What It Shows

- Rule violations detected by `/analyze`
- Frequency count (how many times each rule was missed)
- Rule content that was violated
- Detection timestamp

## Output Format

```json
{
  "count": 2,
  "violations": [
    {
      "id": "viol_xxx",
      "rule_id": "abc123",
      "violation_type": "rule_miss",
      "rule_content": "Gather evidence before...",
      "frequency": 3,
      "detected_at": "2026-03-24T10:30:00",
      "resolved": false
    }
  ]
}
```

## Resolving Violions

```
resolve_rule_violation(violation_id="viol_xxx")
```

## Integration with Workflow

1. Make mistake → User corrects you
2. Run `/analyze` to log the violation
3. Before next task → `/correct` shows active violations
4. Internalize rule → Mark as resolved
