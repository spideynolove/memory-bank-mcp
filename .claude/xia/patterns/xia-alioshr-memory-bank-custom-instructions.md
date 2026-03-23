---
name: xia-alioshr-memory-bank-custom-instructions
source: https://github.com/alioshr/memory-bank-mcp
extracted: 2026-03-24
---

# Custom Instructions / Workflow Pattern — Xỉa from alioshr/memory-bank-mcp

**Source**: https://github.com/alioshr/memory-bank-mcp
**Extracted**: 2026-03-24
**Gap filled**: A had 14+ tools but no workflow guidance for how the AI should orchestrate them. Tools were present but the meta-layer (when to use each, in what order, with what triggers) was absent.

## What this is

A `custom-instructions.md` file that travels with the MCP server and defines the AI's behavioral contract for using the memory bank: pre-flight validation before every task, explicit store/revise/analyze triggers, reinvention prevention gates, and session lifecycle rules.

## Why it fills A's gap

B ships `custom-instructions.md` alongside its server. Users paste it into their AI client's system prompt. This transforms the tools from a passive API into an active workflow the AI follows autonomously. A had no equivalent — Claude would only use the tools when prompted explicitly, missing opportunities to store key decisions or check for reinvention.

## The pattern

Three structural elements:
1. **Pre-Flight Validation** — read all memory resources before every task to reconstruct context
2. **Explicit triggers** — define exactly when each tool fires (not "use when helpful" but "call before implementing any new functionality")
3. **Lifecycle rules** — session start, during-work cadence, documentation triggers, session close

## How to apply here

Applied as:
- `MEMORY_BANK_INSTRUCTIONS.md` in project root — full workflow reference
- `memory_guide` MCP prompt (main.py:582) updated to a compact version of the same workflow

Users include `MEMORY_BANK_INSTRUCTIONS.md` in their CLAUDE.md or MCP client system prompt.

## Original context

B's `custom-instructions.md` defines: Pre-Flight Validation (check project dir, core files, custom docs), Plan Mode (list_directory → strategy in activeContext.md), Act Mode (JSON ops with specific formatting), documentation update triggers (≥25% code impact, new patterns, user request, context ambiguity), and a hierarchical file structure (projectbrief → productContext/systemPatterns/techContext → activeContext → progress.md).
