# XIALOGUE — Memory Bank MCP

## Current evolved state of A

Memory Bank MCP is a FastMCP-based MCP server (Python, SQLite) exposing 24 tools for structured memory storage within developer sessions. It supports sessions with problem/success-criteria framing, typed memories with confidence scores and contradiction detection, collection organization, codebase context loading, automatic learning capture via hooks, mid-session checkpoints, rule violation tracking, and health monitoring.

As of 2026-03-23, the project borrowed the **session lifecycle pattern** from `rlancemartin/claude-diary`: a `/diary` slash command for narrative session capture, a `/reflect` command for cross-session synthesis into CLAUDE.md rule proposals, and a `pre_compact.py` hook for automatic capture before context compaction. All storage is project-local under `.claude/`.

As of 2026-03-24, the project borrowed the **multi-dimensional extraction pattern** from `obra/claude-memory-extractor`: a `/extract` slash command that runs Five Whys + Psychological Driver + Systems Thinking in parallel then synthesizes with an epistemic humility check before storing. The Memory model and SQLite schema gained three new fields: `trigger` (when to apply), `memory_type` (rule/preference/pattern/case_study/constraint), and `has_user_correction` (boolean). The `/diary` command now captures a "Correction Events" section, and `/reflect` flags correction-priority entries before pattern analysis. The DB init migrates existing databases automatically via `ALTER TABLE`.

As of 2026-03-24, the project borrowed the **custom instructions / workflow pattern** from `alioshr/memory-bank-mcp`: a `MEMORY_BANK_INSTRUCTIONS.md` file that defines the AI's behavioral contract for using the memory bank (pre-flight validation, explicit store/revise/analyze triggers, reinvention prevention gates, session lifecycle rules). The `memory_guide` MCP prompt was updated from a flat tool list to a compact version of the same workflow. This fills the meta-layer gap: A had 14+ tools but no guidance on when or how to orchestrate them.

As of 2026-03-24, the project borrowed the **priority system + disclosure triggers + system paths** from `Dataojitori/nocturne_memory`: a `priority` field (0=core identity max 5, 1=key facts max 15, 2+=general), a `disclosure` field for "when to recall" triggers, and three MCP resources (`system://boot`, `system://index`, `system://recent`) for standardized entry points. The schema, models, database migration, and `store_memory` tool were updated accordingly. This fills the memory organization gap: A had ad-hoc storage with no deterministic recall strategy.

As of 2026-03-24, the project borrowed the **hook-based automatic capture + tool error extraction** from `BayramAnnakov/claude-reflect`: a `user_prompt_submit.py` hook that detects correction patterns in user messages and queues learning events, plus a `tool_errors` table with aggregation by frequency. This fills the automatic trigger gap: A had storage tools but no automatic mechanism to capture learning opportunities. New tools: `extract_tool_errors()`, `get_tool_errors()`, `resolve_tool_error()`, `get_frequent_errors()`. New resource: `memory://tool-errors`.

As of 2026-03-24, the project borrowed the **context router with attention dynamics** from `GMaN1911/claude-cognitive`: attention-based file injection with HOT/WARM/COLD tiers, keyword activation, co-activation between related memories, decay rates per category, and history tracking for debugging attention behavior. This fills the intelligent context selection gap: A had persistent storage but no mechanism to prioritize which memories to inject during context compaction or to track memory attention across turns. The pattern integrates via a new `context_router.py` hook and adds attention state persistence in `.claude/attn_state.json`.

As of 2026-03-24, the project borrowed **three reliability patterns** from `HelloRuru/claude-memory-engine`:

1. **Mid-session checkpoint**: Every 20 messages, `user_prompt_submit.py` saves a checkpoint with the last few records. This provides reliable save points independent of session-end or pre-compact hooks. The checkpoint counter persists in `.claude/checkpoints/message_count.json`.

2. **Correction cycle**: `/analyze` compares user edits against stored rules using trigger keyword matching, logging violations to a `rule_violations` table with frequency tracking. `/correct` reviews active violations before starting work. This fills the mistake-tracking gap: A had storage but no systematic way to detect when rules were being missed.

3. **Health checks**: `/check` (daily) provides quick database stats, `/full-check` (weekly) runs comprehensive audit including frequent errors, unresolved violations, and attention state. This fills the system maintenance gap: A had no visibility into system health or accumulation of problems.

New tools: `analyze_corrections()`, `get_rule_violations()`, `resolve_rule_violation()`. New commands: `analyze.md`, `correct.md`, `check.md`, `full-check.md`. New model: `RuleViolation`. New database table: `rule_violations` with frequency aggregation.

As of 2026-03-24, the project borrowed **four patterns** from `memvid/claude-brain`:

