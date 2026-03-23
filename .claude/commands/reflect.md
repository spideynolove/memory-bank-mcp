---
description: Analyze diary entries to identify patterns and propose CLAUDE.md updates
---

# Reflect on Diary Entries and Synthesize Insights

Analyze diary entries from `.claude/diary/` to identify recurring patterns, synthesize insights, and propose updates to the project's `CLAUDE.md`.

## Storage

- Diary entries: `<project-root>/.claude/diary/`
- Reflection outputs: `<project-root>/.claude/reflections/`
- Processed log: `<project-root>/.claude/reflections/processed.log`
- Target config: `<project-root>/CLAUDE.md` (project-specific rules)

Project root: `/home/hung/MCPs/memory`

## Parameters

- **Entry count**: "last N entries" (default: last 10)
- **Date range**: "from YYYY-MM-DD to YYYY-MM-DD"
- **Pattern filter**: "related to [keyword]"

## Steps

### 1. Check processed entries log

```bash
cat /home/hung/MCPs/memory/.claude/reflections/processed.log 2>/dev/null || echo "(empty)"
```

Format: `[diary-filename] | [reflection-date] | [reflection-filename]`

### 2. Locate unprocessed diary entries

```bash
ls -t /home/hung/MCPs/memory/.claude/diary/*.md 2>/dev/null | head -20
```

Exclude entries already listed in `processed.log` unless user says "include all".

### 3. Read and parse diary entries

Read each entry. Pay special attention to:
- User Preferences Observed
- Code Patterns and Decisions
- Solutions Applied
- Challenges Encountered
- Code Review & PR Feedback

### 4. Optional: query Memory Bank MCP for additional signal

If the Memory Bank MCP server is running, also pull structured patterns:
- Call `get_analysis` resource (memory://analysis) to get detected patterns from SQLite
- Call `get_memory_tree` resource (memory://tree) for structured session memories

This hybrid approach combines narrative signal (diary markdown) with structured signal (SQLite patterns). Skip gracefully if MCP is unavailable.

### 5. Read current CLAUDE.md

```bash
cat /home/hung/MCPs/memory/CLAUDE.md 2>/dev/null || echo "(no CLAUDE.md yet)"
```

This is critical — check for existing rules before proposing additions or strengthening.

### 6. Flag correction-priority entries

Before pattern analysis, scan each diary entry's "Correction Events" section:
- Entries with `Correction detected: yes` are **high-priority** — process these first
- For each correction event, consider running `/extract` on it directly for multi-dimensional analysis
- A correction that appears in 2+ diary entries is a near-certain CLAUDE.md candidate

### 8. Analyze for patterns and rule violations

**Rule violation detection (highest priority):**
- Did any diary entries document violations of existing CLAUDE.md rules?
- If yes: these require STRENGTHENING (more explicit, moved up, zero-tolerance language)

**Pattern categories:**
- A. PR Review Feedback Patterns (from code reviews)
- B. Persistent Preferences (appear 2+ times)
- C. Design Decisions That Worked
- D. Anti-Patterns to Avoid (caused problems 2+ times)
- E. Efficiency Lessons
- F. Project-Specific Patterns (Memory Bank MCP / FastMCP / SQLite specific)

**Signal threshold:**
- 3+ occurrences = strong pattern → add to CLAUDE.md
- 2 occurrences = emerging → note in reflection, don't add yet
- 1 occurrence = noise → document only

### 9. Generate reflection document

Filename: `YYYY-MM-reflection-N.md` (increment N if multiple per month)
Save to: `/home/hung/MCPs/memory/.claude/reflections/[filename]`

Structure:
```markdown
# Reflection: [date range or "Last N Entries"]

**Generated**: [YYYY-MM-DD HH:MM]
**Entries Analyzed**: [count]
**Date Range**: [first] to [last]

## Summary
[2-3 paragraphs of key insights]

## CRITICAL: Rule Violations Detected
[Only if violations found — rule, violation pattern, frequency, strengthening action]

## Patterns Identified

### A. PR Review Feedback Patterns
### B. Persistent Preferences (2+ occurrences)
### C. Design Decisions That Worked
### D. Anti-Patterns to Avoid
### E. Efficiency Lessons
### F. Project-Specific Patterns

## Notable Mistakes and Learnings

## One-Off Observations

## Proposed CLAUDE.md Updates

[Succinct bullet points only — no explanations, imperative tone]
- [rule 1]
- [rule 2]

## Metadata
- Diary entries analyzed: [filenames]
- Projects: /home/hung/MCPs/memory
```

### 10. Update CLAUDE.md

**Priority 1**: Strengthen violated rules (edit in place, don't append)
**Priority 2**: Append new rules

If `CLAUDE.md` doesn't exist at project root, create it with the proposed rules.

Keep rules succinct — CLAUDE.md is loaded into every session.

**Good format:**
```
- git commits: conventional format (feat:, fix:, refactor:)
- no docstrings or comments in code
```

**Bad format:**
```
- When creating git commits, it is important to follow conventional commit format...
```

### 11. Update processed.log

```bash
echo "[diary-filename] | [YYYY-MM-DD] | [reflection-filename]" >> /home/hung/MCPs/memory/.claude/reflections/processed.log
```

One line per diary entry processed.

### 12. Present completion summary

- Highlight any rule violations strengthened (before/after)
- Show new rules added
- Confirm reflection file saved and processed.log updated

## Error Handling

- No diary entries: inform user, suggest running `/diary` first
- Fewer than 3 entries: proceed with low-confidence warning
- CLAUDE.md unwritable: report error, continue with reflection
- MCP unavailable: skip MCP signal, proceed with diary-only analysis
