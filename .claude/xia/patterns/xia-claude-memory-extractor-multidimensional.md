---
name: xia-claude-memory-extractor-multidimensional
source: https://github.com/obra/claude-memory-extractor
extracted: 2026-03-24
---

# Multi-Dimensional Extraction Pattern — Xỉa from claude-memory-extractor

**Source**: https://github.com/obra/claude-memory-extractor
**Extracted**: 2026-03-24
**Gap filled**: A's contradiction detection was simple keyword polarity; no structured way to extract deep lessons from events; memories lacked trigger conditions and type classification; correction events were not distinguished from normal session content.

## What this is

Three interlocking improvements to how A captures and classifies memories: (1) a `/extract` slash command that runs Five Whys + Psychological Driver + Systems Thinking in parallel and synthesizes with epistemic humility checks before calling `store_memory`, (2) `trigger` + `memory_type` + `has_user_correction` fields on the Memory model/DB, (3) correction-priority signal in diary entries and reflect workflow.

## Why it fills A's gap

B's core insight: extracting lessons is hard because agents converge on obvious interpretations and miss genuine ambiguity. The multi-dimensional framework (root cause + hidden motivation + prevention gate) produces more nuanced, actionable memories. B's epistemic humility check prevents overconfident extraction from ambiguous cases — a failure mode B documented experimentally (15/15 agents confidently wrong on an ambiguous JWT vs sessions debate).

## The pattern

```
event → /extract:
  Stage 1: three parallel lenses
    A. Five Whys (root cause)
    B. Hidden Motivation (psychological driver)
    C. Systems Thinking (prevention gate function)
  Stage 2: epistemic check
    confidence 1-5 | methodology vs technical | alternative readings
    if confidence < 4 OR genuine tradeoff → acknowledge uncertainty
  Stage 3: synthesize → store_memory(
    trigger="when this applies",
    memory_type="rule|preference|pattern|case_study|constraint",
    has_user_correction=bool
  )
```

Memory schema additions:
```python
trigger: Optional[str]           # "when to apply this"
memory_type: Optional[str]       # rule | preference | pattern | case_study | constraint
has_user_correction: bool        # user explicitly corrected Claude in this event
```

## How to apply here

- `/extract` → `.claude/commands/extract.md`
- Memory dataclass → `models.py`: `trigger`, `memory_type`, `has_user_correction`
- DB schema → `schema.sql` + `_init_database` migration via `ALTER TABLE`
- `database.py`: `add_memory`, `get_memory`, `update_memory` updated
- `main.py`: `engine.add_memory` + `store_memory` tool updated with new params
- `/diary` → "Correction Events" section detects user corrections
- `/reflect` → step 6 flags correction-priority entries before pattern analysis

## Original context

B used this framework to extract memories from historical JSONL session files in batch. A adapted it as an on-demand `/extract` command that can process a diary entry or free-form event description, then writes directly to the SQLite DB via `store_memory`.