1. **Endless Mode compression**: Large tool outputs (Read, Bash, Grep, etc.) are compressed to ~500 tokens while preserving key information (imports, exports, functions, errors). This fills the token waste gap: A stored full verbose outputs, now compresses 20x while retaining essential information.

2. **Git diff file capture**: Session-end hook captures file modifications via git diff since PostToolUse doesn't reliably fire for Edit operations. Also falls back to `find -mmin -30` for untracked directories. This fills the missing edits gap: A could miss file modifications.

3. **In-memory deduplication**: Time-based cache (60s window) prevents storing duplicate observations using MD5 content hashing. Persists to `.claude/checkpoints/dedup_cache.json`. This fills the duplicate spam gap: A had no deduplication.

4. **Auto session summary**: Session-end hook automatically generates structured summary including key decisions, files modified, and summary sentence. Stored to `.claude/summaries/summary_{timestamp}.json`. This fills the auto-synthesis gap: A had manual diary but no automatic session summary.

---

## Borrow history

| Date | Source | Pattern | Gap filled | Saved to |
|------|--------|---------|------------|----------|
| 2026-03-23 | [rlancemartin/claude-diary](https://github.com/rlancemartin/claude-diary) | Session lifecycle (diary + reflect + pre-compact hook) | No narrative capture, no cross-session synthesis, no automatic pre-compact save | .claude/xia/patterns/xia-claude-diary-session-lifecycle.md |
| 2026-03-24 | [obra/claude-memory-extractor](https://github.com/obra/claude-memory-extractor) | Multi-dimensional extraction (Five Whys + epistemic humility + trigger/type/correction fields) | Shallow contradiction detection, no lesson extraction framework, no trigger conditions on memories | .claude/xia/patterns/xia-claude-memory-extractor-multidimensional.md |
| 2026-03-24 | [alioshr/memory-bank-mcp](https://github.com/alioshr/memory-bank-mcp) | Custom instructions / workflow pattern (pre-flight validation, store/revise triggers, reinvention gate, session lifecycle) | 14+ tools with no orchestration guidance — AI only used tools when explicitly prompted | .claude/xia/patterns/xia-alioshr-memory-bank-custom-instructions.md |
| 2026-03-24 | [Dataojitori/nocturne_memory](https://github.com/Dataojitori/nocturne_memory) | Priority system + disclosure triggers + system paths (priority weights, "when to recall" field, system://boot/index/recent) | No priority-based organization, no explicit retrieval triggers, no standardized startup sequence | .claude/xia/patterns/xia-nocturne-memory-priority-disclosure-system-paths.md |
| 2026-03-24 | [BayramAnnakov/claude-reflect](https://github.com/BayramAnnakov/claude-reflect) | Hook-based automatic capture + tool error extraction (user_prompt_submit hook, correction pattern detection, tool error aggregation) | No automatic trigger mechanism for learning, no systematic tracking of tool errors | .claude/xia/patterns/xia-claude-reflect-hook-based-automatic-capture.md, .claude/xia/patterns/xia-claude-reflect-tool-error-extraction.md |
| 2026-03-24 | [GMaN1911/claude-cognitive](https://github.com/GMaN1911/claude-cognitive) | Context router with attention dynamics (HOT/WARM/COLD tiers, keyword activation, co-activation, decay rates, history tracking) | No intelligent context selection when working with large memory banks — all memories treated equally, leading to token waste and irrelevant context injection | .claude/xia/patterns/xia-claude-cognitive-context-router.md |
| 2026-03-24 | [HelloRuru/claude-memory-engine](https://github.com/HelloRuru/claude-memory-engine) | Three reliability patterns (mid-session checkpoint, correction cycle, health checks) | No mid-session save points, no systematic rule violation tracking, no system health monitoring | .claude/xia/patterns/xia-claude-memory-engine-reliability-patterns.md |
| 2026-03-24 | [memvid/claude-brain](https://github.com/memvid/claude-brain) | Endless Mode compression (tool output compression to ~500 tokens) | Token waste on verbose tool outputs | .claude/xia/patterns/xia-claude-brain-endless-mode-compression.md |
| 2026-03-24 | [memvid/claude-brain](https://github.com/memvid/claude-brain) | Git diff file capture (session-end file change tracking) | Missing Edit operations in hooks (PostToolUse bug) | .claude/xia/patterns/xia-claude-brain-git-diff-capture.md |
| 2026-03-24 | [memvid/claude-brain](https://github.com/memvid/claude-brain) | In-memory deduplication (60s window, MD5 hashing) | Duplicate observations spamming memory | .claude/xia/patterns/xia-claude-brain-in-memory-deduplication.md |
| 2026-03-24 | [memvid/claude-brain](https://github.com/memvid/claude-brain) | Auto session summary (structured session-end synthesis) | No automatic end-of-session synthesis | .claude/xia/patterns/xia-claude-brain-auto-session-summary.md |
