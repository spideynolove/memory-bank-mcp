# Memory Bank MCP — Custom Instructions

My memory resets between sessions. I rely ENTIRELY on the Memory Bank MCP and MUST run Pre-Flight Validation before every task.

---

## Pre-Flight Validation

Before starting any task:

1. Read `system://boot` — load core identity memories (priority 0-1)
2. Read `memory://tree` — check for an active session and its main thread
3. Read `memory://codebase-patterns` — recall known patterns for this project
4. Read `memory://validation-checks` — recall past reinvention checks

If no active session exists → call `create_memory_session` with the current problem.
If a session exists → continue from the last memory in the main thread.

---

## Session Lifecycle

### Starting a session

```
create_memory_session(
  problem="<what I am solving>",
  success_criteria="<how I know I'm done>",
  constraints="<hard limits, comma-separated>",
  session_type="coding_session" | "debugging_session" | "architecture_session" | "general"
)
```

Use `coding_session` for implementation work, `debugging_session` for bug hunts, `architecture_session` for design decisions.

### During a session — store triggers

Call `store_memory` when:
- A significant decision is made (why this approach over alternatives)
- A non-obvious dependency or constraint is discovered
- A bug root cause is identified
- An assumption is validated or invalidated
- A pattern is observed that will recur

```
store_memory(
  content="<what I learned or decided>",
  confidence=0.9,           # 0.5 = uncertain, 0.9 = confident, 1.0 = verified
  dependencies="id1,id2",   # prior memories this builds on
  memory_type="rule" | "preference" | "pattern" | "case_study" | "constraint",
  priority=0 | 1 | 2+,      # 0 = core identity (max 5), 1 = key facts (max 15), 2+ = general
  disclosure="<when to recall this memory>"
)
```

### Priority levels

| Priority | Meaning | Recommended limit |
|----------|---------|-------------------|
| 0 | Core identity, "who I am", "who my user is" | Max 5 |
| 1 | Key facts, high-frequency patterns, critical constraints | Max 15 |
| 2+ | General memories, observations, notes | Unlimited |

Use `priority=0` for memories that should be loaded at every session startup (via `system://boot`).
Use `priority=1` for memories that are frequently referenced but not identity-defining.

### Disclosure triggers

`disclosure` answers "when should I recall this memory?"

Good examples:
- "when user mentions project X"
- "when discussing database schema"
- "when implementing authentication"
- "when user asks about deployment"

Bad examples:
- "important" (too vague)
- "remember" (no trigger condition)
- "" (empty = no automatic recall)

### Revising memories

Call `revise_memory` when new evidence contradicts an existing memory. Never leave contradictions unresolved.

```
revise_memory(memory_id="<id>", new_content="<updated understanding>", confidence=0.8)
```

### Analyzing

Call `analyze_memories` when:
- The session is getting long and clarity is needed
- Preparing to make a final decision
- Contradictions are suspected

---

## Reinvention Prevention

Before implementing any new functionality:

```
prevent_reinvention_check(functionality_description="<what I am about to build>")
```

If matches exist → use the existing pattern or API. Only proceed with new implementation if the check returns no matches.

---

## Codebase Context

At the start of a coding session on an unfamiliar codebase:

```
load_codebase_context(project_path="<absolute path>")
```

Then read `memory://codebase-patterns` to see what was loaded.

Before using a new package:

```
validate_package_usage(code_snippet="<my intended usage>")
discover_packages()  # if unsure what's available
```

---

## Collections

Use `create_collection` when exploring alternatives — e.g., two competing approaches to a design decision.

```
create_collection(name="<label>", from_memory="<seed-memory-id>", purpose="<why comparing>")
```

Use `merge_collection` once a winner is chosen to consolidate into the main thread.

---

## Documentation Triggers

Update the Memory Bank when:
- A task is completed (store a summary memory with `confidence=1.0`)
- A pattern is discovered that will recur (`store_codebase_pattern`)
- An assumption proved wrong (`revise_memory` the original)
- ≥25% of the codebase is touched in one session

---

## Resource Reference

| Resource | What it contains |
|----------|-----------------|
| `system://boot` | Core identity memories (priority 0-1) |
| `system://index` | All memories grouped by priority |
| `system://recent` | Last 20 modified memories |
| `memory://tree` | Active session, main thread, collections |
| `memory://analysis` | Quality metrics, contradiction flags |
| `memory://patterns` | Session-level learning insights |
| `memory://codebase-patterns` | Stored code patterns and structures |
| `memory://validation-checks` | Past reinvention check results |
| `memory://packages` | Discovered package APIs |
| `memory://tool-errors` | Aggregated tool errors by frequency |

## Tool Error Tracking

The `user_prompt_submit` hook automatically captures tool errors and correction events to `.claude/learnings/`. Process queued events:

```
extract_tool_errors()           # Import queued errors into database
get_tool_errors(tool_name="")   # Query errors by tool or all
get_frequent_errors(min=3)      # Show recurring problems
resolve_tool_error(error_id)    # Mark error as resolved
```

Use `get_frequent_errors()` before implementing to avoid repeating known failures.
