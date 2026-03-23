import json
import re
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any


PROJECT_ROOT = Path(__file__).parent.parent.parent
LEARNINGS_DIR = PROJECT_ROOT / ".claude" / "learnings"
CHECKPOINT_DIR = PROJECT_ROOT / ".claude" / "checkpoints"
DEDUP_CACHE_FILE = PROJECT_ROOT / ".claude" / "checkpoints" / "dedup_cache.json"
LEARNINGS_DIR.mkdir(parents=True, exist_ok=True)
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(Path(__file__).parent))
from compression import compress_tool_output, get_compression_stats

CHECKPOINT_INTERVAL = 20
MESSAGE_COUNT_FILE = CHECKPOINT_DIR / "message_count.json"
DEDUP_WINDOW_MS = 60000


def load_dedup_cache() -> Dict[str, int]:
    try:
        if DEDUP_CACHE_FILE.exists():
            return json.loads(DEDUP_CACHE_FILE.read_text())
    except Exception:
        pass
    return {}


def save_dedup_cache(cache: Dict[str, int]) -> None:
    try:
        DEDUP_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        DEDUP_CACHE_FILE.write_text(json.dumps(cache))
    except Exception:
        pass


def clean_dedup_cache(cache: Dict[str, int]) -> Dict[str, int]:
    now = int(datetime.now().timestamp() * 1000)
    cutoff = now - DEDUP_WINDOW_MS * 2
    return {k: v for k, v in cache.items() if v > cutoff}


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
    import hashlib
    return hashlib.md5(content.encode()[:500]).hexdigest()


CORRECTION_PATTERNS = [
    r"not\s+that",
    r"don't\s+do\s+that",
    r"wrong",
    r"incorrect",
    r"no,\s+not",
    r"actually\s+no",
    r"stop",
    r"don't",
    r"shouldn't",
    r"wouldn't",
    r"couldn't",
    r"can't\s+do",
    r"doesn't\s+work",
    r"failed",
    r"error",
    r"mistake",
    r"fix\s+this",
    r"correct\s+that",
    r"undo",
    r"revert"
]

POSITIVITY_PATTERNS = [
    r"correct",
    r"right",
    r"perfect",
    r"good",
    r"exactly",
    r"yes,\s+that",
    r"works\s+well",
    r"success",
    r"great",
    r"love\s+it"
]

EXPLICIT_PATTERNS = [
    r"remember\s+that",
    r"don't\s+forget",
    r"keep\s+in\s+mind",
    r"note\s+that",
    r"important",
    r"always",
    r"never"
]

GUARDRAIL_PATTERNS = [
    r"don't\s+ever",
    r"never\s+do",
    r"avoid",
    r"stay\s+away\s+from",
    r"forbidden",
    r"not\s+allowed"
]


def get_message_count() -> int:
    try:
        if MESSAGE_COUNT_FILE.exists():
            data = json.loads(MESSAGE_COUNT_FILE.read_text())
            return data.get("count", 0)
        return 0
    except Exception:
        return 0


def increment_message_count() -> int:
    count = get_message_count()
    new_count = count + 1
    MESSAGE_COUNT_FILE.write_text(json.dumps({"count": new_count}))
    return new_count


def should_checkpoint() -> bool:
    count = get_message_count()
    return (count + 1) % CHECKPOINT_INTERVAL == 0


def save_checkpoint(records: list) -> dict:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    checkpoint_file = CHECKPOINT_DIR / f"checkpoint_{timestamp}.jsonl"

    summary = {
        "timestamp": datetime.now().isoformat(),
        "message_count": get_message_count() + 1,
        "records_count": len(records),
        "last_few_records": records[-5:] if len(records) >= 5 else records
    }

    with open(checkpoint_file, "w") as f:
        f.write(json.dumps(summary) + "\n")

    return {
        "checkpoint_file": str(checkpoint_file),
        "message_count": summary["message_count"],
        "records_saved": summary["records_count"]
    }


def read_transcript():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return []
        lines = [l for l in raw.strip().splitlines() if l.strip()]
        records = []
        for line in lines:
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return records
    except Exception:
        return []


def detect_correction_patterns(content: str) -> list:
    matches = []
    content_lower = content.lower()

    for pattern in CORRECTION_PATTERNS:
        if re.search(pattern, content_lower):
            matches.append(("correction", pattern))

    for pattern in POSITIVITY_PATTERNS:
        if re.search(pattern, content_lower):
            matches.append(("positive", pattern))

    for pattern in EXPLICIT_PATTERNS:
        if re.search(pattern, content_lower):
            matches.append(("explicit", pattern))

    for pattern in GUARDRAIL_PATTERNS:
        if re.search(pattern, content_lower):
            matches.append(("guardrail", pattern))

    return matches


def extract_context_around_correction(records: list, correction_index: int, window: int = 3) -> dict:
    start_idx = max(0, correction_index - window)
    end_idx = min(len(records), correction_index + window + 1)

    context_records = records[start_idx:end_idx]

    context = {
        "before": [],
        "correction": records[correction_index],
        "after": []
    }

    for i, record in enumerate(context_records):
        if start_idx + i < correction_index:
            context["before"].append(record)
        elif start_idx + i > correction_index:
            context["after"].append(record)

    return context


