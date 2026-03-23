---
name: xia-claude-brain-in-memory-deduplication
source: https://github.com/memvid/claude-brain
extracted: 2026-03-24
---

# In-Memory Deduplication — Xỉa from claude-brain

**Source**: [memvid/claude-brain](https://github.com/memvid/claude-brain)
**Extracted**: 2026-03-24
**Gap filled**: Duplicate observations spamming memory

## What this is

A time-based deduplication cache that prevents storing the same observation within a configurable window (default: 60 seconds). Uses MD5 content hashing for fast lookup and persists cache to disk for session continuity.

## Why it fills A's gap

Memory Bank MCP's user_prompt_submit hook could queue duplicate learning events if the same correction pattern appears multiple times within a short window, wasting storage and creating noisy memories.

## The pattern

```python
DEDUP_WINDOW_MS = 60000
DEDUP_CACHE_FILE = CHECKPOINT_DIR / "dedup_cache.json"

def load_dedup_cache() -> Dict[str, int]:
    if DEDUP_CACHE_FILE.exists():
        return json.loads(DEDUP_CACHE_FILE.read_text())
    return {}

def is_duplicate(content_hash: str, cache: Dict[str, int]) -> bool:
    if content_hash not in cache:
        return False
    now = int(datetime.now().timestamp() * 1000)
    return now - cache[content_hash] < DEDUP_WINDOW_MS

def mark_observed(content_hash: str, cache: Dict[str, int]) -> None:
    cache[content_hash] = int(datetime.now().timestamp() * 1000)
    if len(cache) > 100:
        clean_dedup_cache(cache)

def content_hash(content: str) -> str:
    return hashlib.md5(content.encode()[:500]).hexdigest()
```

## How to apply here

Implemented in `.claude/hooks/user_prompt_submit.py`:
- Cache stored at `.claude/checkpoints/dedup_cache.json`
- Hashes content (first 500 chars) with MD5
- Cleans old entries (> 2x window) on each mark
- Persists to disk after processing

## Original context

claude-brain's `post-tool-use.ts` uses an in-memory Map to track recent observations by `tool:input` hash, preventing duplicate captures within 1-minute windows.
