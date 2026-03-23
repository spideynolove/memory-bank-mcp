---
name: xia-claude-cognitive-context-router
source: https://github.com/GMaN1911/claude-cognitive
extracted: 2026-03-24
---

# Context Router with Attention Dynamics — Xỉa from claude-cognitive

**Source**: [GMaN1911/claude-cognitive](https://github.com/GMaN1911/claude-cognitive)
**Extracted**: 2026-03-24
**Gap filled**: No intelligent context selection when working with large memory banks — all memories treated equally, leading to token waste and irrelevant context injection

## What this is

Attention-based file injection system with cognitive dynamics:
- **HOT** (>0.8): Full file injection - active development
- **WARM** (0.25-0.8): Headers only - background awareness
- **COLD** (<0.25): Evicted from context

Files decay when not mentioned, activate on keywords, and co-activate with related files.

## Why it fills A's gap

Memory Bank MCP has 19+ tools for storing memories but no intelligent mechanism to:
1. Prioritize which memories to inject based on current conversation
2. Decay irrelevant memories when context compacts
3. Boost related memories when a topic is mentioned
4. Track attention history for debugging

The Context Router adds a working memory layer on top of the persistent SQLite storage, providing 64-95% token savings while maintaining coherence.

## The pattern

```python
from pathlib import Path
from datetime import datetime
import json

PROJECT_STATE = Path(".claude/attn_state.json")
HISTORY_FILE = Path.home() / ".claude" / "attention_history.jsonl"

DECAY_RATES = {
    "systems/": 0.85,
    "modules/": 0.70,
    "integrations/": 0.80,
    "docs/": 0.75,
    "default": 0.70
}

HOT_THRESHOLD = 0.8
WARM_THRESHOLD = 0.25
KEYWORD_BOOST = 1.0
COACTIVATION_BOOST = 0.35

MAX_HOT_FILES = 4
MAX_WARM_FILES = 8
MAX_TOTAL_CHARS = 25000

def update_attention(state: dict, prompt: str) -> tuple:
    prompt_lower = prompt.lower()
    directly_activated = set()

    for path in state["scores"]:
        decay = get_decay_rate(path)
        state["scores"][path] *= decay

    for path, keywords in KEYWORDS.items():
        if any(kw in prompt_lower for kw in keywords):
            state["scores"][path] = KEYWORD_BOOST
            directly_activated.add(path)

    for activated_path in directly_activated:
        if activated_path in CO_ACTIVATION:
            for related_path in CO_ACTIVATION[activated_path]:
                if related_path in state["scores"]:
                    current = state["scores"][related_path]
                    state["scores"][related_path] = min(1.0, current + COACTIVATION_BOOST)

    return state, directly_activated
```

## How to apply here

**Integration point 1: New hook script**
Create `.claude/hooks/context_router.py` that:
- Loads memory metadata from SQLite (`database.py`)
- Maps memory content to keywords (use `trigger` field from Memory model)
- Maintains attention scores in `.claude/attn_state.json`
- Injects HOT memories as full content, WARM memories as summaries

**Integration point 2: Extend Memory model**
The Memory model already has `trigger` and `disclosure` fields — repurpose them:
- `trigger` → keywords for activation (comma-separated)
- `disclosure` → "when to recall" maps to attention dynamics

**Integration point 3: Hook registration**
Add to `settings.json`:
```json
{
  "hooks": {
    "UserPromptSubmit": [
      ".claude/hooks/user_prompt_submit.py",
      ".claude/hooks/context_router.py"
    ]
  }
}
```

**Integration point 4: Query interface**
Add MCP tool `get_attention_state()` returning current HOT/WARM/COLD classification for debugging.

**Integration point 5: Memory retrieval enhancement**
Modify `get_memory()` in `database.py` to accept attention filtering:
```python
def get_memories_by_tier(min_attention: float = 0.0) -> list:
    c.execute("""
        SELECT id, content, trigger, priority, disclosure
        FROM memories
        WHERE attention_score >= ?
        ORDER BY attention_score DESC
    """, (min_attention,))
```

**Seam detection summary:**
| Component | A (current) | B (context router) | Integration |
|-----------|-------------|-------------------|-------------|
| Storage | SQLite `memories` table | JSON state file | Hybrid: SQLite for persistence, JSON for transient attention |
| Keywords | `trigger` field (string) | `KEYWORDS` dict | Extract from `trigger` field, build in-memory mapping |
| Decay | None | `DECAY_RATES` per category | Use `priority` field as decay proxy (0=slow decay, 2+=fast decay) |
| Hook | `user_prompt_submit.py` | `context-router-v2.py` | Chain both hooks in UserPromptSubmit |
| History | None | `attention_history.jsonl` | Add new table `attention_history` to SQLite |

## Original context

claude-cognitive uses this for:
- Fractal documentation (`systems/`, `modules/`, `integrations/` directories)
- Multi-instance coordination (8+ concurrent Claude Code instances)
- Production: 1M+ lines across 3,200+ Python modules
- Token savings: 79% cold start, 70% warm context

Memory Bank MCP would use it for:
- Prioritizing which memories to inject during context compaction
- Co-activating related memories when a topic is mentioned
- Tracking memory attention history for learning what gets referenced
- Reducing token waste on low-priority or stale memories