def extract_tool_errors(records: list) -> list:
    errors = []

    for record in records:
        content = record.get("content") or (record.get("message") or {}).get("content")

        if not content:
            continue

        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    tool_name = block.get("name", "unknown")

                    if "result" in block:
                        result = block.get("result", {})
                        if isinstance(result, dict):
                            if result.get("isError") or result.get("error"):
                                errors.append({
                                    "tool": tool_name,
                                    "error": result.get("error") or result.get("content", "Unknown error"),
                                    "timestamp": record.get("timestamp", datetime.now().isoformat())
                                })
                        elif isinstance(result, str) and ("error" in result.lower() or "failed" in result.lower()):
                            errors.append({
                                "tool": tool_name,
                                "error": result[:500],
                                "timestamp": record.get("timestamp", datetime.now().isoformat())
                            })

    return errors


def extract_learning_event(records: list, correction_index: int) -> dict:
    correction_record = records[correction_index]
    content = correction_record.get("content") or (correction_record.get("message") or {}).get("content", "")

    if isinstance(content, list):
        content_text = ""
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                content_text += block.get("text", "")
        content = content_text

    patterns = detect_correction_patterns(content)
    context = extract_context_around_correction(records, correction_index)

    memory_type = "correction"
    for ptype, _ in patterns:
        if ptype in ["positive", "explicit", "guardrail"]:
            memory_type = ptype
            break

    truncated_content = content[:1000] if len(content) > 1000 else content

    return {
        "timestamp": datetime.now().isoformat(),
        "content": truncated_content,
        "patterns_detected": patterns,
        "memory_type": memory_type,
        "context": context,
        "priority": 1 if memory_type in ["correction", "guardrail"] else 2,
        "trigger": "user_correction_event"
    }


def queue_learning(event: dict):
    queue_file = LEARNINGS_DIR / "learnings_queue.jsonl"

    queue_entry = {
        "id": f"learning_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
        "event": event,
        "status": "pending",
        "queued_at": datetime.now().isoformat()
    }

    with open(queue_file, "a") as f:
        f.write(json.dumps(queue_entry) + "\n")


def process_transcript(records: list, dedup_cache: Dict[str, int]) -> dict:
    corrections_found = []
    tool_errors = []
    compress_stats = {"compressed": 0, "original_size": 0, "saved": 0}

    for i, record in enumerate(records):
        role = record.get("role") or (record.get("message") or {}).get("role")

        if role == "user":
            content = record.get("content") or (record.get("message") or {}).get("content", "")

            if isinstance(content, list):
                content_text = ""
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        content_text += block.get("text", "")
                content = content_text

            content_hash_val = content_hash(content)

            if is_duplicate(content_hash_val, dedup_cache):
                continue

            patterns = detect_correction_patterns(content)

            if patterns:
                learning_event = extract_learning_event(records, i)
                queue_learning(learning_event)
                mark_observed(content_hash_val, dedup_cache)
                corrections_found.append({
                    "index": i,
                    "patterns": patterns,
                    "type": learning_event["memory_type"]
                })

        elif role == "assistant":
            content = record.get("content") or (record.get("message") or {}).get("content", "")

            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_use":
                        tool_name = block.get("name", "")
                        tool_input = block.get("input", {})
                        result = block.get("result", {})

                        if tool_name in ("Read", "Bash", "Grep", "Glob", "Edit", "Write"):
                            result_content = result.get("content", "") if isinstance(result, dict) else str(result)

                            if result_content and len(result_content) > 3000:
                                compression_result = compress_tool_output(tool_name, tool_input, result_content)
                                if compression_result["was_compressed"]:
                                    compress_stats["compressed"] += 1
                                    compress_stats["original_size"] += compression_result["original_size"]
                                    compress_stats["saved"] += compression_result["original_size"] - len(compression_result["compressed"])

    tool_errors = extract_tool_errors(records)

    if tool_errors:
        errors_file = LEARNINGS_DIR / "tool_errors.jsonl"
        for error in tool_errors:
            error_entry = {
                "id": f"error_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
                "error": error,
                "status": "pending",
                "queued_at": datetime.now().isoformat()
            }
            with open(errors_file, "a") as f:
                f.write(json.dumps(error_entry) + "\n")

    return {
        "corrections_found": len(corrections_found),
        "tool_errors_found": len(tool_errors),
        "learning_events_queued": len(corrections_found),
        "details": corrections_found,
        "compression": compress_stats if compress_stats["compressed"] > 0 else None
    }


def main():
    records = read_transcript()

    if not records:
        print(json.dumps({"status": "no_records"}))
        return

    current_count = increment_message_count()
    is_checkpoint = current_count % CHECKPOINT_INTERVAL == 0

    dedup_cache = load_dedup_cache()
    dedup_cache = clean_dedup_cache(dedup_cache)

    result = process_transcript(records, dedup_cache)

    save_dedup_cache(dedup_cache)

    checkpoint_info = None
    if is_checkpoint:
        checkpoint_info = save_checkpoint(records)

    response = {
        "status": "success",
        "hook": "user_prompt_submit",
        "timestamp": datetime.now().isoformat(),
        "message_count": current_count,
        **result
    }

    if checkpoint_info:
        response["checkpoint"] = checkpoint_info

    print(json.dumps(response))


if __name__ == "__main__":
    main()
