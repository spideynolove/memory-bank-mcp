---
description: Create a structured diary entry from the current session transcript
---

# Create Diary Entry from Current Session

Create a structured diary entry documenting what happened in the current session. Entries are stored project-locally in `.claude/diary/` and travel with the repository.

## Storage

All diary entries go to: `<project-root>/.claude/diary/YYYY-MM-DD-session-N.md`

The project root is `/home/hung/MCPs/memory` (or wherever this repo is checked out).

## Approach: Context-First Strategy

**Primary method (use this first):**
Reflect on the conversation history loaded in this session. You have access to:
- All user messages and requests
- Your responses and tool invocations
- Files read, edited, or written
- Errors encountered and solutions applied
- Design decisions discussed
- User preferences expressed

**JSONL fallback (only if context is insufficient):**
```bash
SESSION_FILE=$(ls -t ~/.claude/projects/-$(echo "{{ cwd }}" | sed 's/\//-/g' | sed 's/^-//')/*.jsonl 2>/dev/null | head -1) && \
if [ -z "$SESSION_FILE" ]; then \
  echo "ERROR: No session file found"; \
else \
  echo "FOUND: $SESSION_FILE" && ls -lh "$SESSION_FILE"; \
fi
```

Extract metadata only when needed:
```bash
SESSION_FILE="[path-from-above]" && \
echo "=== TOOL COUNTS ===" && \
jq -r 'select(.message.content[]?.name) | .message.content[].name' "$SESSION_FILE" | sort | uniq -c && \
echo "=== FILES MODIFIED ===" && \
grep -o '"filePath":"[^"]*"' "$SESSION_FILE" | sort -u
```

## Steps

### 1. Determine the entry filename

```bash
PROJECT_ROOT="/home/hung/MCPs/memory"
TODAY=$(date +%Y-%m-%d)
N=1
while [ -f "$PROJECT_ROOT/.claude/diary/${TODAY}-session-${N}.md" ]; do N=$((N+1)); done
DIARY_FILE="$PROJECT_ROOT/.claude/diary/${TODAY}-session-${N}.md"
echo "Will save to: $DIARY_FILE"
```

### 2. Create the diary entry

Write the entry using the Write tool (not bash echo). Template:

```markdown
# Session Diary Entry

**Date**: [YYYY-MM-DD]
**Time**: [HH:MM]
**Session ID**: [from JSONL filename if available, else "unknown"]
**Project**: /home/hung/MCPs/memory
**Git Branch**: [run: git -C /home/hung/MCPs/memory branch --show-current]

## Task Summary
[2-3 sentences: what the user was trying to accomplish]

## Work Summary
- [bullet: features implemented]
- [bullet: bugs fixed]
- [bullet: refactoring done]

## Design Decisions Made
- [decision: why X was chosen over Y]

## Actions Taken
- Files edited: [list]
- Commands run: [list]
- Key tools used: [list]

## Code Review & PR Feedback
- [any feedback about code quality or style]

## Challenges Encountered
- [errors hit, failed approaches, debugging steps]

## Solutions Applied
- [how problems were resolved]

## User Preferences Observed

### Commit & PR Preferences:
- [patterns around commits, PRs]

### Code Quality Preferences:
- [testing, linting, style]

### Technical Preferences:
- [libraries, patterns, frameworks]

## Code Patterns and Decisions
[technical patterns used or established]

## Context and Technologies
[project type, languages, frameworks involved this session]

## Correction Events
[Scan the conversation for user corrections — any message where the user said "no", "wrong", "that's not right", "actually", "stop doing X", or gave explicit negative feedback about Claude's approach.]
- Correction detected: [yes/no]
- If yes: [what Claude did → what the user corrected → what the right approach was]

## Notes
[any other observations]
```

### 3. Save the entry

Use the Write tool to write to the determined `$DIARY_FILE` path.

### 4. Optional: bridge to Memory Bank MCP

If the Memory Bank MCP server is running, call `store_memory` with a condensed version of the session summary. This makes the session searchable via the SQLite DB in addition to the markdown file. Gracefully skip if the MCP tool is unavailable.

### 5. Confirm

Show the saved path and a 2-line summary of what was captured.

## Guidelines

- Be factual and specific — include concrete file paths, error messages
- Capture the 'why' behind decisions, not just the what
- Document ALL user preferences (commits, PRs, linting, testing, code style)
- Include failures — what didn't work is valuable
- Use context-first; only parse JSONL when truly necessary
