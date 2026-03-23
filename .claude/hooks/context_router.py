import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Tuple

PROJECT_ROOT = Path(__file__).parent.parent.parent
STATE_FILE = PROJECT_ROOT / ".claude" / "attn_state.json"
HISTORY_FILE = Path.home() / ".claude" / "attention_history.jsonl"

HOT_THRESHOLD = 0.8
WARM_THRESHOLD = 0.25
KEYWORD_BOOST = 1.0
COACTIVATION_BOOST = 0.35

MAX_HOT_MEMORIES = 4
MAX_WARM_MEMORIES = 8
MAX_TOTAL_CHARS = 25000

DECAY_BY_PRIORITY = {
    0: 0.90,
    1: 0.85,
    2: 0.70,
    3: 0.60,
}


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except (json.JSONDecodeError, Exception):
            pass
    return {
        "scores": {},
        "turn_count": 0,
        "last_update": datetime.now().isoformat(),
    }


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    state["last_update"] = datetime.now().isoformat()
    STATE_FILE.write_text(json.dumps(state, indent=2))


def load_memories_for_attention() -> List[dict]:
    db_path = PROJECT_ROOT / "memory.db"
    if not db_path.exists():
        return []

    import sqlite3

    memories = []
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, content, trigger, priority, disclosure, memory_type
            FROM memories
            ORDER BY timestamp DESC
        """)
        for row in cursor.fetchall():
            memories.append({
                "id": row[0],
                "content": row[1],
                "trigger": row[2] or "",
                "priority": row[3] or 2,
                "disclosure": row[4] or "",
                "memory_type": row[5] or "general",
            })
    return memories


def get_decay_rate(priority: int) -> float:
    return DECAY_BY_PRIORITY.get(priority, DECAY_BY_PRIORITY[2])


def extract_keywords(trigger: str) -> List[str]:
    if not trigger:
        return []
    keywords = []
    for part in trigger.split(","):
        part = part.strip().lower()
        if part:
            keywords.append(part)
    return keywords


def build_keyword_index(memories: List[dict]) -> Dict[str, List[str]]:
    index = {}
    for memory in memories:
        keywords = extract_keywords(memory["trigger"])
        for kw in keywords:
            if kw not in index:
                index[kw] = []
            index[kw].append(memory["id"])
    return index


def find_co_activation(memories: List[dict]) -> Dict[str, List[str]]:
    co_activation = {}
    for memory in memories:
        disclosure = memory.get("disclosure", "")
        if "when" in disclosure.lower() and memory["id"] not in co_activation:
            similar = [
                m["id"] for m in memories
                if m["id"] != memory["id"]
                and m.get("memory_type") == memory.get("memory_type")
            ]
            if similar:
                co_activation[memory["id"]] = similar[:3]
    return co_activation


def update_attention(state: dict, prompt: str, keyword_index: Dict[str, List[str]], co_activation: Dict[str, List[str]]) -> Tuple[dict, Set[str]]:
    prompt_lower = prompt.lower()
    directly_activated: Set[str] = set()

    for memory_id in state["scores"]:
        priority = state["scores"].get("priority", 2)
        decay = get_decay_rate(priority)
        state["scores"][memory_id]["score"] *= decay

    for keyword, memory_ids in keyword_index.items():
        if keyword in prompt_lower:
            for memory_id in memory_ids:
                state["scores"][memory_id]["score"] = KEYWORD_BOOST
                directly_activated.add(memory_id)

    for activated_id in directly_activated:
        if activated_id in co_activation:
            for related_id in co_activation[activated_id]:
                if related_id in state["scores"]:
                    current = state["scores"][related_id]["score"]
                    state["scores"][related_id]["score"] = min(1.0, current + COACTIVATION_BOOST)

    for memory_id, data in state["scores"].items():
        priority = data.get("priority", 2)
        if priority == 0 and data["score"] < WARM_THRESHOLD + 0.1:
            state["scores"][memory_id]["score"] = WARM_THRESHOLD + 0.1

    state["turn_count"] = state.get("turn_count", 0) + 1
    return state, directly_activated


def get_tier(score: float) -> str:
    if score >= HOT_THRESHOLD:
        return "HOT"
    elif score >= WARM_THRESHOLD:
        return "WARM"
    return "COLD"


def build_context_output(state: dict, memories: List[dict]) -> Tuple[str, dict]:
    memory_by_id = {m["id"]: m for m in memories}

    sorted_items = sorted(
        state["scores"].items(),
        key=lambda x: x[1]["score"],
        reverse=True
    )

    hot_blocks = []
    warm_blocks = []
    stats = {"hot": 0, "warm": 0, "cold": 0}
    total_chars = 0

    for memory_id, data in sorted_items:
        score = data["score"]
        memory = memory_by_id.get(memory_id)
        if not memory:
            continue

        tier = get_tier(score)

        if tier == "HOT" and stats["hot"] < MAX_HOT_MEMORIES:
            content = memory["content"]
            if total_chars + len(content) < MAX_TOTAL_CHARS:
                header = f"🔥 HOT [{memory['memory_type']}] (score: {score:.2f})"
                hot_blocks.append(f"━━━ {header} ━━━\n{content}")
                total_chars += len(content)
                stats["hot"] += 1
            else:
                tier = "WARM"

        if tier == "WARM" and stats["warm"] < MAX_WARM_MEMORIES:
            summary = memory["content"][:300]
            if total_chars + len(summary) < MAX_TOTAL_CHARS:
                header = f"🌡️ WARM [{memory['memory_type']}] (score: {score:.2f})"
                warm_blocks.append(f"━━━ {header} ━━━\n{summary}...")
                total_chars += len(summary)
                stats["warm"] += 1
            else:
                stats["cold"] += 1
        elif tier == "COLD":
            stats["cold"] += 1

    output_parts = []
    output_parts.append(f"╔══ ATTENTION STATE [Turn {state['turn_count']}] ══╗")
    output_parts.append(f"║ 🔥 Hot: {stats['hot']} │ 🌡️ Warm: {stats['warm']} │ ❄️ Cold: {stats['cold']} ║")
    output_parts.append(f"║ Total chars: {total_chars:,} / {MAX_TOTAL_CHARS:,} ║")
    output_parts.append("╚" + "═" * 38 + "╝")

    output_parts.extend(hot_blocks)
    output_parts.extend(warm_blocks)

    return "\n\n".join(output_parts), stats


def append_history(state: dict, prev_state: dict, activated: Set[str], prompt: str, stats: dict):
    entry = {
        "turn": state["turn_count"],
        "timestamp": datetime.now().isoformat(),
        "prompt_preview": prompt[:100],
        "activated": sorted(list(activated)),
        "hot": sorted([k for k, v in state["scores"].items() if get_tier(v["score"]) == "HOT"]),
        "warm": sorted([k for k, v in state["scores"].items() if get_tier(v["score"]) == "WARM"]),
        "cold_count": stats["cold"],
        "total_chars": len(stats.get("output", "")),
    }

    try:
        if not HISTORY_FILE.exists():
            HISTORY_FILE.parent.mkdir(exist_ok=True)
            HISTORY_FILE.touch()
        with open(HISTORY_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


def main():
    try:
        input_data = json.loads(sys.stdin.read())
        prompt = input_data.get("prompt", "")
    except (json.JSONDecodeError, Exception):
        prompt = sys.stdin.read() if sys.stdin else ""

    if not prompt.strip():
        return

    memories = load_memories_for_attention()
    if not memories:
        return

    state_file = load_state()
    prev_state = json.loads(json.dumps(state_file))

    keyword_index = build_keyword_index(memories)
    co_activation = find_co_activation(memories)

    for memory in memories:
        memory_id = memory["id"]
        if memory_id not in state_file["scores"]:
            state_file["scores"][memory_id] = {
                "score": 0.0,
                "priority": memory["priority"],
            }

    state, activated = update_attention(state_file, prompt, keyword_index, co_activation)

    output, stats = build_context_output(state, memories)
    stats["output"] = output

    append_history(state, prev_state, activated, prompt, stats)

    save_state(state)

    if stats["hot"] > 0 or stats["warm"] > 0:
        print(output)


if __name__ == "__main__":
    main()
