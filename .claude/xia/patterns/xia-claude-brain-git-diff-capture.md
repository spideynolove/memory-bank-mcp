---
name: xia-claude-brain-git-diff-capture
source: https://github.com/memvid/claude-brain
extracted: 2026-03-24
---

# Git Diff File Capture — Xỉa from claude-brain

**Source**: [memvid/claude-brain](https://github.com/memvid/claude-brain)
**Extracted**: 2026-03-24
**Gap filled**: Missing Edit operations in hooks (PostToolUse doesn't fire for Edits)

## What this is

A session-end hook that captures file modifications via git diff since PostToolUse hooks don't reliably fire for Edit operations. Captures both git-tracked changes and recently modified files in untracked directories.

## Why it fills A's gap

Memory Bank MCP relies on hooks to capture learning events, but Claude Code's PostToolUse hook has a bug where it doesn't fire for Edit operations. This means file modifications could be missed entirely.

## The pattern

```python
def capture_file_changes_via_git(project_root: Path) -> Dict[str, Any]:
    all_changed_files = []

    diff_names = subprocess.run(["git", "diff", "--name-only", "HEAD"],
                                cwd=project_root, capture_output=True, text=True, timeout=3)
    all_changed_files.extend(diff_names.stdout.strip().split("\n"))

    staged_names = subprocess.run(["git", "diff", "--cached", "--name-only"],
                                  cwd=project_root, capture_output=True, text=True, timeout=3)
    all_changed_files.extend(staged_names.stdout.strip().split("\n"))

    recent_files = subprocess.run([
        "find", ".", "-maxdepth", "4", "-type", "f",
        "-mmin", "-30", "!", "-path", "*/node_modules/*"
    ], cwd=project_root, capture_output=True, text=True, timeout=5, shell=True)

    return {"files": all_changed_files, "git_diff_stat": git_diff_content}
```

## How to apply here

Implemented in `.claude/hooks/stop.py`:
- Runs at session end via Stop hook
- Captures: `git diff --name-only HEAD`, `git diff --cached --name-only`
- Falls back to `find -mmin -30` for untracked directories
- Stores file list in session summary

## Original context

claude-brain's `stop.ts` hook captures file changes at session end as a workaround for the PostToolUse bug. This ensures all file modifications are recorded even when the Edit hook doesn't fire.
