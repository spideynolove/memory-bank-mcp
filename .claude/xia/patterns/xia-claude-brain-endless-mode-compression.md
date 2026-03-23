---
name: xia-claude-brain-endless-mode-compression
source: https://github.com/memvid/claude-brain
extracted: 2026-03-24
---

# Endless Mode Compression — Xỉa from claude-brain

**Source**: [memvid/claude-brain](https://github.com/memvid/claude-brain)
**Extracted**: 2026-03-24
**Gap filled**: Token waste on verbose tool outputs (Read, Bash, Grep, etc.)

## What this is

A compression system that reduces large tool outputs to ~500 tokens while preserving key information. Compresses outputs by tool type:
- **Read**: Extracts imports, exports, functions, classes, errors + first/last lines
- **Bash**: Extracts errors, success indicators, output stats + context
- **Grep**: Summarizes matches, files found, top results
- **Glob**: Groups by directory, shows top dirs and sample files
- **Edit/Write**: Brief summary + limited output

## Why it fills A's gap

Memory Bank MCP stores full tool outputs in memories, wasting tokens on verbose content that could be compressed 20x while retaining the key information needed for future recall.

## The pattern

```python
TARGET_COMPRESSED_SIZE = 2000
COMPRESSION_THRESHOLD = 3000

def compress_tool_output(tool_name: str, tool_input: Dict[str, Any], output: str) -> Dict[str, Any]:
    original_size = len(output)
    if original_size <= COMPRESSION_THRESHOLD:
        return {"compressed": output, "was_compressed": False, "original_size": original_size}

    compressed = _compress_by_tool_type(tool_name, tool_input, output)
    return {
        "compressed": _truncate_to_target(compressed),
        "was_compressed": True,
        "original_size": original_size
    }

def _compress_file_read(tool_input: Dict[str, Any], output: str) -> str:
    lines = output.split("\n")
    parts = [f"File: {file_name} ({len(lines)} lines)"]
    parts.extend([
        f"\nImports: {', '.join(_extract_imports(output)[:10])}",
        f"\nExports: {', '.join(_extract_exports(output)[:10])}",
        f"\nFunctions: {', '.join(_extract_function_signatures(output)[:10])}",
        f"\nClasses: {', '.join(_extract_class_names(output))}",
        "\n--- First 10 lines ---", *lines[:10],
        "\n--- Last 5 lines ---", *lines[-5:]
    ])
    return "".join(parts)
```

## How to apply here

Implemented in `.claude/hooks/compression.py` with tool-specific compressors:
- Use in `user_prompt_submit.py` when processing tool outputs
- Compression stats tracked: `compressed`, `original_size`, `saved`
- Applied to: Read, Bash, Grep, Glob, Edit, Write tools
- Threshold: 3000 chars → Target: 2000 chars

## Original context

claude-brain uses compression in `post-tool-use.ts` hook to capture observations. The compression enables storing 20x more context before hitting token limits, as each tool use that returns large output gets compressed to ~500 tokens while keeping the essential information.
