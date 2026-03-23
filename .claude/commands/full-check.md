---
description: Weekly comprehensive audit of the memory system
---

# Full Memory Audit

Comprehensive weekly audit of the entire memory system.

## Usage

Run multiple checks in sequence:

```
get_database_info()
get_frequent_errors(min_frequency=3)
get_rule_violations(unresolved_only=true)
get_attention_state()
```

## What It Checks

1. **Database Info** — All tables, sizes, counts
2. **Frequent Tool Errors** — Tools failing 3+ times
3. **Unresolved Violations** — Rules being missed repeatedly
4. **Attention State** — Memory attention patterns

## Interpreting Results

- **Frequent errors** → Tools or patterns needing attention
- **High violation count** → Rules not being internalized
- **Large database** → Consider `/reflect` to clean up
- **Skewed attention** → Some memories getting too much/little focus

## When to Run

- Weekly as comprehensive audit
- Before major cleanup sessions
- When investigating system issues
- After big feature additions

## Actions to Take

Based on findings:
1. High violation frequency → Review rule triggers
2. Many frequent errors → Check tool usage patterns
3. Large database → Run `/reflect` to consolidate
4. Low attention on key rules → Use `boost_memory_attention()`

## Related

- `/check` — Daily quick scan
- `/reflect` — Clean up and consolidate memories
